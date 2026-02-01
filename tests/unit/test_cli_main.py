"""Unit tests for the CLI main entry point."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner
import yt2audi
from yt2audi.cli.main import app, _manual_parse_args, version_callback

runner = CliRunner()

class TestCLIMain:
    """Test suite for CLI main application."""

    def test_manual_parse_args(self):
        """Test the manual argument parser helper."""
        value_opts = {"--profile", "-p"}
        args = ["url", "--profile", "test", "-p", "other", "--flag"]
        pos, opts = _manual_parse_args(args, value_opts)
        
        assert pos == ["url"]
        assert opts["--profile"] == "test"
        assert opts["-p"] == "other"
        assert opts["--flag"] is True

    def test_version_callback(self):
        """Test the version callback directly."""
        with patch("yt2audi.cli.main.console.print") as mock_print:
            with pytest.raises(typer.Exit):
                version_callback(True)
            mock_print.assert_called()
            assert any(yt2audi.__version__ in str(arg) for arg in mock_print.call_args[0])

    @patch("yt2audi.cli.main.load_profile")
    @patch("yt2audi.cli.main.configure_logging")
    @patch("yt2audi.cli.main.Downloader")
    @patch("yt2audi.cli.main.Converter")
    @patch("yt2audi.cli.helpers.process_single_video")
    def test_download_command(self, mock_process, mock_conv_class, mock_dl_class, mock_log, mock_load, sample_profile, tmp_path):
        """Test 'download' command execution."""
        mock_load.return_value = sample_profile
        mock_process.return_value = [Path("out.mp4")]
        
        # Invoke command
        result = runner.invoke(app, ["download", "https://youtube.com/watch?v=123", "-p", "test_profile"])
        
        assert result.exit_code == 0
        assert "Complete!" in result.stdout
        mock_load.assert_called_with("test_profile")
        mock_process.assert_called_once()

    def test_download_command_missing_url(self):
        """Test 'download' command fails without URL."""
        result = runner.invoke(app, ["download"])
        assert result.exit_code == 1
        assert "Missing argument 'URL'" in result.stdout

    @patch("yt2audi.cli.main.load_profile")
    @patch("yt2audi.core.pipeline.ProcessingPipeline")
    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    def test_batch_command_success(self, mock_set, mock_new, mock_pipeline_class, mock_load, sample_profile, tmp_path):
        """Test 'batch' command execution."""
        mock_load.return_value = sample_profile
        urls_file = tmp_path / "urls.txt"
        urls_file.write_text("https://url1\n#comment\nhttps://url2")
        
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_new.return_value = mock_loop
        mock_loop.run_until_complete.return_value = ["url1", "url2"]
        
        result = runner.invoke(app, ["batch", str(urls_file)])
        
        assert result.exit_code == 0
        assert "Summary:" in result.stdout
        assert "Succeeded: 2" in result.stdout

    @patch("yt2audi.cli.main.load_profile")
    @patch("yt2audi.cli.main.Downloader")
    @patch("yt2audi.core.pipeline.ProcessingPipeline")
    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    def test_playlist_command_success(self, mock_set, mock_new, mock_pipeline_class, mock_dl_class, mock_load, sample_profile):
        """Test 'playlist' command execution."""
        mock_load.return_value = sample_profile
        mock_dl = mock_dl_class.return_value
        mock_dl.get_playlist_urls.return_value = ["url1", "url2"]
        
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_new.return_value = mock_loop
        mock_loop.run_until_complete.return_value = ["url1", "url2"]
        
        result = runner.invoke(app, ["playlist", "https://playlist_url"])
        
        assert result.exit_code == 0
        assert "Found 2 videos" in result.stdout
        assert "Succeeded: 2" in result.stdout

    @patch("yt2audi.cli.main.list_available_profiles")
    @patch("yt2audi.cli.main.load_profile")
    def test_profiles_command(self, mock_load, mock_list):
        """Test 'profiles' command execution."""
        mock_list.return_value = ["prof1", "prof2"]
        mock_prof = MagicMock()
        mock_prof.profile.description = "Test Description"
        mock_prof.profile.name = "Profile Name"
        mock_load.return_value = mock_prof
        
        result = runner.invoke(app, ["profiles"])
        
        assert result.exit_code == 0
        assert "prof1" in result.stdout
        assert "prof2" in result.stdout
        assert "Test Description" in result.stdout
