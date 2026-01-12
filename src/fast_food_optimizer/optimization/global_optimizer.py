"""Global route optimization combining cluster sequencing and intra-cluster routing.

This module provides end-to-end route optimization that sequences clusters
and optimizes routes within each cluster.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.optimization.distance import DistanceCalculator
from fast_food_optimizer.optimization.tsp_solver import TSPSolver
from fast_food_optimizer.optimization.route_optimizer import (
    IntraClusterOptimizer,
    OptimizedRoute,
    RouteMetrics,
)
from fast_food_optimizer.utils.logging import get_logger, log_performance


@dataclass
class GlobalRoute:
    """Complete route through all clusters.

    Attributes:
        cluster_sequence: Ordered list of cluster IDs to visit
        cluster_routes: Dictionary mapping cluster_id to OptimizedRoute
        total_distance: Total route distance (km)
        total_restaurants: Total number of restaurants
        estimated_time_hours: Estimated time to complete route
        start_location: Starting coordinates (lat, lng)
        end_location: Ending coordinates (lat, lng)
    """

    cluster_sequence: List[int]
    cluster_routes: Dict[int, OptimizedRoute]
    total_distance: float
    total_restaurants: int
    estimated_time_hours: float
    start_location: Optional[Tuple[float, float]] = None
    end_location: Optional[Tuple[float, float]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "cluster_sequence": self.cluster_sequence,
            "cluster_routes": {
                cid: route.to_dict() for cid, route in self.cluster_routes.items()
            },
            "total_distance": self.total_distance,
            "total_restaurants": self.total_restaurants,
            "estimated_time_hours": self.estimated_time_hours,
            "start_location": self.start_location,
            "end_location": self.end_location,
        }

    def get_all_restaurants(self) -> List[Restaurant]:
        """Get ordered list of all restaurants in route."""
        all_restaurants = []
        for cluster_id in self.cluster_sequence:
            if cluster_id in self.cluster_routes:
                all_restaurants.extend(self.cluster_routes[cluster_id].restaurants)
        return all_restaurants


class GlobalRouteOptimizer:
    """Optimizes complete routes across all clusters.

    Combines inter-cluster sequencing with intra-cluster optimization
    to create end-to-end routes.

    Example:
        >>> optimizer = GlobalRouteOptimizer()
        >>> global_route = optimizer.optimize_global_route(
        ...     clusters,
        ...     start_location=(40.7589, -111.8883)
        ... )
        >>> print(f"Total: {global_route.total_restaurants} restaurants")
        >>> print(f"Distance: {global_route.total_distance:.2f}km")
    """

    def __init__(
        self,
        distance_calculator: Optional[DistanceCalculator] = None,
        tsp_solver: Optional[TSPSolver] = None,
        intra_optimizer: Optional[IntraClusterOptimizer] = None,
    ):
        """Initialize global route optimizer.

        Args:
            distance_calculator: Distance calculator instance
            tsp_solver: TSP solver for cluster sequencing
            intra_optimizer: Intra-cluster optimizer
        """
        self.distance_calculator = distance_calculator or DistanceCalculator()
        self.tsp_solver = tsp_solver or TSPSolver()
        self.intra_optimizer = intra_optimizer or IntraClusterOptimizer()
        self.logger = get_logger(__name__)

        # Optimization statistics
        self.optimization_stats = {
            "routes_optimized": 0,
            "total_restaurants": 0,
            "total_distance": 0.0,
        }

    @log_performance
    def optimize_global_route(
        self,
        clusters: Dict[int, List[Restaurant]],
        start_location: Optional[Tuple[float, float]] = None,
        end_location: Optional[Tuple[float, float]] = None,
        algorithm: str = "auto",
        time_budget_hours: float = 24.0,
    ) -> GlobalRoute:
        """Optimize complete route across all clusters.

        Args:
            clusters: Dictionary mapping cluster_id to restaurants
            start_location: Optional starting point (lat, lng)
            end_location: Optional ending point (lat, lng)
            algorithm: TSP algorithm for cluster sequencing
            time_budget_hours: Available time budget

        Returns:
            Optimized global route

        Example:
            >>> route = optimizer.optimize_global_route(
            ...     clusters,
            ...     start_location=(40.7589, -111.8883),
            ...     time_budget_hours=24.0
            ... )
        """
        self.logger.info(f"Optimizing global route across {len(clusters)} clusters")

        # Filter out noise cluster
        valid_clusters = {
            cid: restaurants
            for cid, restaurants in clusters.items()
            if cid != -1
        }

        if not valid_clusters:
            raise ValueError("No valid clusters to optimize")

        # Step 1: Optimize routes within each cluster
        self.logger.info("Step 1: Optimizing intra-cluster routes")
        cluster_routes = self.intra_optimizer.optimize_all_clusters(
            valid_clusters, algorithm=algorithm
        )

        # Step 2: Calculate cluster centroids and inter-cluster distances
        self.logger.info("Step 2: Calculating cluster centroids")
        cluster_centroids = self._calculate_cluster_centroids(cluster_routes)

        # Step 3: Sequence clusters
        self.logger.info("Step 3: Sequencing clusters")
        cluster_sequence = self._sequence_clusters(
            cluster_centroids,
            start_location,
            end_location,
            algorithm,
        )

        # Step 4: Calculate total metrics
        self.logger.info("Step 4: Calculating route metrics")
        total_distance = self._calculate_total_distance(
            cluster_sequence,
            cluster_routes,
            cluster_centroids,
            start_location,
            end_location,
        )

        total_restaurants = sum(
            route.metrics.num_restaurants for route in cluster_routes.values()
        )

        # Estimate time: assume 3 min per restaurant + travel time
        # Travel time: distance / 5 km/h walking speed
        restaurant_time = total_restaurants * (3 / 60)  # hours
        travel_time = total_distance / 5.0  # hours at 5 km/h
        estimated_time = restaurant_time + travel_time

        # Update statistics
        self.optimization_stats["routes_optimized"] += 1
        self.optimization_stats["total_restaurants"] += total_restaurants
        self.optimization_stats["total_distance"] += total_distance

        self.logger.info(
            f"Global route optimized: {total_restaurants} restaurants, "
            f"{total_distance:.2f}km, ~{estimated_time:.1f}h"
        )

        return GlobalRoute(
            cluster_sequence=cluster_sequence,
            cluster_routes=cluster_routes,
            total_distance=total_distance,
            total_restaurants=total_restaurants,
            estimated_time_hours=estimated_time,
            start_location=start_location,
            end_location=end_location,
        )

    def generate_alternative_routes(
        self,
        clusters: Dict[int, List[Restaurant]],
        start_location: Optional[Tuple[float, float]] = None,
        num_alternatives: int = 3,
    ) -> List[GlobalRoute]:
        """Generate multiple alternative routes.

        Args:
            clusters: Dictionary of clusters
            start_location: Starting location
            num_alternatives: Number of alternatives to generate

        Returns:
            List of alternative global routes

        Example:
            >>> alternatives = optimizer.generate_alternative_routes(
            ...     clusters,
            ...     start_location=(40.7589, -111.8883),
            ...     num_alternatives=3
            ... )
            >>> for i, route in enumerate(alternatives):
            ...     print(f"Route {i+1}: {route.total_distance:.2f}km")
        """
        self.logger.info(f"Generating {num_alternatives} alternative routes")

        alternatives = []

        # Strategy 1: Different algorithms
        algorithms = ["nearest_neighbor", "2opt"]
        for i, algorithm in enumerate(algorithms[:num_alternatives]):
            try:
                route = self.optimize_global_route(
                    clusters,
                    start_location=start_location,
                    algorithm=algorithm,
                )
                alternatives.append(route)
            except Exception as e:
                self.logger.warning(f"Failed to generate route with {algorithm}: {e}")

        # Strategy 2: Different starting clusters (if we need more)
        if len(alternatives) < num_alternatives and len(clusters) > 2:
            # Try starting from different clusters
            cluster_ids = [cid for cid in clusters.keys() if cid != -1]
            for cluster_id in cluster_ids[:num_alternatives - len(alternatives)]:
                try:
                    # Use first restaurant in cluster as start
                    first_restaurant = clusters[cluster_id][0]
                    alt_start = (
                        first_restaurant.coordinates.latitude,
                        first_restaurant.coordinates.longitude,
                    )
                    route = self.optimize_global_route(
                        clusters,
                        start_location=alt_start,
                        algorithm="2opt",
                    )
                    alternatives.append(route)
                except Exception as e:
                    self.logger.warning(f"Failed to generate route from cluster {cluster_id}: {e}")

        self.logger.info(f"Generated {len(alternatives)} alternative routes")
        return alternatives

    def validate_global_route(
        self,
        route: GlobalRoute,
        time_budget_hours: float = 24.0,
        min_restaurants: int = 150,
    ) -> Dict[str, any]:
        """Validate global route against requirements.

        Args:
            route: Global route to validate
            time_budget_hours: Time budget in hours
            min_restaurants: Minimum restaurants required

        Returns:
            Dictionary with validation results

        Example:
            >>> validation = optimizer.validate_global_route(route)
            >>> if validation["valid"]:
            ...     print("Route meets all requirements!")
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "metrics": {},
        }

        # Check restaurant count
        if route.total_restaurants < min_restaurants:
            validation["errors"].append(
                f"Route has {route.total_restaurants} restaurants, "
                f"need at least {min_restaurants}"
            )
            validation["valid"] = False

        # Check time budget
        if route.estimated_time_hours > time_budget_hours:
            validation["errors"].append(
                f"Route takes {route.estimated_time_hours:.1f}h, "
                f"exceeds budget of {time_budget_hours}h"
            )
            validation["valid"] = False

        # Check for duplicate restaurants across clusters
        all_restaurants = route.get_all_restaurants()
        place_ids = [r.place_id for r in all_restaurants]
        if len(place_ids) != len(set(place_ids)):
            validation["errors"].append("Route contains duplicate restaurants")
            validation["valid"] = False

        # Calculate restaurants per hour
        if route.estimated_time_hours > 0:
            restaurants_per_hour = route.total_restaurants / route.estimated_time_hours
            validation["metrics"]["restaurants_per_hour"] = restaurants_per_hour

            if restaurants_per_hour < 10:
                validation["warnings"].append(
                    f"Low efficiency: {restaurants_per_hour:.1f} restaurants/hour"
                )

        # Check cluster count
        if len(route.cluster_sequence) < 2:
            validation["warnings"].append("Route has very few clusters")

        return validation

    def _calculate_cluster_centroids(
        self,
        cluster_routes: Dict[int, OptimizedRoute],
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate geographic centroid for each cluster.

        Args:
            cluster_routes: Optimized routes for each cluster

        Returns:
            Dictionary mapping cluster_id to (lat, lng) centroid
        """
        centroids = {}

        for cluster_id, route in cluster_routes.items():
            centroid = self.distance_calculator.calculate_cluster_centroid(
                route.restaurants
            )
            centroids[cluster_id] = centroid

        return centroids

    def _sequence_clusters(
        self,
        cluster_centroids: Dict[int, Tuple[float, float]],
        start_location: Optional[Tuple[float, float]],
        end_location: Optional[Tuple[float, float]],
        algorithm: str,
    ) -> List[int]:
        """Determine optimal sequence for visiting clusters.

        Args:
            cluster_centroids: Cluster centroids
            start_location: Starting location
            end_location: Ending location
            algorithm: TSP algorithm

        Returns:
            Ordered list of cluster IDs
        """
        cluster_ids = list(cluster_centroids.keys())

        if len(cluster_ids) == 0:
            return []
        if len(cluster_ids) == 1:
            return cluster_ids

        # Build distance matrix between cluster centroids
        n = len(cluster_ids)
        distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lng1 = cluster_centroids[cluster_ids[i]]
                    lat2, lng2 = cluster_centroids[cluster_ids[j]]
                    distance = self.distance_calculator._haversine(lat1, lng1, lat2, lng2)
                    distance_matrix[i, j] = distance

        # Solve TSP for cluster sequence
        if algorithm == "auto":
            solution = self.tsp_solver.solve_auto(distance_matrix, quality="balanced")
        elif algorithm == "nearest_neighbor":
            # Find start index if start_location provided
            start_idx = 0
            if start_location:
                min_dist = float('inf')
                for i, cluster_id in enumerate(cluster_ids):
                    centroid = cluster_centroids[cluster_id]
                    dist = self.distance_calculator._haversine(
                        start_location[0], start_location[1],
                        centroid[0], centroid[1]
                    )
                    if dist < min_dist:
                        min_dist = dist
                        start_idx = i

            solution = self.tsp_solver.solve_nearest_neighbor(
                distance_matrix, start_idx=start_idx
            )
        else:
            solution = self.tsp_solver.solve_2opt(distance_matrix)

        # Convert indices to cluster IDs
        cluster_sequence = [cluster_ids[i] for i in solution.route]

        return cluster_sequence

    def _calculate_total_distance(
        self,
        cluster_sequence: List[int],
        cluster_routes: Dict[int, OptimizedRoute],
        cluster_centroids: Dict[int, Tuple[float, float]],
        start_location: Optional[Tuple[float, float]],
        end_location: Optional[Tuple[float, float]],
    ) -> float:
        """Calculate total distance for global route.

        Args:
            cluster_sequence: Ordered cluster IDs
            cluster_routes: Routes within clusters
            cluster_centroids: Cluster centroids
            start_location: Starting location
            end_location: Ending location

        Returns:
            Total distance in km
        """
        total = 0.0

        # Distance from start to first cluster
        if start_location and cluster_sequence:
            first_centroid = cluster_centroids[cluster_sequence[0]]
            total += self.distance_calculator._haversine(
                start_location[0], start_location[1],
                first_centroid[0], first_centroid[1]
            )

        # Distance within and between clusters
        for i, cluster_id in enumerate(cluster_sequence):
            # Add intra-cluster distance
            total += cluster_routes[cluster_id].metrics.total_distance

            # Add inter-cluster distance to next cluster
            if i < len(cluster_sequence) - 1:
                next_cluster_id = cluster_sequence[i + 1]
                c1 = cluster_centroids[cluster_id]
                c2 = cluster_centroids[next_cluster_id]
                total += self.distance_calculator._haversine(c1[0], c1[1], c2[0], c2[1])

        # Distance from last cluster to end
        if end_location and cluster_sequence:
            last_centroid = cluster_centroids[cluster_sequence[-1]]
            total += self.distance_calculator._haversine(
                last_centroid[0], last_centroid[1],
                end_location[0], end_location[1]
            )

        return total

    def get_stats(self) -> dict:
        """Get optimization statistics.

        Returns:
            Dictionary with statistics
        """
        stats = self.optimization_stats.copy()

        if stats["routes_optimized"] > 0:
            stats["avg_restaurants_per_route"] = (
                stats["total_restaurants"] / stats["routes_optimized"]
            )
            stats["avg_distance_per_route"] = (
                stats["total_distance"] / stats["routes_optimized"]
            )
        else:
            stats["avg_restaurants_per_route"] = 0
            stats["avg_distance_per_route"] = 0

        return stats

    def reset_stats(self) -> None:
        """Reset optimization statistics."""
        self.optimization_stats = {
            "routes_optimized": 0,
            "total_restaurants": 0,
            "total_distance": 0.0,
        }
