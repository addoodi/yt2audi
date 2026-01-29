"""Entry point for running yt2audi as a module."""

import sys

# Enable Windows long path support (paths > 260 characters)
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        
        # Define constants
        PROCESS_PLACEHOLDER_MODE = 1
        
        # Try to enable long path support
        # This requires Windows 10 version 1607 or later
        try:
            ntdll = ctypes.WinDLL('ntdll')
            ntdll.RtlSetProcessPlaceholderCompatibilityMode(PROCESS_PLACEHOLDER_MODE)
        except (OSError, AttributeError):
            # Function not available on older Windows versions
            # Fall back to standard path handling
            pass
    except ImportError:
        # ctypes not available, skip long path support
        pass

from yt2audi.cli.main import app

if __name__ == "__main__":
    app()
