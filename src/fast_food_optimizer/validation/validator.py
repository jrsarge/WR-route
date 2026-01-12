"""Data validation framework for restaurant data quality.

This module provides comprehensive validation checks for restaurant data
to ensure accuracy and completeness before route optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from fast_food_optimizer.models.restaurant import Restaurant, Coordinates
from fast_food_optimizer.utils.exceptions import DataValidationError
from fast_food_optimizer.utils.logging import get_logger, log_performance


class ValidationResult:
    """Result of a validation check.

    Attributes:
        passed: Whether validation passed
        field: Field that was validated
        message: Validation message
        severity: Severity level (error, warning, info)
    """

    def __init__(
        self,
        passed: bool,
        field: str,
        message: str,
        severity: str = "error",
    ):
        self.passed = passed
        self.field = field
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "field": self.field,
            "message": self.message,
            "severity": self.severity,
        }


class DataValidator:
    """Validates restaurant data for quality and completeness.

    Performs comprehensive validation checks including:
    - Required field presence
    - Coordinate validity
    - Data format validation
    - Business logic validation
    - Cross-field validation

    Example:
        >>> validator = DataValidator()
        >>> results = validator.validate_restaurant(restaurant)
        >>> if validator.is_valid(results):
        ...     print("Restaurant is valid")
    """

    def __init__(
        self,
        strict_mode: bool = False,
        require_operating_hours: bool = False,
    ):
        """Initialize data validator.

        Args:
            strict_mode: If True, warnings are treated as errors
            require_operating_hours: If True, operating hours are required
        """
        self.strict_mode = strict_mode
        self.require_operating_hours = require_operating_hours
        self.logger = get_logger(__name__)

        # Validation statistics
        self.validation_stats = {
            "total_validated": 0,
            "total_passed": 0,
            "total_failed": 0,
            "errors": 0,
            "warnings": 0,
        }

    @log_performance
    def validate_restaurant(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate a single restaurant.

        Args:
            restaurant: Restaurant to validate

        Returns:
            List of ValidationResult objects

        Example:
            >>> results = validator.validate_restaurant(restaurant)
            >>> for result in results:
            ...     if not result.passed:
            ...         print(f"Error: {result.message}")
        """
        self.validation_stats["total_validated"] += 1

        results = []

        # Required field checks
        results.extend(self._validate_required_fields(restaurant))

        # Coordinate validation
        results.extend(self._validate_coordinates(restaurant))

        # Name validation
        results.extend(self._validate_name(restaurant))

        # Address validation
        results.extend(self._validate_address(restaurant))

        # Rating validation
        results.extend(self._validate_rating(restaurant))

        # Confidence score validation
        results.extend(self._validate_confidence(restaurant))

        # Operating hours validation
        results.extend(self._validate_operating_hours(restaurant))

        # Contact info validation
        results.extend(self._validate_contact_info(restaurant))

        # Business logic validation
        results.extend(self._validate_business_logic(restaurant))

        # Update statistics
        if self.is_valid(results):
            self.validation_stats["total_passed"] += 1
        else:
            self.validation_stats["total_failed"] += 1

        for result in results:
            if not result.passed:
                if result.severity == "error":
                    self.validation_stats["errors"] += 1
                elif result.severity == "warning":
                    self.validation_stats["warnings"] += 1

        return results

    def _validate_required_fields(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate required fields are present."""
        results = []

        # place_id is required
        if not restaurant.place_id or len(restaurant.place_id.strip()) < 10:
            results.append(ValidationResult(
                passed=False,
                field="place_id",
                message=f"Invalid place_id: '{restaurant.place_id}'",
                severity="error",
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                field="place_id",
                message="place_id is valid",
                severity="info",
            ))

        # name is required
        if not restaurant.name or len(restaurant.name.strip()) < 2:
            results.append(ValidationResult(
                passed=False,
                field="name",
                message=f"Invalid name: '{restaurant.name}'",
                severity="error",
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                field="name",
                message="name is valid",
                severity="info",
            ))

        # coordinates are required (validated separately)
        if not restaurant.coordinates:
            results.append(ValidationResult(
                passed=False,
                field="coordinates",
                message="Missing coordinates",
                severity="error",
            ))

        return results

    def _validate_coordinates(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate coordinate data."""
        results = []

        if not restaurant.coordinates:
            return results

        coords = restaurant.coordinates

        # Latitude range
        if not (-90 <= coords.latitude <= 90):
            results.append(ValidationResult(
                passed=False,
                field="latitude",
                message=f"Latitude {coords.latitude} out of range [-90, 90]",
                severity="error",
            ))

        # Longitude range
        if not (-180 <= coords.longitude <= 180):
            results.append(ValidationResult(
                passed=False,
                field="longitude",
                message=f"Longitude {coords.longitude} out of range [-180, 180]",
                severity="error",
            ))

        # Check for null island (0, 0)
        if coords.latitude == 0.0 and coords.longitude == 0.0:
            results.append(ValidationResult(
                passed=False,
                field="coordinates",
                message="Coordinates are (0, 0) - likely invalid",
                severity="warning",
            ))

        # Valid coordinates
        if -90 <= coords.latitude <= 90 and -180 <= coords.longitude <= 180:
            results.append(ValidationResult(
                passed=True,
                field="coordinates",
                message="Coordinates are valid",
                severity="info",
            ))

        return results

    def _validate_name(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate restaurant name."""
        results = []

        # Check for suspicious names
        suspicious_patterns = ["test", "untitled", "unknown", "null", "n/a"]
        name_lower = restaurant.name.lower()

        if any(pattern in name_lower for pattern in suspicious_patterns):
            results.append(ValidationResult(
                passed=False,
                field="name",
                message=f"Suspicious name: '{restaurant.name}'",
                severity="warning",
            ))

        # Check for very short names
        if len(restaurant.name.strip()) < 3:
            results.append(ValidationResult(
                passed=False,
                field="name",
                message=f"Name too short: '{restaurant.name}'",
                severity="warning",
            ))

        return results

    def _validate_address(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate address."""
        results = []

        if not restaurant.address or len(restaurant.address.strip()) < 5:
            results.append(ValidationResult(
                passed=False,
                field="address",
                message="Missing or incomplete address",
                severity="warning",
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                field="address",
                message="Address present",
                severity="info",
            ))

        return results

    def _validate_rating(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate rating if present."""
        results = []

        if restaurant.rating is not None:
            if not (0 <= restaurant.rating <= 5):
                results.append(ValidationResult(
                    passed=False,
                    field="rating",
                    message=f"Rating {restaurant.rating} out of range [0, 5]",
                    severity="error",
                ))
            else:
                results.append(ValidationResult(
                    passed=True,
                    field="rating",
                    message=f"Rating {restaurant.rating} is valid",
                    severity="info",
                ))

        return results

    def _validate_confidence(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate confidence score."""
        results = []

        if not (0 <= restaurant.confidence_score <= 1):
            results.append(ValidationResult(
                passed=False,
                field="confidence_score",
                message=f"Confidence {restaurant.confidence_score} out of range [0, 1]",
                severity="error",
            ))
        else:
            # Warn about low confidence
            if restaurant.confidence_score < 0.5:
                results.append(ValidationResult(
                    passed=False,
                    field="confidence_score",
                    message=f"Low confidence score: {restaurant.confidence_score:.2f}",
                    severity="warning",
                ))
            else:
                results.append(ValidationResult(
                    passed=True,
                    field="confidence_score",
                    message=f"Confidence {restaurant.confidence_score:.2f} is good",
                    severity="info",
                ))

        return results

    def _validate_operating_hours(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate operating hours if present."""
        results = []

        if self.require_operating_hours and not restaurant.operating_hours:
            results.append(ValidationResult(
                passed=False,
                field="operating_hours",
                message="Operating hours required but missing",
                severity="error",
            ))
        elif not restaurant.operating_hours:
            results.append(ValidationResult(
                passed=False,
                field="operating_hours",
                message="Operating hours missing",
                severity="warning",
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                field="operating_hours",
                message="Operating hours present",
                severity="info",
            ))

        return results

    def _validate_contact_info(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate contact information."""
        results = []

        # Phone validation (optional but recommended)
        if not restaurant.phone:
            results.append(ValidationResult(
                passed=False,
                field="phone",
                message="Phone number missing",
                severity="info",
            ))

        # Website validation (optional)
        if restaurant.website:
            if not (restaurant.website.startswith("http://") or
                    restaurant.website.startswith("https://")):
                results.append(ValidationResult(
                    passed=False,
                    field="website",
                    message=f"Invalid website URL: {restaurant.website}",
                    severity="warning",
                ))

        return results

    def _validate_business_logic(self, restaurant: Restaurant) -> List[ValidationResult]:
        """Validate business logic rules."""
        results = []

        # If marked as fast food, confidence should be reasonable
        if restaurant.is_fast_food and restaurant.confidence_score < 0.3:
            results.append(ValidationResult(
                passed=False,
                field="is_fast_food",
                message=f"Marked as fast food but low confidence: {restaurant.confidence_score:.2f}",
                severity="warning",
            ))

        # If not fast food, confidence should also be reasonable
        if not restaurant.is_fast_food and restaurant.confidence_score > 0.7:
            results.append(ValidationResult(
                passed=False,
                field="is_fast_food",
                message=f"Not marked as fast food but high confidence: {restaurant.confidence_score:.2f}",
                severity="warning",
            ))

        return results

    def is_valid(self, results: List[ValidationResult]) -> bool:
        """Check if validation results indicate valid data.

        Args:
            results: List of ValidationResult objects

        Returns:
            True if all checks passed or only warnings
        """
        for result in results:
            if not result.passed:
                # In strict mode, warnings are errors
                if self.strict_mode and result.severity == "warning":
                    return False
                # Errors always fail validation
                if result.severity == "error":
                    return False
        return True

    @log_performance
    def validate_batch(
        self,
        restaurants: List[Restaurant],
        fail_fast: bool = False,
    ) -> Dict[str, Any]:
        """Validate a batch of restaurants.

        Args:
            restaurants: List of restaurants to validate
            fail_fast: If True, stop on first validation failure

        Returns:
            Dictionary with validation results and statistics

        Example:
            >>> report = validator.validate_batch(restaurants)
            >>> print(f"Valid: {report['valid_count']}/{report['total_count']}")
        """
        self.logger.info(f"Validating batch of {len(restaurants)} restaurants")

        valid_restaurants = []
        invalid_restaurants = []
        validation_results = {}

        for restaurant in restaurants:
            results = self.validate_restaurant(restaurant)
            validation_results[restaurant.place_id] = results

            if self.is_valid(results):
                valid_restaurants.append(restaurant)
            else:
                invalid_restaurants.append(restaurant)

                if fail_fast:
                    self.logger.warning(
                        f"Validation failed for {restaurant.name} (fail_fast=True)"
                    )
                    break

        report = {
            "total_count": len(restaurants),
            "valid_count": len(valid_restaurants),
            "invalid_count": len(invalid_restaurants),
            "valid_percentage": (len(valid_restaurants) / len(restaurants) * 100) if restaurants else 0,
            "valid_restaurants": valid_restaurants,
            "invalid_restaurants": invalid_restaurants,
            "validation_results": validation_results,
            "statistics": self.get_stats(),
        }

        self.logger.info(
            f"Validation complete: {len(valid_restaurants)}/{len(restaurants)} valid "
            f"({report['valid_percentage']:.1f}%)"
        )

        return report

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics.

        Returns:
            Dictionary with validation statistics
        """
        return self.validation_stats.copy()

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            "total_validated": 0,
            "total_passed": 0,
            "total_failed": 0,
            "errors": 0,
            "warnings": 0,
        }

    def generate_report(
        self,
        validation_results: Dict[str, List[ValidationResult]],
    ) -> str:
        """Generate a human-readable validation report.

        Args:
            validation_results: Dictionary of place_id -> ValidationResults

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("DATA VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        lines.append(f"Total Restaurants: {len(validation_results)}")
        lines.append("")

        # Count issues by severity
        total_errors = 0
        total_warnings = 0

        for results in validation_results.values():
            for result in results:
                if not result.passed:
                    if result.severity == "error":
                        total_errors += 1
                    elif result.severity == "warning":
                        total_warnings += 1

        lines.append(f"Errors: {total_errors}")
        lines.append(f"Warnings: {total_warnings}")
        lines.append("")

        # List issues by restaurant
        for place_id, results in validation_results.items():
            issues = [r for r in results if not r.passed]
            if issues:
                lines.append(f"Place ID: {place_id}")
                for issue in issues:
                    symbol = "❌" if issue.severity == "error" else "⚠️"
                    lines.append(f"  {symbol} [{issue.severity.upper()}] {issue.field}: {issue.message}")
                lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)
