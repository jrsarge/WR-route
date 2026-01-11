"""Unit tests for logging utilities."""

import logging
import tempfile
import time
from pathlib import Path

import pytest

from fast_food_optimizer.utils.logging import (
    ProgressLogger,
    get_logger,
    log_api_call,
    log_performance,
    setup_logging,
)


class TestLogging:
    """Test suite for logging setup and configuration."""

    def test_setup_logging_console_only(self):
        """Test logging setup with console output only."""
        setup_logging(level="INFO", console=True)

        logger = logging.getLogger()
        assert logger.level == logging.INFO
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"

        setup_logging(level="DEBUG", log_file=str(log_file), console=False)

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert log_file.exists()

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that logging setup creates log directory if needed."""
        log_file = tmp_path / "logs" / "test.log"

        setup_logging(log_file=str(log_file))

        assert log_file.parent.exists()
        assert log_file.exists()

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"


class TestLogPerformanceDecorator:
    """Test suite for log_performance decorator."""

    def test_log_performance_success(self, caplog):
        """Test performance logging for successful function."""
        caplog.set_level(logging.INFO)

        @log_performance
        def test_function():
            time.sleep(0.1)
            return "result"

        result = test_function()

        assert result == "result"
        assert any("Completed test_function" in record.message for record in caplog.records)

    def test_log_performance_with_exception(self, caplog):
        """Test performance logging for function that raises exception."""
        caplog.set_level(logging.ERROR)

        @log_performance
        def test_function_error():
            time.sleep(0.05)
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_function_error()

        assert any("Failed test_function_error" in record.message for record in caplog.records)


class TestLogAPICallDecorator:
    """Test suite for log_api_call decorator."""

    def test_log_api_call_redacts_sensitive_data(self, caplog):
        """Test that API call logging redacts sensitive data."""
        caplog.set_level(logging.DEBUG)

        @log_api_call
        def test_api_call(location, api_key=None, token=None):
            return {"result": "success"}

        result = test_api_call("test_location", api_key="secret123", token="token456")

        assert result == {"result": "success"}

        # Check that sensitive data was redacted in logs
        log_messages = [record.message for record in caplog.records]
        assert not any("secret123" in msg for msg in log_messages)
        assert not any("token456" in msg for msg in log_messages)

    def test_log_api_call_logs_non_sensitive_data(self, caplog):
        """Test that API call logging includes non-sensitive data."""
        caplog.set_level(logging.DEBUG)

        @log_api_call
        def test_api_call(location, radius):
            return {"result": "success"}

        test_api_call("Salt Lake City", radius=5000)

        # Check that non-sensitive data is logged
        assert any("API call: test_api_call" in record.message for record in caplog.records)

    def test_log_api_call_with_exception(self, caplog):
        """Test API call logging when exception occurs."""
        caplog.set_level(logging.ERROR)

        @log_api_call
        def test_api_call_error():
            raise ValueError("API error")

        with pytest.raises(ValueError):
            test_api_call_error()

        assert any("API call failed" in record.message for record in caplog.records)


class TestProgressLogger:
    """Test suite for ProgressLogger context manager."""

    def test_progress_logger_with_total(self, caplog):
        """Test progress logger with known total."""
        caplog.set_level(logging.INFO)

        with ProgressLogger("Test operation", total=100) as progress:
            assert progress.total == 100
            progress.update(50, "Halfway done")

        assert any("Starting Test operation" in record.message for record in caplog.records)
        assert any("Completed Test operation" in record.message for record in caplog.records)

    def test_progress_logger_without_total(self, caplog):
        """Test progress logger without known total."""
        caplog.set_level(logging.INFO)

        with ProgressLogger("Unknown operation") as progress:
            assert progress.total is None
            progress.update(1, "Processing item")

        assert any("Starting Unknown operation" in record.message for record in caplog.records)

    def test_progress_logger_with_exception(self, caplog):
        """Test progress logger when exception occurs."""
        caplog.set_level(logging.ERROR)

        with pytest.raises(ValueError):
            with ProgressLogger("Failing operation", total=10):
                raise ValueError("Operation failed")

        assert any("Failed Failing operation" in record.message for record in caplog.records)

    def test_progress_logger_updates(self, caplog):
        """Test progress logger update logging."""
        caplog.set_level(logging.INFO)

        with ProgressLogger("Test operation", total=100) as progress:
            # Should log at 10% intervals
            progress.update(10)
            progress.update(20)
            progress.update(50)
            progress.update(100)

        # Check that progress updates were logged
        progress_logs = [r for r in caplog.records if "Test operation:" in r.message]
        assert len(progress_logs) >= 2  # At least some progress updates
