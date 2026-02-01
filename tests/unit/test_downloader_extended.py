"""Extended unit tests for Downloader class."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from yt2audi.core.downloader import Downloader
from yt2audi.exceptions import DownloadError

@pytest.fixture
def downloader(sample_profile):
    return Downloader(sample_profile)

class TestDownloaderExtended:
    """Extended tests for Downloader coverage."""

    def test_build_format_string_variations(self, downloader):
        """Test format string generation for different quality settings."""
        # 1. Low resolution (480p)
        downloader.profile.video.max_height = 480
        downloader.profile.video.codec = "h264"
        fmt = downloader._build_optimized_format_string()
        assert "height<=480" in fmt
        assert "vcodec^=avc" in fmt

        # 2. HD (720p)
        downloader.profile.video.max_height = 720
        fmt = downloader._build_optimized_format_string()
        assert "height<=720" in fmt

        # 3. Full HD (1080p)
        downloader.profile.video.max_height = 1080
        fmt = downloader._build_optimized_format_string()
        assert "height<=1080" in fmt

        # 4. Custom codec
        downloader.profile.video.codec = "vp9"
        fmt = downloader._build_optimized_format_string()
        assert "vcodec^=vp9" in fmt

    @patch("yt_dlp.YoutubeDL")
    def test_download_playlist_success(self, mock_ydl_class, downloader, tmp_path):
        """Test successful playlist download."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        # Mock extract_info
        mock_ydl.extract_info.return_value = {
            "entries": [{"id": "1"}, {"id": "2"}],
            "title": "Playlist"
        }
        
        # Mock glob finding files
        out_dir = tmp_path / "playlist_out"
        out_dir.mkdir()
        (out_dir / "vid1.mp4").touch()
        (out_dir / "vid2.mp4").touch()
        
        # We need to patch pathlib glob or rely on actual files. 
        # Since implementation uses output_dir.glob("*"), we use real tmp_path.
        
        results = downloader.download_playlist("https://playlist", output_dir=out_dir)
        
        assert len(results) == 2
        mock_ydl.download.assert_called_once()
        # Verify opts include playlistend if set
        downloader.download_config.playlist_end = 5
        downloader.download_playlist("https://playlist", output_dir=out_dir)
        args, kwargs = mock_ydl_class.call_args
        # yt_dlp.YoutubeDL(opts) -> opts is first arg
        if args:
            opts = args[0]
        else:
            opts = kwargs.get('params', {})
            
        assert opts['playlistend'] == 5

    @patch("yt_dlp.YoutubeDL")
    def test_download_playlist_extraction_fail(self, mock_ydl_class, downloader, tmp_path):
        """Test playlist download when extraction fails."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = None
        
        with pytest.raises(DownloadError, match="Could not extract playlist info"):
            downloader.download_playlist("https://playlist", output_dir=tmp_path)

    @patch("yt_dlp.YoutubeDL")
    def test_download_playlist_download_fail(self, mock_ydl_class, downloader, tmp_path):
        """Test playlist download when actual download fails."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        # Info extraction works
        mock_ydl.extract_info.return_value = {"entries": []}
        # Download fails
        import yt_dlp
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError(" Fail ")
        
        with pytest.raises(DownloadError, match="Failed to download playlist"):
            downloader.download_playlist("https://playlist", output_dir=tmp_path)
