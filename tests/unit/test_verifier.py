"""Unit tests for ManualVerifier."""

from unittest.mock import Mock, patch
import pytest

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.validation.verifier import ManualVerifier


class TestManualVerifier:
    """Test suite for manual verification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.verifier = ManualVerifier()

    def create_test_restaurant(
        self,
        place_id: str,
        name: str,
        is_fast_food: bool = False,
        confidence: float = 0.5,
    ) -> Restaurant:
        """Helper to create test restaurants."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St",
            coordinates=coords,
            is_fast_food=is_fast_food,
            confidence_score=confidence,
        )

    def test_verify_single_yes(self):
        """Test verifying single restaurant as fast food."""
        restaurant = self.create_test_restaurant(
            "ChIJTest1234567890",
            "Test Restaurant",
        )

        with patch("builtins.input", return_value="y"):
            is_fast_food, confidence = self.verifier.verify_single(restaurant)

        assert is_fast_food is True
        assert confidence == 1.0

    def test_verify_single_no(self):
        """Test rejecting single restaurant as fast food."""
        restaurant = self.create_test_restaurant(
            "ChIJTest1234567890",
            "Test Restaurant",
        )

        with patch("builtins.input", return_value="n"):
            is_fast_food, confidence = self.verifier.verify_single(restaurant)

        assert is_fast_food is False
        assert confidence == 0.0

    def test_verify_single_invalid_then_valid(self):
        """Test invalid input followed by valid input."""
        restaurant = self.create_test_restaurant(
            "ChIJTest1234567890",
            "Test Restaurant",
        )

        with patch("builtins.input", side_effect=["invalid", "x", "yes"]):
            is_fast_food, confidence = self.verifier.verify_single(restaurant)

        assert is_fast_food is True
        assert confidence == 1.0

    def test_get_stats_initial(self):
        """Test getting initial statistics."""
        stats = self.verifier.get_stats()

        assert stats["total_reviewed"] == 0
        assert stats["confirmed_fast_food"] == 0
        assert stats["rejected_fast_food"] == 0
        assert stats["skipped"] == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        # Manually increment stats
        self.verifier.verification_stats["total_reviewed"] = 5
        self.verifier.verification_stats["confirmed_fast_food"] = 3

        self.verifier.reset_stats()

        stats = self.verifier.get_stats()
        assert stats["total_reviewed"] == 0
        assert stats["confirmed_fast_food"] == 0

    def test_verify_batch_no_low_confidence(self):
        """Test batch verification with all high confidence."""
        restaurants = [
            self.create_test_restaurant(
                f"ChIJTest{i}234567890",
                f"Restaurant {i}",
                is_fast_food=True,
                confidence=0.9,
            )
            for i in range(3)
        ]

        result = self.verifier.verify_batch(restaurants, confidence_threshold=0.7)

        # All restaurants should be returned unchanged
        assert len(result) == 3
        assert all(r.confidence_score == 0.9 for r in result)

    def test_export_low_confidence(self, tmp_path):
        """Test exporting low confidence restaurants."""
        restaurants = [
            self.create_test_restaurant(
                "ChIJTest1234567890",
                "Restaurant 1",
                confidence=0.4,
            ),
            self.create_test_restaurant(
                "ChIJTest2234567890",
                "Restaurant 2",
                confidence=0.8,
            ),
        ]

        # Mock DataPersistence
        with patch("fast_food_optimizer.validation.verifier.DataPersistence") as mock_persistence:
            mock_instance = Mock()
            mock_persistence.return_value = mock_instance
            mock_instance.save_csv.return_value = tmp_path / "low_confidence.csv"

            self.verifier.export_low_confidence(
                restaurants,
                confidence_threshold=0.7,
                output_file="low_confidence",
            )

            # Should export only the low confidence restaurant
            mock_instance.save_csv.assert_called_once()
            exported_restaurants = mock_instance.save_csv.call_args[0][0]
            assert len(exported_restaurants) == 1
            assert exported_restaurants[0].name == "Restaurant 1"

    def test_export_low_confidence_none(self):
        """Test exporting when no low confidence restaurants."""
        restaurants = [
            self.create_test_restaurant(
                "ChIJTest1234567890",
                "Restaurant 1",
                confidence=0.9,
            ),
        ]

        with patch("fast_food_optimizer.validation.verifier.DataPersistence") as mock_persistence:
            mock_instance = Mock()
            mock_persistence.return_value = mock_instance

            self.verifier.export_low_confidence(
                restaurants,
                confidence_threshold=0.7,
            )

            # Should not call save_csv
            mock_instance.save_csv.assert_not_called()
