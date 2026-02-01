"""Video downloader using yt-dlp."""

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from yt2audi.core.cache import MetadataCache
from yt2audi.exceptions import DownloadError
from yt2audi.models.profile import DownloadConfig, Profile
from yt2audi.utils import get_temp_dir, is_valid_url, is_youtube_url, sanitize_filename

logger = structlog.get_logger(__name__)


class Downloader:
    """YouTube video downloader using yt-dlp."""

    def __init__(self, profile: Profile) -> None:
        """Initialize downloader.

        Args:
            profile: Download profile configuration
        """
        self.profile = profile
        self.download_config = profile.download
        self.temp_dir = get_temp_dir()
        self.cache = MetadataCache()

        logger.info("downloader_initialized", profile=profile.profile.name)

    async def extract_info_async(self, url: str) -> dict[str, Any]:
        """Extract video info asynchronously.
        
        Args:
            url: YouTube URL
            
        Returns:
            yt-dlp info dictionary
        """
        return await asyncio.to_thread(self.extract_info, url)

    def extract_info(self, url: str) -> dict[str, Any]:
        """Extract video info.
        
        Args:
            url: YouTube URL
            
        Returns:
            yt-dlp info dictionary
            
        Raises:
            ValueError: If URL is invalid
            DownloadError: If extraction fails
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
            
        # Check cache
        cached = self.cache.get(url)
        if cached:
            return cached
            
        ydl_opts = self._get_ydl_opts("dummy", ignore_archive=True)
        # Faster extraction
        ydl_opts.update({
            "skip_download": True,
            "extract_flat": "in_playlist", # Don't expand playlists fully on simple check
        })
        
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise DownloadError(f"Failed to extract info for {url}")
                
                # Cache result
                self.cache.set(url, info)
                return info
                
        except Exception as e:
            logger.error("extract_info_failed", url=url, error=str(e))
            raise DownloadError(f"Failed to extract info for {url}: {e}") from e

    def _build_optimized_format_string(self) -> str:
        """Build yt-dlp format string optimized for profile's target output.

        This matches download quality to the conversion target to avoid downloading
        unnecessarily large files (e.g., downloading 4K when converting to 720x540).

        Returns:
            Optimized yt-dlp format selector string
        """
        video_cfg = self.profile.video
        audio_cfg = self.profile.audio
        output_cfg = self.profile.output

        # Calculate target video constraints
        # Add 20% headroom to max_height to allow for some quality margin
        # But use standard resolutions (480p, 720p) as thresholds
        if video_cfg.max_height <= 480:
            max_download_height = 480
        elif video_cfg.max_height <= 540:
            max_download_height = 720  # 720p is standard, gives good quality for 540p output
        elif video_cfg.max_height <= 720:
            max_download_height = 720
        elif video_cfg.max_height <= 1080:
            max_download_height = 1080
        else:
            max_download_height = video_cfg.max_height

        # FPS: add small headroom (30fps is common even if we cap at 25)
        max_fps = min(video_cfg.max_fps + 5, 60)

        # Audio bitrate: match target (no need to download 320kbps if we output 128kbps)
        max_audio_bitrate = audio_cfg.bitrate_kbps

        # Codec preferences
        video_codec_pref = "vcodec^=avc" if video_cfg.codec == "h264" else f"vcodec^={video_cfg.codec}"
        audio_codec_pref = audio_cfg.codec  # aac, mp3, opus

        # Container preference
        container_pref = output_cfg.container  # mp4, mkv, etc.

        # Build format selector with quality constraints
        # Priority: resolution -> fps -> codec -> container
        format_parts = []

        # Video format selection
        video_filter = (
            f"bestvideo[height<={max_download_height}]"
            f"[fps<={max_fps}]"
            f"[{video_codec_pref}]"
            f"[ext={container_pref}]"
        )

        # Audio format selection
        audio_filter = (
            f"bestaudio[abr<={max_audio_bitrate}]"
            f"[acodec^={audio_codec_pref}]"
            f"[ext=m4a]"
        )

        # Build complete format string with fallbacks
        # 1. Best match: height + fps + codec + container constraints
        format_parts.append(f"{video_filter}+{audio_filter}")

        # 2. Relaxed codec constraint (just height + fps + container)
        format_parts.append(
            f"bestvideo[height<={max_download_height}][fps<={max_fps}][ext={container_pref}]+"
            f"bestaudio[abr<={max_audio_bitrate}][ext=m4a]"
        )

        # 3. Relaxed container (just height + fps)
        format_parts.append(
            f"bestvideo[height<={max_download_height}][fps<={max_fps}]+"
            f"bestaudio[abr<={max_audio_bitrate}]"
        )

        # 4. Just height constraint
        format_parts.append(
            f"bestvideo[height<={max_download_height}]+"
            f"bestaudio"
        )

        # 5. Best combined format with height constraint
        format_parts.append(f"best[height<={max_download_height}][ext={container_pref}]")

        # 6. Best combined format with container preference
        format_parts.append(f"best[ext={container_pref}]")

        # 7. Last resort: any best format
        format_parts.append("best")

        format_string = "/".join(format_parts)

        logger.info(
            "format_string_built",
            max_height=max_download_height,
            max_fps=max_fps,
            max_audio_bitrate=max_audio_bitrate,
            video_codec=video_cfg.codec,
            audio_codec=audio_cfg.codec,
            format_string=format_string[:200] + "..." if len(format_string) > 200 else format_string,
        )

        return format_string

    def _get_ydl_opts(
        self,
        output_template: str,
        progress_hook: Callable[[dict[str, Any]], None] | None = None,
        use_optimized_format: bool = True,
        ignore_archive: bool = False,
    ) -> dict[str, Any]:
        """Build yt-dlp options dictionary.

        Args:
            output_template: Output filename template
            progress_hook: Optional progress callback
            use_optimized_format: Use profile-optimized format string (default: True)
            ignore_archive: Ignore download archive (force download)

        Returns:
            yt-dlp options dictionary
        """
        from yt2audi.config import expand_path

        # Use optimized format string if requested or if format_preference is "auto"
        if use_optimized_format or self.download_config.format_preference == "auto":
            format_string = self._build_optimized_format_string()
        else:
            format_string = self.download_config.format_preference

        opts: dict[str, Any] = {
            "format": format_string,
            "outtmpl": str(output_template),
            "retries": self.download_config.retries,
            "fragment_retries": self.download_config.fragment_retries,
            "restrictfilenames": True,  # Avoid special characters
            "noplaylist": True,  # Override for single videos
            "ignoreerrors": False,
            "no_warnings": False,
            "quiet": False,
            "no_color": True,
            # Bypassing 403s and blocklists:
            # We avoid hardcoding specific clients (like android/ios) unless we have a PO Token
            # because yt-dlp might fail if those clients are enforced without a token.
            # "extractor_args": {
            #     "youtube": {
            #         "player_client": ["android", "ios", "web"],
            #         "player_skip": ["webpage", "configs", "js"],
            #     }
            # },
            # Use IPv4 as IPv6 often triggers blocks
            "source_address": "0.0.0.0",
            # Resume support
            "continuedl": True,
            "nopart": False,  # Use .part files for better resume detection
            "hls_prefer_native": True, # Better for long streams
            "concurrent_fragment_downloads": 3, # Speed up multi-part downloads
            # Thumbnail downloading
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegThumbnailsConvertor",
                    "format": "jpg",
                }
            ],
            # JS Runtime - helps with YouTube extraction scripts
            "js_runtimes": {"node": {}},
            "remote_components": ["ejs:github"],
        }
        
        # Authentication / PO Token
        if self.download_config.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.download_config.cookies_from_browser, None, None, None)
        
        if self.download_config.cookies_file:
            cookies_path = expand_path(self.download_config.cookies_file)
            if cookies_path.exists():
                opts["cookiefile"] = str(cookies_path)

        # PO Token handling
        if self.download_config.po_token:
            # If token provided, we can try to force clients or just pass the token
            # Note: PO Token format for args is usually "youtube:po_token=web+<token>" etc.
            # But the user asked to "adjust accordingly" based on the guide.
            # We will pass it for web+ios+android as safest bet if provided.
            token = self.download_config.po_token
            opts["extractor_args"] = {
                "youtube": {
                    "po_token": [
                        f"web+{token}", 
                        f"ios+{token}",
                        f"android+{token}"
                    ]
                }
            }

        # Download archive for resume functionality
        # We skip archive if explicitly requested (e.g. for temp downloads)
        if self.download_config.download_archive and not ignore_archive:
            archive_path = expand_path(self.download_config.download_archive)
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            opts["download_archive"] = str(archive_path)

        # Rate limiting
        if self.download_config.rate_limit_mbps:
            # Convert Mbps to bytes per second
            rate_limit_bytes = int(self.download_config.rate_limit_mbps * 1024 * 1024 / 8)
            opts["ratelimit"] = rate_limit_bytes

        # Progress hook
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]

        return opts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((DownloadError, ConnectionError)),
        reraise=True,
    )
    def download_video(
        self,
        url: str,
        output_dir: Path | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> tuple[Path, dict[str, Any]]:
        """Download a single video.

        Args:
            url: YouTube video URL
            output_dir: Output directory (defaults to temp_dir)
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (Path to downloaded video file, info_dict)

        Raises:
            DownloadError: If download fails
            ValueError: If URL is invalid
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")

        if not is_youtube_url(url):
            logger.warning("non_youtube_url", url=url)

        output_dir = output_dir or self.temp_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Output template
        output_template = output_dir / "%(title)s_%(id)s.%(ext)s"

        logger.info("download_started", url=url, output_dir=str(output_dir))

        try:
            import yt_dlp

            # Ignore archive for single video downloads to ensure we get the file
            # even if it was previously recorded but deleted.
            ydl_opts = self._get_ydl_opts(
                str(output_template), 
                progress_callback,
                ignore_archive=True
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise DownloadError(f"Could not extract video info from {url}")

                # Get expected filename
                filename = ydl.prepare_filename(info)
                output_path = Path(filename)

                # Download
                ydl.download([url])

                if not output_path.exists():
                    raise DownloadError(f"Download completed but file not found: {output_path}")

                logger.info(
                    "download_completed",
                    url=url,
                    path=str(output_path),
                    size_mb=output_path.stat().st_size / 1024 / 1024,
                )

                return output_path, info

        except yt_dlp.utils.DownloadError as e:
            logger.error("download_failed", url=url, error=str(e))
            raise DownloadError(f"Failed to download {url}: {e}") from e
        except Exception as e:
            logger.error("download_error", url=url, error=str(e))
            raise DownloadError(f"Unexpected error downloading {url}: {e}") from e

    async def download_video_async(
        self,
        url: str,
        output_dir: Path | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> tuple[Path, dict[str, Any]]:
        """Download a single video asynchronously.

        Args:
            url: YouTube video URL
            output_dir: Output directory
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (Path to downloaded video file, info_dict)
        """
        return await asyncio.to_thread(
            self.download_video, url, output_dir, progress_callback
        )

    async def download_batch_async(
        self,
        urls: list[str],
        output_dir: Path | None = None,
        progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
        max_concurrent: int = 3,
    ) -> list[Path]:
        """Download multiple videos concurrently.

        Args:
            urls: List of YouTube URLs
            output_dir: Output directory
            progress_callback: Optional callback(url, progress_dict)
            max_concurrent: Maximum number of concurrent downloads

        Returns:
            List of paths to downloaded videos
        """
        output_dir = output_dir or self.temp_dir
        semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info("async_batch_download_started", url_count=len(urls), concurrent=max_concurrent)

        async def _download_task(url: str) -> Path | None:
            async with semaphore:
                try:
                    # Wrap progress callback to include URL
                    def _progress_hook(d: dict[str, Any]) -> None:
                        if progress_callback:
                            progress_callback(url, d)

                    return await self.download_video_async(url, output_dir, _progress_hook)
                except Exception as e:
                    logger.error("async_batch_item_failed", url=url, error=str(e))
                    return None

        # Create tasks for all URLs
        tasks = [_download_task(url) for url in urls]
        
        # Run tasks and wait for completion
        results = await asyncio.gather(*tasks)
        
        # Filter out failures
        successful_results = [r for r in results if r is not None]
        # successful_results is a list of (Path, dict)

        logger.info(
            "async_batch_download_completed",
            total=len(urls),
            succeeded=len(successful_results),
            failed=len(urls) - len(successful_results),
        )

        return successful_results

    def download_batch(
        self,
        urls: list[str],
        output_dir: Path | None = None,
        progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
        use_async: bool = False,
        max_concurrent: int = 3,
    ) -> list[Path]:
        """Download multiple videos.

        Args:
            urls: List of YouTube URLs
            output_dir: Output directory
            progress_callback: Optional callback(url, progress_dict)
            use_async: Whether to use concurrent downloads
            max_concurrent: Max concurrent downloads if use_async is True

        Returns:
            List of paths to downloaded videos
        """
        if use_async:
            try:
                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(
                        self.download_batch_async(urls, output_dir, progress_callback, max_concurrent)
                    )
                except RuntimeError:
                    # If loop is already running, we can't use run_until_complete
                    # This shouldn't happen in the CLI as it's currently synchronous
                    logger.warning("async_batch_loop_running_trying_fallback")
                    pass
            except Exception as e:
                logger.warning("async_batch_failed_falling_back_to_sync", error=str(e))
                # Fallback to sync

        output_dir = output_dir or self.temp_dir
        results: list[tuple[Path, dict[str, Any]]] = []

        logger.info("batch_download_started", url_count=len(urls))

        for i, url in enumerate(urls, 1):
            logger.info("batch_progress", current=i, total=len(urls), url=url)

            try:
                # Wrap progress callback to include URL
                def _progress_hook(d: dict[str, Any]) -> None:
                    if progress_callback:
                        progress_callback(url, d)

                path, info = self.download_video(url, output_dir, _progress_hook)
                results.append((path, info))

            except Exception as e:
                logger.error("batch_item_failed", url=url, error=str(e))
                # Continue with next video

        logger.info(
            "batch_download_completed",
            total=len(urls),
            succeeded=len(results),
            failed=len(urls) - len(results),
        )

        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((DownloadError, ConnectionError)),
        reraise=True,
    )
    def download_playlist(
        self,
        playlist_url: str,
        output_dir: Path | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[Path]:
        """Download entire YouTube playlist.

        Args:
            playlist_url: YouTube playlist URL
            output_dir: Output directory
            progress_callback: Optional callback for progress updates

        Returns:
            List of paths to downloaded videos

        Raises:
            DownloadError: If playlist download fails
        """
        if not is_valid_url(playlist_url):
            raise ValueError(f"Invalid URL: {playlist_url}")

        output_dir = output_dir or self.temp_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_template = output_dir / "%(playlist_index)s_%(title)s_%(id)s.%(ext)s"

        logger.info("playlist_download_started", url=playlist_url)

        try:
            import yt_dlp

            ydl_opts = self._get_ydl_opts(str(output_template), progress_callback)

            # Override for playlist
            ydl_opts["noplaylist"] = False
            ydl_opts["playliststart"] = self.download_config.playlist_start
            if self.download_config.playlist_end:
                ydl_opts["playlistend"] = self.download_config.playlist_end
            if self.download_config.playlist_reverse:
                ydl_opts["playlist_reverse"] = True

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract playlist info
                info = ydl.extract_info(playlist_url, download=False)
                if not info:
                    raise DownloadError(f"Could not extract playlist info from {playlist_url}")

                # Get video count
                entries = info.get("entries", [])
                video_count = len(entries)
                logger.info("playlist_info", url=playlist_url, video_count=video_count)

                # Download playlist
                ydl.download([playlist_url])

                # Find downloaded files
                downloaded_files = sorted(output_dir.glob("*"))
                downloaded_videos = [f for f in downloaded_files if f.suffix in [".mp4", ".mkv", ".webm"]]

                logger.info(
                    "playlist_download_completed",
                    url=playlist_url,
                    expected=video_count,
                    downloaded=len(downloaded_videos),
                )

                return downloaded_videos

        except yt_dlp.utils.DownloadError as e:
            logger.error("playlist_download_failed", url=playlist_url, error=str(e))
            raise DownloadError(f"Failed to download playlist {playlist_url}: {e}") from e
        except Exception as e:
            logger.error("playlist_error", url=playlist_url, error=str(e))
            raise DownloadError(f"Unexpected error downloading playlist {playlist_url}: {e}") from e

    async def get_playlist_urls_async(self, playlist_url: str) -> list[str]:
        """Extract video URLs from a playlist asynchronously.

        Args:
            playlist_url: YouTube playlist URL

        Returns:
            List of video URLs
        """
        return await asyncio.to_thread(self.get_playlist_urls, playlist_url)

    def get_playlist_urls(self, playlist_url: str) -> list[str]:
        """Extract video URLs from a playlist.

        Args:
            playlist_url: YouTube playlist URL

        Returns:
            List of video URLs
        """
        import yt_dlp

        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "playliststart": self.download_config.playlist_start,
            "playlistend": self.download_config.playlist_end,
            "playlist_reverse": self.download_config.playlist_reverse,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if not info or "entries" not in info:
                    return []

                return [
                    f"https://www.youtube.com/watch?v={entry['id']}"
                    for entry in info["entries"]
                    if entry.get("id")
                ]
        except Exception as e:
            logger.error("playlist_extraction_failed", url=playlist_url, error=str(e))
            return []

    def extract_info(self, url: str, download: bool = False) -> dict[str, Any]:
        """Extract video information without downloading.

        Args:
            url: YouTube video URL
            download: Whether to download the video

        Returns:
            Dictionary with video metadata

        Raises:
            DownloadError: If info extraction fails
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")

        logger.info("extracting_video_info", url=url)

        # Try cache first
        cached_info = self.cache.get(url)
        if cached_info:
            return cached_info

        try:
            import yt_dlp

            ydl_opts = {"quiet": True, "no_warnings": True}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise DownloadError(f"Could not extract info from {url}")

                # Cache the result
                self.cache.set(url, info)
                return info

        except Exception as e:
            logger.error("info_extraction_failed", url=url, error=str(e))
            raise DownloadError(f"Failed to extract info from {url}: {e}") from e
