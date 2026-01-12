"""Route optimization for restaurant clusters.

This module provides route optimization within clusters using TSP algorithms.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.optimization.distance import DistanceCalculator
from fast_food_optimizer.optimization.tsp_solver import TSPSolver, TSPSolution
from fast_food_optimizer.utils.logging import get_logger, log_performance


@dataclass
class RouteMetrics:
    """Metrics for a route.

    Attributes:
        total_distance: Total distance in km
        num_restaurants: Number of restaurants visited
        avg_distance: Average distance between restaurants (km)
        efficiency_score: Route efficiency (0-1, higher is better)
    """

    total_distance: float
    num_restaurants: int
    avg_distance: float
    efficiency_score: float

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "total_distance": self.total_distance,
            "num_restaurants": self.num_restaurants,
            "avg_distance": self.avg_distance,
            "efficiency_score": self.efficiency_score,
        }


@dataclass
class OptimizedRoute:
    """Optimized route through restaurants.

    Attributes:
        restaurants: Ordered list of restaurants in route
        metrics: Route quality metrics
        algorithm: Algorithm used for optimization
        computation_time: Time taken to optimize (seconds)
    """

    restaurants: List[Restaurant]
    metrics: RouteMetrics
    algorithm: str
    computation_time: float

    def to_dict(self) -> dict:
        """Convert route to dictionary."""
        return {
            "restaurants": [r.place_id for r in self.restaurants],
            "metrics": self.metrics.to_dict(),
            "algorithm": self.algorithm,
            "computation_time": self.computation_time,
        }


class IntraClusterOptimizer:
    """Optimizes routes within restaurant clusters.

    Uses TSP algorithms to find optimal or near-optimal routes
    through restaurants in a cluster.

    Example:
        >>> optimizer = IntraClusterOptimizer()
        >>> route = optimizer.optimize_cluster(cluster_restaurants)
        >>> print(f"Route distance: {route.metrics.total_distance:.2f}km")
    """

    def __init__(
        self,
        distance_calculator: Optional[DistanceCalculator] = None,
        tsp_solver: Optional[TSPSolver] = None,
    ):
        """Initialize intra-cluster optimizer.

        Args:
            distance_calculator: Distance calculator instance
            tsp_solver: TSP solver instance
        """
        self.distance_calculator = distance_calculator or DistanceCalculator()
        self.tsp_solver = tsp_solver or TSPSolver()
        self.logger = get_logger(__name__)

        # Optimization statistics
        self.optimization_stats = {
            "clusters_optimized": 0,
            "total_distance_optimized": 0.0,
            "total_restaurants": 0,
        }

    @log_performance
    def optimize_cluster(
        self,
        restaurants: List[Restaurant],
        algorithm: str = "auto",
        start_restaurant: Optional[Restaurant] = None,
    ) -> OptimizedRoute:
        """Optimize route through restaurants in a cluster.

        Args:
            restaurants: List of restaurants in cluster
            algorithm: TSP algorithm to use:
                - "auto": Automatically select best algorithm
                - "nearest_neighbor": Fast greedy algorithm
                - "2opt": Local search improvement
                - "ortools": Optimal solution (small clusters only)
            start_restaurant: Optional starting restaurant

        Returns:
            Optimized route with metrics

        Example:
            >>> route = optimizer.optimize_cluster(cluster, algorithm="2opt")
            >>> for restaurant in route.restaurants:
            ...     print(f"Visit: {restaurant.name}")
        """
        if len(restaurants) == 0:
            raise ValueError("Cannot optimize empty cluster")

        if len(restaurants) == 1:
            # Single restaurant - trivial route
            metrics = RouteMetrics(
                total_distance=0.0,
                num_restaurants=1,
                avg_distance=0.0,
                efficiency_score=1.0,
            )
            return OptimizedRoute(
                restaurants=restaurants,
                metrics=metrics,
                algorithm="trivial",
                computation_time=0.0,
            )

        self.logger.info(
            f"Optimizing cluster with {len(restaurants)} restaurants using {algorithm}"
        )

        # Calculate distance matrix
        distance_matrix = self.distance_calculator.calculate_distance_matrix(
            restaurants
        )

        # Determine start index
        start_idx = 0
        if start_restaurant is not None:
            try:
                start_idx = restaurants.index(start_restaurant)
            except ValueError:
                self.logger.warning(
                    f"Start restaurant not in cluster, using first restaurant"
                )

        # Solve TSP
        if algorithm == "auto":
            solution = self.tsp_solver.solve_auto(distance_matrix, quality="balanced")
        elif algorithm == "nearest_neighbor":
            solution = self.tsp_solver.solve_nearest_neighbor(
                distance_matrix, start_idx=start_idx
            )
        elif algorithm == "2opt":
            solution = self.tsp_solver.solve_2opt(distance_matrix)
        elif algorithm == "ortools":
            solution = self.tsp_solver.solve_ortools(distance_matrix)
        else:
            raise ValueError(
                f"Invalid algorithm: {algorithm}. "
                "Must be 'auto', 'nearest_neighbor', '2opt', or 'ortools'"
            )

        # Convert indices to restaurants
        optimized_restaurants = [restaurants[i] for i in solution.route]

        # Calculate metrics
        metrics = self._calculate_route_metrics(
            optimized_restaurants, distance_matrix, solution
        )

        # Update statistics
        self.optimization_stats["clusters_optimized"] += 1
        self.optimization_stats["total_distance_optimized"] += metrics.total_distance
        self.optimization_stats["total_restaurants"] += len(restaurants)

        self.logger.info(
            f"Cluster optimized: {len(restaurants)} restaurants, "
            f"distance={metrics.total_distance:.2f}km, "
            f"efficiency={metrics.efficiency_score:.2f}"
        )

        return OptimizedRoute(
            restaurants=optimized_restaurants,
            metrics=metrics,
            algorithm=solution.algorithm,
            computation_time=solution.computation_time,
        )

    @log_performance
    def optimize_all_clusters(
        self,
        clusters: Dict[int, List[Restaurant]],
        algorithm: str = "auto",
    ) -> Dict[int, OptimizedRoute]:
        """Optimize routes for all clusters.

        Args:
            clusters: Dictionary mapping cluster_id to restaurants
            algorithm: TSP algorithm to use

        Returns:
            Dictionary mapping cluster_id to optimized routes

        Example:
            >>> routes = optimizer.optimize_all_clusters(clusters)
            >>> for cluster_id, route in routes.items():
            ...     print(f"Cluster {cluster_id}: {route.metrics.total_distance:.2f}km")
        """
        optimized_routes = {}

        for cluster_id, restaurants in clusters.items():
            if cluster_id == -1:
                # Skip noise points
                self.logger.info("Skipping noise cluster (-1)")
                continue

            try:
                route = self.optimize_cluster(restaurants, algorithm=algorithm)
                optimized_routes[cluster_id] = route
            except Exception as e:
                self.logger.error(
                    f"Failed to optimize cluster {cluster_id}: {e}", exc_info=True
                )

        self.logger.info(
            f"Optimized {len(optimized_routes)} clusters with "
            f"total {self.optimization_stats['total_restaurants']} restaurants"
        )

        return optimized_routes

    def compare_algorithms(
        self,
        restaurants: List[Restaurant],
    ) -> Dict[str, OptimizedRoute]:
        """Compare different optimization algorithms on same cluster.

        Args:
            restaurants: List of restaurants in cluster

        Returns:
            Dictionary mapping algorithm name to route

        Example:
            >>> comparison = optimizer.compare_algorithms(cluster)
            >>> for algo, route in comparison.items():
            ...     print(f"{algo}: {route.metrics.total_distance:.2f}km")
        """
        if len(restaurants) < 2:
            self.logger.warning("Cluster too small for comparison")
            return {}

        algorithms = ["nearest_neighbor", "2opt"]

        # Add OR-Tools for small clusters
        if len(restaurants) <= 30:
            algorithms.append("ortools")

        results = {}

        for algorithm in algorithms:
            try:
                route = self.optimize_cluster(restaurants, algorithm=algorithm)
                results[algorithm] = route
            except Exception as e:
                self.logger.error(f"Algorithm {algorithm} failed: {e}")

        return results

    def validate_route(
        self,
        route: OptimizedRoute,
    ) -> Dict[str, any]:
        """Validate route quality and constraints.

        Args:
            route: Route to validate

        Returns:
            Dictionary with validation results

        Example:
            >>> validation = optimizer.validate_route(route)
            >>> if validation["valid"]:
            ...     print("Route is valid")
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }

        # Check for duplicate restaurants
        place_ids = [r.place_id for r in route.restaurants]
        if len(place_ids) != len(set(place_ids)):
            validation["errors"].append("Route contains duplicate restaurants")
            validation["valid"] = False

        # Check for empty route
        if len(route.restaurants) == 0:
            validation["errors"].append("Route is empty")
            validation["valid"] = False

        # Check efficiency score
        if route.metrics.efficiency_score < 0.5:
            validation["warnings"].append(
                f"Low efficiency score: {route.metrics.efficiency_score:.2f}"
            )

        # Check average distance
        if route.metrics.avg_distance > 2.0:  # > 2km average
            validation["warnings"].append(
                f"High average distance between restaurants: "
                f"{route.metrics.avg_distance:.2f}km"
            )

        return validation

    def _calculate_route_metrics(
        self,
        restaurants: List[Restaurant],
        distance_matrix: np.ndarray,
        solution: TSPSolution,
    ) -> RouteMetrics:
        """Calculate quality metrics for a route.

        Args:
            restaurants: Ordered list of restaurants in route
            distance_matrix: Distance matrix
            solution: TSP solution

        Returns:
            Route metrics
        """
        n = len(restaurants)

        # Total distance from TSP solution
        total_distance = solution.distance

        # Average distance
        avg_distance = total_distance / (n - 1) if n > 1 else 0.0

        # Calculate efficiency score
        # Compare to naive distance (straight line from first to last)
        if n > 1:
            first_idx = solution.route[0]
            last_idx = solution.route[-1]
            direct_distance = distance_matrix[first_idx][last_idx]

            # Efficiency = direct distance / actual distance
            # (1.0 = perfect efficiency, lower = more detours)
            if total_distance > 0:
                efficiency_score = min(1.0, direct_distance / total_distance)
            else:
                efficiency_score = 1.0
        else:
            efficiency_score = 1.0

        return RouteMetrics(
            total_distance=total_distance,
            num_restaurants=n,
            avg_distance=avg_distance,
            efficiency_score=efficiency_score,
        )

    def get_stats(self) -> dict:
        """Get optimization statistics.

        Returns:
            Dictionary with optimization statistics
        """
        stats = self.optimization_stats.copy()

        if stats["clusters_optimized"] > 0:
            stats["avg_restaurants_per_cluster"] = (
                stats["total_restaurants"] / stats["clusters_optimized"]
            )
            stats["avg_distance_per_cluster"] = (
                stats["total_distance_optimized"] / stats["clusters_optimized"]
            )
        else:
            stats["avg_restaurants_per_cluster"] = 0
            stats["avg_distance_per_cluster"] = 0

        return stats

    def reset_stats(self) -> None:
        """Reset optimization statistics."""
        self.optimization_stats = {
            "clusters_optimized": 0,
            "total_distance_optimized": 0.0,
            "total_restaurants": 0,
        }
