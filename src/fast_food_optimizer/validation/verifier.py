"""Manual verification tool for restaurant classifications.

This module provides an interactive command-line interface for manually
verifying and adjusting fast food restaurant classifications.
"""

from typing import List, Optional, Tuple
import sys

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.data.persistence import DataPersistence
from fast_food_optimizer.utils.logging import get_logger


class ManualVerifier:
    """Interactive tool for manually verifying restaurant classifications.

    Allows users to review and adjust is_fast_food flags and confidence scores
    for restaurants in a dataset.

    Example:
        >>> verifier = ManualVerifier()
        >>> restaurants = persistence.load_json("restaurants")
        >>> verified = verifier.verify_batch(restaurants)
        >>> persistence.save_json(verified, "restaurants_verified")
    """

    def __init__(self) -> None:
        """Initialize manual verifier."""
        self.logger = get_logger(__name__)
        self.verification_stats = {
            "total_reviewed": 0,
            "confirmed_fast_food": 0,
            "rejected_fast_food": 0,
            "skipped": 0,
        }

    def verify_batch(
        self,
        restaurants: List[Restaurant],
        confidence_threshold: float = 0.7,
    ) -> List[Restaurant]:
        """Interactively verify a batch of restaurants.

        Only restaurants with confidence below threshold are presented for review.

        Args:
            restaurants: List of restaurants to verify
            confidence_threshold: Only review below this confidence (0.0-1.0)

        Returns:
            List of verified restaurants (all restaurants, with updates)

        Example:
            >>> restaurants = verifier.verify_batch(restaurants, confidence_threshold=0.6)
        """
        self.logger.info(f"Starting manual verification of {len(restaurants)} restaurants")

        # Filter to low-confidence restaurants
        to_review = [
            r for r in restaurants
            if r.confidence_score < confidence_threshold
        ]

        self.logger.info(
            f"Found {len(to_review)} restaurants with confidence < {confidence_threshold}"
        )

        if not to_review:
            print("\n✅ All restaurants have high confidence scores. No manual verification needed.")
            return restaurants

        print(f"\n{'='*70}")
        print(f"MANUAL VERIFICATION - {len(to_review)} restaurants to review")
        print(f"{'='*70}")
        print("\nCommands:")
        print("  y/yes - Confirm as fast food")
        print("  n/no  - Reject as fast food (not fast food)")
        print("  s/skip - Skip this restaurant")
        print("  q/quit - Save and quit")
        print(f"{'='*70}\n")

        # Create lookup for quick updates
        restaurant_lookup = {r.place_id: r for r in restaurants}

        for i, restaurant in enumerate(to_review, 1):
            print(f"\n--- Restaurant {i}/{len(to_review)} ---")
            print(f"Name: {restaurant.name}")
            print(f"Address: {restaurant.address}")
            print(f"Current: {'✅ Fast Food' if restaurant.is_fast_food else '❌ Not Fast Food'}")
            print(f"Confidence: {restaurant.confidence_score:.2f}")
            if restaurant.place_types:
                print(f"Types: {', '.join(restaurant.place_types[:5])}")
            if restaurant.rating:
                print(f"Rating: {restaurant.rating} stars")

            # Get user input
            while True:
                response = input("\nVerify [y/n/s/q]: ").strip().lower()

                if response in ["q", "quit"]:
                    print(f"\n✅ Saved verification progress. {i-1} restaurants reviewed.")
                    self._print_stats()
                    return restaurants

                elif response in ["s", "skip"]:
                    self.verification_stats["skipped"] += 1
                    break

                elif response in ["y", "yes"]:
                    # Confirm as fast food
                    restaurant_lookup[restaurant.place_id].is_fast_food = True
                    restaurant_lookup[restaurant.place_id].confidence_score = 1.0
                    self.verification_stats["confirmed_fast_food"] += 1
                    self.verification_stats["total_reviewed"] += 1
                    print("✅ Confirmed as fast food")
                    break

                elif response in ["n", "no"]:
                    # Reject as fast food
                    restaurant_lookup[restaurant.place_id].is_fast_food = False
                    restaurant_lookup[restaurant.place_id].confidence_score = 0.0
                    self.verification_stats["rejected_fast_food"] += 1
                    self.verification_stats["total_reviewed"] += 1
                    print("❌ Marked as not fast food")
                    break

                else:
                    print("Invalid input. Please enter y/n/s/q")

        print(f"\n{'='*70}")
        print("✅ Verification complete!")
        self._print_stats()
        print(f"{'='*70}\n")

        return restaurants

    def verify_single(self, restaurant: Restaurant) -> Tuple[bool, float]:
        """Verify a single restaurant interactively.

        Args:
            restaurant: Restaurant to verify

        Returns:
            Tuple of (is_fast_food, confidence_score)

        Example:
            >>> is_fast_food, confidence = verifier.verify_single(restaurant)
        """
        print(f"\n--- Verify Restaurant ---")
        print(f"Name: {restaurant.name}")
        print(f"Address: {restaurant.address}")
        print(f"Current: {'✅ Fast Food' if restaurant.is_fast_food else '❌ Not Fast Food'}")
        print(f"Confidence: {restaurant.confidence_score:.2f}")

        while True:
            response = input("\nIs this fast food? [y/n]: ").strip().lower()

            if response in ["y", "yes"]:
                return True, 1.0
            elif response in ["n", "no"]:
                return False, 0.0
            else:
                print("Invalid input. Please enter y or n")

    def export_low_confidence(
        self,
        restaurants: List[Restaurant],
        confidence_threshold: float = 0.7,
        output_file: str = "low_confidence_restaurants",
    ) -> None:
        """Export low-confidence restaurants to CSV for manual review.

        Args:
            restaurants: List of restaurants
            confidence_threshold: Export below this confidence
            output_file: Base filename for export

        Example:
            >>> verifier.export_low_confidence(restaurants, 0.6, "to_review")
        """
        low_confidence = [
            r for r in restaurants
            if r.confidence_score < confidence_threshold
        ]

        if not low_confidence:
            self.logger.info("No low-confidence restaurants to export")
            return

        persistence = DataPersistence()
        csv_path = persistence.save_csv(low_confidence, output_file)

        self.logger.info(
            f"Exported {len(low_confidence)} low-confidence restaurants to {csv_path}"
        )
        print(f"\n✅ Exported {len(low_confidence)} restaurants for manual review:")
        print(f"   {csv_path}")
        print(f"\n   Review in spreadsheet software and re-import with updated classifications.\n")

    def _print_stats(self) -> None:
        """Print verification statistics."""
        print(f"\nVerification Statistics:")
        print(f"  Total Reviewed: {self.verification_stats['total_reviewed']}")
        print(f"  Confirmed Fast Food: {self.verification_stats['confirmed_fast_food']}")
        print(f"  Rejected Fast Food: {self.verification_stats['rejected_fast_food']}")
        print(f"  Skipped: {self.verification_stats['skipped']}")

    def get_stats(self) -> dict:
        """Get verification statistics.

        Returns:
            Dictionary with verification stats
        """
        return self.verification_stats.copy()

    def reset_stats(self) -> None:
        """Reset verification statistics."""
        self.verification_stats = {
            "total_reviewed": 0,
            "confirmed_fast_food": 0,
            "rejected_fast_food": 0,
            "skipped": 0,
        }
