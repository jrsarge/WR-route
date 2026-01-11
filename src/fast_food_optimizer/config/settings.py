"""Configuration management for Fast Food Route Optimizer.

This module handles loading and validation of configuration settings from
environment variables and provides a centralized Config class for accessing
application settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from fast_food_optimizer.utils.exceptions import ConfigurationError


class Config:
    """Central configuration management for the application.

    Loads configuration from environment variables with sensible defaults.
    Validates critical settings on initialization.

    Example:
        >>> config = Config()
        >>> api_key = config.google_maps_api_key
        >>> radius = config.default_search_radius
    """

    def __init__(self, env_file: Optional[str] = None) -> None:
        """Initialize configuration by loading environment variables.

        Args:
            env_file: Optional path to .env file. If None, looks for .env in
                     current directory and parent directories.

        Raises:
            ConfigurationError: If required configuration is missing or invalid.
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Google Maps API Configuration
        self._google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self._validate_api_key()

        # API Rate Limiting
        self.google_maps_rate_limit = int(
            os.getenv("GOOGLE_MAPS_RATE_LIMIT", "50")
        )

        # Search Configuration
        self.default_search_radius = int(
            os.getenv("DEFAULT_SEARCH_RADIUS", "50000")
        )
        self.max_restaurants = int(os.getenv("MAX_RESTAURANTS", "1000"))

        # Optimization Settings
        self.cluster_min_restaurants = int(
            os.getenv("CLUSTER_MIN_RESTAURANTS", "3")
        )
        self.cluster_eps_km = float(os.getenv("CLUSTER_EPS_KM", "0.5"))
        self.walking_speed_kmh = float(os.getenv("WALKING_SPEED_KMH", "5.0"))

        # Output Configuration
        self.export_directory = Path(
            os.getenv("EXPORT_DIRECTORY", "./exports")
        )
        self.data_directory = Path(os.getenv("DATA_DIRECTORY", "./data"))
        self.cache_directory = self.data_directory / "cache"

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE")

        # Create directories if they don't exist
        self.export_directory.mkdir(parents=True, exist_ok=True)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.cache_directory.mkdir(parents=True, exist_ok=True)

    @property
    def google_maps_api_key(self) -> str:
        """Get Google Maps API key.

        Returns:
            Google Maps API key string.

        Raises:
            ConfigurationError: If API key is not configured.
        """
        if not self._google_maps_api_key:
            raise ConfigurationError(
                "Google Maps API key not configured. "
                "Set GOOGLE_MAPS_API_KEY environment variable."
            )
        return self._google_maps_api_key

    def _validate_api_key(self) -> None:
        """Validate Google Maps API key format.

        Raises:
            ConfigurationError: If API key format is invalid.
        """
        if not self._google_maps_api_key:
            raise ConfigurationError(
                "GOOGLE_MAPS_API_KEY environment variable is required. "
                "Get your API key from https://console.cloud.google.com/"
            )

        if len(self._google_maps_api_key) < 20:
            raise ConfigurationError(
                f"Invalid Google Maps API key format. "
                f"Expected at least 20 characters, got {len(self._google_maps_api_key)}"
            )

    def validate_search_radius(self, radius: int) -> bool:
        """Validate search radius value.

        Args:
            radius: Search radius in meters.

        Returns:
            True if valid.

        Raises:
            ConfigurationError: If radius is invalid.
        """
        if radius < 100:
            raise ConfigurationError(
                f"Search radius too small: {radius}m. Minimum is 100m."
            )
        if radius > 100000:
            raise ConfigurationError(
                f"Search radius too large: {radius}m. Maximum is 100km."
            )
        return True

    def __repr__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        return (
            f"Config("
            f"rate_limit={self.google_maps_rate_limit}, "
            f"search_radius={self.default_search_radius}m, "
            f"max_restaurants={self.max_restaurants}, "
            f"walking_speed={self.walking_speed_kmh}km/h"
            f")"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get global configuration instance.

    Args:
        reload: If True, reload configuration from environment.

    Returns:
        Global Config instance.

    Example:
        >>> config = get_config()
        >>> api_key = config.google_maps_api_key
    """
    global _config
    if _config is None or reload:
        _config = Config()
    return _config
