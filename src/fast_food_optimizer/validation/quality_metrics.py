"""Data quality metrics and reporting for restaurant datasets.

This module provides comprehensive quality metrics to assess the completeness
and accuracy of restaurant data before route optimization.
"""

from typing import List, Dict, Any
from datetime import datetime

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.utils.logging import get_logger, log_performance


class QualityMetrics:
    """Calculates and reports data quality metrics.

    Provides comprehensive quality assessment including:
    - Completeness metrics
    - Accuracy indicators
    - Distribution analysis
    - Quality scores

    Example:
        >>> metrics = QualityMetrics()
        >>> report = metrics.calculate_metrics(restaurants)
        >>> print(f"Overall quality: {report['quality_score']:.1f}%")
    """

    def __init__(self):
        """Initialize quality metrics calculator."""
        self.logger = get_logger(__name__)

    @log_performance
    def calculate_metrics(
        self,
        restaurants: List[Restaurant],
    ) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics for a dataset.

        Args:
            restaurants: List of restaurants to analyze

        Returns:
            Dictionary with quality metrics

        Example:
            >>> metrics_report = metrics.calculate_metrics(restaurants)
            >>> metrics_report['completeness']['coordinates']
            100.0
        """
        if not restaurants:
            return self._empty_metrics()

        total_count = len(restaurants)

        # Completeness metrics
        completeness = self._calculate_completeness(restaurants, total_count)

        # Accuracy metrics
        accuracy = self._calculate_accuracy(restaurants, total_count)

        # Distribution metrics
        distribution = self._calculate_distribution(restaurants)

        # Quality score (weighted average)
        quality_score = self._calculate_quality_score(completeness, accuracy)

        # Quality gates (pass/fail criteria)
        quality_gates = self._check_quality_gates(completeness, accuracy, total_count)

        report = {
            "dataset_info": {
                "total_restaurants": total_count,
                "generated_at": datetime.utcnow().isoformat(),
            },
            "completeness": completeness,
            "accuracy": accuracy,
            "distribution": distribution,
            "quality_score": quality_score,
            "quality_gates": quality_gates,
        }

        return report

    def _calculate_completeness(
        self,
        restaurants: List[Restaurant],
        total: int,
    ) -> Dict[str, float]:
        """Calculate completeness metrics (% of fields present)."""
        metrics = {
            "place_id": 0,
            "name": 0,
            "address": 0,
            "coordinates": 0,
            "operating_hours": 0,
            "phone": 0,
            "website": 0,
            "rating": 0,
            "place_types": 0,
        }

        for restaurant in restaurants:
            if restaurant.place_id and len(restaurant.place_id.strip()) >= 10:
                metrics["place_id"] += 1
            if restaurant.name and len(restaurant.name.strip()) >= 2:
                metrics["name"] += 1
            if restaurant.address and len(restaurant.address.strip()) >= 5:
                metrics["address"] += 1
            if restaurant.coordinates:
                metrics["coordinates"] += 1
            if restaurant.operating_hours:
                metrics["operating_hours"] += 1
            if restaurant.phone:
                metrics["phone"] += 1
            if restaurant.website:
                metrics["website"] += 1
            if restaurant.rating is not None:
                metrics["rating"] += 1
            if restaurant.place_types:
                metrics["place_types"] += 1

        # Convert to percentages
        for key in metrics:
            metrics[key] = (metrics[key] / total) * 100

        return metrics

    def _calculate_accuracy(
        self,
        restaurants: List[Restaurant],
        total: int,
    ) -> Dict[str, Any]:
        """Calculate accuracy metrics."""
        valid_coordinates = 0
        valid_ratings = 0
        valid_confidence = 0
        high_confidence = 0

        for restaurant in restaurants:
            # Valid coordinates (not null island)
            if restaurant.coordinates:
                if not (restaurant.coordinates.latitude == 0.0 and
                        restaurant.coordinates.longitude == 0.0):
                    valid_coordinates += 1

            # Valid ratings
            if restaurant.rating is not None and 0 <= restaurant.rating <= 5:
                valid_ratings += 1

            # Valid confidence scores
            if 0 <= restaurant.confidence_score <= 1:
                valid_confidence += 1

                # High confidence (>= 0.7)
                if restaurant.confidence_score >= 0.7:
                    high_confidence += 1

        return {
            "valid_coordinates_pct": (valid_coordinates / total) * 100,
            "valid_ratings_pct": (valid_ratings / total) * 100 if restaurants else 0,
            "valid_confidence_pct": (valid_confidence / total) * 100,
            "high_confidence_pct": (high_confidence / total) * 100,
        }

    def _calculate_distribution(
        self,
        restaurants: List[Restaurant],
    ) -> Dict[str, Any]:
        """Calculate distribution metrics."""
        fast_food_count = sum(1 for r in restaurants if r.is_fast_food)
        not_fast_food_count = len(restaurants) - fast_food_count

        # Confidence score distribution
        confidence_buckets = {
            "0.0-0.3": 0,
            "0.3-0.5": 0,
            "0.5-0.7": 0,
            "0.7-0.9": 0,
            "0.9-1.0": 0,
        }

        for restaurant in restaurants:
            score = restaurant.confidence_score
            if score < 0.3:
                confidence_buckets["0.0-0.3"] += 1
            elif score < 0.5:
                confidence_buckets["0.3-0.5"] += 1
            elif score < 0.7:
                confidence_buckets["0.5-0.7"] += 1
            elif score < 0.9:
                confidence_buckets["0.7-0.9"] += 1
            else:
                confidence_buckets["0.9-1.0"] += 1

        # Rating distribution
        rating_buckets = {
            "1-2": 0,
            "2-3": 0,
            "3-4": 0,
            "4-5": 0,
        }

        for restaurant in restaurants:
            if restaurant.rating is not None:
                rating = restaurant.rating
                if rating < 2:
                    rating_buckets["1-2"] += 1
                elif rating < 3:
                    rating_buckets["2-3"] += 1
                elif rating < 4:
                    rating_buckets["3-4"] += 1
                else:
                    rating_buckets["4-5"] += 1

        return {
            "fast_food_count": fast_food_count,
            "not_fast_food_count": not_fast_food_count,
            "fast_food_percentage": (fast_food_count / len(restaurants)) * 100 if restaurants else 0,
            "confidence_distribution": confidence_buckets,
            "rating_distribution": rating_buckets,
        }

    def _calculate_quality_score(
        self,
        completeness: Dict[str, float],
        accuracy: Dict[str, Any],
    ) -> float:
        """Calculate overall quality score (0-100).

        Weighted average of key metrics:
        - Required fields completeness: 40%
        - Optional fields completeness: 20%
        - Accuracy metrics: 40%
        """
        # Required fields (40%)
        required_score = (
            completeness["place_id"] * 0.15 +
            completeness["name"] * 0.15 +
            completeness["coordinates"] * 0.10
        )

        # Optional but important fields (20%)
        optional_score = (
            completeness["address"] * 0.05 +
            completeness["operating_hours"] * 0.10 +
            completeness["rating"] * 0.05
        )

        # Accuracy (40%)
        accuracy_score = (
            accuracy["valid_coordinates_pct"] * 0.15 +
            accuracy["valid_confidence_pct"] * 0.10 +
            accuracy["high_confidence_pct"] * 0.15
        )

        quality_score = required_score + optional_score + accuracy_score

        return round(quality_score, 2)

    def _check_quality_gates(
        self,
        completeness: Dict[str, float],
        accuracy: Dict[str, Any],
        total_count: int,
    ) -> Dict[str, Any]:
        """Check if dataset meets quality gate requirements.

        Quality Gates:
        - Less than 2% duplicates (checked elsewhere)
        - 95%+ restaurants have valid coordinates
        - 90%+ restaurants have operating hours
        - All required data passes validation
        """
        gates = {
            "valid_coordinates": {
                "threshold": 95.0,
                "actual": accuracy["valid_coordinates_pct"],
                "passed": accuracy["valid_coordinates_pct"] >= 95.0,
            },
            "operating_hours": {
                "threshold": 90.0,
                "actual": completeness["operating_hours"],
                "passed": completeness["operating_hours"] >= 90.0,
            },
            "required_fields": {
                "threshold": 100.0,
                "actual": min(
                    completeness["place_id"],
                    completeness["name"],
                    completeness["coordinates"],
                ),
                "passed": (
                    completeness["place_id"] >= 100.0 and
                    completeness["name"] >= 100.0 and
                    completeness["coordinates"] >= 100.0
                ),
            },
            "high_confidence": {
                "threshold": 70.0,
                "actual": accuracy["high_confidence_pct"],
                "passed": accuracy["high_confidence_pct"] >= 70.0,
            },
        }

        # Overall pass status
        all_passed = all(gate["passed"] for gate in gates.values())
        gates["all_passed"] = all_passed

        return gates

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics for empty dataset."""
        return {
            "dataset_info": {
                "total_restaurants": 0,
                "generated_at": datetime.utcnow().isoformat(),
            },
            "completeness": {},
            "accuracy": {},
            "distribution": {},
            "quality_score": 0.0,
            "quality_gates": {"all_passed": False},
        }

    def generate_report(
        self,
        restaurants: List[Restaurant],
        detailed: bool = True,
    ) -> str:
        """Generate a human-readable quality metrics report.

        Args:
            restaurants: List of restaurants
            detailed: If True, include detailed breakdowns

        Returns:
            Formatted report string
        """
        metrics = self.calculate_metrics(restaurants)

        lines = []
        lines.append("=" * 70)
        lines.append("DATA QUALITY METRICS REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {metrics['dataset_info']['generated_at']}")
        lines.append(f"Total Restaurants: {metrics['dataset_info']['total_restaurants']}")
        lines.append("")

        # Quality Score
        lines.append(f"Overall Quality Score: {metrics['quality_score']:.1f}/100")
        lines.append("")

        # Completeness
        lines.append("Completeness Metrics:")
        comp = metrics["completeness"]
        lines.append(f"  Place ID: {comp['place_id']:.1f}%")
        lines.append(f"  Name: {comp['name']:.1f}%")
        lines.append(f"  Coordinates: {comp['coordinates']:.1f}%")
        lines.append(f"  Address: {comp['address']:.1f}%")
        lines.append(f"  Operating Hours: {comp['operating_hours']:.1f}%")
        lines.append(f"  Phone: {comp['phone']:.1f}%")
        lines.append(f"  Website: {comp['website']:.1f}%")
        lines.append(f"  Rating: {comp['rating']:.1f}%")
        lines.append("")

        # Accuracy
        lines.append("Accuracy Metrics:")
        acc = metrics["accuracy"]
        lines.append(f"  Valid Coordinates: {acc['valid_coordinates_pct']:.1f}%")
        lines.append(f"  High Confidence (>=0.7): {acc['high_confidence_pct']:.1f}%")
        lines.append("")

        # Distribution
        dist = metrics["distribution"]
        lines.append("Distribution:")
        lines.append(f"  Fast Food: {dist['fast_food_count']} ({dist['fast_food_percentage']:.1f}%)")
        lines.append(f"  Not Fast Food: {dist['not_fast_food_count']}")
        lines.append("")

        # Quality Gates
        gates = metrics["quality_gates"]
        lines.append("Quality Gates:")
        for gate_name, gate_data in gates.items():
            if gate_name == "all_passed":
                continue
            status = "✅ PASS" if gate_data["passed"] else "❌ FAIL"
            lines.append(
                f"  {gate_name.replace('_', ' ').title()}: "
                f"{gate_data['actual']:.1f}% (threshold: {gate_data['threshold']:.1f}%) {status}"
            )
        lines.append("")

        overall_status = "✅ ALL GATES PASSED" if gates["all_passed"] else "❌ SOME GATES FAILED"
        lines.append(f"Overall Status: {overall_status}")
        lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)
