"""Unit tests for the USBManager class."""

import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt2audi.transfer.usb import USBManager, USBTransferError

class TestUSBManager:
    """Test suite for USBManager class."""

    @patch("os.name", "nt")
    @patch("ctypes.windll.kernel32.GetLogicalDrives")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    def test_get_removable_drives_windows(self, mock_drive_type, mock_logical_drives):
        """Test removable drive detection on Windows."""
        # Mocking bitmask for drives A: and D: (1 | 8 = 9)
        mock_logical_drives.return_value = 9
        # A: (index 0) is DRIVE_REMOVABLE (2), D: (index 3) is DRIVE_FIXED (3)
        mock_drive_type.side_effect = lambda path: 2 if "A:" in path else 3
        
        drives = USBManager.get_removable_drives()
        assert len(drives) == 1
        assert drives[0] == Path("A:\\")

    @patch("os.name", "posix")
    def test_get_removable_drives_non_windows(self):
        """Test removable drive detection on non-Windows."""
        assert USBManager.get_removable_drives() == []

    def test_find_best_drive_preferred_exists(self, tmp_path):
        """Test drive selection when preferred path exists."""
        pref = tmp_path / "usb"
        pref.mkdir()
        result = USBManager.find_best_drive(str(pref))
        assert result == pref

    @patch.object(USBManager, "get_removable_drives")
    def test_find_best_drive_fallback(self, mock_get_removable, tmp_path):
        """Test fallback to removable drives."""
        mock_get_removable.return_value = [Path("D:\\")]
        
        # Preferred doesn't exist
        result = USBManager.find_best_drive("Z:\\nonexistent")
        assert result == Path("D:\\")
        
        # No preferred, use first removable
        result = USBManager.find_best_drive(None)
        assert result == Path("D:\\")

    @patch.object(USBManager, "get_removable_drives")
    def test_find_best_drive_none_found(self, mock_get_removable):
        """Test when no drives are found."""
        mock_get_removable.return_value = []
        assert USBManager.find_best_drive(None) is None

    def test_copy_to_usb_success(self, tmp_path):
        """Test successful copy to USB."""
        usb_root = tmp_path / "usb"
        usb_root.mkdir()
        
        src_file = tmp_path / "test.mp4"
        src_file.write_text("content")
        
        # Mock disk usage to report plenty of space
        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.return_value = MagicMock(free=1024*1024*100)
            
            results = USBManager.copy_to_usb([src_file], usb_root, subdir="VideoOut", delete_original=True)
            
            assert len(results) == 1
            assert results[0] == usb_root / "VideoOut" / "test.mp4"
            assert results[0].exists()
            assert not src_file.exists()

    def test_copy_to_usb_no_space(self, tmp_path):
        """Test copy failure due to lack of space."""
        usb_root = tmp_path / "usb"
        usb_root.mkdir()
        
        src_file = tmp_path / "test.mp4"
        src_file.write_text("some content")
        
        with patch("shutil.disk_usage") as mock_usage:
            # Report 0 free space
            mock_usage.return_value = MagicMock(free=0)
            
            with pytest.raises(USBTransferError, match="Not enough space"):
                USBManager.copy_to_usb([src_file], usb_root)

    def test_copy_to_usb_source_not_found(self, tmp_path):
        """Test handling of missing source files."""
        usb_root = tmp_path / "usb"
        usb_root.mkdir()
        
        missing = tmp_path / "ghost.mp4"
        results = USBManager.copy_to_usb([missing], usb_root)
        assert len(results) == 0

    def test_copy_to_usb_mkdir_failure(self):
        """Test failure when directory cannot be created."""
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(USBTransferError, match="Failed to create directory"):
                USBManager.copy_to_usb([Path("src")], Path("root"))

    def test_copy_to_usb_copy_failure(self, tmp_path):
        """Test generic copy failure handling."""
        usb_root = tmp_path / "usb"
        usb_root.mkdir()
        src = tmp_path / "fail.mp4"
        src.touch()
        
        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.return_value = MagicMock(free=1000000)
            with patch("shutil.copy2", side_effect=OSError("I/O Error")):
                with pytest.raises(USBTransferError, match="Failed to copy"):
                    USBManager.copy_to_usb([src], usb_root)
