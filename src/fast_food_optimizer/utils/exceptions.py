"""Custom exception hierarchy for Fast Food Route Optimizer.

This module defines all custom exceptions used throughout the application,
providing clear error handling and user-friendly error messages.
"""

from typing import Optional


class FastFoodOptimizerError(Exception):
    """Base exception for all Fast Food Route Optimizer errors.

    All custom exceptions in this application should inherit from this base class
    to enable consistent error handling and logging.

    Attributes:
        message: Human-readable error message
        error_code: Optional error code for programmatic handling
        context: Optional additional context about the error
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize the exception with message and optional context.

        Args:
            message: Human-readable error message
            error_code: Optional error code (e.g., "API_001")
            context: Optional dictionary with additional error context
        """
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed error representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"context={self.context!r}"
            f")"
        )


class ConfigurationError(FastFoodOptimizerError):
    """Raised when configuration is missing or invalid.

    This exception is raised during application initialization when required
    configuration settings are missing, invalid, or improperly formatted.

    Example:
        >>> raise ConfigurationError(
        ...     "Google Maps API key not configured",
        ...     error_code="CFG_001"
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Description of the configuration problem
            error_code: Optional error code (default: "CFG_ERROR")
            context: Optional additional context
        """
        super().__init__(
            message,
            error_code or "CFG_ERROR",
            context,
        )


class APIConnectionError(FastFoodOptimizerError):
    """Raised when Google Maps API connection fails.

    This exception is raised when there are issues communicating with the
    Google Maps API, including network errors, authentication failures, and
    API quota exceeded errors.

    Example:
        >>> raise APIConnectionError(
        ...     "Failed to connect to Google Maps API",
        ...     error_code="API_001",
        ...     context={"status_code": 401}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize API connection error.

        Args:
            message: Description of the API error
            error_code: Optional error code (default: "API_ERROR")
            context: Optional context (HTTP status, response body, etc.)
        """
        super().__init__(
            message,
            error_code or "API_ERROR",
            context,
        )


class DataValidationError(FastFoodOptimizerError):
    """Raised when data validation fails.

    This exception is raised when restaurant data, coordinates, or other
    input data fails validation checks. It includes information about which
    validation rules failed.

    Example:
        >>> raise DataValidationError(
        ...     "Invalid latitude value",
        ...     error_code="VAL_001",
        ...     context={"latitude": 200.0, "expected_range": "[-90, 90]"}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize data validation error.

        Args:
            message: Description of the validation failure
            error_code: Optional error code (default: "VAL_ERROR")
            context: Optional context (invalid values, validation rules, etc.)
        """
        super().__init__(
            message,
            error_code or "VAL_ERROR",
            context,
        )


class RouteOptimizationError(FastFoodOptimizerError):
    """Raised when route optimization fails.

    This exception is raised when the route optimization algorithms fail to
    find a solution, encounter computational issues, or produce invalid routes.

    Example:
        >>> raise RouteOptimizationError(
        ...     "TSP solver failed to converge",
        ...     error_code="OPT_001",
        ...     context={"algorithm": "nearest_neighbor", "iterations": 1000}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize route optimization error.

        Args:
            message: Description of the optimization failure
            error_code: Optional error code (default: "OPT_ERROR")
            context: Optional context (algorithm details, input size, etc.)
        """
        super().__init__(
            message,
            error_code or "OPT_ERROR",
            context,
        )


class ClusteringError(FastFoodOptimizerError):
    """Raised when restaurant clustering fails.

    This exception is raised when density-based clustering algorithms fail
    to group restaurants properly or encounter computational issues.

    Example:
        >>> raise ClusteringError(
        ...     "DBSCAN clustering produced no valid clusters",
        ...     error_code="CLU_001",
        ...     context={"eps": 0.5, "min_samples": 3, "restaurants": 100}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize clustering error.

        Args:
            message: Description of the clustering failure
            error_code: Optional error code (default: "CLU_ERROR")
            context: Optional context (algorithm parameters, data size, etc.)
        """
        super().__init__(
            message,
            error_code or "CLU_ERROR",
            context,
        )


class ExportError(FastFoodOptimizerError):
    """Raised when data export fails.

    This exception is raised when exporting route data to GPX, CSV, KML, or
    other formats fails due to formatting issues, file system errors, or
    invalid data.

    Example:
        >>> raise ExportError(
        ...     "Failed to write GPX file",
        ...     error_code="EXP_001",
        ...     context={"format": "gpx", "path": "/path/to/file.gpx"}
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """Initialize export error.

        Args:
            message: Description of the export failure
            error_code: Optional error code (default: "EXP_ERROR")
            context: Optional context (format, file path, etc.)
        """
        super().__init__(
            message,
            error_code or "EXP_ERROR",
            context,
        )


# Error code constants for common scenarios
class ErrorCodes:
    """Common error codes for programmatic error handling."""

    # Configuration errors
    CFG_MISSING_API_KEY = "CFG_001"
    CFG_INVALID_API_KEY = "CFG_002"
    CFG_INVALID_SETTING = "CFG_003"

    # API errors
    API_CONNECTION_FAILED = "API_001"
    API_AUTH_FAILED = "API_002"
    API_QUOTA_EXCEEDED = "API_003"
    API_RATE_LIMITED = "API_004"
    API_INVALID_RESPONSE = "API_005"

    # Validation errors
    VAL_INVALID_COORDINATES = "VAL_001"
    VAL_MISSING_REQUIRED_FIELD = "VAL_002"
    VAL_INVALID_DATA_FORMAT = "VAL_003"

    # Optimization errors
    OPT_NO_SOLUTION = "OPT_001"
    OPT_TIMEOUT = "OPT_002"
    OPT_INVALID_INPUT = "OPT_003"

    # Clustering errors
    CLU_NO_CLUSTERS = "CLU_001"
    CLU_INVALID_PARAMETERS = "CLU_002"

    # Export errors
    EXP_FILE_WRITE_FAILED = "EXP_001"
    EXP_INVALID_FORMAT = "EXP_002"
