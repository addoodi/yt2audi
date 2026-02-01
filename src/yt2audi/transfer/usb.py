"""USB drive detection and file transfer management."""

import ctypes
import os
import shutil
from pathlib import Path
from typing import Optional

import structlog

from yt2audi.exceptions import YT2AudiError

logger = structlog.get_logger(__name__)


class USBTransferError(YT2AudiError):
    """Raised when USB transfer fails."""


class USBManager:
    """Manages detection and file transfer to USB drives."""

    @staticmethod
    def get_removable_drives() -> list[Path]:
        """List all removable drives connected to the system (Windows).

        Returns:
            List of Path objects representing drive roots.
        """
        drives = []
        if os.name != "nt":
            # For non-Windows, we could look in /Volumes or /media
            # but for now, we focus on the user's Windows environment.
            return []

        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                # DRIVE_REMOVABLE = 2
                if drive_type == 2:
                    drives.append(Path(drive_path))
            bitmask >>= 1
        return drives

    @staticmethod
    def find_best_drive(preferred_path: Optional[str] = None) -> Optional[Path]:
        """Find the best USB drive to use.

        Args:
            preferred_path: Optional specific path to check first.

        Returns:
            Path to the selected drive or None if no suitable drive found.
        """
        if preferred_path:
            path = Path(preferred_path)
            if path.exists():
                return path
            logger.warning("preferred_usb_not_found", path=preferred_path)

        removable = USBManager.get_removable_drives()
        if not removable:
            return None

        # If multiple, favor ones that already have a "Videos" folder or similar?
        # For now, just take the first one found.
        return removable[0]

    @staticmethod
    def copy_to_usb(
        file_paths: list[Path],
        usb_root: Path,
        subdir: str = "Videos",
        delete_original: bool = False,
    ) -> list[Path]:
        """Copy files to a USB drive.

        Args:
            file_paths: List of files to copy.
            usb_root: Root path of the USB drive.
            subdir: Subdirectory on the USB to copy into.
            delete_original: Whether to delete the source files after copy.

        Returns:
            List of Paths to the files on the USB.

        Raises:
            USBTransferError: If transfer fails.
        """
        target_dir = usb_root / subdir
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise USBTransferError(f"Failed to create directory {target_dir}: {e}") from e

        copied_paths = []
        for src in file_paths:
            if not src.exists():
                logger.warning("source_file_not_found", path=str(src))
                continue

            dst = target_dir / src.name
            logger.info("copying_to_usb", src=str(src), dst=str(dst))

            try:
                # Check space
                usage = shutil.disk_usage(usb_root)
                if usage.free < src.stat().st_size:
                    raise USBTransferError(
                        f"Not enough space on {usb_root}. "
                        f"Need {src.stat().st_size / (1024**2):.1f}MB, "
                        f"have {usage.free / (1024**2):.1f}MB"
                    )

                shutil.copy2(src, dst)
                copied_paths.append(dst)

                if delete_original:
                    src.unlink()

            except Exception as e:
                logger.error("usb_copy_failed", src=str(src), error=str(e))
                raise USBTransferError(f"Failed to copy {src.name} to USB: {e}") from e

        return copied_paths
