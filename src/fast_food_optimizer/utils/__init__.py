"""Utility functions and helpers for Fast Food Route Optimizer."""

from fast_food_optimizer.utils.logging import get_logger, setup_logging
from fast_food_optimizer.utils.exceptions import (
    FastFoodOptimizerError,
    APIConnectionError,
    RouteOptimizationError,
    DataValidationError,
    ConfigurationError,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "FastFoodOptimizerError",
    "APIConnectionError",
    "RouteOptimizationError",
    "DataValidationError",
    "ConfigurationError",
]
