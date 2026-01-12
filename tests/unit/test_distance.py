"""Unit tests for DistanceCalculator."""

import pytest
import numpy as np

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.distance import DistanceCalculator


class TestDistanceCalculator:
    """Test suite for distance calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = DistanceCalculator()

    def create_restaurant(
        self,
        place_id: str,
        name: str,
        latitude: float,
        longitude: float,
    ) -> Restaurant:
        """Helper to create restaurant with specific coordinates."""
        coords = Coordinates(latitude=latitude, longitude=longitude)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.9,
        )

    def test_calculate_distance_same_location(self):
        """Test distance between same location is zero."""
        restaurant = self.create_restaurant(
            "ChIJTest1234567890",
            "Restaurant 1",
            40.7589,
            -111.8883,
        )

        distance = self.calculator.calculate_distance(restaurant, restaurant)

        assert distance == pytest.approx(0.0, abs=0.001)

    def test_calculate_distance_known_distance(self):
        """Test distance calculation with known coordinates."""
        # Salt Lake City to Provo (approximately 62 km)
        slc = self.create_restaurant(
            "ChIJTest1234567890",
            "Restaurant SLC",
            40.7589,
            -111.8883,
        )
        provo = self.create_restaurant(
            "ChIJTest2234567890",
            "Restaurant Provo",
            40.2338,
            -111.6585,
        )

        distance = self.calculator.calculate_distance(slc, provo)

        # Should be approximately 62 km
        assert 60 < distance < 65

    def test_calculate_distance_symmetry(self):
        """Test that distance(A,B) == distance(B,A)."""
        r1 = self.create_restaurant(
            "ChIJTest1234567890",
            "Restaurant 1",
            40.7589,
            -111.8883,
        )
        r2 = self.create_restaurant(
            "ChIJTest2234567890",
            "Restaurant 2",
            40.2338,
            -111.6585,
        )

        d1 = self.calculator.calculate_distance(r1, r2)
        d2 = self.calculator.calculate_distance(r2, r1)

        assert d1 == pytest.approx(d2)

    def test_calculate_distance_updates_stats(self):
        """Test that distance calculations update statistics."""
        r1 = self.create_restaurant(
            "ChIJTest1234567890",
            "Restaurant 1",
            40.7589,
            -111.8883,
        )
        r2 = self.create_restaurant(
            "ChIJTest2234567890",
            "Restaurant 2",
            40.2338,
            -111.6585,
        )

        initial_stats = self.calculator.get_stats()
        initial_count = initial_stats["total_calculations"]

        self.calculator.calculate_distance(r1, r2)

        updated_stats = self.calculator.get_stats()
        assert updated_stats["total_calculations"] == initial_count + 1

    def test_haversine_formula(self):
        """Test Haversine formula directly."""
        # Test with known coordinates
        # New York (40.7128° N, 74.0060° W) to London (51.5074° N, 0.1278° W)
        # Approximate distance: 5,570 km

        distance = self.calculator._haversine(40.7128, -74.0060, 51.5074, -0.1278)

        # Should be approximately 5,570 km
        assert 5500 < distance < 5650

    def test_calculate_distance_matrix_shape(self):
        """Test distance matrix has correct shape."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.1, -111.8883)
            for i in range(5)
        ]

        matrix = self.calculator.calculate_distance_matrix(restaurants)

        assert matrix.shape == (5, 5)
        assert isinstance(matrix, np.ndarray)

    def test_calculate_distance_matrix_diagonal_zero(self):
        """Test distance matrix diagonal is zero."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.1, -111.8883)
            for i in range(5)
        ]

        matrix = self.calculator.calculate_distance_matrix(restaurants)

        # Diagonal should be all zeros (distance from point to itself)
        assert np.allclose(np.diag(matrix), 0.0)

    def test_calculate_distance_matrix_symmetry(self):
        """Test distance matrix is symmetric."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.1, -111.8883)
            for i in range(5)
        ]

        matrix = self.calculator.calculate_distance_matrix(restaurants)

        # Matrix should be symmetric
        assert np.allclose(matrix, matrix.T)

    def test_calculate_distance_matrix_single_restaurant(self):
        """Test distance matrix with single restaurant."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)
        ]

        matrix = self.calculator.calculate_distance_matrix(restaurants)

        assert matrix.shape == (1, 1)
        assert matrix[0, 0] == pytest.approx(0.0)

    def test_calculate_distance_matrix_consistency(self):
        """Test distance matrix matches pairwise calculations."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.1, -111.8883)
            for i in range(3)
        ]

        matrix = self.calculator.calculate_distance_matrix(restaurants)

        # Check that matrix values match individual calculations
        for i in range(len(restaurants)):
            for j in range(len(restaurants)):
                expected = self.calculator.calculate_distance(restaurants[i], restaurants[j])
                assert matrix[i, j] == pytest.approx(expected, rel=1e-9)

    def test_find_nearest_neighbors_basic(self):
        """Test finding nearest neighbors."""
        target = self.create_restaurant(
            "ChIJTest0234567890",
            "Target",
            40.7589,
            -111.8883,
        )

        candidates = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589 + 0.01, -111.8883),  # Close
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7589 + 0.5, -111.8883),   # Far
            self.create_restaurant("ChIJTest3234567890", "R3", 40.7589 + 0.02, -111.8883),  # Medium
        ]

        neighbors = self.calculator.find_nearest_neighbors(target, candidates, k=2)

        assert len(neighbors) == 2
        # Should return closest two in order
        assert neighbors[0][0].name == "R1"
        assert neighbors[1][0].name == "R3"

    def test_find_nearest_neighbors_excludes_self(self):
        """Test that find_nearest_neighbors excludes the target restaurant."""
        target = self.create_restaurant(
            "ChIJTest0234567890",
            "Target",
            40.7589,
            -111.8883,
        )

        candidates = [
            target,  # Include target in candidates
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589 + 0.01, -111.8883),
        ]

        neighbors = self.calculator.find_nearest_neighbors(target, candidates, k=5)

        # Should only return R1, not target
        assert len(neighbors) == 1
        assert neighbors[0][0].name == "R1"

    def test_find_nearest_neighbors_k_larger_than_candidates(self):
        """Test when k is larger than number of candidates."""
        target = self.create_restaurant(
            "ChIJTest0234567890",
            "Target",
            40.7589,
            -111.8883,
        )

        candidates = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589 + 0.01, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7589 + 0.02, -111.8883),
        ]

        neighbors = self.calculator.find_nearest_neighbors(target, candidates, k=10)

        # Should return all candidates
        assert len(neighbors) == 2

    def test_calculate_total_distance_empty_route(self):
        """Test total distance for empty route."""
        distance = self.calculator.calculate_total_distance([])
        assert distance == 0.0

    def test_calculate_total_distance_single_restaurant(self):
        """Test total distance for single restaurant."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)

        distance = self.calculator.calculate_total_distance([r1])

        assert distance == 0.0

    def test_calculate_total_distance_multiple_restaurants(self):
        """Test total distance for route with multiple restaurants."""
        route = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),  # ~1.11 km north
            self.create_restaurant("ChIJTest3234567890", "R3", 40.7789, -111.8883),  # ~1.11 km north
        ]

        distance = self.calculator.calculate_total_distance(route)

        # Should be approximately 2.22 km (two segments)
        assert 2.0 < distance < 2.5

    def test_calculate_cluster_diameter_empty(self):
        """Test cluster diameter for empty cluster."""
        diameter = self.calculator.calculate_cluster_diameter([])
        assert diameter == 0.0

    def test_calculate_cluster_diameter_single(self):
        """Test cluster diameter for single restaurant."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)

        diameter = self.calculator.calculate_cluster_diameter([r1])

        assert diameter == 0.0

    def test_calculate_cluster_diameter_multiple(self):
        """Test cluster diameter for multiple restaurants."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),
            self.create_restaurant("ChIJTest3234567890", "R3", 40.7789, -111.8883),
        ]

        diameter = self.calculator.calculate_cluster_diameter(restaurants)

        # Diameter is max distance (R1 to R3)
        expected_max = self.calculator.calculate_distance(restaurants[0], restaurants[2])
        assert diameter == pytest.approx(expected_max)

    def test_calculate_cluster_centroid_empty(self):
        """Test cluster centroid for empty cluster."""
        lat, lng = self.calculator.calculate_cluster_centroid([])

        assert lat == 0.0
        assert lng == 0.0

    def test_calculate_cluster_centroid_single(self):
        """Test cluster centroid for single restaurant."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)

        lat, lng = self.calculator.calculate_cluster_centroid([r1])

        assert lat == pytest.approx(40.7589)
        assert lng == pytest.approx(-111.8883)

    def test_calculate_cluster_centroid_multiple(self):
        """Test cluster centroid for multiple restaurants."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.0, -111.0),
            self.create_restaurant("ChIJTest2234567890", "R2", 42.0, -113.0),
        ]

        lat, lng = self.calculator.calculate_cluster_centroid(restaurants)

        # Centroid should be average
        assert lat == pytest.approx(41.0)
        assert lng == pytest.approx(-112.0)

    def test_get_stats(self):
        """Test getting statistics."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)
        r2 = self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883)

        # Make some calculations
        self.calculator.calculate_distance(r1, r2)
        self.calculator.calculate_distance_matrix([r1, r2])

        stats = self.calculator.get_stats()

        assert stats["total_calculations"] >= 1
        assert stats["matrix_calculations"] >= 1

    def test_reset_stats(self):
        """Test resetting statistics."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)
        r2 = self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883)

        # Make some calculations
        self.calculator.calculate_distance(r1, r2)

        # Reset
        self.calculator.reset_stats()

        stats = self.calculator.get_stats()
        assert stats["total_calculations"] == 0
        assert stats["matrix_calculations"] == 0
