"""Unit tests for DataPersistence."""

import json
from pathlib import Path

import pytest

from fast_food_optimizer.data.persistence import DataPersistence
from fast_food_optimizer.models.restaurant import Coordinates, Restaurant


class TestDataPersistence:
    """Test suite for data persistence."""

    def setup_method(self):
        """Set up test fixtures."""
        # Will use tmp_path fixture per test
        pass

    def create_test_restaurants(self, count=3):
        """Create test restaurant data."""
        restaurants = []
        for i in range(count):
            coords = Coordinates(
                latitude=40.7589 + (i * 0.01),
                longitude=-111.8883 + (i * 0.01),
            )
            restaurant = Restaurant(
                place_id=f"ChIJTest{i}234567890",
                name=f"Restaurant {i}",
                address=f"{i*100} Main St",
                coordinates=coords,
                is_fast_food=True,
            )
            restaurants.append(restaurant)
        return restaurants

    def test_save_json(self, tmp_path):
        """Test saving restaurants to JSON."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        filepath = persistence.save_json(restaurants, "test_data")

        assert filepath.exists()
        assert filepath.suffix == ".json"

    def test_load_json(self, tmp_path):
        """Test loading restaurants from JSON."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        # Save first
        persistence.save_json(restaurants, "test_data")

        # Then load
        loaded = persistence.load_json("test_data")

        assert len(loaded) == 3
        assert loaded[0].place_id == restaurants[0].place_id
        assert loaded[0].name == restaurants[0].name

    def test_save_csv(self, tmp_path):
        """Test saving restaurants to CSV."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        filepath = persistence.save_csv(restaurants, "test_data")

        assert filepath.exists()
        assert filepath.suffix == ".csv"

    def test_save_both(self, tmp_path):
        """Test saving both JSON and CSV."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        json_path, csv_path = persistence.save_both(restaurants, "test_data")

        assert json_path.exists()
        assert csv_path.exists()
        assert json_path.suffix == ".json"
        assert csv_path.suffix == ".csv"

    def test_save_without_overwrite(self, tmp_path):
        """Test that existing files are not overwritten without flag."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        # Save twice without overwrite
        path1 = persistence.save_json(restaurants, "test_data", overwrite=False)
        path2 = persistence.save_json(restaurants, "test_data", overwrite=False)

        assert path1 != path2  # Different filenames (timestamp added)
        assert path1.exists()
        assert path2.exists()

    def test_list_saved_files(self, tmp_path):
        """Test listing saved files."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        persistence.save_json(restaurants, "test1")
        persistence.save_json(restaurants, "test2")

        files = persistence.list_saved_files("json")

        assert len(files) >= 2

    def test_get_file_info(self, tmp_path):
        """Test getting file metadata."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        persistence.save_json(restaurants, "test_data")

        info = persistence.get_file_info("test_data.json")

        assert info is not None
        assert info["format"] == "json"
        assert info["count"] == 3
        assert info["size_bytes"] > 0

    def test_roundtrip_preserves_data(self, tmp_path):
        """Test that save/load roundtrip preserves all data."""
        persistence = DataPersistence(data_dir=str(tmp_path))
        restaurants = self.create_test_restaurants(3)

        # Set some additional fields
        restaurants[0].rating = 4.5
        restaurants[0].phone = "801-555-1234"

        # Save and load
        persistence.save_json(restaurants, "test_data")
        loaded = persistence.load_json("test_data")

        # Verify all data preserved
        assert loaded[0].rating == 4.5
        assert loaded[0].phone == "801-555-1234"
        assert loaded[0].coordinates.latitude == restaurants[0].coordinates.latitude
