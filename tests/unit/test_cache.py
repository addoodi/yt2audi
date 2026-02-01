"""Unit tests for the MetadataCache class."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt2audi.core.cache import MetadataCache

class TestMetadataCache:
    """Test suite for MetadataCache class."""

    def test_init_default_path(self, tmp_path):
        """Test initialization with default path."""
        with patch("yt2audi.core.cache.get_config_dir", return_value=tmp_path):
            cache = MetadataCache()
            assert cache.cache_file == tmp_path / "cache" / "metadata.json"

    def test_load_cache_success(self, tmp_path):
        """Test successful cache loading from disk."""
        cache_file = tmp_path / "cache.json"
        data = {"url1": {"data": {"id": "1"}, "_cached_at": time.time()}}
        cache_file.write_text(json.dumps(data))
        
        cache = MetadataCache(cache_file=cache_file)
        assert cache.get("url1") == {"id": "1"}

    def test_load_cache_corrupted(self, tmp_path):
        """Test handling of corrupted cache file."""
        cache_file = tmp_path / "bad.json"
        cache_file.write_text("{broken json")
        
        cache = MetadataCache(cache_file=cache_file)
        assert cache._cache == {}

    def test_get_expired(self, tmp_path):
        """Test that expired entries are handled correctly."""
        cache_file = tmp_path / "cache.json"
        # 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        data = {"url_old": {"data": {"id": "old"}, "_cached_at": old_time}}
        cache_file.write_text(json.dumps(data))
        
        cache = MetadataCache(cache_file=cache_file, expiration_days=7)
        assert cache.get("url_old") is None
        assert "url_old" not in cache._cache

    def test_set_and_save(self, tmp_path):
        """Test setting an entry and verify it's saved to disk."""
        cache_file = tmp_path / "new_cache.json"
        cache = MetadataCache(cache_file=cache_file)
        
        info = {"id": "v123", "title": "Video"}
        cache.set("url123", info)
        
        assert cache_file.exists()
        with open(cache_file, "r") as f:
            saved_data = json.load(f)
            assert "url123" in saved_data
            assert saved_data["url123"]["data"] == info

    def test_clear(self, tmp_path):
        """Test clearing the cache."""
        cache_file = tmp_path / "clear_me.json"
        cache_file.touch()
        cache = MetadataCache(cache_file=cache_file)
        cache._cache = {"a": "b"}
        
        cache.clear()
        assert cache._cache == {}
        assert not cache_file.exists()
