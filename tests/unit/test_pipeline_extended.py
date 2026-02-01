"""Extended unit tests for Pipeline class."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from yt2audi.core.pipeline import ProcessingPipeline
from yt2audi.core.history import HistoryManager

class TestPipelineExtended:
    """Extended pipeline tests."""

    @pytest.mark.asyncio
    @patch("yt2audi.core.pipeline.Downloader")
    @patch("yt2audi.core.pipeline.Converter")
    @patch("yt2audi.core.pipeline.Splitter.handle_size_exceed")
    async def test_process_one_simple_flow(self, mock_split, mock_conv_cls, mock_dl_cls, sample_profile, tmp_path):
        """Test simple process_one flow to force coverage."""
        pipeline = ProcessingPipeline(sample_profile)
        pipeline.history = MagicMock(spec=HistoryManager)
        pipeline.history.is_processed.return_value = False
        
        mock_dl = mock_dl_cls.return_value
        mock_dl.extract_info_async = AsyncMock(return_value={"id": "test"})
        mock_dl.download_video_async = AsyncMock(return_value=(tmp_path / "dl.mp4", {"id": "test"}))
        
        mock_conv = mock_conv_cls.return_value
        mock_conv.convert_video_async = AsyncMock(return_value=tmp_path / "out.mp4")
        mock_conv.get_output_path.return_value = tmp_path / "out.mp4"
        
        mock_split.return_value = [tmp_path / "out.mp4"]
        
        # Ensure files behave
        (tmp_path / "dl.mp4").touch()
        (tmp_path / "out.mp4").touch()
        
        with patch.object(Path, "exists", return_value=False): # Force download/convert
             results = await pipeline.process_one("url", tmp_path)
             
        assert len(results) == 1
        mock_dl.download_video_async.assert_called()
        mock_conv.convert_video_async.assert_called()

