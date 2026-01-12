"""Traveling Salesman Problem (TSP) solvers for route optimization.

This module provides multiple TSP algorithms for finding optimal or
near-optimal routes through restaurants.
"""

from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass

from fast_food_optimizer.utils.logging import get_logger, log_performance


@dataclass
class TSPSolution:
    """Solution to a TSP problem.

    Attributes:
        route: List of indices representing the route order
        distance: Total distance of the route
        algorithm: Name of algorithm used
        computation_time: Time taken to compute (seconds)
    """

    route: List[int]
    distance: float
    algorithm: str
    computation_time: float

    def to_dict(self) -> dict:
        """Convert solution to dictionary."""
        return {
            "route": self.route,
            "distance": self.distance,
            "algorithm": self.algorithm,
            "computation_time": self.computation_time,
        }


class TSPSolver:
    """Solves Traveling Salesman Problem using multiple algorithms.

    Provides both optimal and heuristic approaches for route optimization.
    Optimal solutions use OR-Tools for small problems, heuristics for large.

    Example:
        >>> solver = TSPSolver()
        >>> solution = solver.solve_nearest_neighbor(distance_matrix)
        >>> improved = solver.solve_2opt(distance_matrix, solution.route)
    """

    def __init__(self):
        """Initialize TSP solver."""
        self.logger = get_logger(__name__)

        # Solver statistics
        self.solver_stats = {
            "problems_solved": 0,
            "total_distance_saved": 0.0,
        }

    @log_performance
    def solve_nearest_neighbor(
        self,
        distance_matrix: np.ndarray,
        start_idx: int = 0,
    ) -> TSPSolution:
        """Solve TSP using nearest neighbor heuristic.

        Greedy algorithm: Always visit nearest unvisited node.
        Fast but not optimal. Good for initial solution.

        Args:
            distance_matrix: NxN distance matrix
            start_idx: Starting node index

        Returns:
            TSP solution

        Time Complexity: O(n²)
        """
        import time

        start_time = time.time()

        n = len(distance_matrix)
        unvisited = set(range(n))
        route = [start_idx]
        unvisited.remove(start_idx)

        current = start_idx
        total_distance = 0.0

        # Greedily select nearest neighbor
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            total_distance += distance_matrix[current][nearest]
            route.append(nearest)
            current = nearest
            unvisited.remove(nearest)

        computation_time = time.time() - start_time

        self.solver_stats["problems_solved"] += 1

        self.logger.info(
            f"Nearest Neighbor: {n} nodes, distance={total_distance:.2f}km, "
            f"time={computation_time:.3f}s"
        )

        return TSPSolution(
            route=route,
            distance=total_distance,
            algorithm="nearest_neighbor",
            computation_time=computation_time,
        )

    @log_performance
    def solve_2opt(
        self,
        distance_matrix: np.ndarray,
        initial_route: Optional[List[int]] = None,
        max_iterations: int = 1000,
    ) -> TSPSolution:
        """Solve TSP using 2-opt local search.

        Iteratively improves route by reversing segments.
        Better quality than nearest neighbor but slower.

        Args:
            distance_matrix: NxN distance matrix
            initial_route: Starting route (uses nearest neighbor if None)
            max_iterations: Maximum improvement iterations

        Returns:
            Improved TSP solution

        Time Complexity: O(n² × iterations)
        """
        import time

        start_time = time.time()

        n = len(distance_matrix)

        # Get initial route if not provided
        if initial_route is None:
            nn_solution = self.solve_nearest_neighbor(distance_matrix)
            route = nn_solution.route.copy()
            initial_distance = nn_solution.distance
        else:
            route = initial_route.copy()
            initial_distance = self._calculate_route_distance(distance_matrix, route)

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # Calculate change in distance if we reverse route[i:j+1]
                    if self._2opt_improvement(distance_matrix, route, i, j):
                        # Reverse the segment
                        route[i : j + 1] = reversed(route[i : j + 1])
                        improved = True

        final_distance = self._calculate_route_distance(distance_matrix, route)
        computation_time = time.time() - start_time

        improvement = initial_distance - final_distance
        self.solver_stats["problems_solved"] += 1
        self.solver_stats["total_distance_saved"] += improvement

        self.logger.info(
            f"2-Opt: {n} nodes, distance={final_distance:.2f}km, "
            f"improved by {improvement:.2f}km, "
            f"iterations={iteration}, time={computation_time:.3f}s"
        )

        return TSPSolution(
            route=route,
            distance=final_distance,
            algorithm="2opt",
            computation_time=computation_time,
        )

    def _2opt_improvement(
        self,
        distance_matrix: np.ndarray,
        route: List[int],
        i: int,
        j: int,
    ) -> bool:
        """Check if 2-opt swap improves the route.

        Args:
            distance_matrix: Distance matrix
            route: Current route
            i: Start of segment to reverse
            j: End of segment to reverse

        Returns:
            True if swap improves route
        """
        # Current edges: (i-1, i) and (j, j+1)
        # New edges: (i-1, j) and (i, j+1)

        n = len(route)

        # Handle edge cases
        i_prev = route[i - 1]
        i_node = route[i]
        j_node = route[j]
        j_next = route[(j + 1) % n] if j + 1 < n else route[0]

        # Current distance
        current_dist = (
            distance_matrix[i_prev][i_node] + distance_matrix[j_node][j_next]
        )

        # New distance after reversing
        new_dist = distance_matrix[i_prev][j_node] + distance_matrix[i_node][j_next]

        return new_dist < current_dist

    def solve_christofides(
        self,
        distance_matrix: np.ndarray,
    ) -> TSPSolution:
        """Solve TSP using Christofides algorithm.

        Guaranteed to be within 1.5x optimal for metric TSP.
        More complex but better quality than simple heuristics.

        Args:
            distance_matrix: NxN distance matrix

        Returns:
            TSP solution

        Note: This is a placeholder for future implementation.
        Currently uses 2-opt as fallback.
        """
        self.logger.warning(
            "Christofides algorithm not yet implemented, using 2-opt instead"
        )
        return self.solve_2opt(distance_matrix)

    def solve_ortools(
        self,
        distance_matrix: np.ndarray,
        time_limit_seconds: int = 30,
    ) -> TSPSolution:
        """Solve TSP using Google OR-Tools (optimal solution).

        Uses constraint programming for optimal or near-optimal solution.
        Best for small problems (< 50 nodes).

        Args:
            distance_matrix: NxN distance matrix
            time_limit_seconds: Maximum computation time

        Returns:
            TSP solution (optimal or best found)

        Note: Requires OR-Tools to be installed.
        """
        try:
            from ortools.constraint_solver import routing_enums_pb2
            from ortools.constraint_solver import pywrapcp
        except ImportError:
            self.logger.warning(
                "OR-Tools not installed, falling back to 2-opt. "
                "Install with: pip install ortools"
            )
            return self.solve_2opt(distance_matrix)

        import time

        start_time = time.time()

        n = len(distance_matrix)

        # Create routing model
        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 1000)  # Convert to meters

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit_seconds

        # Solve
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            # Extract route
            route = []
            index = routing.Start(0)
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))

            # Calculate distance
            distance = self._calculate_route_distance(distance_matrix, route)

            computation_time = time.time() - start_time

            self.solver_stats["problems_solved"] += 1

            self.logger.info(
                f"OR-Tools: {n} nodes, distance={distance:.2f}km, "
                f"time={computation_time:.3f}s"
            )

            return TSPSolution(
                route=route,
                distance=distance,
                algorithm="ortools",
                computation_time=computation_time,
            )
        else:
            self.logger.warning("OR-Tools failed to find solution, using 2-opt")
            return self.solve_2opt(distance_matrix)

    def solve_auto(
        self,
        distance_matrix: np.ndarray,
        quality: str = "balanced",
    ) -> TSPSolution:
        """Automatically select best algorithm based on problem size and quality.

        Args:
            distance_matrix: NxN distance matrix
            quality: Desired quality level:
                - "fast": Nearest neighbor only
                - "balanced": 2-opt with good settings
                - "best": OR-Tools for small problems, 2-opt for large

        Returns:
            TSP solution
        """
        n = len(distance_matrix)

        if quality == "fast":
            return self.solve_nearest_neighbor(distance_matrix)

        elif quality == "balanced":
            # Use 2-opt with moderate iterations
            return self.solve_2opt(distance_matrix, max_iterations=500)

        elif quality == "best":
            # Use OR-Tools for small problems, 2-opt for large
            if n <= 30:
                return self.solve_ortools(distance_matrix, time_limit_seconds=30)
            else:
                return self.solve_2opt(distance_matrix, max_iterations=1000)

        else:
            raise ValueError(
                f"Invalid quality level: {quality}. "
                "Must be 'fast', 'balanced', or 'best'"
            )

    def compare_algorithms(
        self,
        distance_matrix: np.ndarray,
    ) -> dict:
        """Compare all available algorithms on the same problem.

        Args:
            distance_matrix: NxN distance matrix

        Returns:
            Dictionary with results from each algorithm
        """
        results = {}

        # Try all algorithms
        algorithms = [
            ("nearest_neighbor", lambda: self.solve_nearest_neighbor(distance_matrix)),
            ("2opt", lambda: self.solve_2opt(distance_matrix)),
        ]

        # Add OR-Tools if small problem
        n = len(distance_matrix)
        if n <= 30:
            algorithms.append(
                ("ortools", lambda: self.solve_ortools(distance_matrix, time_limit_seconds=10))
            )

        for name, solver_func in algorithms:
            try:
                solution = solver_func()
                results[name] = solution.to_dict()
            except Exception as e:
                self.logger.error(f"Algorithm {name} failed: {e}")
                results[name] = {"error": str(e)}

        return results

    def _calculate_route_distance(
        self,
        distance_matrix: np.ndarray,
        route: List[int],
    ) -> float:
        """Calculate total distance for a route.

        Args:
            distance_matrix: Distance matrix
            route: List of node indices

        Returns:
            Total route distance
        """
        total = 0.0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i + 1]]
        return total

    def get_stats(self) -> dict:
        """Get solver statistics.

        Returns:
            Dictionary with solver statistics
        """
        return self.solver_stats.copy()

    def reset_stats(self) -> None:
        """Reset solver statistics."""
        self.solver_stats = {
            "problems_solved": 0,
            "total_distance_saved": 0.0,
        }
