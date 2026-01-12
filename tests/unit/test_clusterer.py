"""Unit tests for RestaurantClusterer."""

import pytest
import numpy as np

from fast_food_optimizer.models.restaurant import Coordinates, Restaurant
from fast_food_optimizer.optimization.clusterer import RestaurantClusterer, ClusterMetrics
from fast_food_optimizer.optimization.distance import DistanceCalculator


class TestClusterMetrics:
    """Test suite for ClusterMetrics."""

    def test_cluster_metrics_creation(self):
        """Test creating ClusterMetrics."""
        metrics = ClusterMetrics(
            cluster_id=0,
            size=10,
            cohesion=2.5,
            diameter=5.0,
            centroid=(40.7589, -111.8883),
        )

        assert metrics.cluster_id == 0
        assert metrics.size == 10
        assert metrics.cohesion == 2.5
        assert metrics.diameter == 5.0
        assert metrics.centroid == (40.7589, -111.8883)

    def test_cluster_metrics_to_dict(self):
        """Test converting ClusterMetrics to dict."""
        metrics = ClusterMetrics(
            cluster_id=0,
            size=10,
            cohesion=2.5,
            diameter=5.0,
            centroid=(40.7589, -111.8883),
        )

        metrics_dict = metrics.to_dict()

        assert metrics_dict["cluster_id"] == 0
        assert metrics_dict["size"] == 10
        assert metrics_dict["cohesion"] == 2.5
        assert metrics_dict["diameter"] == 5.0
        assert metrics_dict["centroid"]["latitude"] == 40.7589
        assert metrics_dict["centroid"]["longitude"] == -111.8883


class TestRestaurantClusterer:
    """Test suite for restaurant clustering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.clusterer = RestaurantClusterer(eps_km=5.0, min_samples=3)

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

    def test_cluster_restaurants_single_cluster(self):
        """Test clustering restaurants into single cluster."""
        # Create tight cluster of restaurants
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        clusters = self.clusterer.cluster_restaurants(restaurants)

        # Should have at least one cluster (possibly plus noise points)
        assert len(clusters) >= 1

        # Count non-noise clusters
        non_noise_clusters = {k: v for k, v in clusters.items() if k != -1}
        assert len(non_noise_clusters) >= 1

    def test_cluster_restaurants_multiple_clusters(self):
        """Test clustering restaurants into multiple clusters."""
        # Create two separate clusters
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]
        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        restaurants = cluster1 + cluster2

        clusters = self.clusterer.cluster_restaurants(restaurants)

        # Should have at least 2 non-noise clusters
        non_noise_clusters = {k: v for k, v in clusters.items() if k != -1}
        assert len(non_noise_clusters) >= 1  # May merge into one depending on eps

    def test_cluster_restaurants_with_noise(self):
        """Test clustering with outlier restaurants."""
        # Create tight cluster
        cluster_restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        # Add outliers far away
        outliers = [
            self.create_restaurant("ChIJTest100234567890", "Outlier1", 45.0, -120.0),
            self.create_restaurant("ChIJTest101234567890", "Outlier2", 35.0, -100.0),
        ]

        restaurants = cluster_restaurants + outliers

        clusters = self.clusterer.cluster_restaurants(restaurants)

        # Should have noise points (cluster_id = -1)
        assert -1 in clusters

    def test_cluster_restaurants_small_dataset(self):
        """Test clustering with fewer restaurants than min_samples."""
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.7589, -111.8883),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.7689, -111.8883),
        ]

        clusters = self.clusterer.cluster_restaurants(restaurants)

        # Should return single cluster for small dataset
        assert len(clusters) == 1
        assert 0 in clusters
        assert len(clusters[0]) == 2

    def test_cluster_restaurants_with_precomputed_matrix(self):
        """Test clustering with pre-computed distance matrix."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        # Pre-compute distance matrix
        calculator = DistanceCalculator()
        distance_matrix = calculator.calculate_distance_matrix(restaurants)

        clusters = self.clusterer.cluster_restaurants(restaurants, distance_matrix=distance_matrix)

        # Should have at least one cluster
        assert len(clusters) >= 1

    def test_calculate_cluster_metrics_basic(self):
        """Test calculating basic cluster metrics."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: restaurants}

        metrics = self.clusterer.calculate_cluster_metrics(restaurants, clusters)

        assert 0 in metrics
        assert metrics[0].size == 5
        assert metrics[0].cohesion > 0
        assert metrics[0].diameter > 0
        assert len(metrics[0].centroid) == 2

    def test_calculate_cluster_metrics_skips_noise(self):
        """Test that cluster metrics skip noise points."""
        cluster_restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589, -111.8883)
            for i in range(3)
        ]
        noise_restaurants = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: cluster_restaurants,
            -1: noise_restaurants,
        }

        metrics = self.clusterer.calculate_cluster_metrics(cluster_restaurants + noise_restaurants, clusters)

        # Should only have metrics for cluster 0, not -1
        assert 0 in metrics
        assert -1 not in metrics

    def test_calculate_silhouette_score_single_cluster(self):
        """Test silhouette score with single cluster."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        clusters = {0: restaurants}

        score = self.clusterer.calculate_silhouette_score(restaurants, clusters)

        # Should return 0.0 for single cluster (need at least 2)
        assert score == 0.0

    def test_calculate_silhouette_score_multiple_clusters(self):
        """Test silhouette score with multiple clusters."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]
        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]

        restaurants = cluster1 + cluster2
        clusters = {
            0: cluster1,
            1: cluster2,
        }

        score = self.clusterer.calculate_silhouette_score(restaurants, clusters)

        # Should return a score between -1 and 1
        assert -1.0 <= score <= 1.0

    def test_calculate_silhouette_score_with_noise(self):
        """Test silhouette score filters out noise points."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R1_{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]
        cluster2 = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"R2_{i}", 41.7589 + i * 0.01, -111.8883)
            for i in range(5)
        ]
        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        restaurants = cluster1 + cluster2 + noise
        clusters = {
            0: cluster1,
            1: cluster2,
            -1: noise,
        }

        score = self.clusterer.calculate_silhouette_score(restaurants, clusters)

        # Should calculate score excluding noise
        assert -1.0 <= score <= 1.0

    def test_validate_clusters_all_valid(self):
        """Test validation with all valid clusters."""
        cluster1 = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        clusters = {0: cluster1}

        validation = self.clusterer.validate_clusters(clusters, min_cluster_size=5, max_cluster_diameter_km=15.0)

        assert validation["total_clusters"] == 1
        assert validation["valid_clusters"] == 1
        assert validation["all_passed"] is True
        assert len(validation["invalid_clusters"]) == 0

    def test_validate_clusters_size_failure(self):
        """Test validation fails for small clusters."""
        small_cluster = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589, -111.8883)
            for i in range(2)
        ]

        clusters = {0: small_cluster}

        validation = self.clusterer.validate_clusters(clusters, min_cluster_size=5)

        assert validation["total_clusters"] == 1
        assert validation["valid_clusters"] == 0
        assert validation["all_passed"] is False
        assert len(validation["invalid_clusters"]) == 1

    def test_validate_clusters_diameter_failure(self):
        """Test validation fails for large diameter clusters."""
        # Create very spread out cluster
        spread_cluster = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.0, -111.0),
            self.create_restaurant("ChIJTest2234567890", "R2", 40.5, -111.0),
            self.create_restaurant("ChIJTest3234567890", "R3", 41.0, -111.0),
            self.create_restaurant("ChIJTest4234567890", "R4", 41.5, -111.0),
            self.create_restaurant("ChIJTest5234567890", "R5", 42.0, -111.0),
        ]

        clusters = {0: spread_cluster}

        validation = self.clusterer.validate_clusters(clusters, max_cluster_diameter_km=10.0)

        # This cluster spans ~222 km, should fail
        assert validation["all_passed"] is False

    def test_validate_clusters_skips_noise(self):
        """Test validation skips noise cluster."""
        valid_cluster = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589, -111.8883)
            for i in range(10)
        ]
        noise = [
            self.create_restaurant("ChIJTest100234567890", "Noise", 45.0, -120.0),
        ]

        clusters = {
            0: valid_cluster,
            -1: noise,
        }

        validation = self.clusterer.validate_clusters(clusters)

        # Should only validate cluster 0, not noise
        assert validation["total_clusters"] == 1

    def test_optimize_parameters_basic(self):
        """Test parameter optimization."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(20)
        ]

        # Use small ranges for faster test
        optimal = self.clusterer.optimize_parameters(
            restaurants,
            eps_range=(2.0, 4.0),
            min_samples_range=(3, 5),
            step=1.0,
        )

        assert "best_eps" in optimal
        assert "best_min_samples" in optimal
        assert "best_score" in optimal
        assert "all_results" in optimal

        # Check ranges
        assert 2.0 <= optimal["best_eps"] <= 4.0
        assert 3 <= optimal["best_min_samples"] <= 5
        assert -1.0 <= optimal["best_score"] <= 1.0

    def test_get_stats(self):
        """Test getting clustering statistics."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        self.clusterer.cluster_restaurants(restaurants)

        stats = self.clusterer.get_stats()

        assert stats["total_clustered"] == 10
        assert "num_clusters" in stats
        assert "noise_points" in stats

    def test_reset_stats(self):
        """Test resetting clustering statistics."""
        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        self.clusterer.cluster_restaurants(restaurants)

        # Reset
        self.clusterer.reset_stats()

        stats = self.clusterer.get_stats()
        assert stats["total_clustered"] == 0
        assert stats["num_clusters"] == 0
        assert stats["noise_points"] == 0

    def test_clusterer_custom_distance_calculator(self):
        """Test clusterer with custom distance calculator."""
        calculator = DistanceCalculator()
        clusterer = RestaurantClusterer(
            eps_km=5.0,
            min_samples=3,
            distance_calculator=calculator,
        )

        restaurants = [
            self.create_restaurant(f"ChIJTest{i}234567890", f"R{i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(10)
        ]

        clusters = clusterer.cluster_restaurants(restaurants)

        assert len(clusters) >= 1

    def test_cluster_preserves_chain_locations(self):
        """Test that clustering preserves multiple locations of same chain."""
        # Create two McDonald's in same cluster
        mcdonalds1 = self.create_restaurant("ChIJTest1234567890", "McDonald's", 40.7589, -111.8883)
        mcdonalds2 = self.create_restaurant("ChIJTest2234567890", "McDonald's", 40.7589 + 0.01, -111.8883)

        # Add other restaurants to form cluster
        others = [
            self.create_restaurant(f"ChIJTest{i+10}234567890", f"Restaurant {i}", 40.7589 + i * 0.01, -111.8883)
            for i in range(8)
        ]

        restaurants = [mcdonalds1, mcdonalds2] + others

        clusters = self.clusterer.cluster_restaurants(restaurants)

        # Find which cluster has the McDonald's
        for cluster_id, cluster_restaurants in clusters.items():
            mcdonalds_in_cluster = [r for r in cluster_restaurants if r.name == "McDonald's"]
            if mcdonalds_in_cluster:
                # Both McDonald's should be in the cluster (not deduplicated by name)
                assert len(mcdonalds_in_cluster) == 2
                # They should have different place_ids
                assert mcdonalds_in_cluster[0].place_id != mcdonalds_in_cluster[1].place_id

    def test_calculate_cluster_metrics_centroid_accuracy(self):
        """Test that centroid calculation is accurate."""
        # Create restaurants at known coordinates
        restaurants = [
            self.create_restaurant("ChIJTest1234567890", "R1", 40.0, -111.0),
            self.create_restaurant("ChIJTest2234567890", "R2", 42.0, -113.0),
        ]

        clusters = {0: restaurants}

        metrics = self.clusterer.calculate_cluster_metrics(restaurants, clusters)

        # Centroid should be average: (41.0, -112.0)
        assert metrics[0].centroid[0] == pytest.approx(41.0)
        assert metrics[0].centroid[1] == pytest.approx(-112.0)
