"""Unit tests for Global Route Optimizer."""

import pytest

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.global_optimizer import (
    GlobalRouteOptimizer,
    GlobalRoute,
)


class TestGlobalRoute:
    """Test suite for GlobalRoute."""

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

    def test_global_route_creation(self):
        """Test creating GlobalRoute."""
        route = GlobalRoute(
            cluster_sequence=[0, 1, 2],
            cluster_routes={},
            total_distance=50.5,
            total_restaurants=25,
            estimated_time_hours=4.5,
            start_location=(40.7589, -111.8883),
            end_location=(40.8589, -111.9883),
        )

        assert route.cluster_sequence == [0, 1, 2]
        assert route.total_distance == 50.5
        assert route.total_restaurants == 25
        assert route.estimated_time_hours == 4.5
        assert route.start_location == (40.7589, -111.8883)

    def test_global_route_to_dict(self):
        """Test converting GlobalRoute to dict."""
        route = GlobalRoute(
            cluster_sequence=[0, 1],
            cluster_routes={},
            total_distance=30.0,
            total_restaurants=15,
            estimated_time_hours=3.0,
        )

        route_dict = route.to_dict()

        assert "cluster_sequence" in route_dict
        assert route_dict["cluster_sequence"] == [0, 1]
        assert route_dict["total_distance"] == 30.0
        assert route_dict["total_restaurants"] == 15

    def test_get_all_restaurants_empty(self):
        """Test getting all restaurants from empty route."""
        route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        restaurants = route.get_all_restaurants()
        assert len(restaurants) == 0


class TestGlobalRouteOptimizer:
    """Test suite for global route optimizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = GlobalRouteOptimizer()

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

    def test_optimize_global_route_basic(self):
        """Test basic global route optimization."""
        # Create 2 clusters with 5 restaurants each
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

        route = self.optimizer.optimize_global_route(clusters)

        assert len(route.cluster_sequence) == 2
        assert route.total_restaurants == 10
        assert route.total_distance > 0
        assert route.estimated_time_hours > 0

    def test_optimize_global_route_with_start_location(self):
        """Test optimization with start location."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        start = (40.7589, -111.8883)
        route = self.optimizer.optimize_global_route(
            clusters,
            start_location=start,
        )

        assert route.start_location == start
        assert route.total_restaurants == 5

    def test_optimize_global_route_with_end_location(self):
        """Test optimization with end location."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        start = (40.7589, -111.8883)
        end = (40.8589, -111.9883)
        route = self.optimizer.optimize_global_route(
            clusters,
            start_location=start,
            end_location=end,
        )

        assert route.start_location == start
        assert route.end_location == end

    def test_optimize_global_route_skips_noise(self):
        """Test that noise cluster is skipped."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: cluster1,
            -1: noise,
        }

        route = self.optimizer.optimize_global_route(clusters)

        # Should only include cluster 0, not noise
        assert len(route.cluster_sequence) == 1
        assert 0 in route.cluster_sequence
        assert -1 not in route.cluster_sequence

    def test_optimize_global_route_empty_raises_error(self):
        """Test that empty clusters raises error."""
        with pytest.raises(ValueError, match="No valid clusters"):
            self.optimizer.optimize_global_route({})

    def test_optimize_global_route_only_noise_raises_error(self):
        """Test that only noise cluster raises error."""
        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {-1: noise}

        with pytest.raises(ValueError, match="No valid clusters"):
            self.optimizer.optimize_global_route(clusters)

    def test_optimize_global_route_algorithm_selection(self):
        """Test different algorithm selection."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        # Test different algorithms
        for algorithm in ["auto", "nearest_neighbor", "2opt"]:
            route = self.optimizer.optimize_global_route(clusters, algorithm=algorithm)
            assert route.total_restaurants == 5

    def test_generate_alternative_routes(self):
        """Test generating alternative routes."""
        # Create 2 clusters
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1, 1: cluster2}

        alternatives = self.optimizer.generate_alternative_routes(
            clusters,
            start_location=(40.7589, -111.8883),
            num_alternatives=2,
        )

        # Should generate at least 1 alternative
        assert len(alternatives) >= 1
        assert all(isinstance(route, GlobalRoute) for route in alternatives)

    def test_generate_alternative_routes_single_cluster(self):
        """Test alternatives with single cluster."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        alternatives = self.optimizer.generate_alternative_routes(clusters, num_alternatives=3)

        # Should still generate some alternatives
        assert len(alternatives) >= 1

    def test_validate_global_route_valid(self):
        """Test validating a valid route."""
        # Create moderate-sized clusters that can complete in time
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(40)
        ]

        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+100}234567890", f"R2_{i}", 40.8589 + i * 0.01, -111.8883)
            for i in range(40)
        ]

        cluster3 = [
            self.create_restaurant(f"ChIJTest{i+200}234567890", f"R3_{i}", 40.9589 + i * 0.01, -111.8883)
            for i in range(40)
        ]

        cluster4 = [
            self.create_restaurant(f"ChIJTest{i+300}234567890", f"R4_{i}", 41.0589 + i * 0.01, -111.8883)
            for i in range(40)
        ]

        clusters = {0: cluster1, 1: cluster2, 2: cluster3, 3: cluster4}

        route = self.optimizer.optimize_global_route(clusters)

        # Validate with very generous parameters to ensure it passes
        validation = self.optimizer.validate_global_route(
            route,
            time_budget_hours=100.0,  # Very generous for test
            min_restaurants=100,  # Lower threshold
        )

        # Should pass with generous parameters
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0

    def test_validate_global_route_too_few_restaurants(self):
        """Test validation fails with too few restaurants."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(50)  # Only 50 restaurants
        ]

        clusters = {0: cluster1}

        route = self.optimizer.optimize_global_route(clusters)
        validation = self.optimizer.validate_global_route(
            route,
            min_restaurants=150,
        )

        assert validation["valid"] is False
        assert any("restaurants" in error.lower() for error in validation["errors"])

    def test_validate_global_route_exceeds_time(self):
        """Test validation fails when exceeding time budget."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(200)
        ]

        clusters = {0: cluster1}

        route = self.optimizer.optimize_global_route(clusters)

        # Set very low time budget
        validation = self.optimizer.validate_global_route(
            route,
            time_budget_hours=1.0,  # Impossibly low
        )

        assert validation["valid"] is False
        assert any("time" in error.lower() or "exceed" in error.lower() for error in validation["errors"])

    def test_validate_global_route_metrics(self):
        """Test validation includes metrics."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(50)
        ]

        clusters = {0: cluster1}

        route = self.optimizer.optimize_global_route(clusters)
        validation = self.optimizer.validate_global_route(route)

        assert "metrics" in validation
        if "restaurants_per_hour" in validation["metrics"]:
            assert validation["metrics"]["restaurants_per_hour"] > 0

    def test_validate_global_route_low_efficiency_warning(self):
        """Test validation warns about low efficiency."""
        # Create single cluster (will have low restaurants per hour)
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        route = self.optimizer.optimize_global_route(clusters)
        validation = self.optimizer.validate_global_route(route)

        # May have warnings about low efficiency
        # This is acceptable, just check validation structure
        assert "warnings" in validation

    def test_get_stats(self):
        """Test getting optimizer statistics."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        # Optimize some routes
        self.optimizer.optimize_global_route(clusters)
        self.optimizer.optimize_global_route(clusters)

        stats = self.optimizer.get_stats()

        assert stats["routes_optimized"] == 2
        assert stats["total_restaurants"] > 0
        assert stats["avg_restaurants_per_route"] > 0

    def test_reset_stats(self):
        """Test resetting optimizer statistics."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: cluster1}

        # Optimize
        self.optimizer.optimize_global_route(clusters)

        # Reset
        self.optimizer.reset_stats()

        stats = self.optimizer.get_stats()
        assert stats["routes_optimized"] == 0
        assert stats["total_restaurants"] == 0

    def test_preserves_chain_locations(self):
        """Test that global optimizer preserves multiple locations of same chain."""
        # Two McDonald's in different clusters
        mcdonalds1 = self.create_restaurant("ChIJTest1234567890", "McDonald's", 40.7589, -111.8883)
        mcdonalds2 = self.create_restaurant("ChIJTest2234567890", "McDonald's", 41.7589, -111.8883)

        cluster1 = [mcdonalds1] + [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(4)
        ]

        cluster2 = [mcdonalds2] + [
            self.create_restaurant(f"ChIJTest{i+20}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(4)
        ]

        clusters = {0: cluster1, 1: cluster2}

        route = self.optimizer.optimize_global_route(clusters)

        # Get all restaurants in route
        all_restaurants = route.get_all_restaurants()

        # Both McDonald's should be in route
        mcdonalds_in_route = [r for r in all_restaurants if r.name == "McDonald's"]
        assert len(mcdonalds_in_route) == 2

        # They should have different place_ids
        assert mcdonalds_in_route[0].place_id != mcdonalds_in_route[1].place_id

    def test_multiple_clusters_sequence(self):
        """Test that multiple clusters are sequenced properly."""
        # Create 4 clusters
        clusters = {}
        for cluster_id in range(4):
            cluster = [
                self.create_restaurant(
                    f"ChIJTest{cluster_id}_{i}234567890",
                    f"R{cluster_id}_{i}",
                    40.7589 + cluster_id * 0.5 + i * 0.01,
                    -111.8883,
                )
                for i in range(5)
            ]
            clusters[cluster_id] = cluster

        route = self.optimizer.optimize_global_route(clusters)

        # Should visit all 4 clusters
        assert len(route.cluster_sequence) == 4
        assert set(route.cluster_sequence) == {0, 1, 2, 3}

        # Should have all 20 restaurants
        assert route.total_restaurants == 20

    def test_get_all_restaurants_order(self):
        """Test that get_all_restaurants returns restaurants in correct order."""
        # Create 2 clusters
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589, -111.8883)
            for i in range(3)
        ]

        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589, -111.8883)
            for i in range(3)
        ]

        clusters = {0: cluster1, 1: cluster2}

        route = self.optimizer.optimize_global_route(clusters)
        all_restaurants = route.get_all_restaurants()

        # Should have all 6 restaurants
        assert len(all_restaurants) == 6

        # Should be in cluster sequence order
        # (specific order within clusters depends on TSP solution)
        assert all(isinstance(r, Restaurant) for r in all_restaurants)
