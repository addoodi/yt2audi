"""Video file splitter for FAT32 compatibility."""

import subprocess
from pathlib import Path

import structlog

from yt2audi.exceptions import ConversionError
from yt2audi.models.profile import OnSizeExceed

logger = structlog.get_logger(__name__)


class Splitter:
    """Split videos into FAT32-compatible chunks."""

    @staticmethod
    def get_file_size_gb(path: Path) -> float:
        """Get file size in gigabytes.

        Args:
            path: File path

        Returns:
            Size in GB
        """
        if not path.exists():
            return 0.0
        return path.stat().st_size / (1024**3)

    @staticmethod
    def split_video(
        input_path: Path,
        max_size_gb: float,
        output_dir: Path | None = None,
        part_template: str = "{stem}_part{num:03d}.{ext}",
    ) -> list[Path]:
        """Split video into chunks under max_size_gb.

        Uses FFmpeg segment muxer for seamless splitting without re-encoding.

        Args:
            input_path: Input video file
            max_size_gb: Maximum size per chunk in gigabytes
            output_dir: Output directory (defaults to input file directory)
            part_template: Template for part filenames (uses format() with stem, num, ext)

        Returns:
            List of output chunk paths

        Raises:
            ConversionError: If splitting fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        current_size_gb = Splitter.get_file_size_gb(input_path)

        if current_size_gb <= max_size_gb:
            logger.info(
                "split_not_needed",
                path=str(input_path),
                size_gb=current_size_gb,
                max_size_gb=max_size_gb,
            )
            return [input_path]

        output_dir = output_dir or input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert GB to bytes for FFmpeg
        max_size_bytes = int(max_size_gb * 1024**3)

        # Build output pattern for FFmpeg segment muxer
        # FFmpeg expects %03d as a literal string (it will replace it with numbers)
        # Don't use the template's format spec here - build the pattern directly
        output_pattern = str(
            output_dir / f"{input_path.stem}_part%03d{input_path.suffix}"
        )

        logger.info(
            "splitting_video",
            input=str(input_path),
            size_gb=current_size_gb,
            max_size_gb=max_size_gb,
            output_pattern=output_pattern,
        )

        try:
            # FFmpeg's segment muxer doesn't support -segment_size directly.
            # We must calculate duration based on bitrate.
            # Get duration and bitrate using ffprobe
            probe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,bitrate",
                "-of",
                "default=noprint_wrappers=1",
                str(input_path),
            ]
            probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            
            # Parse output lines like "duration=19.133243"
            probe_data = {}
            for line in probe_res.stdout.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    probe_data[k.strip()] = v.strip()
            
            duration = float(probe_data.get("duration", 0))
            bitrate = float(probe_data.get("bitrate", 0))

            if bitrate <= 0:
                # Fallback: estimate bitrate from file size
                if duration > 0:
                    bitrate = (input_path.stat().st_size * 8) / duration
                else:
                    bitrate = 1_000_000 # 1 Mbps fallback

            # Target duration (s) = target size (bits) / bitrate (bits/s)
            target_duration = (max_size_bytes * 8) / bitrate
            # Use slightly less to be safe
            target_duration = max(1.0, target_duration * 0.95)

            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c",
                "copy",
                "-map",
                "0",
                "-f",
                "segment",
                "-segment_time",
                str(target_duration),
                "-reset_timestamps",
                "1",
                output_pattern,
            ]

            logger.debug("ffmpeg_split_command", cmd=" ".join(cmd))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
                check=True,
            )

            # Find generated chunks
            parts = sorted(output_dir.glob(f"{input_path.stem}_part*{input_path.suffix}"))

            if not parts:
                raise ConversionError("Splitting completed but no output files found")

            logger.info(
                "video_split_completed",
                input=str(input_path),
                parts_created=len(parts),
                parts=[str(p) for p in parts],
            )

            return parts

        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg_split_failed", input=str(input_path), error=e.stderr)
            raise ConversionError(f"FFmpeg splitting failed: {e.stderr}") from e
        except Exception as e:
            logger.error("split_error", input=str(input_path), error=str(e))
            raise ConversionError(f"Failed to split {input_path}: {e}") from e

    @staticmethod
    def compress_to_size(
        input_path: Path,
        target_size_gb: float,
        reduction_factor: float = 0.8,
        output_path: Path | None = None,
    ) -> Path:
        """Compress video to fit under target size by reducing bitrate.

        Args:
            input_path: Input video file
            target_size_gb: Target size in gigabytes
            reduction_factor: Bitrate reduction factor (0.8 = 80% of calculated bitrate)
            output_path: Output path (defaults to input_compressed.ext)

        Returns:
            Path to compressed video

        Raises:
            ConversionError: If compression fails
        """
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")

        if output_path is None:
            output_path = input_path.with_stem(f"{input_path.stem}_compressed")

        logger.info(
            "compressing_video",
            input=str(input_path),
            target_size_gb=target_size_gb,
            reduction_factor=reduction_factor,
        )

        try:
            # Get duration using ffprobe
            probe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(input_path),
            ]

            duration_result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            duration = float(duration_result.stdout.strip())

            # Calculate target bitrate
            # Size (bytes) = bitrate (bits/s) * duration (s) / 8
            target_size_bytes = target_size_gb * 1024**3
            target_bitrate_bps = (target_size_bytes * 8) / duration
            target_bitrate_kbps = int((target_bitrate_bps / 1000) * reduction_factor)

            # Reserve some for audio (assume 128k)
            audio_bitrate_kbps = 128
            video_bitrate_kbps = max(500, target_bitrate_kbps - audio_bitrate_kbps)

            logger.info(
                "compression_settings",
                duration=duration,
                target_size_gb=target_size_gb,
                video_bitrate_kbps=video_bitrate_kbps,
                audio_bitrate_kbps=audio_bitrate_kbps,
            )

            # Compress with calculated bitrate
            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-b:v",
                f"{video_bitrate_kbps}k",
                "-maxrate",
                f"{video_bitrate_kbps}k",
                "-bufsize",
                f"{video_bitrate_kbps * 2}k",
                "-b:a",
                f"{audio_bitrate_kbps}k",
                "-y",
                str(output_path),
            ]

            logger.debug("ffmpeg_compress_command", cmd=" ".join(cmd))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour max
                check=True,
            )

            if not output_path.exists():
                raise ConversionError("Compression completed but output file not found")

            output_size_gb = Splitter.get_file_size_gb(output_path)

            logger.info(
                "video_compressed",
                input=str(input_path),
                output=str(output_path),
                input_size_gb=Splitter.get_file_size_gb(input_path),
                output_size_gb=output_size_gb,
                target_size_gb=target_size_gb,
                achieved=output_size_gb <= target_size_gb,
            )

            return output_path

        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg_compress_failed", input=str(input_path), error=e.stderr)
            raise ConversionError(f"FFmpeg compression failed: {e.stderr}") from e
        except Exception as e:
            logger.error("compress_error", input=str(input_path), error=str(e))
            raise ConversionError(f"Failed to compress {input_path}: {e}") from e

    @staticmethod
    def handle_size_exceed(
        input_path: Path,
        max_size_gb: float,
        action: OnSizeExceed,
        output_dir: Path | None = None,
    ) -> list[Path]:
        """Handle file size exceeding maximum according to specified action.

        Args:
            input_path: Input video file
            max_size_gb: Maximum allowed size in GB
            action: Action to take (split, compress, warn, skip)
            output_dir: Output directory

        Returns:
            List of output files (may be original, split, or compressed)

        Raises:
            ConversionError: If handling fails
        """
        current_size_gb = Splitter.get_file_size_gb(input_path)

        if current_size_gb <= max_size_gb:
            logger.info("size_check_passed", path=str(input_path), size_gb=current_size_gb)
            return [input_path]

        logger.warning(
            "size_exceeded",
            path=str(input_path),
            size_gb=current_size_gb,
            max_size_gb=max_size_gb,
            action=action.value,
        )

        if action == OnSizeExceed.SPLIT:
            return Splitter.split_video(input_path, max_size_gb, output_dir)

        elif action == OnSizeExceed.COMPRESS:
            compressed = Splitter.compress_to_size(
                input_path,
                max_size_gb,
                reduction_factor=0.8,
                output_path=output_dir / f"{input_path.stem}_compressed{input_path.suffix}"
                if output_dir
                else None,
            )
            return [compressed]

        elif action == OnSizeExceed.WARN:
            logger.warning(
                "size_warning_only",
                path=str(input_path),
                size_gb=current_size_gb,
                max_size_gb=max_size_gb,
                message="File exceeds maximum size but action=warn, keeping original",
            )
            return [input_path]

        elif action == OnSizeExceed.SKIP:
            logger.warning(
                "size_skip",
                path=str(input_path),
                size_gb=current_size_gb,
                max_size_gb=max_size_gb,
                message="File exceeds maximum size and action=skip, returning empty list",
            )
            return []

        else:
            raise ConversionError(f"Unknown size exceed action: {action}")
