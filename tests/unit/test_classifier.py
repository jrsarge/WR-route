"""Unit tests for FastFoodClassifier."""

import pytest

from fast_food_optimizer.data.classifier import FastFoodClassifier


class TestFastFoodClassifier:
    """Test suite for fast food classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = FastFoodClassifier()

    def test_classify_known_chain(self):
        """Test classification of known fast food chain."""
        is_fast_food, confidence = self.classifier.classify(
            name="McDonald's",
            place_types=["restaurant", "food", "point_of_interest"],
        )

        assert is_fast_food is True
        assert confidence >= 0.8  # Chain name gives high confidence

    def test_classify_with_takeaway_type(self):
        """Test classification with meal_takeaway type."""
        is_fast_food, confidence = self.classifier.classify(
            name="Quick Bites",
            place_types=["restaurant", "meal_takeaway", "food"],
        )

        assert is_fast_food is True
        assert confidence >= 0.5

    def test_classify_excluded_type(self):
        """Test that excluded types return False."""
        is_fast_food, confidence = self.classifier.classify(
            name="The Wine Bar",
            place_types=["bar", "night_club"],
        )

        assert is_fast_food is False
        assert confidence == 0.0

    def test_classify_sit_down_restaurant(self):
        """Test that sit-down restaurant has low confidence."""
        is_fast_food, confidence = self.classifier.classify(
            name="The Fancy Dining Room",
            place_types=["restaurant"],
        )

        # Should have low confidence without fast food indicators
        assert confidence < 0.5

    def test_classify_multiple_mcdonalds(self):
        """Test that multiple McDonald's locations all classify as fast food.

        CRITICAL: Validates chain locations policy.
        """
        # Three different McDonald's locations
        names = [
            "McDonald's - Downtown",
            "McDonald's - University Area",
            "McDonald's - Airport",
        ]

        for name in names:
            is_fast_food, confidence = self.classifier.classify(
                name=name,
                place_types=["restaurant", "food"],
            )

            assert is_fast_food is True
            assert confidence >= 0.8

    def test_classify_batch(self):
        """Test batch classification."""
        restaurants = [
            {"name": "McDonald's", "place_types": ["restaurant"]},
            {"name": "Subway", "place_types": ["meal_takeaway"]},
            {"name": "Fancy Steakhouse", "place_types": ["restaurant"]},
        ]

        results = self.classifier.classify_batch(restaurants)

        assert len(results) == 3
        assert results[0][0] is True  # McDonald's
        assert results[1][0] is True  # Subway
        # Fancy Steakhouse might be True or False depending on confidence

    def test_classify_starbucks(self):
        """Test classification of Starbucks (cafe/coffee)."""
        is_fast_food, confidence = self.classifier.classify(
            name="Starbucks",
            place_types=["cafe", "food", "store"],
        )

        assert is_fast_food is True
        assert confidence >= 0.8

    def test_classify_food_court_vendor(self):
        """Test classification of food court vendor."""
        is_fast_food, confidence = self.classifier.classify(
            name="Panda Express",
            place_types=["restaurant", "meal_takeaway"],
            description="Food court location",
        )

        assert is_fast_food is True

    def test_get_chain_name(self):
        """Test extracting chain name from restaurant name."""
        assert "mcdonald" == self.classifier.get_chain_name("McDonald's - Downtown")
        assert "subway" == self.classifier.get_chain_name("Subway Restaurant")
        assert "Joe's Diner" == self.classifier.get_chain_name("Joe's Diner")

    def test_confidence_capped_at_one(self):
        """Test that confidence never exceeds 1.0."""
        is_fast_food, confidence = self.classifier.classify(
            name="McDonald's",  # Chain name: +0.8
            place_types=["restaurant", "food", "meal_takeaway"],  # +0.6 + 0.2
        )

        assert confidence <= 1.0
