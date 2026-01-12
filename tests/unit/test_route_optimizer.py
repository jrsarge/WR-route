"""Unit tests for Route Optimizer."""

import pytest

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.route_optimizer import (
    IntraClusterOptimizer,
    OptimizedRoute,
    RouteMetrics,
)


class TestRouteMetrics:
    """Test suite for RouteMetrics."""

    def test_route_metrics_creation(self):
        """Test creating RouteMetrics."""
        metrics = RouteMetrics(
            total_distance=25.5,
            num_restaurants=10,
            avg_distance=2.83,
            efficiency_score=0.85,
        )

        assert metrics.total_distance == 25.5
        assert metrics.num_restaurants == 10
        assert metrics.avg_distance == 2.83
        assert metrics.efficiency_score == 0.85

    def test_route_metrics_to_dict(self):
        """Test converting RouteMetrics to dict."""
        metrics = RouteMetrics(
            total_distance=15.0,
            num_restaurants=5,
            avg_distance=3.75,
            efficiency_score=0.9,
        )

        metrics_dict = metrics.to_dict()

        assert metrics_dict["total_distance"] == 15.0
        assert metrics_dict["num_restaurants"] == 5
        assert metrics_dict["avg_distance"] == 3.75
        assert metrics_dict["efficiency_score"] == 0.9


class TestOptimizedRoute:
    """Test suite for OptimizedRoute."""

    def create_restaurant(self, place_id: str, name: str, lat: float, lng: float) -> Restaurant:
        """Helper to create restaurant."""
        coords = Coordinates(latitude=lat, longitude=lng)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.9,
        )

    def test_optimized_route_creation(self):
        """Test creating OptimizedRoute."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),
        ]

        metrics = RouteMetrics(
            total_distance=10.0,
            num_restaurants=2,
            avg_distance=10.0,
            efficiency_score=0.95,
        )

        route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.05,
        )

        assert len(route.restaurants) == 2
        assert route.metrics.total_distance == 10.0
        assert route.algorithm == "2opt"
        assert route.computation_time == 0.05

    def test_optimized_route_to_dict(self):
        """Test converting OptimizedRoute to dict."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
        ]

        metrics = RouteMetrics(
            total_distance=0.0,
            num_restaurants=1,
            avg_distance=0.0,
            efficiency_score=1.0,
        )

        route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="trivial",
            computation_time=0.0,
        )

        route_dict = route.to_dict()

        assert "restaurants" in route_dict
        assert route_dict["restaurants"] == ["ChIJTest1234567890"]
        assert "metrics" in route_dict
        assert route_dict["algorithm"] == "trivial"


class TestIntraClusterOptimizer:
    """Test suite for intra-cluster optimizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = IntraClusterOptimizer()

    def create_restaurant(self, place_id: str, name: str, lat: float, lng: float) -> Restaurant:
        """Helper to create restaurant."""
        coords = Coordinates(latitude=lat, longitude=lng)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.9,
        )

    def test_optimize_cluster_single_restaurant(self):
        """Test optimizing cluster with single restaurant."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
        ]

        route = self.optimizer.optimize_cluster(restaurants)

        assert len(route.restaurants) == 1
        assert route.metrics.total_distance == 0.0
        assert route.metrics.efficiency_score == 1.0
        assert route.algorithm == "trivial"

    def test_optimize_cluster_empty_raises_error(self):
        """Test that optimizing empty cluster raises error."""
        with pytest.raises(ValueError, match="Cannot optimize empty cluster"):
            self.optimizer.optimize_cluster([])

    def test_optimize_cluster_multiple_restaurants(self):
        """Test optimizing cluster with multiple restaurants."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        route = self.optimizer.optimize_cluster(restaurants, algorithm="nearest_neighbor")

        assert len(route.restaurants) == 5
        assert route.metrics.num_restaurants == 5
        assert route.metrics.total_distance > 0
        assert 0 <= route.metrics.efficiency_score <= 1.0
        assert route.algorithm == "nearest_neighbor"

    def test_optimize_cluster_with_start_restaurant(self):
        """Test optimization with specific start restaurant."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),
            self.create_restaurant("ChIJTest3234567890", "R3", 40.7789, -111.8883),
        ]

        start_restaurant = restaurants[1]
        route = self.optimizer.optimize_cluster(
            restaurants,
            algorithm="nearest_neighbor",
            start_restaurant=start_restaurant,
        )

        # Should start with the specified restaurant
        assert route.restaurants[0] == start_restaurant

    def test_optimize_cluster_invalid_algorithm(self):
        """Test optimization with invalid algorithm."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),
        ]

        with pytest.raises(ValueError, match="Invalid algorithm"):
            self.optimizer.optimize_cluster(restaurants, algorithm="invalid")

    def test_optimize_cluster_auto_algorithm(self):
        """Test optimization with auto algorithm selection."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        route = self.optimizer.optimize_cluster(restaurants, algorithm="auto")

        assert len(route.restaurants) == 5
        # Auto should select 2opt for balanced quality
        assert route.algorithm in ["2opt", "ortools"]

    def test_optimize_cluster_2opt_algorithm(self):
        """Test optimization with 2-opt algorithm."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        route = self.optimizer.optimize_cluster(restaurants, algorithm="2opt")

        assert len(route.restaurants) == 5
        assert route.algorithm == "2opt"

    def test_optimize_all_clusters(self):
        """Test optimizing all clusters."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {
            0: cluster1,
            1: cluster2,
        }

        routes = self.optimizer.optimize_all_clusters(clusters)

        assert len(routes) == 2
        assert 0 in routes
        assert 1 in routes
        assert len(routes[0].restaurants) == 5
        assert len(routes[1].restaurants) == 5

    def test_optimize_all_clusters_skips_noise(self):
        """Test that optimize_all_clusters skips noise cluster."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: cluster1,
            -1: noise,  # Noise cluster
        }

        routes = self.optimizer.optimize_all_clusters(clusters)

        # Should only optimize cluster 0, not noise
        assert len(routes) == 1
        assert 0 in routes
        assert -1 not in routes

    def test_compare_algorithms(self):
        """Test comparing different algorithms."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        comparison = self.optimizer.compare_algorithms(restaurants)

        # Should have at least nearest_neighbor and 2opt
        assert "nearest_neighbor" in comparison
        assert "2opt" in comparison

        # Check that routes are valid
        assert len(comparison["nearest_neighbor"].restaurants) == 5
        assert len(comparison["2opt"].restaurants) == 5

    def test_compare_algorithms_small_cluster(self):
        """Test comparison with small cluster."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
        ]

        comparison = self.optimizer.compare_algorithms(restaurants)

        # Too small for comparison
        assert len(comparison) == 0

    def test_validate_route_valid(self):
        """Test validating a valid route."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        route = self.optimizer.optimize_cluster(restaurants)
        validation = self.optimizer.validate_route(route)

        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_route_with_duplicates(self):
        """Test validation catches duplicate restaurants."""
        r1 = self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883)
        restaurants = [r1, r1]  # Duplicate

        metrics = RouteMetrics(
            total_distance=0.0,
            num_restaurants=2,
            avg_distance=0.0,
            efficiency_score=1.0,
        )

        route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="test",
            computation_time=0.0,
        )

        validation = self.optimizer.validate_route(route)

        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert any("duplicate" in error.lower() for error in validation["errors"])

    def test_validate_route_empty(self):
        """Test validation catches empty route."""
        metrics = RouteMetrics(
            total_distance=0.0,
            num_restaurants=0,
            avg_distance=0.0,
            efficiency_score=1.0,
        )

        route = OptimizedRoute(
            restaurants=[],
            metrics=metrics,
            algorithm="test",
            computation_time=0.0,
        )

        validation = self.optimizer.validate_route(route)

        assert validation["valid"] is False
        assert any("empty" in error.lower() for error in validation["errors"])

    def test_validate_route_low_efficiency(self):
        """Test validation warns about low efficiency."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
        ]

        metrics = RouteMetrics(
            total_distance=10.0,
            num_restaurants=1,
            avg_distance=10.0,
            efficiency_score=0.3,  # Low efficiency
        )

        route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="test",
            computation_time=0.0,
        )

        validation = self.optimizer.validate_route(route)

        # Should be valid but have warning
        assert validation["valid"] is True
        assert len(validation["warnings"]) > 0

    def test_get_stats(self):
        """Test getting optimizer statistics."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        # Optimize some clusters
        self.optimizer.optimize_cluster(restaurants)
        self.optimizer.optimize_cluster(restaurants)

        stats = self.optimizer.get_stats()

        assert stats["clusters_optimized"] == 2
        assert stats["total_restaurants"] == 10
        assert stats["avg_restaurants_per_cluster"] == 5.0
        assert stats["total_distance_optimized"] > 0

    def test_reset_stats(self):
        """Test resetting optimizer statistics."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        # Optimize
        self.optimizer.optimize_cluster(restaurants)

        # Reset
        self.optimizer.reset_stats()

        stats = self.optimizer.get_stats()
        assert stats["clusters_optimized"] == 0
        assert stats["total_restaurants"] == 0
        assert stats["total_distance_optimized"] == 0.0

    def test_preserves_chain_locations(self):
        """Test that optimizer preserves multiple locations of same chain."""
        # Two McDonald's in cluster
        mcdonalds1 = self.create_restaurant("ChIJTest1234567890", "McDonald's", 40.7589, -111.8883)
        mcdonalds2 = self.create_restaurant("ChIJTest2234567890", "McDonald's", 40.7589 + 0.01, -111.8883)

        # Add other restaurants
        others = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        restaurants = [mcdonalds1, mcdonalds2] + others

        route = self.optimizer.optimize_cluster(restaurants)

        # Both McDonald's should be in route
        mcdonalds_in_route = [r for r in route.restaurants if r.name == "McDonald's"]
        assert len(mcdonalds_in_route) == 2

        # They should have different place_ids
        assert mcdonalds_in_route[0].place_id != mcdonalds_in_route[1].place_id

    def test_route_metrics_accuracy(self):
        """Test that route metrics are calculated accurately."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.0, -111.0),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.1, -111.0),
            self.create_restaurant("ChIJTest3234567890", "R3", 40.2, -111.0),
        ]

        route = self.optimizer.optimize_cluster(restaurants)

        # Check metrics make sense
        assert route.metrics.num_restaurants == 3
        assert route.metrics.total_distance > 0
        assert route.metrics.avg_distance > 0
        assert 0 <= route.metrics.efficiency_score <= 1.0

        # Average distance should be total / (n-1)
        expected_avg = route.metrics.total_distance / 2
        assert route.metrics.avg_distance == pytest.approx(expected_avg, rel=0.01)
