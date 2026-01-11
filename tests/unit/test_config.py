"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from fast_food_optimizer.config.settings import Config, get_config
from fast_food_optimizer.utils.exceptions import ConfigurationError


class TestConfig:
    """Test suite for Config class."""

    def test_config_missing_api_key(self, monkeypatch):
        """Test that Config raises error when API key is missing."""
        monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            Config()

        assert "GOOGLE_MAPS_API_KEY" in str(exc_info.value)
        assert exc_info.value.error_code == "CFG_ERROR"

    def test_config_invalid_api_key_format(self, monkeypatch):
        """Test that Config validates API key format."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "short")

        with pytest.raises(ConfigurationError) as exc_info:
            Config()

        assert "Invalid Google Maps API key format" in str(exc_info.value)

    def test_config_valid_api_key(self, monkeypatch):
        """Test that Config accepts valid API key."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)

        config = Config()

        assert config.google_maps_api_key == "a" * 40

    def test_config_default_values(self, monkeypatch):
        """Test that Config sets correct default values."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)

        config = Config()

        assert config.google_maps_rate_limit == 50
        assert config.default_search_radius == 50000
        assert config.max_restaurants == 1000
        assert config.cluster_min_restaurants == 3
        assert config.cluster_eps_km == 0.5
        assert config.walking_speed_kmh == 5.0

    def test_config_custom_values(self, monkeypatch):
        """Test that Config loads custom environment values."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        monkeypatch.setenv("GOOGLE_MAPS_RATE_LIMIT", "100")
        monkeypatch.setenv("DEFAULT_SEARCH_RADIUS", "25000")
        monkeypatch.setenv("MAX_RESTAURANTS", "500")
        monkeypatch.setenv("WALKING_SPEED_KMH", "6.0")

        config = Config()

        assert config.google_maps_rate_limit == 100
        assert config.default_search_radius == 25000
        assert config.max_restaurants == 500
        assert config.walking_speed_kmh == 6.0

    def test_config_creates_directories(self, monkeypatch, tmp_path):
        """Test that Config creates required directories."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        monkeypatch.setenv("EXPORT_DIRECTORY", str(tmp_path / "exports"))
        monkeypatch.setenv("DATA_DIRECTORY", str(tmp_path / "data"))

        config = Config()

        assert config.export_directory.exists()
        assert config.data_directory.exists()
        assert config.cache_directory.exists()

    def test_validate_search_radius_valid(self, monkeypatch):
        """Test search radius validation with valid values."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        config = Config()

        assert config.validate_search_radius(1000) is True
        assert config.validate_search_radius(50000) is True
        assert config.validate_search_radius(100000) is True

    def test_validate_search_radius_too_small(self, monkeypatch):
        """Test search radius validation with value too small."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        config = Config()

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate_search_radius(50)

        assert "too small" in str(exc_info.value)

    def test_validate_search_radius_too_large(self, monkeypatch):
        """Test search radius validation with value too large."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        config = Config()

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate_search_radius(200000)

        assert "too large" in str(exc_info.value)

    def test_config_repr(self, monkeypatch):
        """Test Config string representation."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        config = Config()

        repr_str = repr(config)

        assert "Config(" in repr_str
        assert "rate_limit=50" in repr_str
        assert "search_radius=50000" in repr_str

    def test_get_config_singleton(self, monkeypatch):
        """Test that get_config returns same instance."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_reload(self, monkeypatch):
        """Test that get_config can reload configuration."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "a" * 40)
        config1 = get_config()

        monkeypatch.setenv("GOOGLE_MAPS_RATE_LIMIT", "100")
        config2 = get_config(reload=True)

        assert config1 is not config2
        assert config2.google_maps_rate_limit == 100

    def test_config_from_env_file(self, tmp_path, monkeypatch):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GOOGLE_MAPS_API_KEY=test_key_from_env_file_1234567890\n"
            "DEFAULT_SEARCH_RADIUS=30000\n"
        )

        # Clear environment to ensure values come from file
        monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

        config = Config(env_file=str(env_file))

        assert config.google_maps_api_key == "test_key_from_env_file_1234567890"
        assert config.default_search_radius == 30000
