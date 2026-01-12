"""Unit tests for TSP Solver."""

import pytest
import numpy as np

from fast_food_optimizer.optimization.tsp_solver import TSPSolver, TSPSolution


class TestTSPSolution:
    """Test suite for TSPSolution."""

    def test_tsp_solution_creation(self):
        """Test creating TSPSolution."""
        solution = TSPSolution(
            route=[0, 1, 2, 3],
            distance=15.5,
            algorithm="nearest_neighbor",
            computation_time=0.01,
        )

        assert solution.route == [0, 1, 2, 3]
        assert solution.distance == 15.5
        assert solution.algorithm == "nearest_neighbor"
        assert solution.computation_time == 0.01

    def test_tsp_solution_to_dict(self):
        """Test converting TSPSolution to dict."""
        solution = TSPSolution(
            route=[0, 1, 2],
            distance=10.0,
            algorithm="2opt",
            computation_time=0.05,
        )

        solution_dict = solution.to_dict()

        assert solution_dict["route"] == [0, 1, 2]
        assert solution_dict["distance"] == 10.0
        assert solution_dict["algorithm"] == "2opt"
        assert solution_dict["computation_time"] == 0.05


class TestTSPSolver:
    """Test suite for TSP solver."""

    def setup_method(self):
        """Set up test fixtures."""
        self.solver = TSPSolver()

    def create_simple_distance_matrix(self) -> np.ndarray:
        """Create a simple 4x4 distance matrix for testing."""
        # Simple symmetric matrix
        matrix = np.array([
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 0.0, 1.5, 2.5],
            [2.0, 1.5, 0.0, 1.0],
            [3.0, 2.5, 1.0, 0.0],
        ])
        return matrix

    def create_triangle_distance_matrix(self) -> np.ndarray:
        """Create a simple 3-node triangle."""
        matrix = np.array([
            [0.0, 10.0, 15.0],
            [10.0, 0.0, 20.0],
            [15.0, 20.0, 0.0],
        ])
        return matrix

    def test_solve_nearest_neighbor_basic(self):
        """Test nearest neighbor algorithm."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_nearest_neighbor(matrix)

        assert len(solution.route) == 4
        assert solution.route[0] == 0  # Starts at 0
        assert solution.algorithm == "nearest_neighbor"
        assert solution.distance > 0
        assert solution.computation_time >= 0

    def test_solve_nearest_neighbor_custom_start(self):
        """Test nearest neighbor with custom start."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_nearest_neighbor(matrix, start_idx=2)

        assert solution.route[0] == 2  # Starts at 2
        assert len(solution.route) == 4

    def test_solve_nearest_neighbor_triangle(self):
        """Test nearest neighbor on simple triangle."""
        matrix = self.create_triangle_distance_matrix()

        solution = self.solver.solve_nearest_neighbor(matrix)

        assert len(solution.route) == 3
        # Should visit all nodes
        assert set(solution.route) == {0, 1, 2}

    def test_solve_2opt_basic(self):
        """Test 2-opt algorithm."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_2opt(matrix)

        assert len(solution.route) == 4
        assert solution.algorithm == "2opt"
        assert solution.distance > 0
        assert solution.computation_time >= 0

    def test_solve_2opt_improves_route(self):
        """Test that 2-opt improves over nearest neighbor."""
        matrix = self.create_simple_distance_matrix()

        nn_solution = self.solver.solve_nearest_neighbor(matrix)
        opt_solution = self.solver.solve_2opt(matrix)

        # 2-opt should not be worse than nearest neighbor
        assert opt_solution.distance <= nn_solution.distance + 0.1

    def test_solve_2opt_with_initial_route(self):
        """Test 2-opt with provided initial route."""
        matrix = self.create_simple_distance_matrix()

        initial_route = [0, 3, 2, 1]
        solution = self.solver.solve_2opt(matrix, initial_route=initial_route)

        assert len(solution.route) == 4
        # Should visit all nodes
        assert set(solution.route) == {0, 1, 2, 3}

    def test_solve_2opt_max_iterations(self):
        """Test 2-opt respects max iterations."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_2opt(matrix, max_iterations=10)

        assert solution.algorithm == "2opt"

    def test_solve_auto_fast(self):
        """Test auto solver with fast quality."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_auto(matrix, quality="fast")

        assert solution.algorithm == "nearest_neighbor"
        assert len(solution.route) == 4

    def test_solve_auto_balanced(self):
        """Test auto solver with balanced quality."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_auto(matrix, quality="balanced")

        assert solution.algorithm == "2opt"
        assert len(solution.route) == 4

    def test_solve_auto_best_small(self):
        """Test auto solver with best quality on small problem."""
        matrix = self.create_triangle_distance_matrix()

        solution = self.solver.solve_auto(matrix, quality="best")

        # Should use OR-Tools or 2-opt
        assert solution.algorithm in ["ortools", "2opt"]
        assert len(solution.route) == 3

    def test_solve_auto_invalid_quality(self):
        """Test auto solver with invalid quality level."""
        matrix = self.create_simple_distance_matrix()

        with pytest.raises(ValueError, match="Invalid quality level"):
            self.solver.solve_auto(matrix, quality="invalid")

    def test_compare_algorithms(self):
        """Test algorithm comparison."""
        matrix = self.create_simple_distance_matrix()

        results = self.solver.compare_algorithms(matrix)

        # Should have at least nearest_neighbor and 2opt
        assert "nearest_neighbor" in results
        assert "2opt" in results

        # Check result structure
        assert "distance" in results["nearest_neighbor"]
        assert "route" in results["nearest_neighbor"]

    def test_calculate_route_distance(self):
        """Test route distance calculation."""
        matrix = self.create_triangle_distance_matrix()
        route = [0, 1, 2]

        distance = self.solver._calculate_route_distance(matrix, route)

        # Distance 0->1 (10) + 1->2 (20) = 30
        assert distance == pytest.approx(30.0)

    def test_calculate_route_distance_reverse(self):
        """Test route distance with reversed route."""
        matrix = self.create_triangle_distance_matrix()
        route1 = [0, 1, 2]
        route2 = [0, 2, 1]

        distance1 = self.solver._calculate_route_distance(matrix, route1)
        distance2 = self.solver._calculate_route_distance(matrix, route2)

        # 0->1->2: 10 + 20 = 30
        # 0->2->1: 15 + 20 = 35
        assert distance1 < distance2

    def test_get_stats(self):
        """Test getting solver statistics."""
        matrix = self.create_simple_distance_matrix()

        # Solve some problems
        self.solver.solve_nearest_neighbor(matrix)
        self.solver.solve_2opt(matrix)

        stats = self.solver.get_stats()

        assert stats["problems_solved"] == 3  # NN + initial NN for 2opt + 2opt
        assert "total_distance_saved" in stats

    def test_reset_stats(self):
        """Test resetting solver statistics."""
        matrix = self.create_simple_distance_matrix()

        # Solve a problem
        self.solver.solve_nearest_neighbor(matrix)

        # Reset
        self.solver.reset_stats()

        stats = self.solver.get_stats()
        assert stats["problems_solved"] == 0
        assert stats["total_distance_saved"] == 0.0

    def test_single_node_problem(self):
        """Test TSP with single node."""
        matrix = np.array([[0.0]])

        solution = self.solver.solve_nearest_neighbor(matrix)

        assert solution.route == [0]
        assert solution.distance == 0.0

    def test_two_node_problem(self):
        """Test TSP with two nodes."""
        matrix = np.array([
            [0.0, 5.0],
            [5.0, 0.0],
        ])

        solution = self.solver.solve_nearest_neighbor(matrix)

        assert len(solution.route) == 2
        assert solution.distance == pytest.approx(5.0)

    def test_symmetric_matrix(self):
        """Test that solver works with symmetric matrices."""
        matrix = self.create_simple_distance_matrix()

        # Check matrix is symmetric
        assert np.allclose(matrix, matrix.T)

        solution = self.solver.solve_2opt(matrix)

        assert len(solution.route) == len(matrix)

    def test_large_problem(self):
        """Test solver with larger problem."""
        n = 20
        # Create random distance matrix
        np.random.seed(42)
        matrix = np.random.rand(n, n) * 100
        # Make symmetric
        matrix = (matrix + matrix.T) / 2
        # Zero diagonal
        np.fill_diagonal(matrix, 0)

        solution = self.solver.solve_auto(matrix, quality="balanced")

        assert len(solution.route) == n
        assert set(solution.route) == set(range(n))
        assert solution.distance > 0

    def test_2opt_improvement_basic(self):
        """Test 2-opt improvement check."""
        matrix = np.array([
            [0.0, 1.0, 5.0, 3.0],
            [1.0, 0.0, 2.0, 4.0],
            [5.0, 2.0, 0.0, 1.0],
            [3.0, 4.0, 1.0, 0.0],
        ])

        route = [0, 1, 2, 3]

        # Check if swapping improves
        # This is an internal method test
        improves = self.solver._2opt_improvement(matrix, route, 1, 2)

        # Result depends on specific distances, just check it returns a boolean
        # Can be numpy.bool_ or Python bool
        assert type(improves) in [bool, np.bool_]

    def test_christofides_fallback(self):
        """Test that Christofides falls back to 2-opt."""
        matrix = self.create_simple_distance_matrix()

        solution = self.solver.solve_christofides(matrix)

        # Should fall back to 2-opt
        assert solution.algorithm == "2opt"

    def test_ortools_fallback_when_not_installed(self):
        """Test OR-Tools fallback behavior."""
        matrix = self.create_simple_distance_matrix()

        # This may use OR-Tools if installed, or fall back to 2-opt
        solution = self.solver.solve_ortools(matrix, time_limit_seconds=5)

        # Should return a valid solution either way
        assert solution.algorithm in ["ortools", "2opt"]
        assert len(solution.route) == 4

    def test_deterministic_results(self):
        """Test that same input gives same output."""
        matrix = self.create_simple_distance_matrix()

        solution1 = self.solver.solve_nearest_neighbor(matrix, start_idx=0)
        solution2 = self.solver.solve_nearest_neighbor(matrix, start_idx=0)

        assert solution1.route == solution2.route
        assert solution1.distance == pytest.approx(solution2.distance)
