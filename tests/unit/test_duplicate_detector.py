"""Unit tests for DuplicateDetector."""

import pytest

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.validation.duplicate_detector import DuplicateDetector


class TestDuplicateDetector:
    """Test suite for duplicate detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DuplicateDetector()

    def create_restaurant(
        self,
        place_id: str,
        name: str,
        latitude: float = 40.7589,
        longitude: float = -111.8883,
        confidence: float = 0.8,
    ) -> Restaurant:
        """Helper to create test restaurant."""
        coords = Coordinates(latitude=latitude, longitude=longitude)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=confidence,
        )

    def test_detect_no_duplicates(self):
        """Test detecting no duplicates."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant 1"),
            self.create_restaurant("ChIJTest2234567890", "Restaurant 2"),
            self.create_restaurant("ChIJTest3234567890", "Restaurant 3"),
        ]

        unique, duplicates = self.detector.detect_duplicates(restaurants)

        assert len(unique) == 3
        assert len(duplicates) == 0

    def test_detect_duplicates_same_place_id(self):
        """Test detecting duplicates by place_id."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),
            self.create_restaurant("ChIJTest2234567890", "Restaurant B"),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),  # Duplicate
        ]

        unique, duplicates = self.detector.detect_duplicates(restaurants)

        assert len(unique) == 2
        assert len(duplicates) == 1
        assert duplicates[0].place_id == "ChIJTest1234567890"

    def test_multiple_locations_not_duplicates(self):
        """Test that multiple locations of same chain are NOT duplicates.

        CRITICAL: Validates chain locations policy.
        """
        restaurants = [
            self.create_restaurant("ChIJMcD1234567890", "McDonald's", 40.7589, -111.8883),
            self.create_restaurant("ChIJMcD2234567890", "McDonald's", 40.7614, -111.8910),
            self.create_restaurant("ChIJMcD3234567890", "McDonald's", 40.7650, -111.8950),
        ]

        unique, duplicates = self.detector.detect_duplicates(restaurants)

        # All three McDonald's should be unique (different place_ids)
        assert len(unique) == 3
        assert len(duplicates) == 0

    def test_remove_duplicates_keep_first(self):
        """Test removing duplicates, keeping first occurrence."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.6),
            self.create_restaurant("ChIJTest2234567890", "Restaurant B", confidence=0.7),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.9),
        ]

        unique = self.detector.remove_duplicates(restaurants, keep="first")

        assert len(unique) == 2
        # Should keep first occurrence (confidence 0.6)
        kept = [r for r in unique if r.place_id == "ChIJTest1234567890"][0]
        assert kept.confidence_score == 0.6

    def test_remove_duplicates_keep_last(self):
        """Test removing duplicates, keeping last occurrence."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.6),
            self.create_restaurant("ChIJTest2234567890", "Restaurant B", confidence=0.7),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.9),
        ]

        unique = self.detector.remove_duplicates(restaurants, keep="last")

        assert len(unique) == 2
        # Should keep last occurrence (confidence 0.9)
        kept = [r for r in unique if r.place_id == "ChIJTest1234567890"][0]
        assert kept.confidence_score == 0.9

    def test_remove_duplicates_keep_best(self):
        """Test removing duplicates, keeping best confidence."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.6),
            self.create_restaurant("ChIJTest2234567890", "Restaurant B", confidence=0.7),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.9),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A", confidence=0.5),
        ]

        unique = self.detector.remove_duplicates(restaurants, keep="best")

        assert len(unique) == 2
        # Should keep best confidence (0.9)
        kept = [r for r in unique if r.place_id == "ChIJTest1234567890"][0]
        assert kept.confidence_score == 0.9

    def test_remove_duplicates_invalid_keep(self):
        """Test invalid keep parameter raises error."""
        restaurants = [self.create_restaurant("ChIJTest1234567890", "Restaurant A")]

        with pytest.raises(ValueError):
            self.detector.remove_duplicates(restaurants, keep="invalid")

    def test_analyze_chain_distribution(self):
        """Test analyzing chain distribution."""
        restaurants = [
            self.create_restaurant("ChIJMcD1234567890", "McDonald's"),
            self.create_restaurant("ChIJMcD2234567890", "McDonald's"),
            self.create_restaurant("ChIJMcD3234567890", "McDonald's"),
            self.create_restaurant("ChIJSub1234567890", "Subway"),
            self.create_restaurant("ChIJSub2234567890", "Subway"),
            self.create_restaurant("ChIJKFC1234567890", "KFC"),
        ]

        analysis = self.detector.analyze_chain_distribution(restaurants)

        assert analysis["total_restaurants"] == 6
        assert analysis["unique_names"] == 3
        assert analysis["chains_with_multiple_locations"] == 2  # McDonald's and Subway
        assert "McDonald's" in analysis["multi_location_chains"]
        assert analysis["multi_location_chains"]["McDonald's"] == 3
        assert "Subway" in analysis["multi_location_chains"]
        assert analysis["multi_location_chains"]["Subway"] == 2

    def test_analyze_chain_distribution_top_chain(self):
        """Test identifying top chain."""
        restaurants = [
            self.create_restaurant(f"ChIJMcD{i}234567890", "McDonald's")
            for i in range(5)
        ] + [
            self.create_restaurant(f"ChIJSub{i}234567890", "Subway")
            for i in range(2)
        ]

        analysis = self.detector.analyze_chain_distribution(restaurants)

        assert analysis["top_chain"] == ("McDonald's", 5)

    def test_find_near_duplicates(self):
        """Test finding suspiciously close restaurants."""
        # Two restaurants with same name, very close together
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Starbucks", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "Starbucks", 40.7590, -111.8884),  # ~15m away
            self.create_restaurant("ChIJTest3234567890", "McDonald's", 40.7700, -111.9000),  # Far away
        ]

        near_dupes = self.detector.find_near_duplicates(restaurants, distance_threshold_km=0.05)

        # Should find one near-duplicate pair (two Starbucks)
        assert len(near_dupes) >= 1
        r1, r2, distance = near_dupes[0]
        assert r1.name == "Starbucks"
        assert r2.name == "Starbucks"
        assert distance < 0.05

    def test_find_near_duplicates_different_names(self):
        """Test that near restaurants with different names are not flagged."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Starbucks", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "McDonald's", 40.7590, -111.8884),  # Different name
        ]

        near_dupes = self.detector.find_near_duplicates(restaurants, distance_threshold_km=0.05)

        # Should NOT flag as near-duplicate (different names)
        assert len(near_dupes) == 0

    def test_get_stats(self):
        """Test getting detection statistics."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),
            self.create_restaurant("ChIJTest2234567890", "Restaurant B"),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),  # Duplicate
        ]

        self.detector.detect_duplicates(restaurants)
        stats = self.detector.get_stats()

        assert stats["total_processed"] == 3
        assert stats["unique_count"] == 2
        assert stats["duplicates_found"] == 1
        assert stats["duplicate_percentage"] > 0

    def test_reset_stats(self):
        """Test resetting detection statistics."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),
        ]

        self.detector.detect_duplicates(restaurants)
        assert self.detector.get_stats()["total_processed"] == 1

        self.detector.reset_stats()
        assert self.detector.get_stats()["total_processed"] == 0

    def test_generate_report(self):
        """Test generating duplicate detection report."""
        restaurants = [
            self.create_restaurant("ChIJMcD1234567890", "McDonald's"),
            self.create_restaurant("ChIJMcD2234567890", "McDonald's"),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),
            self.create_restaurant("ChIJTest1234567890", "Restaurant A"),  # Duplicate
        ]

        report = self.detector.generate_report(restaurants)

        assert "DUPLICATE DETECTION REPORT" in report
        assert "McDonald's" in report  # Chain with multiple locations
        assert "Duplicate Entries" in report

    def test_empty_restaurant_list(self):
        """Test handling empty restaurant list."""
        restaurants = []

        unique, duplicates = self.detector.detect_duplicates(restaurants)

        assert len(unique) == 0
        assert len(duplicates) == 0
