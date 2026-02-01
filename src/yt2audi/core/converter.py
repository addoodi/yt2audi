"""Video converter using FFmpeg with GPU acceleration."""

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

import structlog

from yt2audi.core.gpu_detector import (
    get_encoder_extra_args,
    get_encoder_preset,
    select_best_encoder,
)
from yt2audi.exceptions import ConversionError
from yt2audi.models.profile import EncoderType, Profile
from yt2audi.utils import ensure_extension, get_unique_path

logger = structlog.get_logger(__name__)


class VideoMetadata:
    """Video metadata extracted from FFprobe."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize from FFprobe JSON output."""
        self.data = data
        self.format = data.get("format", {})
        self.video_stream = self._get_video_stream()
        self.audio_stream = self._get_audio_stream()

    def _get_video_stream(self) -> dict[str, Any] | None:
        """Get first video stream."""
        streams = self.data.get("streams", [])
        for stream in streams:
            if stream.get("codec_type") == "video":
                return stream
        return None

    def _get_audio_stream(self) -> dict[str, Any] | None:
        """Get first audio stream."""
        streams = self.data.get("streams", [])
        for stream in streams:
            if stream.get("codec_type") == "audio":
                return stream
        return None

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return float(self.format.get("duration", 0))

    @property
    def bitrate(self) -> int:
        """Get bitrate in bits per second."""
        return int(self.format.get("bit_rate", 0))

    @property
    def size_bytes(self) -> int:
        """Get file size in bytes."""
        return int(self.format.get("size", 0))

    @property
    def width(self) -> int:
        """Get video width."""
        if self.video_stream:
            return int(self.video_stream.get("width", 0))
        return 0

    @property
    def height(self) -> int:
        """Get video height."""
        if self.video_stream:
            return int(self.video_stream.get("height", 0))
        return 0

    @property
    def fps(self) -> float:
        """Get frames per second."""
        if self.video_stream:
            fps_str = self.video_stream.get("r_frame_rate", "0/1")
            try:
                num, den = map(int, fps_str.split("/"))
                return num / den if den else 0
            except (ValueError, ZeroDivisionError):
                return 0
        return 0

    @property
    def codec_name(self) -> str:
        """Get video codec name."""
        if self.video_stream:
            return str(self.video_stream.get("codec_name", "unknown"))
        return "unknown"


class Converter:
    """Video converter using FFmpeg."""

    def __init__(self, profile: Profile) -> None:
        """Initialize converter.

        Args:
            profile: Conversion profile configuration
        """
        self.profile = profile
        self.video_config = profile.video
        self.audio_config = profile.audio
        self.output_config = profile.output

        # Select best encoder
        self.encoder = select_best_encoder(self.video_config.encoder_priority)

        logger.info(
            "converter_initialized", profile=profile.profile.name, encoder=self.encoder.value
        )

    def get_output_path(self, info_dict: dict[str, Any], output_dir: Path | None = None) -> Path:
        """Predict the output path for a video based on its info dictionary.

        Args:
            info_dict: Video info from yt-dlp
            output_dir: Target output directory

        Returns:
            Predicted output Path
        """
        from yt2audi.utils import sanitize_filename
        from yt2audi.config import expand_path

        if output_dir is None:
            output_dir = expand_path(self.output_config.output_dir)

        template = self.output_config.filename_template

        # Prepare context for template
        title = info_dict.get("title", "video")
        video_id = info_dict.get("id", "none")
        uploader = info_dict.get("uploader", "unknown")

        ctx = {
            "title": sanitize_filename(title),
            "id": video_id,
            "uploader": sanitize_filename(uploader),
            "ext": self.output_config.container,
        }

        try:
            filename = template.format(**ctx)
        except Exception:
            # Fallback to standard
            filename = f"{ctx['title']}_{ctx['id']}.{ctx['ext']}"

        return output_dir / filename

    def probe_video(self, input_path: Path) -> VideoMetadata:
        """Extract video metadata using FFprobe.

        Args:
            input_path: Path to video file

        Returns:
            VideoMetadata object

        Raises:
            ConversionError: If probing fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        logger.info("probing_video", path=str(input_path))

        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(input_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            data = json.loads(result.stdout)
            metadata = VideoMetadata(data)

            logger.info(
                "video_probed",
                path=str(input_path),
                duration=metadata.duration,
                resolution=f"{metadata.width}x{metadata.height}",
                fps=metadata.fps,
                codec=metadata.codec_name,
                bitrate_mbps=metadata.bitrate / 1_000_000,
            )

            return metadata

        except subprocess.CalledProcessError as e:
            logger.error("ffprobe_failed", path=str(input_path), error=e.stderr)
            raise ConversionError(f"FFprobe failed for {input_path}: {e.stderr}") from e
        except Exception as e:
            logger.error("probe_error", path=str(input_path), error=str(e))
            raise ConversionError(f"Failed to probe {input_path}: {e}") from e

    def build_ffmpeg_command(
        self,
        input_path: Path,
        output_path: Path,
        metadata: VideoMetadata,
        info_dict: dict[str, Any] | None = None,
        thumbnail_path: Path | None = None,
    ) -> list[str]:
        """Build FFmpeg command with all parameters.

        Args:
            input_path: Input video file
            output_path: Output video file
            metadata: Video metadata from probe
            info_dict: Optional YouTube info dictionary for metadata
            thumbnail_path: Optional path to thumbnail image

        Returns:
            FFmpeg command as list of arguments
        """
        cmd = ["ffmpeg", "-i", str(input_path)]

        if thumbnail_path and thumbnail_path.exists():
            cmd.extend(["-i", str(thumbnail_path)])

        # Map main video and audio, then thumbnail and metadata
        cmd.extend(["-map", "0:v:0", "-map", "0:a:0"])
        
        if thumbnail_path and thumbnail_path.exists():
            cmd.extend(["-map", "1:v:0"])
            # Set thumbnail as a non-encoded attached pic
            cmd.extend(["-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic"])

        # Video encoding (stream 0)
        cmd.extend(["-c:v:0", self.encoder.value])

        # Encoder preset
        preset = get_encoder_preset(self.encoder)
        cmd.extend(["-preset", preset])

        # Quality settings
        extra_args = get_encoder_extra_args(self.encoder, self.video_config.quality_cq)
        cmd.extend(extra_args)

        # Profile and level
        cmd.extend(["-profile:v:0", self.video_config.profile])
        cmd.extend(["-level:v:0", self.video_config.level])

        # Pixel format
        cmd.extend(["-pix_fmt:v:0", self.video_config.pixel_format])

        # Resolution scaling and FPS limiting
        vf_filters = []

        # Scale if needed
        max_width = self.video_config.max_width
        max_height = self.video_config.max_height

        if metadata.width > max_width or metadata.height > max_height:
            if self.video_config.maintain_aspect_ratio:
                scale_filter = (
                    f"scale='min({max_width},iw)':'min({max_height},ih)'"
                    ":force_original_aspect_ratio=decrease"
                )
            else:
                scale_filter = f"scale={max_width}:{max_height}"
            vf_filters.append(scale_filter)

        # FPS limiting
        if metadata.fps > self.video_config.max_fps:
            vf_filters.append(f"fps=fps={self.video_config.max_fps}")

        if vf_filters:
            cmd.extend(["-vf:v:0", ",".join(vf_filters)])

        # Bitrate limiting
        if self.video_config.max_bitrate_mbps != "auto":
            bitrate_mbps = float(self.video_config.max_bitrate_mbps)
            bitrate_kbps = int(bitrate_mbps * 1000)
            cmd.extend(["-b:v:0", f"{bitrate_kbps}k"])
            cmd.extend(["-maxrate:v:0", f"{bitrate_kbps}k"])
            cmd.extend(["-bufsize:v:0", f"{bitrate_kbps * 2}k"])

        # Extra video args
        if self.video_config.extra_video_args:
            cmd.extend(self.video_config.extra_video_args)

        # Audio encoding
        cmd.extend(["-c:a:0", self.audio_config.codec])
        cmd.extend(["-b:a:0", f"{self.audio_config.bitrate_kbps}k"])
        cmd.extend(["-ar:a:0", str(self.audio_config.sample_rate)])
        cmd.extend(["-ac:a:0", str(self.audio_config.channels)])

        # Extra audio args
        if self.audio_config.extra_audio_args:
            cmd.extend(self.audio_config.extra_audio_args)

        # Metadata
        if info_dict:
            title = info_dict.get("title")
            if title:
                cmd.extend(["-metadata", f"title={title}"])
            
            uploader = info_dict.get("uploader") or info_dict.get("artist")
            if uploader:
                cmd.extend(["-metadata", f"artist={uploader}"])
                cmd.extend(["-metadata", f"album_artist={uploader}"])
            
            # Additional tags for car MMI
            album = info_dict.get("playlist_title") or info_dict.get("album") or "YouTube"
            cmd.extend(["-metadata", f"album={album}"])
            
            # Format date (YYYYMMDD to YYYY-MM-DD)
            upload_date = info_dict.get("upload_date")
            if upload_date and len(upload_date) == 8:
                formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
                cmd.extend(["-metadata", f"date={formatted_date}"])
            elif upload_date:
                cmd.extend(["-metadata", f"date={upload_date}"])

            cmd.extend(["-metadata", "genre=Video"])
                
            video_id = info_dict.get("id")
            if video_id:
                cmd.extend(["-metadata", f"comment=YouTube ID: {video_id}"])

        # Strip unwanted streams
        cmd.extend(["-sn"])  # No subtitles (unless embedding)
        cmd.extend(["-dn"])  # No data streams
        cmd.extend(["-map_chapters", "-1"])  # No chapters

        # Faststart for streaming
        if self.output_config.faststart:
            cmd.extend(["-movflags", "+faststart"])

        # Output file
        cmd.extend(["-y", str(output_path)])  # -y = overwrite

        return cmd

    def convert_video(
        self,
        input_path: Path,
        output_dir: Path | None = None,
        output_filename: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
        info_dict: dict[str, Any] | None = None,
        thumbnail_path: Path | None = None,
    ) -> Path:
        """Convert video according to profile settings.

        Args:
            input_path: Input video file
            output_dir: Output directory (defaults to profile setting)
            output_filename: Output filename (defaults to sanitized input name)
            progress_callback: Optional callback(percent, stage)

        Returns:
            Path to converted video

        Raises:
            ConversionError: If conversion fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        # Determine output path
        from yt2audi.config import expand_path
        from yt2audi.utils import sanitize_filename

        if output_dir is None:
            output_dir = expand_path(self.output_config.output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        if output_filename is None:
            output_filename = sanitize_filename(input_path.stem) + f".{self.output_config.container}"

        output_path = output_dir / output_filename
        output_path = ensure_extension(output_path, self.output_config.container)
        output_path = get_unique_path(output_path)

        logger.info(
            "conversion_started",
            input=str(input_path),
            output=str(output_path),
            encoder=self.encoder.value,
        )

        # Probe input video
        if progress_callback:
            progress_callback(5.0, "Analyzing video")

        metadata = self.probe_video(input_path)

        # Build FFmpeg command
        if progress_callback:
            progress_callback(10.0, "Building conversion command")

        cmd = self.build_ffmpeg_command(
            input_path, 
            output_path, 
            metadata,
            info_dict=info_dict,
            thumbnail_path=thumbnail_path
        )

        logger.debug("ffmpeg_command", cmd=" ".join(cmd))

        # Execute conversion
        if progress_callback:
            progress_callback(15.0, "Converting video")

        try:
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            duration = metadata.duration

            while True:
                line = process.stdout.readline()
                if not line:
                    break

                # Parse progress from FFmpeg output
                # Example: "frame= 1234 fps=56 q=28.0 size= 12345kB time=00:01:23.45 bitrate=1234.5kbits/s speed=1.23x"
                if progress_callback and "time=" in line:
                    time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                    if time_match and duration > 0:
                        hours, minutes, seconds = time_match.groups()
                        current_time = (
                            int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                        )
                        percent = min(95.0, 15.0 + (current_time / duration * 80))
                        progress_callback(percent, "Converting video")

            process.wait()

            if process.returncode != 0:
                raise ConversionError(f"FFmpeg exited with code {process.returncode}")

            if not output_path.exists():
                raise ConversionError(f"Conversion completed but output file not found: {output_path}")

            if progress_callback:
                progress_callback(100.0, "Conversion complete")

            logger.info(
                "conversion_completed",
                input=str(input_path),
                output=str(output_path),
                output_size_mb=output_path.stat().st_size / 1024 / 1024,
            )

            return output_path

        except subprocess.SubprocessError as e:
            logger.error("ffmpeg_failed", input=str(input_path), error=str(e))
            raise ConversionError(f"FFmpeg conversion failed: {e}") from e
        except Exception as e:
            logger.error("conversion_error", input=str(input_path), error=str(e))
            raise ConversionError(f"Unexpected conversion error: {e}") from e
        finally:
            # Cleanup if failed
            if process.returncode != 0 and output_path.exists():
                try:
                    output_path.unlink()
                    logger.info("cleaned_up_failed_output", path=str(output_path))
                except Exception:
                    pass

    async def probe_video_async(self, input_path: Path) -> VideoMetadata:
        """Extract video metadata using FFprobe asynchronously.

        Args:
            input_path: Path to video file

        Returns:
            VideoMetadata object
        """
        # Run sync version in thread for simplicity if we don't want to refactor to subprocess
        return await asyncio.to_thread(self.probe_video, input_path)

    async def convert_video_async(
        self,
        input_path: Path,
        output_dir: Path | None = None,
        output_filename: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
        info_dict: dict[str, Any] | None = None,
        thumbnail_path: Path | None = None,
    ) -> Path:
        """Convert video according to profile settings asynchronously.

        Args:
            input_path: Input video file
            output_dir: Output directory
            output_filename: Output filename
            progress_callback: Optional callback(percent, stage)

        Returns:
            Path to converted video
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        from yt2audi.config import expand_path
        from yt2audi.utils import sanitize_filename

        if output_dir is None:
            output_dir = expand_path(self.output_config.output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        if output_filename is None:
            output_filename = sanitize_filename(input_path.stem) + f".{self.output_config.container}"

        output_path = output_dir / output_filename
        output_path = ensure_extension(output_path, self.output_config.container)
        output_path = get_unique_path(output_path)

        logger.info(
            "async_conversion_started",
            input=str(input_path),
            output=str(output_path),
            encoder=self.encoder.value,
        )

        try:
            if progress_callback:
                progress_callback(5.0, "Analyzing video")

            # We reuse the sync probe logic but run it in a thread to be async-friendly
            metadata = await self.probe_video_async(input_path)
            duration = metadata.duration

            if progress_callback:
                progress_callback(10.0, "Building conversion command")

            # Reuse the command builder from the sync version
            cmd_args = self.build_ffmpeg_command(
                input_path, 
                output_path, 
                metadata, 
                info_dict=info_dict, 
                thumbnail_path=thumbnail_path
            )
            # cmd is a list, create_subprocess_exec takes program as first arg, then *args

            if progress_callback:
                progress_callback(15.0, "Converting video")

            # Create the subprocess
            # Note: create_subprocess_exec requires the program as the first argument,
            # and the rest as separate arguments. cmd_args[0] is 'ffmpeg'.
            process = await asyncio.create_subprocess_exec(
                cmd_args[0], *cmd_args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            # Read output for progress
            # We read chunks because FFmpeg uses \r for progress which can cause 
            # asyncio's readline() to hit buffer limits if no \n is found.
            buffer = ""
            last_lines = [] # Keep last few lines for error reporting
            while True:
                chunk_bytes = await process.stdout.read(4096)
                if not chunk_bytes:
                    break
                
                # Decode and accrue
                chunk_str = chunk_bytes.decode("utf-8", errors="replace")
                buffer += chunk_str
                
                # Process complete lines or carriage returns
                while True:
                    # Find nearest newline or carriage return
                    match = re.search(r"[\r\n]", buffer)
                    if not match:
                        break
                    
                    line_end = match.end()
                    line = buffer[:line_end].strip()
                    buffer = buffer[line_end:]
                    
                    if not line:
                        continue
                    
                    # Store line for error reporting (keep last 10)
                    last_lines.append(line)
                    if len(last_lines) > 10:
                        last_lines.pop(0)

                    # Parse progress
                    # FFmpeg output example: "frame= 1234 ... time=00:01:23.45 ..."
                    if progress_callback and "time=" in line:
                        time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                        if time_match and duration > 0:
                            try:
                                hours, minutes, seconds = time_match.groups()
                                current_time = (
                                    int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                                )
                                # Map progress from 15% to 95%
                                percent = min(95.0, 15.0 + (current_time / duration * 80.0))
                                progress_callback(percent, "Converting video")
                            except ValueError:
                                pass

            return_code = await process.wait()

            if return_code != 0:
                error_context = "\n".join(last_lines)
                logger.error("ffmpeg_async_failed", return_code=return_code, last_output=error_context)
                raise ConversionError(f"FFmpeg exited with code {return_code}. Last output:\n{error_context}")

            if not output_path.exists():
                raise ConversionError(f"Conversion completed but output file not found: {output_path}")

            if progress_callback:
                progress_callback(100.0, "Conversion complete")
            
            logger.info(
                "async_conversion_completed",
                input=str(input_path),
                output=str(output_path),
                output_size_mb=output_path.stat().st_size / 1024 / 1024,
            )

            return output_path

        except Exception as e:
            logger.error("async_conversion_error", input=str(input_path), error=str(e))
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass
            # Re-raise as ConversionError
            if isinstance(e, ConversionError):
                raise
            raise ConversionError(f"Async conversion failed: {e}") from e

    def estimate_output_size(self, input_path: Path) -> float:
        """Estimate output file size in GB.

        Args:
            input_path: Input video file

        Returns:
            Estimated size in gigabytes

        This is a rough estimate based on duration and target bitrate.
        """
        metadata = self.probe_video(input_path)

        # Calculate bitrate
        if self.video_config.max_bitrate_mbps == "auto":
            # Use input bitrate
            bitrate_bps = metadata.bitrate
        else:
            # Use configured bitrate
            bitrate_mbps = float(self.video_config.max_bitrate_mbps)
            bitrate_bps = bitrate_mbps * 1_000_000

        # Add audio bitrate
        audio_bitrate_bps = self.audio_config.bitrate_kbps * 1000

        total_bitrate_bps = bitrate_bps + audio_bitrate_bps

        # Estimate size = bitrate * duration
        size_bytes = (total_bitrate_bps / 8) * metadata.duration

        # Convert to GB
        size_gb = size_bytes / (1024**3)

        logger.info(
            "size_estimated",
            input=str(input_path),
            estimated_gb=size_gb,
            duration=metadata.duration,
            bitrate_mbps=total_bitrate_bps / 1_000_000,
        )

        return size_gb
