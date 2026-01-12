"""Unit tests for Restaurant data models."""

from datetime import datetime, time

import pytest
from pydantic import ValidationError

from fast_food_optimizer.models.restaurant import (
    Coordinates,
    DayHours,
    OperatingHours,
    Restaurant,
)
from fast_food_optimizer.utils.exceptions import DataValidationError


class TestCoordinates:
    """Test suite for Coordinates model."""

    def test_valid_coordinates(self):
        """Test creating coordinates with valid values."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)

        assert coords.latitude == 40.7589
        assert coords.longitude == -111.8883

    def test_coordinates_to_tuple(self):
        """Test converting coordinates to tuple."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        lat, lng = coords.to_tuple()

        assert lat == 40.7589
        assert lng == -111.8883

    def test_invalid_latitude_too_low(self):
        """Test that latitude below -90 raises error."""
        with pytest.raises(ValidationError):
            Coordinates(latitude=-100, longitude=-111.8883)

    def test_invalid_latitude_too_high(self):
        """Test that latitude above 90 raises error."""
        with pytest.raises(ValidationError):
            Coordinates(latitude=100, longitude=-111.8883)

    def test_invalid_longitude_too_low(self):
        """Test that longitude below -180 raises error."""
        with pytest.raises(ValidationError):
            Coordinates(latitude=40.7589, longitude=-200)

    def test_invalid_longitude_too_high(self):
        """Test that longitude above 180 raises error."""
        with pytest.raises(ValidationError):
            Coordinates(latitude=40.7589, longitude=200)

    def test_coordinates_string_representation(self):
        """Test string representation of coordinates."""
        coords = Coordinates(latitude=40.758900, longitude=-111.888300)
        coords_str = str(coords)

        assert "40.758900" in coords_str
        assert "-111.888300" in coords_str


class TestDayHours:
    """Test suite for DayHours model."""

    def test_valid_day_hours(self):
        """Test creating day hours with valid times."""
        hours = DayHours(open_time="09:00", close_time="21:00")

        assert hours.open_time == "09:00"
        assert hours.close_time == "21:00"
        assert not hours.is_open_24h
        assert not hours.is_closed

    def test_24_hour_operation(self):
        """Test 24-hour operation flag."""
        hours = DayHours(is_open_24h=True)

        assert hours.is_open_24h
        assert hours.is_open_at(time(3, 0))  # 3:00 AM
        assert hours.is_open_at(time(15, 30))  # 3:30 PM

    def test_closed_all_day(self):
        """Test closed all day flag."""
        hours = DayHours(is_closed=True)

        assert hours.is_closed
        assert not hours.is_open_at(time(12, 0))

    def test_is_open_at_valid_time(self):
        """Test checking if open at a specific time."""
        hours = DayHours(open_time="09:00", close_time="21:00")

        assert hours.is_open_at(time(12, 0))  # Noon
        assert hours.is_open_at(time(9, 0))  # Opening time
        assert hours.is_open_at(time(21, 0))  # Closing time

    def test_is_open_at_invalid_time(self):
        """Test checking if open when closed."""
        hours = DayHours(open_time="09:00", close_time="21:00")

        assert not hours.is_open_at(time(3, 0))  # 3:00 AM
        assert not hours.is_open_at(time(22, 0))  # 10:00 PM

    def test_overnight_hours(self):
        """Test overnight hours (e.g., 22:00 to 02:00)."""
        hours = DayHours(open_time="22:00", close_time="02:00")

        assert hours.is_open_at(time(23, 0))  # 11:00 PM
        assert hours.is_open_at(time(0, 30))  # 12:30 AM
        assert hours.is_open_at(time(1, 45))  # 1:45 AM
        assert not hours.is_open_at(time(12, 0))  # Noon

    def test_invalid_time_format(self):
        """Test invalid time format raises error."""
        with pytest.raises(DataValidationError):
            DayHours(open_time="25:00", close_time="21:00")

        with pytest.raises(DataValidationError):
            DayHours(open_time="09:60", close_time="21:00")


class TestOperatingHours:
    """Test suite for OperatingHours model."""

    def test_operating_hours_all_days(self):
        """Test creating operating hours for all days."""
        monday = DayHours(open_time="09:00", close_time="21:00")
        hours = OperatingHours(
            monday=monday,
            tuesday=monday,
            wednesday=monday,
            thursday=monday,
            friday=monday,
            saturday=monday,
            sunday=monday,
        )

        assert hours.monday == monday
        assert hours.is_open_on_day("monday", time(12, 0))

    def test_is_open_on_day_without_time(self):
        """Test checking if open on a day without specific time."""
        hours = OperatingHours(
            monday=DayHours(open_time="09:00", close_time="21:00"),
            tuesday=DayHours(is_closed=True),
        )

        assert hours.is_open_on_day("monday")
        assert not hours.is_open_on_day("tuesday")

    def test_is_open_on_day_with_time(self):
        """Test checking if open on a day at specific time."""
        hours = OperatingHours(
            monday=DayHours(open_time="09:00", close_time="21:00")
        )

        assert hours.is_open_on_day("monday", time(12, 0))
        assert not hours.is_open_on_day("monday", time(22, 0))


class TestRestaurant:
    """Test suite for Restaurant model."""

    def test_create_valid_restaurant(self):
        """Test creating a valid restaurant."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        restaurant = Restaurant(
            place_id="ChIJTest123456789",
            name="McDonald's",
            address="123 Main St, Salt Lake City, UT",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.9,
        )

        assert restaurant.place_id == "ChIJTest123456789"
        assert restaurant.name == "McDonald's"
        assert restaurant.is_fast_food
        assert restaurant.confidence_score == 0.9

    def test_restaurant_missing_place_id(self):
        """Test that missing place_id raises error."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)

        with pytest.raises(DataValidationError) as exc_info:
            Restaurant(
                place_id="",  # Empty place_id
                name="Test Restaurant",
                address="123 Main St",
                coordinates=coords,
            )

        assert "place_id" in str(exc_info.value)

    def test_restaurant_missing_name(self):
        """Test that missing name raises error."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)

        with pytest.raises(DataValidationError) as exc_info:
            Restaurant(
                place_id="ChIJTest123456789",
                name="",  # Empty name
                address="123 Main St",
                coordinates=coords,
            )

        assert "name" in str(exc_info.value).lower()

    def test_restaurant_invalid_rating(self):
        """Test that invalid rating raises error."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)

        with pytest.raises(DataValidationError):
            Restaurant(
                place_id="ChIJTest123456789",
                name="Test Restaurant",
                address="123 Main St",
                coordinates=coords,
                rating=6.0,  # Invalid: ratings are 0-5
            )

    def test_restaurant_invalid_confidence(self):
        """Test that invalid confidence score raises error."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)

        with pytest.raises(DataValidationError):
            Restaurant(
                place_id="ChIJTest123456789",
                name="Test Restaurant",
                address="123 Main St",
                coordinates=coords,
                confidence_score=1.5,  # Invalid: must be 0-1
            )

    def test_distance_to_another_restaurant(self):
        """Test calculating distance between restaurants."""
        coords1 = Coordinates(latitude=40.7589, longitude=-111.8883)
        coords2 = Coordinates(latitude=40.7614, longitude=-111.8910)

        restaurant1 = Restaurant(
            place_id="ChIJTest1234567",
            name="Restaurant A",
            address="123 Main St",
            coordinates=coords1,
        )

        restaurant2 = Restaurant(
            place_id="ChIJTest2345678",
            name="Restaurant B",
            address="456 Oak Ave",
            coordinates=coords2,
        )

        distance_km = restaurant1.distance_to(restaurant2)

        # These coordinates are about 0.3 km apart
        assert 0.2 < distance_km < 0.5

    def test_restaurant_to_dict(self):
        """Test converting restaurant to dictionary."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        restaurant = Restaurant(
            place_id="ChIJTest123456789",
            name="McDonald's",
            address="123 Main St",
            coordinates=coords,
            place_types=["restaurant", "food"],
            is_fast_food=True,
            confidence_score=0.9,
        )

        restaurant_dict = restaurant.to_dict()

        assert restaurant_dict["place_id"] == "ChIJTest123456789"
        assert restaurant_dict["name"] == "McDonald's"
        assert restaurant_dict["coordinates"]["latitude"] == 40.7589
        assert restaurant_dict["is_fast_food"] is True

    def test_restaurant_from_dict(self):
        """Test creating restaurant from dictionary."""
        data = {
            "place_id": "ChIJTest123456789",
            "name": "McDonald's",
            "address": "123 Main St",
            "coordinates": {"latitude": 40.7589, "longitude": -111.8883},
            "place_types": ["restaurant", "food"],
            "is_fast_food": True,
            "confidence_score": 0.9,
        }

        restaurant = Restaurant.from_dict(data)

        assert restaurant.place_id == "ChIJTest123456789"
        assert restaurant.name == "McDonald's"
        assert restaurant.coordinates.latitude == 40.7589
        assert restaurant.is_fast_food

    def test_restaurant_string_representation(self):
        """Test string representation of restaurant."""
        coords = Coordinates(latitude=40.7589, longitude=-111.8883)
        restaurant = Restaurant(
            place_id="ChIJTest123456789",
            name="McDonald's",
            address="123 Main St",
            coordinates=coords,
        )

        restaurant_str = str(restaurant)

        assert "McDonald's" in restaurant_str
        assert "123 Main St" in restaurant_str

    def test_multiple_restaurants_same_name_different_place_id(self):
        """Test that multiple locations of same chain are valid.

        CRITICAL: This validates the chain locations policy.
        """
        coords1 = Coordinates(latitude=40.7589, longitude=-111.8883)
        coords2 = Coordinates(latitude=40.7614, longitude=-111.8910)

        # Two McDonald's locations - both valid
        mcdonalds_a = Restaurant(
            place_id="ChIJTestMcDonaldsA",
            name="McDonald's",
            address="123 Main St",
            coordinates=coords1,
            is_fast_food=True,
        )

        mcdonalds_b = Restaurant(
            place_id="ChIJTestMcDonaldsB",
            name="McDonald's",
            address="456 Oak Ave",
            coordinates=coords2,
            is_fast_food=True,
        )

        # Both should be valid restaurants
        assert mcdonalds_a.place_id != mcdonalds_b.place_id
        assert mcdonalds_a.name == mcdonalds_b.name
        assert mcdonalds_a.is_fast_food
        assert mcdonalds_b.is_fast_food
