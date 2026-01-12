"""Distance calculations for restaurant routing.

This module provides efficient distance matrix calculations using
the Haversine formula for great-circle distances.
"""

from typing import Dict, List, Tuple
import numpy as np
from math import radians, sin, cos, sqrt, atan2

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.utils.logging import get_logger, log_performance


class DistanceCalculator:
    """Calculates distances between restaurants efficiently.

    Uses Haversine formula for great-circle distances on Earth.
    Optimized for calculating distance matrices for large datasets.

    Example:
        >>> calculator = DistanceCalculator()
        >>> distance_km = calculator.calculate_distance(restaurant1, restaurant2)
        >>> matrix = calculator.calculate_distance_matrix(restaurants)
    """

    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    def __init__(self):
        """Initialize distance calculator."""
        self.logger = get_logger(__name__)

        # Statistics
        self.calculation_stats = {
            "total_calculations": 0,
            "matrix_calculations": 0,
        }

    def calculate_distance(
        self,
        restaurant1: Restaurant,
        restaurant2: Restaurant,
    ) -> float:
        """Calculate distance between two restaurants using Haversine formula.

        Args:
            restaurant1: First restaurant
            restaurant2: Second restaurant

        Returns:
            Distance in kilometers

        Example:
            >>> distance = calculator.calculate_distance(r1, r2)
            >>> print(f"Distance: {distance:.2f} km")
        """
        self.calculation_stats["total_calculations"] += 1

        return self._haversine(
            restaurant1.coordinates.latitude,
            restaurant1.coordinates.longitude,
            restaurant2.coordinates.latitude,
            restaurant2.coordinates.longitude,
        )

    def _haversine(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate Haversine distance between two coordinates.

        Args:
            lat1: Latitude of first point (degrees)
            lon1: Longitude of first point (degrees)
            lat2: Latitude of second point (degrees)
            lon2: Longitude of second point (degrees)

        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = self.EARTH_RADIUS_KM * c

        return distance

    @log_performance
    def calculate_distance_matrix(
        self,
        restaurants: List[Restaurant],
    ) -> np.ndarray:
        """Calculate distance matrix for all restaurant pairs.

        Creates an N×N matrix where element [i,j] is the distance
        from restaurant i to restaurant j in kilometers.

        Args:
            restaurants: List of restaurants

        Returns:
            NxN numpy array of distances (km)

        Example:
            >>> matrix = calculator.calculate_distance_matrix(restaurants)
            >>> # Distance from restaurant 0 to restaurant 5
            >>> distance = matrix[0, 5]
        """
        self.calculation_stats["matrix_calculations"] += 1

        n = len(restaurants)
        self.logger.info(f"Calculating distance matrix for {n} restaurants")

        # Initialize matrix
        matrix = np.zeros((n, n))

        # Extract coordinates into numpy arrays for vectorized operations
        lats = np.array([r.coordinates.latitude for r in restaurants])
        lons = np.array([r.coordinates.longitude for r in restaurants])

        # Convert to radians
        lats_rad = np.radians(lats)
        lons_rad = np.radians(lons)

        # Calculate distance matrix using vectorized operations
        for i in range(n):
            # Calculate distances from restaurant i to all others
            dlat = lats_rad - lats_rad[i]
            dlon = lons_rad - lons_rad[i]

            a = (
                np.sin(dlat / 2) ** 2
                + np.cos(lats_rad[i])
                * np.cos(lats_rad)
                * np.sin(dlon / 2) ** 2
            )
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

            matrix[i, :] = self.EARTH_RADIUS_KM * c

        self.logger.info(
            f"Distance matrix calculated: {n}×{n} = {n*n} distances"
        )

        return matrix

    def find_nearest_neighbors(
        self,
        restaurant: Restaurant,
        candidates: List[Restaurant],
        k: int = 5,
    ) -> List[Tuple[Restaurant, float]]:
        """Find k nearest restaurants to a given restaurant.

        Args:
            restaurant: Target restaurant
            candidates: List of candidate restaurants
            k: Number of neighbors to return

        Returns:
            List of (restaurant, distance) tuples, sorted by distance

        Example:
            >>> neighbors = calculator.find_nearest_neighbors(restaurant, all_restaurants, k=5)
            >>> for neighbor, distance in neighbors:
            ...     print(f"{neighbor.name}: {distance:.2f} km")
        """
        # Calculate distances to all candidates
        distances = []
        for candidate in candidates:
            if candidate.place_id != restaurant.place_id:
                distance = self.calculate_distance(restaurant, candidate)
                distances.append((candidate, distance))

        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]

    def calculate_total_distance(
        self,
        route: List[Restaurant],
    ) -> float:
        """Calculate total distance for a route.

        Args:
            route: Ordered list of restaurants in route

        Returns:
            Total distance in kilometers

        Example:
            >>> route = [r1, r2, r3, r4]
            >>> total_km = calculator.calculate_total_distance(route)
        """
        if len(route) < 2:
            return 0.0

        total = 0.0
        for i in range(len(route) - 1):
            total += self.calculate_distance(route[i], route[i + 1])

        return total

    def calculate_cluster_diameter(
        self,
        restaurants: List[Restaurant],
    ) -> float:
        """Calculate maximum distance within a cluster (diameter).

        Args:
            restaurants: Restaurants in cluster

        Returns:
            Maximum pairwise distance in kilometers

        Example:
            >>> diameter = calculator.calculate_cluster_diameter(cluster)
            >>> print(f"Cluster diameter: {diameter:.2f} km")
        """
        if len(restaurants) < 2:
            return 0.0

        max_distance = 0.0
        for i, r1 in enumerate(restaurants):
            for r2 in restaurants[i + 1 :]:
                distance = self.calculate_distance(r1, r2)
                max_distance = max(max_distance, distance)

        return max_distance

    def calculate_cluster_centroid(
        self,
        restaurants: List[Restaurant],
    ) -> Tuple[float, float]:
        """Calculate geographic centroid of a cluster.

        Args:
            restaurants: Restaurants in cluster

        Returns:
            Tuple of (latitude, longitude)

        Example:
            >>> lat, lng = calculator.calculate_cluster_centroid(cluster)
            >>> print(f"Cluster center: ({lat:.4f}, {lng:.4f})")
        """
        if not restaurants:
            return (0.0, 0.0)

        avg_lat = sum(r.coordinates.latitude for r in restaurants) / len(restaurants)
        avg_lng = sum(r.coordinates.longitude for r in restaurants) / len(restaurants)

        return (avg_lat, avg_lng)

    def get_stats(self) -> Dict[str, int]:
        """Get calculation statistics.

        Returns:
            Dictionary with calculation statistics
        """
        return self.calculation_stats.copy()

    def reset_stats(self) -> None:
        """Reset calculation statistics."""
        self.calculation_stats = {
            "total_calculations": 0,
            "matrix_calculations": 0,
        }
