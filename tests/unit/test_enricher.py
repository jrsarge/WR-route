"""Unit tests for PlaceDetailsEnricher."""

from unittest.mock import Mock, MagicMock
import pytest

from fast_food_optimizer.data.enricher import PlaceDetailsEnricher
from fast_food_optimizer.models.restaurant import Coordinates, DayHours


class TestPlaceDetailsEnricher:
    """Test suite for place details enrichment."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Google client
        self.mock_client = Mock()
        self.enricher = PlaceDetailsEnricher(self.mock_client)

    def test_enrich_restaurant_basic(self):
        """Test enriching restaurant with basic information."""
        place_data = {
            "place_id": "ChIJTest1234567890",
            "name": "Test Restaurant",
            "vicinity": "123 Main St",
            "geometry": {
                "location": {"lat": 40.7589, "lng": -111.8883}
            },
            "types": ["restaurant", "food"],
            "rating": 4.2,
        }

        # Mock get_place_details to return None (no enrichment)
        self.mock_client.get_place_details.return_value = None

        restaurant = self.enricher.enrich_restaurant(place_data, fetch_details=False)

        assert restaurant is not None
        assert restaurant.place_id == "ChIJTest1234567890"
        assert restaurant.name == "Test Restaurant"
        assert restaurant.address == "123 Main St"
        assert restaurant.coordinates.latitude == 40.7589
        assert restaurant.coordinates.longitude == -111.8883
        assert restaurant.rating == 4.2

    def test_enrich_restaurant_missing_place_id(self):
        """Test that missing place_id returns None."""
        place_data = {
            "name": "Test Restaurant",
            "vicinity": "123 Main St",
        }

        restaurant = self.enricher.enrich_restaurant(place_data)

        assert restaurant is None

    def test_enrich_restaurant_missing_coordinates(self):
        """Test that missing coordinates returns None."""
        place_data = {
            "place_id": "ChIJTest1234567890",
            "name": "Test Restaurant",
            "vicinity": "123 Main St",
            "geometry": {},  # Missing location
        }

        restaurant = self.enricher.enrich_restaurant(place_data)

        assert restaurant is None

    def test_enrich_restaurant_with_details(self):
        """Test enriching restaurant with place details."""
        place_data = {
            "place_id": "ChIJTest1234567890",
            "name": "McDonald's",
            "vicinity": "123 Main St",
            "geometry": {
                "location": {"lat": 40.7589, "lng": -111.8883}
            },
            "types": ["restaurant", "food"],
        }

        # Mock place details response
        details = {
            "formatted_phone_number": "+1 801-555-1234",
            "website": "https://www.mcdonalds.com",
            "rating": 4.2,
            "opening_hours": {
                "periods": [
                    {
                        "open": {"day": 1, "time": "0600"},
                        "close": {"day": 1, "time": "2300"},
                    }
                ]
            },
        }
        self.mock_client.get_place_details.return_value = details

        restaurant = self.enricher.enrich_restaurant(place_data, fetch_details=True)

        assert restaurant is not None
        assert restaurant.phone == "+1 801-555-1234"
        assert restaurant.website == "https://www.mcdonalds.com"
        assert restaurant.rating == 4.2
        assert restaurant.operating_hours is not None
        assert restaurant.operating_hours.monday is not None

    def test_parse_operating_hours_basic(self):
        """Test parsing basic operating hours."""
        place_details = {
            "opening_hours": {
                "periods": [
                    {
                        "open": {"day": 1, "time": "0900"},
                        "close": {"day": 1, "time": "2100"},
                    },
                    {
                        "open": {"day": 2, "time": "0900"},
                        "close": {"day": 2, "time": "2100"},
                    },
                ]
            }
        }

        hours = self.enricher._parse_operating_hours(place_details)

        assert hours is not None
        assert hours.monday is not None
        assert hours.monday.open_time == "09:00"
        assert hours.monday.close_time == "21:00"
        assert hours.tuesday is not None
        assert hours.tuesday.open_time == "09:00"
        assert hours.tuesday.close_time == "21:00"

    def test_parse_operating_hours_24h(self):
        """Test parsing 24-hour operation."""
        place_details = {
            "opening_hours": {
                "periods": [
                    {
                        "open": {"day": 0, "time": "0000"},
                        # No close means 24h
                    }
                ]
            }
        }

        hours = self.enricher._parse_operating_hours(place_details)

        assert hours is not None
        assert hours.sunday is not None
        assert hours.sunday.is_open_24h

    def test_parse_operating_hours_empty(self):
        """Test parsing empty operating hours."""
        place_details = {"opening_hours": {}}

        hours = self.enricher._parse_operating_hours(place_details)

        assert hours is None

    def test_format_time(self):
        """Test time formatting from Google format."""
        assert self.enricher._format_time("0600") == "06:00"
        assert self.enricher._format_time("1430") == "14:30"
        assert self.enricher._format_time("2359") == "23:59"
        assert self.enricher._format_time("0000") == "00:00"

    def test_format_time_invalid(self):
        """Test invalid time formatting."""
        assert self.enricher._format_time("") is None
        assert self.enricher._format_time("123") is None
        assert self.enricher._format_time("12345") is None
        assert self.enricher._format_time(None) is None

    def test_enrich_batch(self):
        """Test batch enrichment."""
        places = [
            {
                "place_id": f"ChIJTest{i}234567890",
                "name": f"Restaurant {i}",
                "vicinity": f"{i} Main St",
                "geometry": {
                    "location": {"lat": 40.7589 + i * 0.01, "lng": -111.8883}
                },
                "types": ["restaurant"],
            }
            for i in range(3)
        ]

        self.mock_client.get_place_details.return_value = None

        restaurants = self.enricher.enrich_batch(places, fetch_details=False)

        assert len(restaurants) == 3
        assert all(r.place_id.startswith("ChIJTest") for r in restaurants)

    def test_enrich_batch_with_failures(self):
        """Test batch enrichment with some failures."""
        places = [
            {
                "place_id": "ChIJTest1234567890",
                "name": "Restaurant 1",
                "vicinity": "1 Main St",
                "geometry": {
                    "location": {"lat": 40.7589, "lng": -111.8883}
                },
            },
            {
                # Missing place_id - should fail
                "name": "Restaurant 2",
                "vicinity": "2 Main St",
            },
            {
                "place_id": "ChIJTest3234567890",
                "name": "Restaurant 3",
                "vicinity": "3 Main St",
                "geometry": {
                    "location": {"lat": 40.7589, "lng": -111.8883}
                },
            },
        ]

        self.mock_client.get_place_details.return_value = None

        restaurants = self.enricher.enrich_batch(places, fetch_details=False)

        # Only 2 should succeed
        assert len(restaurants) == 2
        assert restaurants[0].name == "Restaurant 1"
        assert restaurants[1].name == "Restaurant 3"

    def test_get_enrichment_stats(self):
        """Test enrichment statistics tracking."""
        place_data = {
            "place_id": "ChIJTest1234567890",
            "name": "Test Restaurant",
            "vicinity": "123 Main St",
            "geometry": {
                "location": {"lat": 40.7589, "lng": -111.8883}
            },
            "types": ["restaurant"],
            "rating": 4.2,
        }

        details = {
            "formatted_phone_number": "+1 801-555-1234",
            "website": "https://example.com",
        }
        self.mock_client.get_place_details.return_value = details

        # Enrich one restaurant
        self.enricher.enrich_restaurant(place_data, fetch_details=True)

        stats = self.enricher.get_enrichment_stats()

        assert stats["total_processed"] == 1
        assert stats["with_rating"] == 1
        assert stats["with_phone"] == 1
        assert stats["with_website"] == 1
        assert stats["phone_percentage"] == 100.0

    def test_reset_stats(self):
        """Test resetting enrichment statistics."""
        place_data = {
            "place_id": "ChIJTest1234567890",
            "name": "Test Restaurant",
            "vicinity": "123 Main St",
            "geometry": {
                "location": {"lat": 40.7589, "lng": -111.8883}
            },
        }

        self.mock_client.get_place_details.return_value = None

        # Enrich one restaurant
        self.enricher.enrich_restaurant(place_data, fetch_details=False)

        assert self.enricher.get_enrichment_stats()["total_processed"] == 1

        # Reset
        self.enricher.reset_stats()

        assert self.enricher.get_enrichment_stats()["total_processed"] == 0
