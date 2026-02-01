"""Unit tests for the Downloader class."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt2audi.core.downloader import Downloader
from yt2audi.exceptions import DownloadError

@pytest.fixture
def mock_profile(sample_profile):
    """Fixture for a mock profile."""
    return sample_profile

@pytest.fixture
def downloader(mock_profile):
    """Fixture for Downloader instance."""
    return Downloader(mock_profile)

class TestDownloader:
    """Test suite for Downloader class."""

    def test_downloader_init(self, downloader, mock_profile):
        """Test downloader initialization."""
        assert downloader.profile == mock_profile
        assert downloader.download_config == mock_profile.download
        assert isinstance(downloader.temp_dir, Path)

    def test_build_optimized_format_string(self, downloader):
        """Test building optimized format string."""
        format_str = downloader._build_optimized_format_string()
        assert isinstance(format_str, str)
        assert "bestvideo" in format_str
        assert "bestaudio" in format_str

    @patch("yt2audi.config.expand_path")
    def test_get_ydl_opts(self, mock_expand, downloader):
        """Test building yt-dlp options."""
        mock_expand.return_value = Path("/tmp/archive.txt")
        downloader.download_config.download_archive = "archive.txt"
        
        opts = downloader._get_ydl_opts("output.mp4")
        
        assert opts["format"] is not None
        assert opts["outtmpl"] == "output.mp4"
        assert "download_archive" in opts
        assert opts["download_archive"] == str(Path("/tmp/archive.txt"))

    @patch("yt_dlp.YoutubeDL")
    @patch("yt2audi.utils.is_valid_url")
    def test_download_video_success(self, mock_valid, mock_ydl_class, downloader, tmp_path):
        """Test successful video download."""
        mock_valid.return_value = True
        
        # Setup mock YDL
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        mock_ydl.extract_info.return_value = {"id": "test_id", "title": "test_title", "ext": "mp4"}
        output_path = tmp_path / "test_title_test_id.mp4"
        mock_ydl.prepare_filename.return_value = str(output_path)
        
        # Create dummy file to simulate download completion
        output_path.touch()
        
        result, info = downloader.download_video("https://youtube.com/watch?v=123", output_dir=tmp_path)
        
        assert result == output_path
        assert result.exists()
        assert info["id"] == "test_id"
        mock_ydl.download.assert_called_once()

    @patch("yt_dlp.YoutubeDL")
    @patch("yt2audi.utils.is_valid_url", return_value=True)
    def test_download_video_failure(self, mock_valid, mock_ydl_class, downloader, tmp_path):
        """Test handling of download failure."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.download.side_effect = Exception("Network error")
        
        # Matches "Unexpected error..." or "Failed to download..." depending on implementation
        with pytest.raises(DownloadError, match="error"):
            downloader.download_video("https://url", output_dir=tmp_path)

    @patch("yt2audi.utils.is_valid_url")
    def test_download_video_invalid_url(self, mock_valid, downloader):
        """Test download with invalid URL."""
        mock_valid.return_value = False
        with pytest.raises(ValueError, match="Invalid URL"):
            downloader.download_video("invalid_url")

    @pytest.mark.asyncio
    async def test_download_video_async(self, downloader):
        """Test async video download wrapper."""
        with patch.object(downloader, "download_video") as mock_download:
            mock_download.return_value = (Path("test.mp4"), {"id": "test"})
            result, info = await downloader.download_video_async("url")
            assert result == Path("test.mp4")
            mock_download.assert_called_once_with("url", None, None)

    @pytest.mark.asyncio
    async def test_download_batch_async(self, downloader, tmp_path):
        """Test concurrent batch download."""
        async def mock_dl_async(url, output_dir=None, progress_callback=None):
            return tmp_path / f"{url[-3:]}.mp4", {"id": url[-3:]}

        with patch.object(downloader, "download_video_async", side_effect=mock_dl_async):
            urls = ["url1", "url2", "url3"]
            results = await downloader.download_batch_async(urls, output_dir=tmp_path)
            assert len(results) == 3
            assert all(isinstance(r, tuple) for r in results)

    @patch("yt2audi.core.downloader.is_valid_url", return_value=True)
    def test_extract_info_cached(self, mock_valid, downloader):
        """Test extract_info with cache hit."""
        cached_data = {"id": "cached", "title": "Cached Title"}
        with patch.object(downloader.cache, "get", return_value=cached_data):
            info = downloader.extract_info("url")
            assert info == cached_data

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_urls(self, mock_ydl_class, downloader):
        """Test extraction of URLs from a playlist."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "entries": [
                {"webpage_url": "url1", "id": "1"},
                {"webpage_url": "url2", "id": "2"}
            ]
        }
        
        urls = downloader.get_playlist_urls("https://playlist")
        expected = ["https://www.youtube.com/watch?v=1", "https://www.youtube.com/watch?v=2"]
        assert urls == expected

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_urls_error(self, mock_ydl_class, downloader):
        """Test error handling in playlist extraction."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Playlist private")
        
        urls = downloader.get_playlist_urls("url")
        assert urls == []
