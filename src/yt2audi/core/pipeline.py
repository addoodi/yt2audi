"""Concurrent processing pipeline for YT2Audi."""

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional

import structlog

from yt2audi.core.converter import Converter
from yt2audi.core.downloader import Downloader
from yt2audi.core.history import HistoryManager
from yt2audi.core.splitter import Splitter
from yt2audi.models.profile import Profile
from yt2audi.transfer import USBManager

logger = structlog.get_logger(__name__)


class ProcessingPipeline:
    """Manages concurrent download and conversion tasks using an async pipeline.
    
    This pipeline allows for:
    1. Multiple concurrent downloads (limited by semaphore)
    2. Multiple concurrent conversions (limited by semaphore)
    3. Pipelining: Conversion of video A can happen while video B is downloading
    """

    def __init__(
        self,
        profile: Profile,
        max_concurrent_downloads: int = 2,
        max_concurrent_conversions: int = 1,
    ) -> None:
        """Initialize the pipeline.

        Args:
            profile: Processing profile settings
            max_concurrent_downloads: Cap on simultaneous downloads
            max_concurrent_conversions: Cap on simultaneous conversions (usually lower to save CPU/GPU)
        """
        self.profile = profile
        self.downloader = Downloader(profile)
        self.converter = Converter(profile)
        self.history = HistoryManager()
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self.convert_semaphore = asyncio.Semaphore(max_concurrent_conversions)
        
        logger.info(
            "pipeline_initialized",
            max_downloads=max_concurrent_downloads,
            max_conversions=max_concurrent_conversions
        )

    async def process_one(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Optional[Callable[[str, float, str], None]] = None,
    ) -> list[Path]:
        """Process a single video through the full pipeline.

        Args:
            url: YouTube URL
            output_dir: Target output directory
            progress_callback: Optional callback(url, percent, stage)

        Returns:
            List of final output file paths
            
        Raises:
            Exception: Re-raises any error from download or conversion
        """
        # --- Stage 0: Check if already exists in history or filesystem ---
        try:
            info_dict = await self.downloader.extract_info_async(url)
            video_id = info_dict.get("id")
            
            # 1. Check persistent history
            if video_id and self.history.is_processed(video_id):
                logger.info("pipeline_skip_history", url=url, id=video_id)
                if progress_callback:
                    progress_callback(url, 100, "Already in history")
                # Even if in history, try to return the path if we can predict it
                return [self.converter.get_output_path(info_dict, output_dir)]

            # 2. Check filesystem
            expected_path = self.converter.get_output_path(info_dict, output_dir)
            if expected_path.exists():
                logger.info("pipeline_skip_existing", url=url, path=str(expected_path))
                if progress_callback:
                    progress_callback(url, 100, "Already exists")
                # Mark as completed in history if it's already on disk but not in history
                if video_id:
                    self.history.mark_completed(video_id)
                return [expected_path]
        except Exception as e:
            logger.debug("pipeline_precheck_failed", url=url, error=str(e))
            info_dict = None

        # --- Stage 1: Download ---
        async with self.download_semaphore:
            logger.info("pipeline_stage_download", url=url)
            
            def _dl_hook(d: dict[str, Any]) -> None:
                if progress_callback and d.get("status") == "downloading":
                    downloaded = d.get("downloaded_bytes", 0)
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    if total > 0:
                        # Scale download to 0-50%
                        percent = (downloaded / total) * 50
                        progress_callback(url, percent, "Downloading")

            try:
                # If we have info_dict already, it's good, but downloader re-checks
                downloaded_path, info_dict = await self.downloader.download_video_async(
                    url, progress_callback=_dl_hook
                )
            except Exception as e:
                logger.error("pipeline_download_failed", url=url, error=str(e))
                if progress_callback:
                    progress_callback(url, 0, f"Download Failed: {e}")
                raise

        # --- Stage 2: Conversion ---
        # Find thumbnail if downloaded (usually in same temp dir)
        thumbnail_path = None
        if downloaded_path:
            potential_thumbnail = downloaded_path.with_suffix(".jpg")
            if potential_thumbnail.exists():
                thumbnail_path = potential_thumbnail

        conversion_success = False
        async with self.convert_semaphore:
            logger.info("pipeline_stage_conversion", url=url, path=str(downloaded_path))
            
            def _cv_hook(percent: float, stage: str) -> None:
                if progress_callback:
                    # Scale conversion to 50-100%
                    scaled_percent = 50 + (percent * 0.5)
                    progress_callback(url, scaled_percent, stage)

            try:
                converted_path = await self.converter.convert_video_async(
                    downloaded_path, 
                    output_dir=output_dir, 
                    progress_callback=_cv_hook,
                    info_dict=info_dict,
                    thumbnail_path=thumbnail_path
                )
                conversion_success = True
            except Exception as e:
                logger.error("pipeline_conversion_failed", url=url, error=str(e))
                if progress_callback:
                    progress_callback(url, 0, f"Conversion Failed: {e}")
                raise
            finally:
                # ONLY cleanup temporary downloaded files if conversion succeeded
                # This allows resuming conversion if it failed previously
                if conversion_success and downloaded_path.exists():
                    try:
                        downloaded_path.unlink()
                    except Exception:
                        pass
                
                if conversion_success and thumbnail_path and thumbnail_path.exists():
                    try:
                        thumbnail_path.unlink()
                    except Exception:
                        pass

        # --- Stage 3: Split & Finalize ---
        logger.info("pipeline_stage_finalize", url=url, path=str(converted_path))
        if progress_callback:
            progress_callback(url, 95, "Finalizing")

        final_paths = Splitter.handle_size_exceed(
            converted_path,
            self.profile.output.max_file_size_gb,
            self.profile.output.on_size_exceed,
            output_dir,
        )

        # --- Stage 4: Transfer (USB) ---
        if self.profile.transfer.usb_auto_copy:
            logger.info("pipeline_stage_transfer", url=url)
            if progress_callback:
                progress_callback(url, 98, "Copying to USB")
            
            usb_root = USBManager.find_best_drive(self.profile.transfer.usb_mount_path)
            if usb_root:
                loop = asyncio.get_running_loop()
                try:
                    # Run blocking copy in executor
                    final_paths = await loop.run_in_executor(
                        None,
                        USBManager.copy_to_usb,
                        final_paths,
                        usb_root,
                        self.profile.transfer.usb_subdir,
                        False # Don't delete original from output_dir
                    )
                    logger.info("pipeline_transfer_success", url=url, usb=str(usb_root))
                except Exception as e:
                    logger.error("pipeline_transfer_failed", url=url, error=str(e))
            else:
                logger.warning("pipeline_usb_not_found", url=url)

        if progress_callback:
            progress_callback(url, 100, "Complete")
            
        # Record successful completion in history
        if "info_dict" in locals() and info_dict and info_dict.get("id"):
            self.history.mark_completed(info_dict["id"])

        return final_paths

    async def run_batch(
        self,
        urls: list[str],
        output_dir: Path,
        progress_callback: Optional[Callable[[str, float, str], None]] = None,
    ) -> dict[str, list[Path]]:
        """Run a batch of videos through the concurrent pipeline.

        Args:
            urls: List of YouTube URLs
            output_dir: Target output directory
            progress_callback: Optional callback(url, percent, stage)

        Returns:
            Dictionary mapping URL to list of generated file paths
        """
        logger.info("pipeline_batch_started", count=len(urls))
        
        tasks = [self.process_one(url, output_dir, progress_callback) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = {}
        for url, res in zip(urls, results):
            if isinstance(res, Exception):
                logger.error("pipeline_item_failed", url=url, error=str(res))
            else:
                final_results[url] = res
                
        logger.info(
            "pipeline_batch_completed", 
            total=len(urls), 
            succeeded=len(final_results),
            failed=len(urls) - len(final_results)
        )
        return final_results
