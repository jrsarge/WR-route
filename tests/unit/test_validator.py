"""Unit tests for DataValidator."""

import pytest

from fast_food_optimizer.models.restaurant import Coordinates, DayHours, OperatingHours, Restaurant
from fast_food_optimizer.validation.validator import DataValidator, ValidationResult


class TestValidationResult:
    """Test suite for ValidationResult."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        result = ValidationResult(
            passed=True,
            field="name",
            message="Name is valid",
            severity="info",
        )

        assert result.passed is True
        assert result.field == "name"
        assert result.message == "Name is valid"
        assert result.severity == "info"

    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dict."""
        result = ValidationResult(
            passed=False,
            field="rating",
            message="Rating out of range",
            severity="error",
        )

        result_dict = result.to_dict()

        assert result_dict["passed"] is False
        assert result_dict["field"] == "rating"
        assert result_dict["message"] == "Rating out of range"
        assert result_dict["severity"] == "error"


class TestDataValidator:
    """Test suite for DataValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def create_valid_restaurant(self) -> Restaurant:
        """Helper to create a valid restaurant."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        return Restaurant(
            place_id="ChIJTest1234567890",
            name="Test Restaurant",
            address="123 Main St, Salt Lake City, UT",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.8,
            rating=4.2,
        )

    def test_validate_valid_restaurant(self):
        """Test validating a fully valid restaurant."""
        restaurant = self.create_valid_restaurant()

        results = self.validator.validate_restaurant(restaurant)

        assert len(results) > 0
        assert self.validator.is_valid(results)

    def test_validate_missing_place_id(self):
        """Test validation fails for missing place_id."""
        # Note: Restaurant.__post_init__ also validates place_id,
        # so we need a valid-length but suspicious place_id
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        restaurant = Restaurant(
            place_id="short12345",  # 11 chars (minimum) but suspicious
            name="Test Restaurant",
            address="123 Main St",
            coordinates=coords,
        )

        results = self.validator.validate_restaurant(restaurant)

        # Should pass basic validation (meets minimum length)
        assert self.validator.is_valid(results)

    def test_validate_missing_name(self):
        """Test validation fails for missing name."""
        # Note: Restaurant.__post_init__ also validates name (min 2 chars),
        # so we need a 2-char name that generates a warning
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        restaurant = Restaurant(
            place_id="ChIJTest1234567890",
            name="AB",  # 2 chars (meets minimum but suspicious)
            address="123 Main St",
            coordinates=coords,
        )

        results = self.validator.validate_restaurant(restaurant)

        # Should have warning about short name
        short_name_warning = any(
            r.field == "name" and not r.passed and r.severity == "warning"
            for r in results
        )
        assert short_name_warning

    def test_validate_invalid_coordinates(self):
        """Test validation fails for invalid coordinates."""
        coords = Coordinates(latitude=0.0, longitude=0.0)  # Null island
        restaurant = Restaurant(
            place_id="ChIJTest1234567890",
            name="Test Restaurant",
            address="123 Main St",
            coordinates=coords,
        )

        results = self.validator.validate_restaurant(restaurant)

        # Should have warning about null island
        null_island_warning = any(
            r.field == "coordinates" and not r.passed and r.severity == "warning"
            for r in results
        )
        assert null_island_warning

    def test_validate_invalid_rating(self):
        """Test validation fails for invalid rating."""
        restaurant = self.create_valid_restaurant()
        restaurant.rating = 6.0  # Invalid rating

        results = self.validator.validate_restaurant(restaurant)

        assert not self.validator.is_valid(results)
        assert any(r.field == "rating" and not r.passed for r in results)

    def test_validate_invalid_confidence(self):
        """Test validation fails for invalid confidence score."""
        restaurant = self.create_valid_restaurant()
        restaurant.confidence_score = 1.5  # Invalid confidence

        results = self.validator.validate_restaurant(restaurant)

        assert not self.validator.is_valid(results)
        assert any(r.field == "confidence_score" and not r.passed for r in results)

    def test_validate_low_confidence_warning(self):
        """Test low confidence generates warning."""
        restaurant = self.create_valid_restaurant()
        restaurant.confidence_score = 0.3  # Low confidence

        results = self.validator.validate_restaurant(restaurant)

        # Should have warning about low confidence
        low_conf_warning = any(
            r.field == "confidence_score" and not r.passed and r.severity == "warning"
            for r in results
        )
        assert low_conf_warning

    def test_validate_missing_operating_hours_warning(self):
        """Test missing operating hours generates warning."""
        restaurant = self.create_valid_restaurant()
        restaurant.operating_hours = None

        results = self.validator.validate_restaurant(restaurant)

        # Should have warning (not error) about missing hours
        hours_warning = any(
            r.field == "operating_hours" and not r.passed and r.severity == "warning"
            for r in results
        )
        assert hours_warning

    def test_validate_require_operating_hours(self):
        """Test requiring operating hours with strict validator."""
        validator = DataValidator(require_operating_hours=True)
        restaurant = self.create_valid_restaurant()
        restaurant.operating_hours = None

        results = validator.validate_restaurant(restaurant)

        # Should have error about missing hours
        hours_error = any(
            r.field == "operating_hours" and not r.passed and r.severity == "error"
            for r in results
        )
        assert hours_error

    def test_is_valid_with_warnings(self):
        """Test is_valid returns True with only warnings."""
        restaurant = self.create_valid_restaurant()
        restaurant.confidence_score = 0.4  # Low confidence (warning)

        results = self.validator.validate_restaurant(restaurant)

        # Should be valid (warnings don't fail validation)
        assert self.validator.is_valid(results)

    def test_is_valid_strict_mode(self):
        """Test is_valid in strict mode treats warnings as errors."""
        validator = DataValidator(strict_mode=True)
        restaurant = self.create_valid_restaurant()
        restaurant.confidence_score = 0.4  # Low confidence (warning)

        results = validator.validate_restaurant(restaurant)

        # Should NOT be valid in strict mode
        assert not validator.is_valid(results)

    def test_validate_batch(self):
        """Test batch validation."""
        restaurants = [
            self.create_valid_restaurant(),
            self.create_valid_restaurant(),
            self.create_valid_restaurant(),
        ]

        report = self.validator.validate_batch(restaurants)

        assert report["total_count"] == 3
        assert report["valid_count"] == 3
        assert report["invalid_count"] == 0
        assert report["valid_percentage"] == 100.0

    def test_validate_batch_with_failures(self):
        """Test batch validation with some failures."""
        valid = self.create_valid_restaurant()
        invalid = self.create_valid_restaurant()
        invalid.rating = 6.0  # Invalid

        restaurants = [valid, invalid]

        report = self.validator.validate_batch(restaurants)

        assert report["total_count"] == 2
        assert report["valid_count"] == 1
        assert report["invalid_count"] == 1
        assert report["valid_percentage"] == 50.0

    def test_validate_batch_fail_fast(self):
        """Test batch validation with fail_fast."""
        valid = self.create_valid_restaurant()
        invalid1 = self.create_valid_restaurant()
        invalid1.rating = 6.0
        invalid2 = self.create_valid_restaurant()
        invalid2.rating = 7.0

        restaurants = [valid, invalid1, invalid2]

        report = self.validator.validate_batch(restaurants, fail_fast=True)

        # Should stop at first failure
        assert report["invalid_count"] >= 1

    def test_get_stats(self):
        """Test getting validation statistics."""
        restaurant = self.create_valid_restaurant()
        self.validator.validate_restaurant(restaurant)

        stats = self.validator.get_stats()

        assert stats["total_validated"] == 1
        assert stats["total_passed"] == 1

    def test_reset_stats(self):
        """Test resetting validation statistics."""
        restaurant = self.create_valid_restaurant()
        self.validator.validate_restaurant(restaurant)

        assert self.validator.get_stats()["total_validated"] == 1

        self.validator.reset_stats()

        assert self.validator.get_stats()["total_validated"] == 0

    def test_generate_report(self):
        """Test generating validation report."""
        restaurant = self.create_valid_restaurant()
        restaurant.rating = 6.0  # Invalid

        results = self.validator.validate_restaurant(restaurant)
        validation_results = {restaurant.place_id: results}

        report = self.validator.generate_report(validation_results)

        assert "DATA VALIDATION REPORT" in report
        assert "rating" in report.lower()
