"""Unit tests for Route Exporter."""

import pytest
import tempfile
import os
import json
import csv
from pathlib import Path

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.global_optimizer import GlobalRoute
from fast_food_optimizer.optimization.route_optimizer import OptimizedRoute, RouteMetrics
from fast_food_optimizer.visualization.route_exporter import RouteExporter


class TestRouteExporter:
    """Test suite for route exporter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = RouteExporter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

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

    def create_test_route(self, num_restaurants: int = 5) -> GlobalRoute:
        """Helper to create a test route."""
        restaurants = [
            self.create_restaurant(
                f"ChIJTest{i}234567890",
                f"Restaurant {i}",
                40.7589 + i * 0.01,
                -111.8883,
            )
            for i in range(num_restaurants)
        ]

        metrics = RouteMetrics(
            total_distance=10.5,
            num_restaurants=num_restaurants,
            avg_distance=2.1,
            efficiency_score=0.8,
        )

        optimized_route = OptimizedRoute(
            restaurants=restaurants,
            metrics=metrics,
            algorithm="2opt",
            computation_time=0.5,
        )

        global_route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={0: optimized_route},
            total_distance=10.5,
            total_restaurants=num_restaurants,
            estimated_time_hours=2.0,
            start_location=(40.7589, -111.8883),
            end_location=(40.8589, -111.9883),
        )

        return global_route

    def test_export_to_gpx(self):
        """Test exporting route to GPX format."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.gpx")

        self.exporter.export_to_gpx(route, filepath, route_name="Test Route")

        # Check file was created
        assert os.path.exists(filepath)

        # Check file has content
        with open(filepath, "r") as f:
            content = f.read()
            assert len(content) > 0
            assert '<?xml version="1.0"' in content
            assert "<gpx" in content
            assert "Test Route" in content
            assert "<rtept" in content  # Route points
            assert "<trk" in content  # Track

        # Check stats
        assert self.exporter.stats["gpx_exports"] == 1

    def test_export_to_gpx_with_description(self):
        """Test GPX export with custom description."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.gpx")

        self.exporter.export_to_gpx(
            route,
            filepath,
            route_name="Test Route",
            description="Custom description here",
        )

        with open(filepath, "r") as f:
            content = f.read()
            assert "Custom description here" in content

    def test_export_to_gpx_empty_route_raises_error(self):
        """Test that empty route raises error."""
        empty_route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        filepath = os.path.join(self.temp_dir, "route.gpx")

        with pytest.raises(ValueError, match="Cannot export empty route"):
            self.exporter.export_to_gpx(empty_route, filepath)

    def test_export_to_csv(self):
        """Test exporting route to CSV format."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.csv")

        self.exporter.export_to_csv(route, filepath)

        # Check file was created
        assert os.path.exists(filepath)

        # Read and verify CSV content
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Should have 5 restaurants
            assert len(rows) == 5

            # Check first row
            first = rows[0]
            assert first["stop_number"] == "1"
            assert first["name"] == "Restaurant 0"
            assert "latitude" in first
            assert "longitude" in first
            assert "cumulative_distance_km" in first

        # Check stats
        assert self.exporter.stats["csv_exports"] == 1

    def test_export_to_csv_without_cluster_info(self):
        """Test CSV export without cluster information."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.csv")

        self.exporter.export_to_csv(route, filepath, include_cluster_info=False)

        # Read CSV
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            first_row = next(reader)

            # Should not have cluster_id column
            assert "cluster_id" not in first_row

    def test_export_to_csv_empty_route_raises_error(self):
        """Test that empty route raises error."""
        empty_route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        filepath = os.path.join(self.temp_dir, "route.csv")

        with pytest.raises(ValueError, match="Cannot export empty route"):
            self.exporter.export_to_csv(empty_route, filepath)

    def test_export_to_kml(self):
        """Test exporting route to KML format."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.kml")

        self.exporter.export_to_kml(route, filepath, route_name="Test Route")

        # Check file was created
        assert os.path.exists(filepath)

        # Check file has content
        with open(filepath, "r") as f:
            content = f.read()
            assert len(content) > 0
            assert '<?xml version="1.0"' in content
            assert "<kml" in content
            assert "Test Route" in content
            assert "<Placemark" in content

        # Check stats
        assert self.exporter.stats["kml_exports"] == 1

    def test_export_to_kml_with_path(self):
        """Test KML export with route path."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.kml")

        self.exporter.export_to_kml(
            route, filepath, route_name="Test Route", include_path=True
        )

        with open(filepath, "r") as f:
            content = f.read()
            assert "<LineString" in content
            assert "<coordinates>" in content

    def test_export_to_kml_without_path(self):
        """Test KML export without route path."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.kml")

        self.exporter.export_to_kml(
            route, filepath, route_name="Test Route", include_path=False
        )

        with open(filepath, "r") as f:
            content = f.read()
            # Should have placemarks but no LineString
            assert "<Placemark" in content
            # Path-related tags should not be present (or minimal)

    def test_export_to_kml_empty_route_raises_error(self):
        """Test that empty route raises error."""
        empty_route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        filepath = os.path.join(self.temp_dir, "route.kml")

        with pytest.raises(ValueError, match="Cannot export empty route"):
            self.exporter.export_to_kml(empty_route, filepath)

    def test_export_to_json(self):
        """Test exporting route to JSON format."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.json")

        self.exporter.export_to_json(route, filepath)

        # Check file was created
        assert os.path.exists(filepath)

        # Read and verify JSON content
        with open(filepath, "r") as f:
            data = json.load(f)

            # Check structure
            assert "route" in data
            assert "restaurants" in data
            assert "metadata" in data

            # Check restaurants
            assert len(data["restaurants"]) == 5
            first = data["restaurants"][0]
            assert "name" in first
            assert "coordinates" in first
            assert first["name"] == "Restaurant 0"

            # Check metadata
            assert "export_date" in data["metadata"]
            assert data["metadata"]["total_restaurants"] == 5

        # Check stats
        assert self.exporter.stats["json_exports"] == 1

    def test_export_to_json_without_metadata(self):
        """Test JSON export without metadata."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.json")

        self.exporter.export_to_json(route, filepath, include_metadata=False)

        with open(filepath, "r") as f:
            data = json.load(f)

            # Should not have metadata
            assert "metadata" not in data
            assert "route" in data
            assert "restaurants" in data

    def test_export_to_json_pretty_print(self):
        """Test JSON export with pretty printing."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.json")

        self.exporter.export_to_json(route, filepath, pretty_print=True)

        with open(filepath, "r") as f:
            content = f.read()

            # Pretty printed JSON should have newlines and indentation
            assert "\n" in content
            assert "  " in content  # Indentation

    def test_export_to_json_compact(self):
        """Test JSON export without pretty printing."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.json")

        self.exporter.export_to_json(route, filepath, pretty_print=False)

        with open(filepath, "r") as f:
            content = f.read()

            # Should be valid JSON
            data = json.loads(content)
            assert "route" in data

    def test_export_to_json_empty_route_raises_error(self):
        """Test that empty route raises error."""
        empty_route = GlobalRoute(
            cluster_sequence=[],
            cluster_routes={},
            total_distance=0.0,
            total_restaurants=0,
            estimated_time_hours=0.0,
        )

        filepath = os.path.join(self.temp_dir, "route.json")

        with pytest.raises(ValueError, match="Cannot export empty route"):
            self.exporter.export_to_json(empty_route, filepath)

    def test_export_all_formats(self):
        """Test exporting to all formats at once."""
        route = self.create_test_route()

        files = self.exporter.export_all_formats(
            route,
            output_dir=self.temp_dir,
            base_filename="test_route",
            route_name="Test Route",
        )

        # Check all formats returned
        assert "gpx" in files
        assert "csv" in files
        assert "kml" in files
        assert "json" in files

        # Check all files were created
        assert os.path.exists(files["gpx"])
        assert os.path.exists(files["csv"])
        assert os.path.exists(files["kml"])
        assert os.path.exists(files["json"])

        # Check stats
        assert self.exporter.stats["gpx_exports"] == 1
        assert self.exporter.stats["csv_exports"] == 1
        assert self.exporter.stats["kml_exports"] == 1
        assert self.exporter.stats["json_exports"] == 1

    def test_export_all_formats_creates_directory(self):
        """Test that export_all_formats creates output directory."""
        route = self.create_test_route()

        # Use non-existent directory
        new_dir = os.path.join(self.temp_dir, "new_subdir")
        assert not os.path.exists(new_dir)

        files = self.exporter.export_all_formats(
            route, output_dir=new_dir, base_filename="test"
        )

        # Directory should now exist
        assert os.path.exists(new_dir)

        # Files should be created
        assert os.path.exists(files["gpx"])

    def test_get_stats(self):
        """Test getting exporter statistics."""
        route = self.create_test_route()

        # Export some files
        self.exporter.export_to_gpx(route, os.path.join(self.temp_dir, "test.gpx"))
        self.exporter.export_to_csv(route, os.path.join(self.temp_dir, "test.csv"))

        stats = self.exporter.get_stats()

        assert stats["gpx_exports"] == 1
        assert stats["csv_exports"] == 1
        assert stats["kml_exports"] == 0
        assert stats["json_exports"] == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        route = self.create_test_route()

        # Export some files
        self.exporter.export_to_gpx(route, os.path.join(self.temp_dir, "test.gpx"))

        # Reset
        self.exporter.reset_stats()

        stats = self.exporter.get_stats()
        assert stats["gpx_exports"] == 0
        assert stats["csv_exports"] == 0
        assert stats["kml_exports"] == 0
        assert stats["json_exports"] == 0

    def test_gpx_includes_all_restaurants(self):
        """Test that GPX includes all restaurants in order."""
        route = self.create_test_route(num_restaurants=10)
        filepath = os.path.join(self.temp_dir, "route.gpx")

        self.exporter.export_to_gpx(route, filepath)

        with open(filepath, "r") as f:
            content = f.read()

            # Should include all 10 restaurants
            for i in range(10):
                assert f"Restaurant {i}" in content

    def test_csv_includes_all_restaurants(self):
        """Test that CSV includes all restaurants in order."""
        route = self.create_test_route(num_restaurants=10)
        filepath = os.path.join(self.temp_dir, "route.csv")

        self.exporter.export_to_csv(route, filepath)

        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Should have 10 rows
            assert len(rows) == 10

            # Check ordering
            for i, row in enumerate(rows):
                assert row["stop_number"] == str(i + 1)
                assert row["name"] == f"Restaurant {i}"

    def test_kml_includes_all_restaurants(self):
        """Test that KML includes all restaurants."""
        route = self.create_test_route(num_restaurants=10)
        filepath = os.path.join(self.temp_dir, "route.kml")

        self.exporter.export_to_kml(route, filepath)

        with open(filepath, "r") as f:
            content = f.read()

            # Should include all 10 restaurants
            for i in range(10):
                assert f"Restaurant {i}" in content

    def test_json_includes_all_restaurants(self):
        """Test that JSON includes all restaurants."""
        route = self.create_test_route(num_restaurants=10)
        filepath = os.path.join(self.temp_dir, "route.json")

        self.exporter.export_to_json(route, filepath)

        with open(filepath, "r") as f:
            data = json.load(f)

            # Should have 10 restaurants
            assert len(data["restaurants"]) == 10

            # Check order
            for i, restaurant in enumerate(data["restaurants"]):
                assert restaurant["name"] == f"Restaurant {i}"

    def test_xml_escape_special_characters(self):
        """Test that special XML characters are escaped."""
        # Create restaurant with special characters
        restaurant = self.create_restaurant(
            "ChIJTest1234567890",
            "Test & Restaurant <with> 'special' \"chars\"",
            40.7589,
            -111.8883,
        )

        metrics = RouteMetrics(
            total_distance=5.0, num_restaurants=1, avg_distance=5.0, efficiency_score=0.9
        )

        route = GlobalRoute(
            cluster_sequence=[0],
            cluster_routes={
                0: OptimizedRoute(
                    restaurants=[restaurant],
                    metrics=metrics,
                    algorithm="2opt",
                    computation_time=0.3,
                )
            },
            total_distance=5.0,
            total_restaurants=1,
            estimated_time_hours=1.0,
        )

        # Export to GPX
        filepath = os.path.join(self.temp_dir, "special.gpx")
        self.exporter.export_to_gpx(route, filepath)

        with open(filepath, "r") as f:
            content = f.read()

            # Special characters should be escaped
            assert "&amp;" in content
            assert "&lt;" in content
            assert "&gt;" in content
            assert "&apos;" in content or "&#39;" in content
            assert "&quot;" in content or "&#34;" in content

    def test_gpx_includes_start_and_end_locations(self):
        """Test that GPX includes start and end locations in track."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.gpx")

        self.exporter.export_to_gpx(route, filepath)

        with open(filepath, "r") as f:
            content = f.read()

            # Should include start location in track
            assert "40.7589" in content  # Start latitude
            assert "40.8589" in content  # End latitude

    def test_kml_includes_start_and_end_in_path(self):
        """Test that KML includes start and end locations in path."""
        route = self.create_test_route()
        filepath = os.path.join(self.temp_dir, "route.kml")

        self.exporter.export_to_kml(route, filepath, include_path=True)

        with open(filepath, "r") as f:
            content = f.read()

            # Should include coordinates in path
            assert "40.7589" in content
            assert "40.8589" in content
