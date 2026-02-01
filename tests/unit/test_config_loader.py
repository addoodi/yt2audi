"""Unit tests for configuration loading."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt2audi.config.loader import (
    expand_path,
    get_bundled_profiles_dir,
    get_config_dir,
    get_user_profiles_dir,
    list_available_profiles,
    load_app_config,
    load_profile,
    save_app_config,
)
from yt2audi.exceptions import ConfigError
from yt2audi.models.profile import AppConfig


class TestGetConfigDir:
    """Test suite for get_config_dir function."""

    @patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"})
    @patch("os.name", "nt")
    def test_get_config_dir_windows(self) -> None:
        """Test config directory on Windows."""
        result = get_config_dir()
        assert result == Path("C:\\Users\\Test\\AppData\\Roaming\\yt2audi")

    @patch.dict(os.environ, {"APPDATA": ""}, clear=True)
    @patch("os.name", "nt")
    def test_get_config_dir_windows_no_appdata(self) -> None:
        """Test config directory on Windows without APPDATA."""
        with pytest.raises(ConfigError, match="APPDATA"):
            get_config_dir()

    @patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"})
    @patch("os.name", "posix")
    @patch("yt2audi.config.loader.Path")
    def test_get_config_dir_linux_with_xdg(self, mock_path: Mock) -> None:
        """Test config directory on Linux with XDG_CONFIG_HOME."""
        # Setup mock to behave like a path
        mock_path.side_effect = lambda *args: MagicMock()
        
        result = get_config_dir()
        
        # Verify it was called with XDG_CONFIG_HOME
        mock_path.assert_any_call("/custom/config")

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.name", "posix")
    @patch("yt2audi.config.loader.Path")
    @patch("pathlib.Path.home")
    def test_get_config_dir_linux_without_xdg(self, mock_home: Mock, mock_path: Mock) -> None:
        """Test config directory on Linux without XDG_CONFIG_HOME."""
        mock_home.return_value = MagicMock()
        mock_path.return_value = MagicMock()
        
        get_config_dir()
        
        mock_path.home.assert_called_once()


class TestGetBundledProfilesDir:
    """Test suite for get_bundled_profiles_dir function."""

    def test_get_bundled_profiles_dir_from_source(self) -> None:
        """Test getting bundled profiles directory when running from source."""
        result = get_bundled_profiles_dir()
        # Should find configs/profiles relative to project root
        assert result.name == "profiles"
        assert result.parent.name == "configs"

    @patch("sys.frozen", True, create=True)
    @patch("sys._MEIPASS", "/path/to/bundle", create=True)
    def test_get_bundled_profiles_dir_frozen(self) -> None:
        """Test getting bundled profiles directory when frozen (PyInstaller)."""
        with patch("pathlib.Path.exists") as mock_exists:
            # First exists() call returns False (not running from source)
            mock_exists.return_value = False

            result = get_bundled_profiles_dir()
            assert str(result).replace("\\", "/") == "/path/to/bundle/configs/profiles"


class TestGetUserProfilesDir:
    """Test suite for get_user_profiles_dir function."""

    @patch("yt2audi.config.loader.get_config_dir")
    def test_get_user_profiles_dir(self, mock_config_dir: Mock) -> None:
        """Test getting user profiles directory."""
        mock_config_dir.return_value = Path("/home/user/.config/yt2audi")
        result = get_user_profiles_dir()
        assert str(result).replace("\\", "/") == "/home/user/.config/yt2audi/profiles"


class TestListAvailableProfiles:
    """Test suite for list_available_profiles function."""

    def test_list_available_profiles_bundled_only(self, temp_dir: Path) -> None:
        """Test listing profiles from bundled directory only."""
        # Create fake bundled profiles
        bundled_dir = temp_dir / "bundled"
        bundled_dir.mkdir()
        (bundled_dir / "profile1.toml").touch()
        (bundled_dir / "profile2.toml").touch()

        with patch("yt2audi.config.loader.get_user_profiles_dir") as mock_user:
            with patch("yt2audi.config.loader.get_bundled_profiles_dir") as mock_bundled:
                mock_user.return_value = temp_dir / "nonexistent"
                mock_bundled.return_value = bundled_dir

                result = list_available_profiles()

                assert len(result) == 2
                assert "profile1" in result
                assert "profile2" in result
                assert result == sorted(result)  # Should be sorted

    def test_list_available_profiles_user_override(self, temp_dir: Path) -> None:
        """Test that user profiles override bundled profiles."""
        # Create bundled and user profiles
        bundled_dir = temp_dir / "bundled"
        user_dir = temp_dir / "user"
        bundled_dir.mkdir()
        user_dir.mkdir()

        (bundled_dir / "profile1.toml").touch()
        (bundled_dir / "profile2.toml").touch()
        (user_dir / "profile1.toml").touch()  # Override
        (user_dir / "custom.toml").touch()

        with patch("yt2audi.config.loader.get_user_profiles_dir") as mock_user:
            with patch("yt2audi.config.loader.get_bundled_profiles_dir") as mock_bundled:
                mock_user.return_value = user_dir
                mock_bundled.return_value = bundled_dir

                result = list_available_profiles()

                # Should have unique profiles (set deduplication)
                assert len(result) == 3
                assert "profile1" in result
                assert "profile2" in result
                assert "custom" in result


class TestLoadProfile:
    """Test suite for load_profile function."""

    def test_load_profile_from_user_dir(self, temp_dir: Path, sample_profile) -> None:
        """Test loading profile from user directory."""
        user_dir = temp_dir / "user_profiles"
        user_dir.mkdir()

        profile_path = user_dir / "test_profile.toml"

        # Write a minimal TOML profile
        profile_path.write_text(
            """
[profile]
name = "Test Profile"
description = "Test"
version = "1.0.0"

[video]
max_width = 1280
max_height = 720
maintain_aspect_ratio = true
codec = "h264"
profile = "main"
level = "4.0"
pixel_format = "yuv420p"
max_bitrate_mbps = 5.0
max_fps = 30
quality_cq = 23
encoder_priority = ["libx264"]
extra_video_args = []

[audio]
codec = "aac"
bitrate_kbps = 128
sample_rate = 44100
channels = 2
extra_audio_args = []

[subtitles]
embed = false
languages = []
auto_generate = false
burn_in = false

[output]
container = "mp4"
faststart = true
output_dir = "./output"
filename_template = "{title}.{ext}"
max_file_size_gb = 10.0
on_size_exceed = "warn"
split_part_template = "{stem}_part{num:03d}.{ext}"
target_bitrate_reduction = 0.8

[transfer]
usb_auto_copy = false
network_copy = false
verify_checksum = false
delete_after_transfer = false

[download]
format_preference = "best"
retries = 3
fragment_retries = 10
playlist_start = 1
playlist_reverse = false

[logging]
level = "INFO"
format = "json"
rotation_size_mb = 10
rotation_count = 5
"""
        )

        with patch("yt2audi.config.loader.get_user_profiles_dir") as mock_user:
            mock_user.return_value = user_dir

            result = load_profile("test_profile")

            assert result.profile.name == "Test Profile"
            assert result.video.max_width == 1280

    def test_load_profile_not_found(self, temp_dir: Path) -> None:
        """Test loading non-existent profile."""
        with patch("yt2audi.config.loader.get_user_profiles_dir") as mock_user:
            with patch("yt2audi.config.loader.get_bundled_profiles_dir") as mock_bundled:
                with patch("yt2audi.config.loader.list_available_profiles") as mock_list:
                    mock_user.return_value = temp_dir / "nonexistent"
                    mock_bundled.return_value = temp_dir / "nonexistent2"
                    mock_list.return_value = ["profile1", "profile2"]

                    with pytest.raises(ConfigError, match="Profile 'missing' not found"):
                        load_profile("missing")


class TestLoadAppConfig:
    """Test suite for load_app_config function."""

    def test_load_app_config_default(self, temp_dir: Path) -> None:
        """Test loading app config with default values."""
        with patch("yt2audi.config.loader.get_config_dir") as mock_dir:
            mock_dir.return_value = temp_dir / "nonexistent"

            result = load_app_config()

            # Should return default AppConfig
            assert isinstance(result, AppConfig)

    def test_load_app_config_from_file(self, temp_dir: Path) -> None:
        """Test loading app config from file."""
        config_dir = temp_dir / "config"
        config_dir.mkdir()

        app_config_path = config_dir / "app.toml"
        app_config_path.write_text(
            """
[app]
default_profile = "custom_profile"
concurrent_downloads = 4
concurrent_conversions = 4
temp_dir = "/custom/temp"
"""
        )

        with patch("yt2audi.config.loader.get_config_dir") as mock_dir:
            mock_dir.return_value = config_dir

            result = load_app_config()

            assert result.app.default_profile == "custom_profile"
            assert result.app.concurrent_downloads == 4


class TestSaveAppConfig:
    """Test suite for save_app_config function."""

    def test_save_app_config(self, temp_dir: Path) -> None:
        """Test saving app config to file."""
        config_dir = temp_dir / "config"

        config = AppConfig()
        config.app.default_profile = "test_profile"

        with patch("yt2audi.config.loader.get_config_dir") as mock_dir:
            mock_dir.return_value = config_dir

            save_app_config(config)

            # Verify file was created
            saved_path = config_dir / "app.toml"
            assert saved_path.exists()

            # Verify content
            content = saved_path.read_text()
            assert "test_profile" in content


class TestExpandPath:
    """Test suite for expand_path function."""

    @patch("os.path.expanduser")
    @patch("pathlib.Path.home")
    def test_expand_path_with_tilde(self, mock_home: Mock, mock_expanduser: Mock) -> None:
        """Test expanding path with ~ (home directory)."""
        mock_home.return_value = Path("/home/testuser")
        mock_expanduser.side_effect = lambda p: p.replace("~", "/home/testuser")

        result = expand_path("~/documents/file.txt")

        assert str(result).replace("\\", "/") == "/home/testuser/documents/file.txt"

    @patch.dict(os.environ, {"MY_VAR": "/custom/path"})
    def test_expand_path_with_env_var(self) -> None:
        """Test expanding path with environment variable."""
        result = expand_path("$MY_VAR/file.txt")

        assert str(result).replace("\\", "/") == "/custom/path/file.txt"

    @patch("os.path.expanduser")
    @patch("pathlib.Path.home")
    @patch.dict(os.environ, {"DATA_DIR": "/data"})
    def test_expand_path_with_both(self, mock_home: Mock, mock_expanduser: Mock) -> None:
        """Test expanding path with both ~ and environment variable."""
        mock_home.return_value = Path("/home/user")
        mock_expanduser.side_effect = lambda p: p.replace("~", "/home/user")

        result = expand_path("~/$DATA_DIR/file.txt")

        assert str(result).replace("\\", "/") == "/home/user/data/file.txt"
