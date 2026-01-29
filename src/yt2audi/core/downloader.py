"""Video downloader using yt-dlp."""

from pathlib import Path
from typing import Any, Callable

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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

        logger.info("downloader_initialized", profile=profile.profile.name)

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
    ) -> dict[str, Any]:
        """Build yt-dlp options dictionary.

        Args:
            output_template: Output filename template
            progress_hook: Optional progress callback
            use_optimized_format: Use profile-optimized format string (default: True)

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
        }

        # Download archive for resume functionality
        if self.download_config.download_archive:
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
    ) -> Path:
        """Download a single video.

        Args:
            url: YouTube video URL
            output_dir: Output directory (defaults to temp_dir)
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded video file

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

            ydl_opts = self._get_ydl_opts(str(output_template), progress_callback)

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

                return output_path

        except yt_dlp.utils.DownloadError as e:
            logger.error("download_failed", url=url, error=str(e))
            raise DownloadError(f"Failed to download {url}: {e}") from e
        except Exception as e:
            logger.error("download_error", url=url, error=str(e))
            raise DownloadError(f"Unexpected error downloading {url}: {e}") from e

    def download_batch(
        self,
        urls: list[str],
        output_dir: Path | None = None,
        progress_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> list[Path]:
        """Download multiple videos sequentially.

        Args:
            urls: List of YouTube URLs
            output_dir: Output directory
            progress_callback: Optional callback(url, progress_dict)

        Returns:
            List of paths to downloaded videos

        Note:
            Failed downloads are logged but don't stop the batch.
            Check return list length vs input list length to detect failures.
        """
        output_dir = output_dir or self.temp_dir
        downloaded_paths: list[Path] = []

        logger.info("batch_download_started", url_count=len(urls))

        for i, url in enumerate(urls, 1):
            logger.info("batch_progress", current=i, total=len(urls), url=url)

            try:
                # Wrap progress callback to include URL
                def _progress_hook(d: dict[str, Any]) -> None:
                    if progress_callback:
                        progress_callback(url, d)

                path = self.download_video(url, output_dir, _progress_hook)
                downloaded_paths.append(path)

            except Exception as e:
                logger.error("batch_item_failed", url=url, error=str(e))
                # Continue with next video

        logger.info(
            "batch_download_completed",
            total=len(urls),
            succeeded=len(downloaded_paths),
            failed=len(urls) - len(downloaded_paths),
        )

        return downloaded_paths

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

    def get_video_info(self, url: str) -> dict[str, Any]:
        """Extract video information without downloading.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with video metadata

        Raises:
            DownloadError: If info extraction fails
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")

        logger.info("extracting_video_info", url=url)

        try:
            import yt_dlp

            ydl_opts = {"quiet": True, "no_warnings": True}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise DownloadError(f"Could not extract info from {url}")

                # Extract relevant fields
                metadata = {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "duration": info.get("duration"),  # seconds
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "upload_date": info.get("upload_date"),
                    "description": info.get("description"),
                    "thumbnail": info.get("thumbnail"),
                    "formats": len(info.get("formats", [])),
                }

                logger.info(
                    "video_info_extracted",
                    url=url,
                    title=metadata["title"],
                    duration=metadata["duration"],
                )

                return metadata

        except Exception as e:
            logger.error("info_extraction_failed", url=url, error=str(e))
            raise DownloadError(f"Failed to extract info from {url}: {e}") from e
