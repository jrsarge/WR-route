"""Unit tests for Map Visualizer."""

import pytest
import tempfile
import os
from pathlib import Path

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.global_optimizer import GlobalRoute
from fast_food_optimizer.optimization.route_optimizer import OptimizedRoute, RouteMetrics
from fast_food_optimizer.visualization.map_visualizer import MapVisualizer


class TestMapVisualizer:
    """Test suite for map visualizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.visualizer = MapVisualizer()

    def create_restaurant(
        self, place_id: str, name: str, lat: float, lng: float, rating: float = 4.0
    ) -> Restaurant:
        """Helper to create restaurant."""
        coords = Coordinates(latitude=lat, longitude=lng)
        return Restaurant(
            place_id=place_id,
            name=name,
            address="123 Main St, Salt Lake City, UT",
            coordinates=coords,
            is_fast_food=True,
            confidence_score=0.9,
            rating=rating,
        )

    def test_create_base_map(self):
        """Test creating a base map."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center, zoom_start=12)

        assert map_obj is not None
        assert self.visualizer.stats["maps_created"] == 1

    def test_create_base_map_custom_zoom(self):
        """Test creating map with custom zoom."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center, zoom_start=15)

        assert map_obj is not None

    def test_add_restaurant_marker(self):
        """Test adding a restaurant marker."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center)

        restaurant = self.create_restaurant(
            "ChIJTest1234567890", "McDonald's", 40.7589, -111.8883
        )

        self.visualizer.add_restaurant_marker(map_obj, restaurant)

        assert self.visualizer.stats["restaurants_visualized"] == 1

    def test_add_restaurant_marker_with_cluster(self):
        """Test adding marker with cluster ID."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center)

        restaurant = self.create_restaurant(
            "ChIJTest1234567890", "McDonald's", 40.7589, -111.8883
        )

        self.visualizer.add_restaurant_marker(
            map_obj, restaurant, color="red", cluster_id=0
        )

        assert self.visualizer.stats["restaurants_visualized"] == 1

    def test_visualize_restaurants(self):
        """Test visualizing a list of restaurants."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        map_obj = self.visualizer.visualize_restaurants(restaurants)

        assert map_obj is not None
        assert self.visualizer.stats["restaurants_visualized"] == 5

    def test_visualize_restaurants_auto_center(self):
        """Test that center is auto-calculated when not provided."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        map_obj = self.visualizer.visualize_restaurants(restaurants)

        assert map_obj is not None

    def test_visualize_restaurants_empty_raises_error(self):
        """Test that empty restaurant list raises error."""
        with pytest.raises(ValueError, match="No restaurants provided"):
            self.visualizer.visualize_restaurants([])

    def test_visualize_restaurants_with_center(self):
        """Test visualizing restaurants with explicit center."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        center = (40.7589, -111.8883)
        map_obj = self.visualizer.visualize_restaurants(restaurants, center=center)

        assert map_obj is not None

    def test_visualize_clusters(self):
        """Test visualizing restaurant clusters."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        clusters = {
            0: cluster1,
            1: cluster2,
        }

        map_obj = self.visualizer.visualize_clusters(clusters)

        assert map_obj is not None
        assert self.visualizer.stats["restaurants_visualized"] == 6

    def test_visualize_clusters_auto_center(self):
        """Test that cluster center is auto-calculated."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        clusters = {0: cluster1}

        map_obj = self.visualizer.visualize_clusters(clusters)

        assert map_obj is not None

    def test_visualize_clusters_skips_noise_by_default(self):
        """Test that noise cluster is skipped by default."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589, -111.8883)
            for i in range(3)
        ]

        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: cluster1,
            -1: noise,
        }

        map_obj = self.visualizer.visualize_clusters(clusters, show_noise=False)

        # Should only visualize cluster 0, not noise
        assert map_obj is not None
        assert self.visualizer.stats["restaurants_visualized"] == 3

    def test_visualize_clusters_shows_noise_when_requested(self):
        """Test that noise is shown when requested."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589, -111.8883)
            for i in range(3)
        ]

        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: cluster1,
            -1: noise,
        }

        map_obj = self.visualizer.visualize_clusters(clusters, show_noise=True)

        # Should visualize both cluster 0 and noise
        assert map_obj is not None
        assert self.visualizer.stats["restaurants_visualized"] == 4

    def test_visualize_clusters_empty_raises_error(self):
        """Test that empty clusters dict raises error."""
        with pytest.raises(ValueError, match="No clusters provided"):
            self.visualizer.visualize_clusters({})

    def test_visualize_clusters_only_noise_raises_error(self):
        """Test that only noise cluster raises error."""
        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {-1: noise}

        with pytest.raises(ValueError, match="No valid clusters"):
            self.visualizer.visualize_clusters(clusters, show_noise=False)

    def test_visualize_route(self):
        """Test visualizing an optimized route."""
        # Create restaurants
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        # Create metrics
        metrics = RouteMetrics(
            total_distance=10.5,
            num_restaurants=5,
            avg_distance=2.1,
            efficiency_score=0.8,
        )

        # Create optimized route
        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.5,
        )

        # Create global route
        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=10.5,
            total_restaurants=5,
            estimated_time_hours=2.0,
            start_location=(40.7589, -111.8883),
        )

        map_obj = self.visualizer.visualize_route(global_route)

        assert map_obj is not None
        assert self.visualizer.stats["routes_visualized"] == 1

    def test_visualize_route_with_end_location(self):
        """Test visualizing route with end location."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        metrics = RouteMetrics(
            total_distance=5.0,
            num_restaurants=3,
            avg_distance=1.67,
            efficiency_score=0.9,
        )

        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.3,
        )

        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=5.0,
            total_restaurants=3,
            estimated_time_hours=1.5,
            start_location=(40.7589, -111.8883),
            end_location=(40.8589, -111.9883),
        )

        map_obj = self.visualizer.visualize_route(global_route)

        assert map_obj is not None

    def test_visualize_route_no_lines(self):
        """Test visualizing route without line overlay."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        metrics = RouteMetrics(
            total_distance=5.0,
            num_restaurants=3,
            avg_distance=1.67,
            efficiency_score=0.9,
        )

        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.3,
        )

        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=5.0,
            total_restaurants=3,
            estimated_time_hours=1.5,
        )

        map_obj = self.visualizer.visualize_route(global_route, show_route_lines=False)

        assert map_obj is not None

    def test_visualize_route_empty_raises_error(self):
        """Test that empty route raises error."""
        global_route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        with pytest.raises(ValueError, match="Route has no restaurants"):
            self.visualizer.visualize_route(global_route)

    def test_visualize_alternative_routes(self):
        """Test visualizing multiple alternative routes."""
        # Create two routes
        restaurants1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        restaurants2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        metrics1 = RouteMetrics(
            total_distance=5.0,
            num_restaurants=3,
            avg_distance=1.67,
            efficiency_score=0.9,
        )

        metrics2 = RouteMetrics(
            total_distance=6.0,
            num_restaurants=3,
            avg_distance=2.0,
            efficiency_score=0.85,
        )

        route1 = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={
                0: OptimizedRoute(
                    restaurants=restaurants1,
                    metrics=metrics1,
                    algorithm="2opt",
                    computation_time=0.3,
                )
            },
            total_distance=5.0,
            total_restaurants=3,
            estimated_time_hours=1.5,
            start_location=(40.7589, -111.8883),
        )

        route2 = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={
                0: OptimizedRoute(
                    restaurants=restaurants2,
                    metrics=metrics2,
                    algorithm="nearest_neighbor",
                    computation_time=0.2,
                )
            },
            total_distance=6.0,
            total_restaurants=3,
            estimated_time_hours=1.7,
            start_location=(40.7589, -111.8883),
        )

        routes = [route1, route2]

        map_obj = self.visualizer.visualize_alternative_routes(routes)

        assert map_obj is not None

    def test_visualize_alternative_routes_empty_raises_error(self):
        """Test that empty routes list raises error."""
        with pytest.raises(ValueError, match="No routes provided"):
            self.visualizer.visualize_alternative_routes([])

    def test_add_route_overlay(self):
        """Test adding route overlay to map."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center)

        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        metrics = RouteMetrics(
            total_distance=5.0,
            num_restaurants=3,
            avg_distance=1.67,
            efficiency_score=0.9,
        )

        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.3,
        )

        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=5.0,
            total_restaurants=3,
            estimated_time_hours=1.5,
            start_location=(40.7589, -111.8883),
        )

        self.visualizer.add_route_overlay(map_obj, global_route)

        # No error means success
        assert True

    def test_add_route_overlay_custom_style(self):
        """Test adding route overlay with custom styling."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center)

        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(3)
        ]

        metrics = RouteMetrics(
            total_distance=5.0,
            num_restaurants=3,
            avg_distance=1.67,
            efficiency_score=0.9,
        )

        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.3,
        )

        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=5.0,
            total_restaurants=3,
            estimated_time_hours=1.5,
        )

        self.visualizer.add_route_overlay(
            map_obj, global_route, color="#ff0000", weight=5, opacity=0.8
        )

        assert True

    def test_save_map(self):
        """Test saving map to HTML file."""
        center = (40.7589, -111.8883)
        map_obj = self.visualizer.create_base_map(center)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            filepath = f.name

        try:
            self.visualizer.save_map(map_obj, filepath)

            # Check file was created
            assert os.path.exists(filepath)

            # Check file has content
            with open(filepath, "r") as f:
                content = f.read()
                assert len(content) > 0
                assert "leaflet" in content.lower() or "folium" in content.lower()

        finally:
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_get_stats(self):
        """Test getting visualizer statistics."""
        # Create some visualizations
        center = (40.7589, -111.8883)
        self.visualizer.create_base_map(center)
        self.visualizer.create_base_map(center)

        stats = self.visualizer.get_stats()

        assert stats["maps_created"] == 2
        assert isinstance(stats, dict)

    def test_reset_stats(self):
        """Test resetting statistics."""
        # Create visualizations
        center = (40.7589, -111.8883)
        self.visualizer.create_base_map(center)

        # Reset
        self.visualizer.reset_stats()

        stats = self.visualizer.get_stats()
        assert stats["maps_created"] == 0
        assert stats["restaurants_visualized"] == 0
        assert stats["routes_visualized"] == 0

    def test_cluster_colors_consistent(self):
        """Test that cluster colors are consistent."""
        color1 = self.visualizer._get_cluster_color(0)
        color2 = self.visualizer._get_cluster_color(0)

        assert color1 == color2

    def test_route_colors_consistent(self):
        """Test that route colors are consistent."""
        color1 = self.visualizer._get_route_color(0)
        color2 = self.visualizer._get_route_color(0)

        assert color1 == color2

    def test_noise_cluster_color_is_gray(self):
        """Test that noise cluster gets gray color."""
        color = self.visualizer._get_cluster_color(-1)
        assert color == "gray"

    def test_multiple_clusters_different_colors(self):
        """Test that different clusters get different colors."""
        color0 = self.visualizer._get_cluster_color(0)
        color1 = self.visualizer._get_cluster_color(1)

        # Colors should be different (unless we have only 1 color in palette)
        assert color0 != color1 or len(self.visualizer.CLUSTER_COLORS) == 1

    def test_visualize_many_restaurants_uses_marker_cluster(self):
        """Test that many restaurants trigger marker clustering."""
        # Create 60 restaurants (> 50 threshold)
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"Restaurant {i}", 40.7589 + (i % 10) * 0.01, -111.8883 + (i // 10) * 0.01)
            for i in range(60)
        ]

        map_obj = self.visualizer.visualize_restaurants(restaurants)

        # Should create map successfully with marker clustering
        assert map_obj is not None
        assert self.visualizer.stats["restaurants_visualized"] == 60
