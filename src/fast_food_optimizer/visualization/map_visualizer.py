"""Interactive map visualization using Folium.

This module provides tools for visualizing restaurants, clusters, and routes
on interactive maps using the Folium library.
"""

from typing import Dict, List, Optional, Tuple
import folium
from folium import plugins

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.optimization.global_optimizer import GlobalRoute


class MapVisualizer:
    """Creates interactive maps for restaurant routes using Folium.

    This class provides methods to visualize:
    - Individual restaurants with detailed popups
    - Restaurant clusters with color-coding
    - Optimized routes with path overlays
    - Multiple alternative routes

    Maps are mobile-responsive and can be saved as HTML files.

    Example:
        >>> visualizer = MapVisualizer()
        >>> map_obj = visualizer.visualize_clusters(
        ...     clusters,
        ...     center=(40.7589, -111.8883),
        ...     zoom_start=12
        ... )
        >>> visualizer.save_map(map_obj, "clusters.html")
    """

    # Color palette for clusters (ColorBrewer qualitative palette)
    CLUSTER_COLORS = [
        "#e41a1c",  # Red
        "#377eb8",  # Blue
        "#4daf4a",  # Green
        "#984ea3",  # Purple
        "#ff7f00",  # Orange
        "#ffff33",  # Yellow
        "#a65628",  # Brown
        "#f781bf",  # Pink
        "#999999",  # Gray
        "#66c2a5",  # Teal
        "#fc8d62",  # Coral
        "#8da0cb",  # Lavender
    ]

    # Route color palette for alternative routes
    ROUTE_COLORS = [
        "#2c7bb6",  # Blue
        "#d7191c",  # Red
        "#fdae61",  # Orange
        "#abd9e9",  # Light blue
        "#ffffbf",  # Light yellow
    ]

    def __init__(self):
        """Initialize the map visualizer."""
        self.stats = {
            "maps_created": 0,
            "restaurants_visualized": 0,
            "routes_visualized": 0,
        }

    def create_base_map(
        self,
        center: Tuple[float, float],
        zoom_start: int = 12,
        tiles: str = "OpenStreetMap",
    ) -> folium.Map:
        """Create a base Folium map.

        Args:
            center: Tuple of (latitude, longitude) for map center
            zoom_start: Initial zoom level (1-18, default 12)
            tiles: Tile style - "OpenStreetMap", "Stamen Terrain", etc.

        Returns:
            folium.Map: Base map object
        """
        map_obj = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles=tiles,
        )

        # Add fullscreen button
        plugins.Fullscreen(
            position="topright",
            title="Fullscreen",
            title_cancel="Exit fullscreen",
        ).add_to(map_obj)

        self.stats["maps_created"] += 1

        return map_obj

    def add_restaurant_marker(
        self,
        map_obj: folium.Map,
        restaurant: Restaurant,
        color: str = "blue",
        icon: str = "cutlery",
        cluster_id: Optional[int] = None,
    ) -> None:
        """Add a restaurant marker to the map.

        Args:
            map_obj: Folium map object
            restaurant: Restaurant to add
            color: Marker color (blue, red, green, etc.)
            icon: Font Awesome icon name
            cluster_id: Optional cluster ID to display
        """
        # Create popup HTML
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">{restaurant.name}</h4>
            <p style="margin: 5px 0;"><strong>Address:</strong><br>{restaurant.address}</p>
        """

        if restaurant.rating:
            popup_html += f'<p style="margin: 5px 0;"><strong>Rating:</strong> {restaurant.rating}/5</p>'

        if cluster_id is not None:
            popup_html += f'<p style="margin: 5px 0;"><strong>Cluster:</strong> {cluster_id}</p>'

        if restaurant.confidence_score:
            popup_html += f'<p style="margin: 5px 0;"><strong>Confidence:</strong> {restaurant.confidence_score:.1%}</p>'

        popup_html += f'<p style="margin: 5px 0; font-size: 10px; color: #666;"><strong>ID:</strong> {restaurant.place_id[:20]}...</p>'
        popup_html += "</div>"

        # Create marker
        folium.Marker(
            location=(restaurant.coordinates.latitude, restaurant.coordinates.longitude),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=restaurant.name,
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(map_obj)

        self.stats["restaurants_visualized"] += 1

    def visualize_restaurants(
        self,
        restaurants: List[Restaurant],
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 12,
    ) -> folium.Map:
        """Create a map visualizing a list of restaurants.

        Args:
            restaurants: List of restaurants to visualize
            center: Optional map center (auto-calculated if not provided)
            zoom_start: Initial zoom level

        Returns:
            folium.Map: Map with restaurant markers
        """
        if not restaurants:
            raise ValueError("No restaurants provided")

        # Calculate center if not provided
        if center is None:
            avg_lat = sum(r.coordinates.latitude for r in restaurants) / len(restaurants)
            avg_lng = sum(r.coordinates.longitude for r in restaurants) / len(restaurants)
            center = (avg_lat, avg_lng)

        # Create base map
        map_obj = self.create_base_map(center, zoom_start)

        # Add restaurants
        for restaurant in restaurants:
            self.add_restaurant_marker(map_obj, restaurant)

        # Add marker cluster for better performance with many markers
        if len(restaurants) > 50:
            marker_cluster = plugins.MarkerCluster()
            for restaurant in restaurants:
                folium.Marker(
                    location=(restaurant.coordinates.latitude, restaurant.coordinates.longitude),
                    popup=restaurant.name,
                    tooltip=restaurant.name,
                ).add_to(marker_cluster)
            marker_cluster.add_to(map_obj)

        return map_obj

    def visualize_clusters(
        self,
        clusters: Dict[int, List[Restaurant]],
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 11,
        show_noise: bool = False,
    ) -> folium.Map:
        """Create a map visualizing restaurant clusters.

        Each cluster is color-coded, and markers show cluster membership.

        Args:
            clusters: Dictionary mapping cluster_id to list of restaurants
            center: Optional map center (auto-calculated if not provided)
            zoom_start: Initial zoom level
            show_noise: Whether to show noise points (cluster -1)

        Returns:
            folium.Map: Map with color-coded cluster markers
        """
        if not clusters:
            raise ValueError("No clusters provided")

        # Filter out noise if requested
        valid_clusters = {
            cid: rests for cid, rests in clusters.items()
            if show_noise or cid != -1
        }

        if not valid_clusters:
            raise ValueError("No valid clusters to visualize")

        # Calculate center if not provided
        if center is None:
            all_restaurants = [r for rests in valid_clusters.values() for r in rests]
            avg_lat = sum(r.coordinates.latitude for r in all_restaurants) / len(all_restaurants)
            avg_lng = sum(r.coordinates.longitude for r in all_restaurants) / len(all_restaurants)
            center = (avg_lat, avg_lng)

        # Create base map
        map_obj = self.create_base_map(center, zoom_start)

        # Create feature groups for each cluster
        feature_groups = {}

        # Add clusters
        for cluster_id, restaurants in valid_clusters.items():
            if cluster_id == -1:
                color = "gray"
                cluster_name = "Noise"
            else:
                color = self._get_cluster_color(cluster_id)
                cluster_name = f"Cluster {cluster_id}"

            # Create feature group for this cluster
            feature_group = folium.FeatureGroup(name=f"{cluster_name} ({len(restaurants)} restaurants)")

            # Add restaurants to cluster
            for restaurant in restaurants:
                self.add_restaurant_marker(
                    feature_group,
                    restaurant,
                    color=color,
                    cluster_id=cluster_id,
                )

            feature_group.add_to(map_obj)
            feature_groups[cluster_id] = feature_group

        # Add layer control
        folium.LayerControl(position="topright").add_to(map_obj)

        # Add legend
        self._add_cluster_legend(map_obj, valid_clusters)

        return map_obj

    def visualize_route(
        self,
        route: GlobalRoute,
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 11,
        show_route_lines: bool = True,
    ) -> folium.Map:
        """Create a map visualizing an optimized route.

        Shows restaurants in visit order with route overlay lines.

        Args:
            route: GlobalRoute object to visualize
            center: Optional map center (uses route start if not provided)
            zoom_start: Initial zoom level
            show_route_lines: Whether to show route path lines

        Returns:
            folium.Map: Map with route visualization
        """
        if route.total_restaurants == 0:
            raise ValueError("Route has no restaurants")

        # Get center
        if center is None:
            if route.start_location:
                center = route.start_location
            else:
                # Use first restaurant
                all_restaurants = route.get_all_restaurants()
                center = (
                    all_restaurants[0].coordinates.latitude,
                    all_restaurants[0].coordinates.longitude,
                )

        # Create base map
        map_obj = self.create_base_map(center, zoom_start)

        # Add start marker
        if route.start_location:
            folium.Marker(
                location=route.start_location,
                popup="<b>Start Location</b>",
                tooltip="Start",
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
            ).add_to(map_obj)

        # Add end marker
        if route.end_location:
            folium.Marker(
                location=route.end_location,
                popup="<b>End Location</b>",
                tooltip="End",
                icon=folium.Icon(color="red", icon="stop", prefix="fa"),
            ).add_to(map_obj)

        # Add route overlay
        if show_route_lines:
            self.add_route_overlay(map_obj, route, color="#2c7bb6", weight=3, opacity=0.7)

        # Add restaurants with numbering
        all_restaurants = route.get_all_restaurants()
        for i, restaurant in enumerate(all_restaurants, 1):
            # Determine cluster color
            cluster_id = None
            for cid, cluster_route in route.cluster_routes.items():
                if restaurant in cluster_route.restaurants:
                    cluster_id = cid
                    break

            color = self._get_cluster_color(cluster_id) if cluster_id is not None else "blue"

            # Create numbered marker
            folium.Marker(
                location=(restaurant.coordinates.latitude, restaurant.coordinates.longitude),
                popup=self._create_route_popup(restaurant, i, route.total_restaurants),
                tooltip=f"{i}. {restaurant.name}",
                icon=folium.Icon(color=color, icon="info-sign"),
            ).add_to(map_obj)

        # Add route info panel
        self._add_route_info_panel(map_obj, route)

        self.stats["routes_visualized"] += 1

        return map_obj

    def visualize_alternative_routes(
        self,
        routes: List[GlobalRoute],
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 11,
    ) -> folium.Map:
        """Create a map comparing multiple alternative routes.

        Args:
            routes: List of GlobalRoute objects
            center: Optional map center
            zoom_start: Initial zoom level

        Returns:
            folium.Map: Map with multiple route overlays
        """
        if not routes:
            raise ValueError("No routes provided")

        # Get center from first route
        if center is None:
            if routes[0].start_location:
                center = routes[0].start_location
            else:
                all_restaurants = routes[0].get_all_restaurants()
                center = (
                    all_restaurants[0].coordinates.latitude,
                    all_restaurants[0].coordinates.longitude,
                )

        # Create base map
        map_obj = self.create_base_map(center, zoom_start)

        # Add each route as a layer
        for i, route in enumerate(routes):
            color = self._get_route_color(i)
            route_name = f"Route {i+1} ({route.total_distance:.1f}km, {route.estimated_time_hours:.1f}h)"

            # Create feature group for this route
            feature_group = folium.FeatureGroup(name=route_name)

            # Add route overlay to feature group
            self.add_route_overlay(feature_group, route, color=color, weight=4, opacity=0.6)

            feature_group.add_to(map_obj)

        # Add layer control
        folium.LayerControl(position="topright").add_to(map_obj)

        # Add comparison legend
        self._add_routes_comparison_legend(map_obj, routes)

        return map_obj

    def add_route_overlay(
        self,
        map_obj: folium.Map,
        route: GlobalRoute,
        color: str = "#2c7bb6",
        weight: int = 3,
        opacity: float = 0.7,
    ) -> None:
        """Add route path overlay to a map.

        Args:
            map_obj: Folium map object
            route: GlobalRoute to overlay
            color: Line color (hex or name)
            weight: Line width in pixels
            opacity: Line opacity (0-1)
        """
        # Build path through all restaurants
        path_points = []

        # Add start location
        if route.start_location:
            path_points.append(route.start_location)

        # Add restaurants in order
        for cluster_id in route.cluster_sequence:
            if cluster_id in route.cluster_routes:
                cluster_route = route.cluster_routes[cluster_id]
                for restaurant in cluster_route.restaurants:
                    path_points.append((
                        restaurant.coordinates.latitude,
                        restaurant.coordinates.longitude,
                    ))

        # Add end location
        if route.end_location:
            path_points.append(route.end_location)

        # Draw polyline
        folium.PolyLine(
            locations=path_points,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=f"Route: {route.total_distance:.2f}km, {route.estimated_time_hours:.1f}h",
        ).add_to(map_obj)

    def save_map(self, map_obj: folium.Map, filepath: str) -> None:
        """Save a Folium map to an HTML file.

        Args:
            filepath: Output file path (should end in .html)
        """
        map_obj.save(filepath)

    def get_stats(self) -> dict:
        """Get visualization statistics.

        Returns:
            dict: Statistics about maps created and visualized
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset visualization statistics."""
        self.stats = {
            "maps_created": 0,
            "restaurants_visualized": 0,
            "routes_visualized": 0,
        }

    # Private helper methods

    def _get_cluster_color(self, cluster_id: int) -> str:
        """Get color for a cluster ID."""
        if cluster_id == -1:
            return "gray"
        return self.CLUSTER_COLORS[cluster_id % len(self.CLUSTER_COLORS)]

    def _get_route_color(self, route_index: int) -> str:
        """Get color for a route index."""
        return self.ROUTE_COLORS[route_index % len(self.ROUTE_COLORS)]

    def _create_route_popup(
        self,
        restaurant: Restaurant,
        position: int,
        total: int,
    ) -> str:
        """Create popup HTML for a restaurant in a route."""
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">Stop {position}/{total}</h4>
            <h5 style="margin: 0 0 10px 0; color: #555;">{restaurant.name}</h5>
            <p style="margin: 5px 0;"><strong>Address:</strong><br>{restaurant.address}</p>
        """

        if restaurant.rating:
            popup_html += f'<p style="margin: 5px 0;"><strong>Rating:</strong> {restaurant.rating}/5</p>'

        popup_html += "</div>"

        return popup_html

    def _add_cluster_legend(
        self,
        map_obj: folium.Map,
        clusters: Dict[int, List[Restaurant]],
    ) -> None:
        """Add a legend showing cluster colors."""
        legend_html = """
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            width: 200px;
            background-color: white;
            border: 2px solid grey;
            z-index: 9999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        ">
        <h4 style="margin: 0 0 10px 0;">Clusters</h4>
        """

        for cluster_id in sorted(clusters.keys()):
            if cluster_id == -1:
                continue
            color = self._get_cluster_color(cluster_id)
            count = len(clusters[cluster_id])
            legend_html += f"""
            <p style="margin: 5px 0;">
                <i class="fa fa-circle" style="color:{color}"></i>
                Cluster {cluster_id}: {count} restaurants
            </p>
            """

        legend_html += "</div>"

        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_route_info_panel(
        self,
        map_obj: folium.Map,
        route: GlobalRoute,
    ) -> None:
        """Add an information panel showing route statistics."""
        info_html = f"""
        <div style="
            position: fixed;
            top: 80px;
            left: 50px;
            width: 250px;
            background-color: white;
            border: 2px solid grey;
            z-index: 9999;
            font-size: 14px;
            padding: 15px;
            border-radius: 5px;
        ">
        <h4 style="margin: 0 0 10px 0; color: #333;">Route Information</h4>
        <p style="margin: 5px 0;"><strong>Total Restaurants:</strong> {route.total_restaurants}</p>
        <p style="margin: 5px 0;"><strong>Total Distance:</strong> {route.total_distance:.2f} km</p>
        <p style="margin: 5px 0;"><strong>Estimated Time:</strong> {route.estimated_time_hours:.1f} hours</p>
        <p style="margin: 5px 0;"><strong>Clusters:</strong> {len(route.cluster_sequence)}</p>
        """

        if route.estimated_time_hours > 0:
            efficiency = route.total_restaurants / route.estimated_time_hours
            info_html += f'<p style="margin: 5px 0;"><strong>Efficiency:</strong> {efficiency:.1f} rest/hour</p>'

        info_html += "</div>"

        map_obj.get_root().html.add_child(folium.Element(info_html))

    def _add_routes_comparison_legend(
        self,
        map_obj: folium.Map,
        routes: List[GlobalRoute],
    ) -> None:
        """Add a legend comparing multiple routes."""
        legend_html = """
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            width: 300px;
            background-color: white;
            border: 2px solid grey;
            z-index: 9999;
            font-size: 14px;
            padding: 15px;
            border-radius: 5px;
        ">
        <h4 style="margin: 0 0 10px 0;">Route Comparison</h4>
        """

        for i, route in enumerate(routes):
            color = self._get_route_color(i)
            legend_html += f"""
            <p style="margin: 5px 0;">
                <i class="fa fa-minus" style="color:{color}; font-weight: bold;"></i>
                <strong>Route {i+1}:</strong> {route.total_distance:.1f}km,
                {route.estimated_time_hours:.1f}h, {route.total_restaurants} restaurants
            </p>
            """

        legend_html += "</div>"

        map_obj.get_root().html.add_child(folium.Element(legend_html))
