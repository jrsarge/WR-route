"""Unit tests for custom exceptions."""

import pytest

from fast_food_optimizer.utils.exceptions import (
    APIConnectionError,
    ClusteringError,
    ConfigurationError,
    DataValidationError,
    ErrorCodes,
    ExportError,
    FastFoodOptimizerError,
    RouteOptimizationError,
)


class TestFastFoodOptimizerError:
    """Test suite for base exception class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        error = FastFoodOptimizerError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.context == {}

    def test_exception_with_error_code(self):
        """Test exception with error code."""
        error = FastFoodOptimizerError(
            "Test error",
            error_code="TEST_001"
        )

        assert str(error) == "[TEST_001] Test error"
        assert error.error_code == "TEST_001"

    def test_exception_with_context(self):
        """Test exception with additional context."""
        context = {"field": "value", "count": 42}
        error = FastFoodOptimizerError(
            "Test error",
            error_code="TEST_001",
            context=context,
        )

        assert error.context == context
        assert error.context["field"] == "value"
        assert error.context["count"] == 42

    def test_exception_repr(self):
        """Test exception string representation."""
        error = FastFoodOptimizerError(
            "Test error",
            error_code="TEST_001",
            context={"key": "value"},
        )

        repr_str = repr(error)

        assert "FastFoodOptimizerError" in repr_str
        assert "Test error" in repr_str
        assert "TEST_001" in repr_str


class TestConfigurationError:
    """Test suite for ConfigurationError."""

    def test_configuration_error(self):
        """Test ConfigurationError with default error code."""
        error = ConfigurationError("Invalid configuration")

        assert str(error) == "[CFG_ERROR] Invalid configuration"
        assert error.error_code == "CFG_ERROR"

    def test_configuration_error_custom_code(self):
        """Test ConfigurationError with custom error code."""
        error = ConfigurationError(
            "Invalid API key",
            error_code="CFG_002"
        )

        assert error.error_code == "CFG_002"


class TestAPIConnectionError:
    """Test suite for APIConnectionError."""

    def test_api_connection_error(self):
        """Test APIConnectionError with default error code."""
        error = APIConnectionError("Failed to connect")

        assert str(error) == "[API_ERROR] Failed to connect"
        assert error.error_code == "API_ERROR"

    def test_api_connection_error_with_context(self):
        """Test APIConnectionError with HTTP context."""
        error = APIConnectionError(
            "API request failed",
            error_code="API_001",
            context={"status_code": 401, "response": "Unauthorized"},
        )

        assert error.context["status_code"] == 401
        assert error.context["response"] == "Unauthorized"


class TestDataValidationError:
    """Test suite for DataValidationError."""

    def test_data_validation_error(self):
        """Test DataValidationError with validation context."""
        error = DataValidationError(
            "Invalid coordinates",
            error_code="VAL_001",
            context={
                "latitude": 200.0,
                "expected_range": "[-90, 90]"
            },
        )

        assert error.error_code == "VAL_001"
        assert error.context["latitude"] == 200.0


class TestRouteOptimizationError:
    """Test suite for RouteOptimizationError."""

    def test_route_optimization_error(self):
        """Test RouteOptimizationError with algorithm context."""
        error = RouteOptimizationError(
            "TSP solver failed",
            error_code="OPT_001",
            context={"algorithm": "nearest_neighbor", "iterations": 1000},
        )

        assert error.error_code == "OPT_001"
        assert error.context["algorithm"] == "nearest_neighbor"


class TestClusteringError:
    """Test suite for ClusteringError."""

    def test_clustering_error(self):
        """Test ClusteringError with clustering parameters."""
        error = ClusteringError(
            "No clusters found",
            error_code="CLU_001",
            context={"eps": 0.5, "min_samples": 3},
        )

        assert error.error_code == "CLU_001"
        assert error.context["eps"] == 0.5


class TestExportError:
    """Test suite for ExportError."""

    def test_export_error(self):
        """Test ExportError with file context."""
        error = ExportError(
            "Failed to write file",
            error_code="EXP_001",
            context={"format": "gpx", "path": "/path/to/file.gpx"},
        )

        assert error.error_code == "EXP_001"
        assert error.context["format"] == "gpx"


class TestErrorCodes:
    """Test suite for ErrorCodes constants."""

    def test_error_codes_exist(self):
        """Test that all documented error codes exist."""
        # Configuration errors
        assert ErrorCodes.CFG_MISSING_API_KEY == "CFG_001"
        assert ErrorCodes.CFG_INVALID_API_KEY == "CFG_002"
        assert ErrorCodes.CFG_INVALID_SETTING == "CFG_003"

        # API errors
        assert ErrorCodes.API_CONNECTION_FAILED == "API_001"
        assert ErrorCodes.API_AUTH_FAILED == "API_002"
        assert ErrorCodes.API_QUOTA_EXCEEDED == "API_003"
        assert ErrorCodes.API_RATE_LIMITED == "API_004"
        assert ErrorCodes.API_INVALID_RESPONSE == "API_005"

        # Validation errors
        assert ErrorCodes.VAL_INVALID_COORDINATES == "VAL_001"
        assert ErrorCodes.VAL_MISSING_REQUIRED_FIELD == "VAL_002"
        assert ErrorCodes.VAL_INVALID_DATA_FORMAT == "VAL_003"

        # Optimization errors
        assert ErrorCodes.OPT_NO_SOLUTION == "OPT_001"
        assert ErrorCodes.OPT_TIMEOUT == "OPT_002"
        assert ErrorCodes.OPT_INVALID_INPUT == "OPT_003"

        # Clustering errors
        assert ErrorCodes.CLU_NO_CLUSTERS == "CLU_001"
        assert ErrorCodes.CLU_INVALID_PARAMETERS == "CLU_002"

        # Export errors
        assert ErrorCodes.EXP_FILE_WRITE_FAILED == "EXP_001"
        assert ErrorCodes.EXP_INVALID_FORMAT == "EXP_002"
