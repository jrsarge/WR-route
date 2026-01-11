"""Fast Food Route Optimizer - World Record Route Planning System.

This package provides tools for optimizing walking/running routes through
metropolitan areas to visit the maximum number of fast food restaurants
within 24 hours.

Core capabilities:
- Restaurant discovery using Google Maps API
- Density-based clustering for efficient routing
- Route optimization using TSP algorithms
- Interactive map visualization
- Multi-format GPS export (GPX, KML, CSV)
"""

__version__ = "0.1.0"
__author__ = "Jacob Sargent"

from fast_food_optimizer.config.settings import Config
from fast_food_optimizer.utils.exceptions import (
    FastFoodOptimizerError,
    APIConnectionError,
    RouteOptimizationError,
    DataValidationError,
    ConfigurationError,
)

__all__ = [
    "Config",
    "FastFoodOptimizerError",
    "APIConnectionError",
    "RouteOptimizationError",
    "DataValidationError",
    "ConfigurationError",
]
