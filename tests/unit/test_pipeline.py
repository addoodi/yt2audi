"""Unit tests for the ProcessingPipeline class."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from yt2audi.core.pipeline import ProcessingPipeline
from yt2audi.core.history import HistoryManager

@pytest.fixture
def mock_profile(sample_profile):
    """Fixture for a mock profile."""
    return sample_profile

class TestProcessingPipeline:
    """Test suite for ProcessingPipeline class."""

    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    def test_pipeline_init(self, mock_conv_class, mock_dl_class, mock_profile):
        """Test pipeline initialization."""
        pipeline = ProcessingPipeline(mock_profile, max_concurrent_downloads=5, max_concurrent_conversions=2)
        assert pipeline.profile == mock_profile
        mock_dl_class.assert_called_once_with(mock_profile)
        mock_conv_class.assert_called_once_with(mock_profile)
        # Check semaphores
        assert pipeline.download_semaphore._value == 5
        assert pipeline.convert_semaphore._value == 2

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    @patch("yt2audi.core.pipeline.Splitter.handle_size_exceed")
    async def test_process_one_success(self, mock_split, mock_conv_class, mock_dl_class, mock_profile, tmp_path):
        """Test processing a single video through the pipeline."""
        mock_dl = mock_dl_class.return_value
        mock_conv = mock_conv_class.return_value
        
        pipeline = ProcessingPipeline(mock_profile)
        pipeline.history = MagicMock(spec=HistoryManager)
        pipeline.history.is_processed.return_value = False
        
        # Setup async mocks
        mock_dl.extract_info_async = AsyncMock(return_value={"id": "test", "title": "test"})
        mock_dl.download_video_async = AsyncMock(return_value=(Path("downloaded.mp4"), {"id": "test"}))
        mock_conv.convert_video_async = AsyncMock(return_value=Path("converted.mp4"))
        
        expected_out = tmp_path / "expected.mp4"
        mock_conv.get_output_path = MagicMock(return_value=expected_out)
        mock_split.return_value = [Path("final.mp4")]
        
        # We need Path.exists to return False twice (Stage 0 check history then disk) 
        # then True for cleanup check, then True for cleanup downloaded_path, then False for thumbnail
        # Let's use a side_effect that checks the path string to be more robust
        def exists_side_effect(self_path):
            p = str(self_path)
            if "expected.mp4" in p: return False
            if "downloaded.mp4" in p: return True
            if "dl.jpg" in p: return False
            return False

        with patch.object(Path, "exists", autospec=True, side_effect=exists_side_effect):
            with patch.object(Path, "unlink", return_value=None):
                results = await pipeline.process_one("https://url.com", output_dir=tmp_path)
                
                assert results == [Path("final.mp4")]
                mock_dl.download_video_async.assert_called_once()
                mock_conv.convert_video_async.assert_called_once()
                mock_split.assert_called_once()

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    async def test_process_one_download_failure(self, mock_conv_class, mock_dl_class, mock_profile, tmp_path):
        """Test processing with download failure."""
        mock_dl = mock_dl_class.return_value
        mock_conv = mock_conv_class.return_value
        
        mock_dl.extract_info_async = AsyncMock(return_value={"id": "test"})
        mock_dl.download_video_async = AsyncMock(side_effect=Exception("Download failed"))
        mock_conv.get_output_path = MagicMock(return_value=tmp_path / "expected.mp4")
        
        pipeline = ProcessingPipeline(mock_profile)
        pipeline.history = MagicMock(spec=HistoryManager)
        pipeline.history.is_processed.return_value = False
        
        # Stage 0: expected_path.exists() -> False
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(Exception, match="Download failed"):
                await pipeline.process_one("https://url.com", output_dir=tmp_path)

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    @patch("yt2audi.core.pipeline.Splitter.handle_size_exceed")
    async def test_run_batch_success(self, mock_split, mock_conv_class, mock_dl_class, mock_profile, tmp_path):
        """Test successful batch run."""
        mock_dl = mock_dl_class.return_value
        mock_conv = mock_conv_class.return_value
        
        pipeline = ProcessingPipeline(mock_profile)
        pipeline.history = MagicMock(spec=HistoryManager)
        pipeline.history.is_processed.return_value = False
        
        mock_dl.extract_info_async = AsyncMock(return_value={"id": "test", "title": "test"})
        mock_dl.download_video_async = AsyncMock(return_value=(Path("dl.mp4"), {"id": "test"}))
        mock_conv.convert_video_async = AsyncMock(return_value=Path("cv.mp4"))
        mock_conv.get_output_path = MagicMock(return_value=tmp_path / "expected.mp4")
        mock_split.return_value = [Path("final.mp4")]
        
        urls = ["url1", "url2", "url3"]
        
        def exists_side_effect(self_path):
            p = str(self_path)
            if "expected.mp4" in p: return False
            if "dl.mp4" in p: return True
            return False

        with patch.object(Path, "exists", autospec=True, side_effect=exists_side_effect):
            results = await pipeline.run_batch(urls, output_dir=tmp_path)
            
            assert len(results) == 3
            assert all(url in results for url in urls)
            assert mock_dl.download_video_async.call_count == 3

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    async def test_run_batch_with_exceptions(self, mock_conv_class, mock_dl_class, mock_profile, tmp_path):
        """Test batch run where some items fail."""
        pipeline = ProcessingPipeline(mock_profile)
        
        async def mock_process(url, output_dir, progress_callback=None):
            if url == "fail":
                raise Exception("Item failed")
            return [Path("ok.mp4")]
            
        with patch.object(pipeline, "process_one", side_effect=mock_process):
            urls = ["ok1", "fail", "ok2"]
            results = await pipeline.run_batch(urls, output_dir=tmp_path)
            
            assert len(results) == 2
            assert "ok1" in results
            assert "ok2" in results
            assert "fail" not in results

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    @patch("yt2audi.core.pipeline.Splitter.handle_size_exceed")
    async def test_progress_callback(self, mock_split, mock_conv_class, mock_dl_class, mock_profile, tmp_path):
        """Test that progress callback is called at each stage."""
        mock_dl = mock_dl_class.return_value
        mock_conv = mock_conv_class.return_value
        
        pipeline = ProcessingPipeline(mock_profile)
        pipeline.history = MagicMock(spec=HistoryManager)
        pipeline.history.is_processed.return_value = False
        
        # Stage 0 mock
        mock_dl.extract_info_async = AsyncMock(return_value={"id": "test", "title": "test"})

        # Download progress hook setup
        async def dl_side_effect(url, progress_callback=None):
            if progress_callback:
                progress_callback({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100})
            return Path("dl.mp4"), {"id": "test"}
            
        mock_dl.download_video_async = AsyncMock(side_effect=dl_side_effect)
        
        # Convert progress hook setup
        async def cv_side_effect(*args, **kwargs):
            progress_cb = kwargs.get('progress_callback')
            if progress_cb:
                progress_cb(50.0, "Converting")
            return Path("cv.mp4")
            
        mock_conv.convert_video_async = AsyncMock(side_effect=cv_side_effect)
        mock_conv.get_output_path = MagicMock(return_value=tmp_path / "expected.mp4")
        mock_split.return_value = [Path("final.mp4")]
        
        callback = MagicMock()
        
        def exists_side_effect(self_path):
            p = str(self_path)
            if "expected.mp4" in p: return False
            if "dl.mp4" in p: return True
            return False

        with patch.object(Path, "exists", autospec=True, side_effect=exists_side_effect):
            with patch.object(Path, "unlink", return_value=None):
                await pipeline.process_one("url", output_dir=tmp_path, progress_callback=callback)
                
                # Verify callback was called
                callback.assert_any_call("url", 50.0, "Downloading")
                callback.assert_any_call("url", 50.0, "Converting")
                callback.assert_any_call("url", 95, "Finalizing")
                callback.assert_any_call("url", 100, "Complete")
