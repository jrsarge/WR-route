"""Duplicate detection and removal for restaurant data.

This module provides tools to identify and remove duplicate restaurants
while preserving multiple locations of the same chain.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.utils.logging import get_logger, log_performance


class DuplicateDetector:
    """Detects and removes duplicate restaurant entries.

    CRITICAL: This detector deduplicates by place_id ONLY, never by name.
    Multiple locations of the same chain are preserved and valued.

    Example:
        >>> detector = DuplicateDetector()
        >>> unique, duplicates = detector.detect_duplicates(restaurants)
        >>> print(f"Found {len(duplicates)} duplicates")
        >>> cleaned = detector.remove_duplicates(restaurants)
    """

    def __init__(self):
        """Initialize duplicate detector."""
        self.logger = get_logger(__name__)

        # Detection statistics
        self.detection_stats = {
            "total_processed": 0,
            "duplicates_found": 0,
            "unique_count": 0,
        }

    @log_performance
    def detect_duplicates(
        self,
        restaurants: List[Restaurant],
    ) -> Tuple[List[Restaurant], List[Restaurant]]:
        """Detect duplicate restaurants by place_id.

        CRITICAL: Only deduplicates by place_id. Multiple locations of
        the same chain (e.g., two McDonald's) are NOT duplicates.

        Args:
            restaurants: List of restaurants to check

        Returns:
            Tuple of (unique_restaurants, duplicate_restaurants)

        Example:
            >>> unique, dupes = detector.detect_duplicates(restaurants)
            >>> print(f"{len(unique)} unique, {len(dupes)} duplicates")
        """
        self.detection_stats["total_processed"] = len(restaurants)

        seen_place_ids: Set[str] = set()
        unique_restaurants = []
        duplicate_restaurants = []

        for restaurant in restaurants:
            if restaurant.place_id in seen_place_ids:
                # This is a duplicate place_id
                duplicate_restaurants.append(restaurant)
                self.detection_stats["duplicates_found"] += 1
            else:
                # First time seeing this place_id
                seen_place_ids.add(restaurant.place_id)
                unique_restaurants.append(restaurant)

        self.detection_stats["unique_count"] = len(unique_restaurants)

        self.logger.info(
            f"Duplicate detection: {len(unique_restaurants)} unique, "
            f"{len(duplicate_restaurants)} duplicates"
        )

        return unique_restaurants, duplicate_restaurants

    @log_performance
    def remove_duplicates(
        self,
        restaurants: List[Restaurant],
        keep: str = "first",
    ) -> List[Restaurant]:
        """Remove duplicate restaurants, keeping only one per place_id.

        CRITICAL: Deduplicates by place_id ONLY. Multiple locations of
        the same chain name are preserved.

        Args:
            restaurants: List of restaurants
            keep: Which duplicate to keep ("first", "last", "best")
                - "first": Keep first occurrence
                - "last": Keep last occurrence
                - "best": Keep highest confidence score

        Returns:
            List of unique restaurants

        Example:
            >>> unique = detector.remove_duplicates(restaurants, keep="best")
        """
        if keep == "first":
            # Keep first occurrence
            unique, _ = self.detect_duplicates(restaurants)
            return unique

        elif keep == "last":
            # Keep last occurrence
            seen: Dict[str, Restaurant] = {}
            for restaurant in restaurants:
                seen[restaurant.place_id] = restaurant
            return list(seen.values())

        elif keep == "best":
            # Keep highest confidence score
            seen: Dict[str, Restaurant] = {}
            for restaurant in restaurants:
                if restaurant.place_id not in seen:
                    seen[restaurant.place_id] = restaurant
                else:
                    # Keep restaurant with higher confidence
                    if restaurant.confidence_score > seen[restaurant.place_id].confidence_score:
                        seen[restaurant.place_id] = restaurant
            return list(seen.values())

        else:
            raise ValueError(f"Invalid keep parameter: {keep}. Must be 'first', 'last', or 'best'")

    def analyze_chain_distribution(
        self,
        restaurants: List[Restaurant],
    ) -> Dict[str, Any]:
        """Analyze distribution of restaurant chains.

        CRITICAL: Multiple locations of the same chain are GOOD, not duplicates.
        This analysis helps understand chain density.

        Args:
            restaurants: List of restaurants

        Returns:
            Dictionary with chain analysis

        Example:
            >>> analysis = detector.analyze_chain_distribution(restaurants)
            >>> print(f"Chains with multiple locations: {analysis['multi_location_chains']}")
        """
        # Count restaurants by name
        chain_counts = defaultdict(int)
        for restaurant in restaurants:
            chain_counts[restaurant.name] += 1

        # Identify chains with multiple locations
        multi_location_chains = {
            name: count
            for name, count in chain_counts.items()
            if count > 1
        }

        # Sort by count (descending)
        sorted_chains = sorted(
            multi_location_chains.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        total_restaurants = len(restaurants)
        unique_names = len(chain_counts)
        chains_with_multiple = len(multi_location_chains)

        analysis = {
            "total_restaurants": total_restaurants,
            "unique_names": unique_names,
            "chains_with_multiple_locations": chains_with_multiple,
            "multi_location_chains": dict(sorted_chains[:20]),  # Top 20
            "top_chain": sorted_chains[0] if sorted_chains else None,
            "chain_diversity_ratio": unique_names / total_restaurants if total_restaurants > 0 else 0,
        }

        # Log interesting findings
        if chains_with_multiple > 0:
            self.logger.info(
                f"Found {chains_with_multiple} chains with multiple locations "
                f"(this is good for route efficiency!)"
            )
            if sorted_chains:
                top_name, top_count = sorted_chains[0]
                self.logger.info(f"Most common chain: {top_name} ({top_count} locations)")

        return analysis

    def find_near_duplicates(
        self,
        restaurants: List[Restaurant],
        distance_threshold_km: float = 0.05,
    ) -> List[Tuple[Restaurant, Restaurant, float]]:
        """Find restaurants that are suspiciously close to each other.

        This helps identify potential data quality issues where the same
        physical location was collected multiple times with different place_ids.

        NOTE: Multiple locations of the same chain that are genuinely close
        (e.g., two Starbucks in same mall) are NOT issues.

        Args:
            restaurants: List of restaurants
            distance_threshold_km: Max distance in km to consider near-duplicate

        Returns:
            List of tuples (restaurant1, restaurant2, distance_km)

        Example:
            >>> near_dupes = detector.find_near_duplicates(restaurants, 0.05)
            >>> for r1, r2, dist in near_dupes:
            ...     print(f"{r1.name} and {r2.name} are {dist*1000:.0f}m apart")
        """
        near_duplicates = []

        # Check each pair of restaurants
        for i, r1 in enumerate(restaurants):
            for r2 in restaurants[i + 1:]:
                # Skip if different place_ids (they're allowed to be close)
                if r1.place_id == r2.place_id:
                    continue

                # Calculate distance
                distance = r1.distance_to(r2)

                # Check if suspiciously close
                if distance < distance_threshold_km:
                    # Only flag if same name (might be data quality issue)
                    if r1.name.lower() == r2.name.lower():
                        near_duplicates.append((r1, r2, distance))
                        self.logger.warning(
                            f"Potential near-duplicate: {r1.name} at "
                            f"{r1.address} and {r2.address} "
                            f"({distance*1000:.0f}m apart)"
                        )

        return near_duplicates

    def get_stats(self) -> Dict[str, Any]:
        """Get duplicate detection statistics.

        Returns:
            Dictionary with detection statistics
        """
        stats = self.detection_stats.copy()

        if stats["total_processed"] > 0:
            stats["duplicate_percentage"] = (
                stats["duplicates_found"] / stats["total_processed"] * 100
            )
        else:
            stats["duplicate_percentage"] = 0.0

        return stats

    def reset_stats(self) -> None:
        """Reset detection statistics."""
        self.detection_stats = {
            "total_processed": 0,
            "duplicates_found": 0,
            "unique_count": 0,
        }

    def generate_report(
        self,
        restaurants: List[Restaurant],
    ) -> str:
        """Generate a duplicate detection report.

        Args:
            restaurants: List of restaurants to analyze

        Returns:
            Formatted report string
        """
        # Detect duplicates
        unique, duplicates = self.detect_duplicates(restaurants)

        # Analyze chain distribution
        chain_analysis = self.analyze_chain_distribution(unique)

        # Build report
        lines = []
        lines.append("=" * 70)
        lines.append("DUPLICATE DETECTION REPORT")
        lines.append("=" * 70)
        lines.append("")

        lines.append("Summary:")
        lines.append(f"  Total Restaurants: {len(restaurants)}")
        lines.append(f"  Unique Restaurants: {len(unique)}")
        lines.append(f"  Duplicate Entries: {len(duplicates)}")
        if len(restaurants) > 0:
            dup_pct = (len(duplicates) / len(restaurants)) * 100
            lines.append(f"  Duplicate Rate: {dup_pct:.2f}%")
        lines.append("")

        lines.append("Chain Distribution:")
        lines.append(f"  Unique Chain Names: {chain_analysis['unique_names']}")
        lines.append(f"  Chains with Multiple Locations: {chain_analysis['chains_with_multiple_locations']}")
        lines.append("")

        if chain_analysis['multi_location_chains']:
            lines.append("Top Chains (by location count):")
            for name, count in list(chain_analysis['multi_location_chains'].items())[:10]:
                lines.append(f"  {name}: {count} locations")
            lines.append("")

        if duplicates:
            lines.append("Duplicate Entries (by place_id):")
            for dup in duplicates[:10]:  # Show first 10
                lines.append(f"  {dup.name} ({dup.place_id[:20]}...)")
            if len(duplicates) > 10:
                lines.append(f"  ... and {len(duplicates) - 10} more")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)
