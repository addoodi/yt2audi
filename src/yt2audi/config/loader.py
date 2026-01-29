"""Configuration loading and management."""

import os
from pathlib import Path

from yt2audi.exceptions import ConfigError
from yt2audi.models.profile import AppConfig, Profile


def get_config_dir() -> Path:
    """Get the user configuration directory.

    Returns:
        Path to configuration directory

    Platform-specific:
        - Windows: %APPDATA%\\yt2audi
        - macOS/Linux: ~/.config/yt2audi
    """
    if os.name == "nt":  # Windows
        appdata = os.getenv("APPDATA")
        if not appdata:
            raise ConfigError("APPDATA environment variable not set")
        return Path(appdata) / "yt2audi"
    else:  # macOS/Linux
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "yt2audi"
        return Path.home() / ".config" / "yt2audi"


def get_bundled_profiles_dir() -> Path:
    """Get the bundled profiles directory.

    Returns:
        Path to bundled profiles directory
    """
    # When running from source
    project_root = Path(__file__).parent.parent.parent.parent
    bundled_path = project_root / "configs" / "profiles"

    if bundled_path.exists():
        return bundled_path

    # When running from PyInstaller bundle
    import sys

    if getattr(sys, "frozen", False):
        bundle_dir = Path(sys._MEIPASS)  # type: ignore
        return bundle_dir / "configs" / "profiles"

    raise ConfigError(f"Bundled profiles directory not found: {bundled_path}")


def get_user_profiles_dir() -> Path:
    """Get the user profiles directory.

    Returns:
        Path to user profiles directory
    """
    return get_config_dir() / "profiles"


def list_available_profiles() -> list[str]:
    """List all available profile names.

    Returns:
        List of profile names (without .toml extension)

    Looks in:
        1. User profiles directory
        2. Bundled profiles directory
    """
    profiles = set()

    # Check user profiles
    user_dir = get_user_profiles_dir()
    if user_dir.exists():
        for path in user_dir.glob("*.toml"):
            profiles.add(path.stem)

    # Check bundled profiles
    try:
        bundled_dir = get_bundled_profiles_dir()
        for path in bundled_dir.glob("*.toml"):
            profiles.add(path.stem)
    except ConfigError:
        pass  # No bundled profiles available

    return sorted(profiles)


def load_profile(name: str) -> Profile:
    """Load a profile by name.

    Args:
        name: Profile name (without .toml extension)

    Returns:
        Loaded and validated Profile

    Raises:
        ConfigError: If profile not found or invalid

    Precedence:
        1. User profile (~/.config/yt2audi/profiles/{name}.toml)
        2. Bundled profile (configs/profiles/{name}.toml)
    """
    # Try user profile first
    user_path = get_user_profiles_dir() / f"{name}.toml"
    if user_path.exists():
        return Profile.from_toml_file(user_path)

    # Try bundled profile
    try:
        bundled_path = get_bundled_profiles_dir() / f"{name}.toml"
        if bundled_path.exists():
            return Profile.from_toml_file(bundled_path)
    except ConfigError:
        pass

    # Profile not found
    available = list_available_profiles()
    raise ConfigError(
        f"Profile '{name}' not found. Available profiles: {', '.join(available)}"
    )


def load_app_config() -> AppConfig:
    """Load application configuration.

    Returns:
        Loaded and validated AppConfig

    Loads from ~/.config/yt2audi/app.toml if it exists,
    otherwise returns default configuration.
    """
    config_path = get_config_dir() / "app.toml"

    if not config_path.exists():
        return AppConfig()

    try:
        import tomli

        with open(config_path, "rb") as f:
            data = tomli.load(f)
        return AppConfig(**data)
    except Exception as e:
        raise ConfigError(f"Failed to load app config from {config_path}: {e}") from e


def save_app_config(config: AppConfig) -> None:
    """Save application configuration.

    Args:
        config: AppConfig instance to save

    Raises:
        ConfigError: If save fails
    """
    config_path = get_config_dir() / "app.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import tomli_w

        with open(config_path, "wb") as f:
            tomli_w.dump(config.model_dump(), f)
    except Exception as e:
        raise ConfigError(f"Failed to save app config to {config_path}: {e}") from e


def expand_path(path: str) -> Path:
    """Expand user home and environment variables in path.

    Args:
        path: Path string (may contain ~ or env vars)

    Returns:
        Expanded Path object
    """
    return Path(os.path.expandvars(os.path.expanduser(path)))
