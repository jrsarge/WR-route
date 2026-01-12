"""Restaurant clustering for efficient route planning.

This module provides DBSCAN-based clustering to group restaurants
into geographic clusters for optimized routing.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.optimization.distance import DistanceCalculator
from fast_food_optimizer.utils.logging import get_logger, log_performance


class ClusterMetrics:
    """Metrics for evaluating cluster quality.

    Attributes:
        cluster_id: Cluster identifier (-1 for noise points)
        size: Number of restaurants in cluster
        cohesion: Average intra-cluster distance (lower is better)
        diameter: Maximum intra-cluster distance
        centroid: Geographic center (lat, lng)
    """

    def __init__(
        self,
        cluster_id: int,
        size: int,
        cohesion: float,
        diameter: float,
        centroid: Tuple[float, float],
    ):
        """Initialize cluster metrics."""
        self.cluster_id = cluster_id
        self.size = size
        self.cohesion = cohesion
        self.diameter = diameter
        self.centroid = centroid

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "size": self.size,
            "cohesion": self.cohesion,
            "diameter": self.diameter,
            "centroid": {
                "latitude": self.centroid[0],
                "longitude": self.centroid[1],
            },
        }


class RestaurantClusterer:
    """Clusters restaurants using DBSCAN algorithm.

    DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
    groups restaurants that are close together, ideal for route optimization.

    Example:
        >>> clusterer = RestaurantClusterer(eps_km=5.0, min_samples=5)
        >>> clusters = clusterer.cluster_restaurants(restaurants)
        >>> print(f"Found {len(clusters)} clusters")
        >>> metrics = clusterer.calculate_cluster_metrics(restaurants, clusters)
    """

    def __init__(
        self,
        eps_km: float = 5.0,
        min_samples: int = 5,
        distance_calculator: Optional[DistanceCalculator] = None,
    ):
        """Initialize restaurant clusterer.

        Args:
            eps_km: Maximum distance in km between two restaurants
                   to be considered neighbors (DBSCAN epsilon)
            min_samples: Minimum number of restaurants in a neighborhood
                        to form a dense region (DBSCAN min_samples)
            distance_calculator: Distance calculator instance
        """
        self.eps_km = eps_km
        self.min_samples = min_samples
        self.distance_calculator = distance_calculator or DistanceCalculator()
        self.logger = get_logger(__name__)

        # Clustering statistics
        self.clustering_stats = {
            "total_clustered": 0,
            "num_clusters": 0,
            "noise_points": 0,
        }

    @log_performance
    def cluster_restaurants(
        self,
        restaurants: List[Restaurant],
        distance_matrix: Optional[np.ndarray] = None,
    ) -> Dict[int, List[Restaurant]]:
        """Cluster restaurants using DBSCAN algorithm.

        Args:
            restaurants: List of restaurants to cluster
            distance_matrix: Pre-computed distance matrix (optional)
                           If not provided, will be calculated

        Returns:
            Dictionary mapping cluster_id to list of restaurants
            cluster_id = -1 represents noise points (outliers)

        Example:
            >>> clusters = clusterer.cluster_restaurants(restaurants)
            >>> for cluster_id, cluster_restaurants in clusters.items():
            ...     if cluster_id != -1:
            ...         print(f"Cluster {cluster_id}: {len(cluster_restaurants)} restaurants")
        """
        if len(restaurants) < self.min_samples:
            self.logger.warning(
                f"Only {len(restaurants)} restaurants, less than min_samples={self.min_samples}. "
                "Returning single cluster."
            )
            return {0: restaurants}

        self.logger.info(f"Clustering {len(restaurants)} restaurants with DBSCAN")
        self.logger.info(f"Parameters: eps={self.eps_km}km, min_samples={self.min_samples}")

        # Calculate distance matrix if not provided
        if distance_matrix is None:
            self.logger.info("Calculating distance matrix...")
            distance_matrix = self.distance_calculator.calculate_distance_matrix(restaurants)

        # Run DBSCAN
        # metric='precomputed' tells DBSCAN we're providing distances directly
        dbscan = DBSCAN(
            eps=self.eps_km,
            min_samples=self.min_samples,
            metric='precomputed',
        )

        labels = dbscan.fit_predict(distance_matrix)

        # Group restaurants by cluster
        clusters: Dict[int, List[Restaurant]] = {}
        for restaurant, label in zip(restaurants, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(restaurant)

        # Update statistics
        self.clustering_stats["total_clustered"] = len(restaurants)
        self.clustering_stats["num_clusters"] = len([k for k in clusters.keys() if k != -1])
        self.clustering_stats["noise_points"] = len(clusters.get(-1, []))

        self.logger.info(
            f"Clustering complete: {self.clustering_stats['num_clusters']} clusters, "
            f"{self.clustering_stats['noise_points']} noise points"
        )

        # Log cluster sizes
        for cluster_id, cluster_restaurants in clusters.items():
            if cluster_id != -1:
                self.logger.info(f"  Cluster {cluster_id}: {len(cluster_restaurants)} restaurants")

        return clusters

    def calculate_cluster_metrics(
        self,
        restaurants: List[Restaurant],
        clusters: Dict[int, List[Restaurant]],
    ) -> Dict[int, ClusterMetrics]:
        """Calculate quality metrics for each cluster.

        Args:
            restaurants: Original list of restaurants
            clusters: Dictionary mapping cluster_id to restaurants

        Returns:
            Dictionary mapping cluster_id to ClusterMetrics

        Example:
            >>> metrics = clusterer.calculate_cluster_metrics(restaurants, clusters)
            >>> for cluster_id, metric in metrics.items():
            ...     print(f"Cluster {cluster_id}: {metric.size} restaurants, "
            ...           f"cohesion={metric.cohesion:.2f}km")
        """
        cluster_metrics = {}

        for cluster_id, cluster_restaurants in clusters.items():
            if cluster_id == -1:
                # Skip noise points
                continue

            # Calculate cohesion (average intra-cluster distance)
            total_distance = 0.0
            num_pairs = 0

            for i, r1 in enumerate(cluster_restaurants):
                for r2 in cluster_restaurants[i + 1:]:
                    total_distance += self.distance_calculator.calculate_distance(r1, r2)
                    num_pairs += 1

            cohesion = total_distance / num_pairs if num_pairs > 0 else 0.0

            # Calculate diameter
            diameter = self.distance_calculator.calculate_cluster_diameter(cluster_restaurants)

            # Calculate centroid
            centroid = self.distance_calculator.calculate_cluster_centroid(cluster_restaurants)

            # Create metrics
            metrics = ClusterMetrics(
                cluster_id=cluster_id,
                size=len(cluster_restaurants),
                cohesion=cohesion,
                diameter=diameter,
                centroid=centroid,
            )

            cluster_metrics[cluster_id] = metrics

            self.logger.info(
                f"Cluster {cluster_id} metrics: size={metrics.size}, "
                f"cohesion={metrics.cohesion:.2f}km, diameter={metrics.diameter:.2f}km"
            )

        return cluster_metrics

    def calculate_silhouette_score(
        self,
        restaurants: List[Restaurant],
        clusters: Dict[int, List[Restaurant]],
        distance_matrix: Optional[np.ndarray] = None,
    ) -> float:
        """Calculate silhouette score for clustering quality.

        Silhouette score ranges from -1 to 1:
        - 1: Clusters are well-separated and compact
        - 0: Clusters are overlapping
        - -1: Restaurants may be in wrong clusters

        Args:
            restaurants: List of restaurants
            clusters: Clustering result
            distance_matrix: Pre-computed distance matrix (optional)

        Returns:
            Silhouette score (or 0.0 if cannot be calculated)

        Example:
            >>> score = clusterer.calculate_silhouette_score(restaurants, clusters)
            >>> print(f"Silhouette score: {score:.3f}")
        """
        # Need at least 2 clusters to calculate silhouette score
        num_clusters = len([k for k in clusters.keys() if k != -1])
        if num_clusters < 2:
            self.logger.warning("Need at least 2 clusters to calculate silhouette score")
            return 0.0

        # Calculate distance matrix if not provided
        if distance_matrix is None:
            distance_matrix = self.distance_calculator.calculate_distance_matrix(restaurants)

        # Create label array
        labels = np.zeros(len(restaurants), dtype=int)
        restaurant_to_idx = {r.place_id: i for i, r in enumerate(restaurants)}

        for cluster_id, cluster_restaurants in clusters.items():
            for restaurant in cluster_restaurants:
                idx = restaurant_to_idx[restaurant.place_id]
                labels[idx] = cluster_id

        # Filter out noise points (label = -1) for silhouette calculation
        mask = labels != -1
        if np.sum(mask) < 2:
            self.logger.warning("Too few non-noise points for silhouette score")
            return 0.0

        filtered_matrix = distance_matrix[mask][:, mask]
        filtered_labels = labels[mask]

        # Calculate silhouette score
        try:
            score = silhouette_score(filtered_matrix, filtered_labels, metric='precomputed')
            self.logger.info(f"Silhouette score: {score:.3f}")
            return score
        except Exception as e:
            self.logger.error(f"Error calculating silhouette score: {e}")
            return 0.0

    def validate_clusters(
        self,
        clusters: Dict[int, List[Restaurant]],
        min_cluster_size: int = 5,
        max_cluster_diameter_km: float = 15.0,
    ) -> Dict[str, any]:
        """Validate cluster quality against requirements.

        Args:
            clusters: Clustering result
            min_cluster_size: Minimum restaurants per cluster
            max_cluster_diameter_km: Maximum cluster diameter in km

        Returns:
            Dictionary with validation results

        Example:
            >>> validation = clusterer.validate_clusters(clusters)
            >>> if validation["all_passed"]:
            ...     print("All clusters meet quality requirements")
        """
        validation_results = {
            "total_clusters": 0,
            "valid_clusters": 0,
            "invalid_clusters": [],
            "all_passed": True,
        }

        for cluster_id, cluster_restaurants in clusters.items():
            if cluster_id == -1:
                # Skip noise points
                continue

            validation_results["total_clusters"] += 1

            # Check cluster size
            if len(cluster_restaurants) < min_cluster_size:
                validation_results["invalid_clusters"].append({
                    "cluster_id": cluster_id,
                    "reason": f"Size {len(cluster_restaurants)} < minimum {min_cluster_size}",
                })
                validation_results["all_passed"] = False
                continue

            # Check cluster diameter
            diameter = self.distance_calculator.calculate_cluster_diameter(cluster_restaurants)
            if diameter > max_cluster_diameter_km:
                validation_results["invalid_clusters"].append({
                    "cluster_id": cluster_id,
                    "reason": f"Diameter {diameter:.2f}km > maximum {max_cluster_diameter_km}km",
                })
                validation_results["all_passed"] = False
                continue

            # Cluster is valid
            validation_results["valid_clusters"] += 1

        self.logger.info(
            f"Cluster validation: {validation_results['valid_clusters']}/{validation_results['total_clusters']} valid"
        )

        if not validation_results["all_passed"]:
            for invalid in validation_results["invalid_clusters"]:
                self.logger.warning(
                    f"Cluster {invalid['cluster_id']} failed: {invalid['reason']}"
                )

        return validation_results

    def optimize_parameters(
        self,
        restaurants: List[Restaurant],
        eps_range: Tuple[float, float] = (2.0, 10.0),
        min_samples_range: Tuple[int, int] = (3, 10),
        step: float = 1.0,
    ) -> Dict[str, any]:
        """Find optimal DBSCAN parameters using grid search.

        Optimizes based on silhouette score.

        Args:
            restaurants: List of restaurants
            eps_range: Range of eps values to try (km)
            min_samples_range: Range of min_samples values to try
            step: Step size for eps values

        Returns:
            Dictionary with optimal parameters and scores

        Example:
            >>> optimal = clusterer.optimize_parameters(restaurants)
            >>> print(f"Best eps: {optimal['best_eps']}km")
            >>> print(f"Best min_samples: {optimal['best_min_samples']}")
        """
        self.logger.info("Optimizing DBSCAN parameters...")

        # Calculate distance matrix once
        distance_matrix = self.distance_calculator.calculate_distance_matrix(restaurants)

        best_score = -1.0
        best_params = {
            "eps": self.eps_km,
            "min_samples": self.min_samples,
        }

        results = []

        # Grid search
        eps_values = np.arange(eps_range[0], eps_range[1] + step, step)
        min_samples_values = range(min_samples_range[0], min_samples_range[1] + 1)

        for eps in eps_values:
            for min_samples in min_samples_values:
                # Create temporary clusterer
                temp_clusterer = RestaurantClusterer(
                    eps_km=eps,
                    min_samples=min_samples,
                    distance_calculator=self.distance_calculator,
                )

                # Cluster
                clusters = temp_clusterer.cluster_restaurants(
                    restaurants,
                    distance_matrix=distance_matrix,
                )

                # Calculate silhouette score
                score = temp_clusterer.calculate_silhouette_score(
                    restaurants,
                    clusters,
                    distance_matrix=distance_matrix,
                )

                results.append({
                    "eps": eps,
                    "min_samples": min_samples,
                    "score": score,
                    "num_clusters": len([k for k in clusters.keys() if k != -1]),
                    "noise_points": len(clusters.get(-1, [])),
                })

                # Update best
                if score > best_score:
                    best_score = score
                    best_params = {
                        "eps": eps,
                        "min_samples": min_samples,
                    }

        self.logger.info(
            f"Optimal parameters: eps={best_params['eps']}km, "
            f"min_samples={best_params['min_samples']}, "
            f"score={best_score:.3f}"
        )

        return {
            "best_eps": best_params["eps"],
            "best_min_samples": best_params["min_samples"],
            "best_score": best_score,
            "all_results": results,
        }

    def get_stats(self) -> Dict[str, int]:
        """Get clustering statistics.

        Returns:
            Dictionary with clustering statistics
        """
        return self.clustering_stats.copy()

    def reset_stats(self) -> None:
        """Reset clustering statistics."""
        self.clustering_stats = {
            "total_clustered": 0,
            "num_clusters": 0,
            "noise_points": 0,
        }
