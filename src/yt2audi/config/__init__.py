"""Configuration management for YT2Audi."""

from yt2audi.config.defaults import get_default_profile
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

__all__ = [
    "get_default_profile",
    "expand_path",
    "get_bundled_profiles_dir",
    "get_config_dir",
    "get_user_profiles_dir",
    "list_available_profiles",
    "load_app_config",
    "load_profile",
    "save_app_config",
]
