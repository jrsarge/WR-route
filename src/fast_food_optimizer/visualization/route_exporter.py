"""Route export functionality for multiple formats.

This module provides tools for exporting optimized routes to various formats:
- GPX: GPS Exchange Format for GPS devices (Garmin, phone apps)
- CSV: Comma-separated values for spreadsheet analysis
- KML: Keyhole Markup Language for Google Earth
- JSON: JavaScript Object Notation for mobile apps and APIs
"""

import json
import csv
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from fast_food_optimizer.models.restaurant import Restaurant
from fast_food_optimizer.optimization.global_optimizer import GlobalRoute


class RouteExporter:
    """Export optimized routes to multiple file formats.

    This class provides methods to export GlobalRoute objects to:
    - GPX files for GPS navigation
    - CSV files for spreadsheet analysis
    - KML files for Google Earth visualization
    - JSON files for mobile apps and APIs

    All exports include complete route information including:
    - Restaurant details (name, address, coordinates)
    - Route sequence and ordering
    - Distance and time estimates
    - Metadata (creation date, statistics)

    Example:
        >>> exporter = RouteExporter()
        >>>
        >>> # Export to GPX for GPS device
        >>> exporter.export_to_gpx(route, "route.gpx", route_name="SLC Fast Food Tour")
        >>>
        >>> # Export to CSV for analysis
        >>> exporter.export_to_csv(route, "route.csv")
        >>>
        >>> # Export to KML for Google Earth
        >>> exporter.export_to_kml(route, "route.kml")
        >>>
        >>> # Export to JSON for mobile app
        >>> exporter.export_to_json(route, "route.json")
    """

    def __init__(self):
        """Initialize the route exporter."""
        self.stats = {
            "gpx_exports": 0,
            "csv_exports": 0,
            "kml_exports": 0,
            "json_exports": 0,
        }

    def export_to_gpx(
        self,
        route: GlobalRoute,
        filepath: str,
        route_name: str = "Fast Food Route",
        description: Optional[str] = None,
    ) -> None:
        """Export route to GPX format for GPS devices.

        GPX (GPS Exchange Format) is the standard format for GPS devices.
        Works with Garmin, phone apps (Google Maps, Apple Maps), and more.

        The GPX file includes:
        - Route waypoints for each restaurant
        - Route track showing the path
        - Metadata (name, description, creation time)

        Args:
            route: GlobalRoute object to export
            filepath: Output file path (should end in .gpx)
            route_name: Name for the route
            description: Optional route description

        Raises:
            ValueError: If route has no restaurants
        """
        if route.total_restaurants == 0:
            raise ValueError("Cannot export empty route")

        # Get all restaurants in order
        restaurants = route.get_all_restaurants()

        # Generate description if not provided
        if description is None:
            description = (
                f"{route.total_restaurants} restaurants, "
                f"{route.total_distance:.2f}km, "
                f"{route.estimated_time_hours:.1f}h"
            )

        # Build GPX XML
        gpx_content = self._build_gpx_content(
            restaurants,
            route,
            route_name,
            description,
        )

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(gpx_content)

        self.stats["gpx_exports"] += 1

    def export_to_csv(
        self,
        route: GlobalRoute,
        filepath: str,
        include_cluster_info: bool = True,
    ) -> None:
        """Export route to CSV format for spreadsheet analysis.

        CSV format is ideal for:
        - Excel/Google Sheets analysis
        - Data processing and filtering
        - Creating custom reports

        The CSV includes columns:
        - Stop Number
        - Restaurant Name
        - Address
        - Latitude
        - Longitude
        - Rating
        - Cluster ID (optional)
        - Estimated Cumulative Distance
        - Estimated Cumulative Time

        Args:
            route: GlobalRoute object to export
            filepath: Output file path (should end in .csv)
            include_cluster_info: Whether to include cluster information

        Raises:
            ValueError: If route has no restaurants
        """
        if route.total_restaurants == 0:
            raise ValueError("Cannot export empty route")

        # Get all restaurants in order
        restaurants = route.get_all_restaurants()

        # Open CSV file
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            # Define columns
            fieldnames = [
                "stop_number",
                "name",
                "address",
                "latitude",
                "longitude",
                "rating",
            ]

            if include_cluster_info:
                fieldnames.append("cluster_id")

            fieldnames.extend([
                "cumulative_distance_km",
                "cumulative_time_hours",
            ])

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Calculate cumulative metrics
            cumulative_distance = 0.0
            cumulative_time = 0.0

            # Time per restaurant (3 minutes)
            time_per_restaurant = 3 / 60  # hours

            # Write each restaurant
            for i, restaurant in enumerate(restaurants, 1):
                # Find cluster ID
                cluster_id = None
                if include_cluster_info:
                    for cid, cluster_route in route.cluster_routes.items():
                        if restaurant in cluster_route.restaurants:
                            cluster_id = cid
                            break

                # Estimate cumulative metrics
                # (simplified - actual distances would require calculation)
                cumulative_distance = (route.total_distance / route.total_restaurants) * i
                cumulative_time = time_per_restaurant * i

                # Build row
                row = {
                    "stop_number": i,
                    "name": restaurant.name,
                    "address": restaurant.address,
                    "latitude": restaurant.coordinates.latitude,
                    "longitude": restaurant.coordinates.longitude,
                    "rating": restaurant.rating if restaurant.rating else "",
                }

                if include_cluster_info:
                    row["cluster_id"] = cluster_id if cluster_id is not None else ""

                row.update({
                    "cumulative_distance_km": f"{cumulative_distance:.2f}",
                    "cumulative_time_hours": f"{cumulative_time:.2f}",
                })

                writer.writerow(row)

        self.stats["csv_exports"] += 1

    def export_to_kml(
        self,
        route: GlobalRoute,
        filepath: str,
        route_name: str = "Fast Food Route",
        description: Optional[str] = None,
        include_path: bool = True,
    ) -> None:
        """Export route to KML format for Google Earth.

        KML (Keyhole Markup Language) is used by Google Earth and Google Maps.
        Provides rich 3D visualization with placemarks and paths.

        The KML file includes:
        - Placemarks for each restaurant
        - Optional path line showing the route
        - Custom styling with numbered icons
        - Restaurant details in descriptions

        Args:
            route: GlobalRoute object to export
            filepath: Output file path (should end in .kml)
            route_name: Name for the route
            description: Optional route description
            include_path: Whether to include route path line

        Raises:
            ValueError: If route has no restaurants
        """
        if route.total_restaurants == 0:
            raise ValueError("Cannot export empty route")

        # Get all restaurants in order
        restaurants = route.get_all_restaurants()

        # Generate description if not provided
        if description is None:
            description = (
                f"{route.total_restaurants} restaurants, "
                f"{route.total_distance:.2f}km, "
                f"{route.estimated_time_hours:.1f}h"
            )

        # Build KML XML
        kml_content = self._build_kml_content(
            restaurants,
            route,
            route_name,
            description,
            include_path,
        )

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(kml_content)

        self.stats["kml_exports"] += 1

    def export_to_json(
        self,
        route: GlobalRoute,
        filepath: str,
        include_metadata: bool = True,
        pretty_print: bool = True,
    ) -> None:
        """Export route to JSON format for mobile apps and APIs.

        JSON format is ideal for:
        - Mobile app integration
        - Web API consumption
        - JavaScript applications
        - Programmatic processing

        The JSON includes:
        - Complete route structure
        - Restaurant details
        - Route metadata
        - Sequence information

        Args:
            route: GlobalRoute object to export
            filepath: Output file path (should end in .json)
            include_metadata: Whether to include metadata (timestamps, stats)
            pretty_print: Whether to format JSON with indentation

        Raises:
            ValueError: If route has no restaurants
        """
        if route.total_restaurants == 0:
            raise ValueError("Cannot export empty route")

        # Build JSON structure
        data = {
            "route": route.to_dict(),
            "restaurants": [
                self._restaurant_to_dict(r)
                for r in route.get_all_restaurants()
            ],
        }

        # Add metadata if requested
        if include_metadata:
            data["metadata"] = {
                "export_date": datetime.now().isoformat(),
                "total_restaurants": route.total_restaurants,
                "total_distance_km": route.total_distance,
                "estimated_time_hours": route.estimated_time_hours,
                "num_clusters": len(route.cluster_sequence),
            }

            if route.start_location:
                data["metadata"]["start_location"] = {
                    "latitude": route.start_location[0],
                    "longitude": route.start_location[1],
                }

            if route.end_location:
                data["metadata"]["end_location"] = {
                    "latitude": route.end_location[0],
                    "longitude": route.end_location[1],
                }

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            if pretty_print:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

        self.stats["json_exports"] += 1

    def export_all_formats(
        self,
        route: GlobalRoute,
        output_dir: str,
        base_filename: str = "route",
        route_name: str = "Fast Food Route",
    ) -> Dict[str, str]:
        """Export route to all supported formats.

        Convenience method to export a route to GPX, CSV, KML, and JSON
        all at once with consistent naming.

        Args:
            route: GlobalRoute object to export
            output_dir: Directory to save files
            base_filename: Base name for files (without extension)
            route_name: Name for the route (used in GPX/KML)

        Returns:
            dict: Mapping of format name to filepath

        Example:
            >>> exporter = RouteExporter()
            >>> files = exporter.export_all_formats(
            ...     route,
            ...     output_dir="data/exports",
            ...     base_filename="slc_route",
            ...     route_name="Salt Lake City Fast Food Tour"
            ... )
            >>> print(files)
            {
                'gpx': 'data/exports/slc_route.gpx',
                'csv': 'data/exports/slc_route.csv',
                'kml': 'data/exports/slc_route.kml',
                'json': 'data/exports/slc_route.json'
            }
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Build file paths
        files = {
            "gpx": str(Path(output_dir) / f"{base_filename}.gpx"),
            "csv": str(Path(output_dir) / f"{base_filename}.csv"),
            "kml": str(Path(output_dir) / f"{base_filename}.kml"),
            "json": str(Path(output_dir) / f"{base_filename}.json"),
        }

        # Export to each format
        self.export_to_gpx(route, files["gpx"], route_name=route_name)
        self.export_to_csv(route, files["csv"])
        self.export_to_kml(route, files["kml"], route_name=route_name)
        self.export_to_json(route, files["json"])

        return files

    def get_stats(self) -> dict:
        """Get export statistics.

        Returns:
            dict: Statistics about exports performed
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset export statistics."""
        self.stats = {
            "gpx_exports": 0,
            "csv_exports": 0,
            "kml_exports": 0,
            "json_exports": 0,
        }

    # Private helper methods

    def _build_gpx_content(
        self,
        restaurants: List[Restaurant],
        route: GlobalRoute,
        route_name: str,
        description: str,
    ) -> str:
        """Build GPX XML content."""
        # GPX header
        gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gpx += '<gpx version="1.1" creator="Fast Food Route Optimizer"\n'
        gpx += '     xmlns="http://www.topografix.com/GPX/1/1"\n'
        gpx += '     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        gpx += '     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">\n'

        # Metadata
        gpx += "  <metadata>\n"
        gpx += f"    <name>{self._escape_xml(route_name)}</name>\n"
        gpx += f"    <desc>{self._escape_xml(description)}</desc>\n"
        gpx += f"    <time>{datetime.now().isoformat()}</time>\n"
        gpx += "  </metadata>\n"

        # Route waypoints
        gpx += f'  <rte>\n'
        gpx += f"    <name>{self._escape_xml(route_name)}</name>\n"

        for i, restaurant in enumerate(restaurants, 1):
            gpx += "    <rtept "
            gpx += f'lat="{restaurant.coordinates.latitude}" '
            gpx += f'lon="{restaurant.coordinates.longitude}">\n'
            gpx += f"      <name>{self._escape_xml(restaurant.name)}</name>\n"
            gpx += f"      <desc>Stop {i}/{len(restaurants)}: {self._escape_xml(restaurant.address)}</desc>\n"
            gpx += "    </rtept>\n"

        gpx += "  </rte>\n"

        # Track (for visualization)
        gpx += "  <trk>\n"
        gpx += f"    <name>{self._escape_xml(route_name)} - Path</name>\n"
        gpx += "    <trkseg>\n"

        # Add start location if provided
        if route.start_location:
            gpx += f'      <trkpt lat="{route.start_location[0]}" lon="{route.start_location[1]}"/>\n'

        # Add all restaurants
        for restaurant in restaurants:
            gpx += f'      <trkpt lat="{restaurant.coordinates.latitude}" '
            gpx += f'lon="{restaurant.coordinates.longitude}"/>\n'

        # Add end location if provided
        if route.end_location:
            gpx += f'      <trkpt lat="{route.end_location[0]}" lon="{route.end_location[1]}"/>\n'

        gpx += "    </trkseg>\n"
        gpx += "  </trk>\n"

        gpx += "</gpx>\n"

        return gpx

    def _build_kml_content(
        self,
        restaurants: List[Restaurant],
        route: GlobalRoute,
        route_name: str,
        description: str,
        include_path: bool,
    ) -> str:
        """Build KML XML content."""
        # KML header
        kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        kml += "  <Document>\n"
        kml += f"    <name>{self._escape_xml(route_name)}</name>\n"
        kml += f"    <description>{self._escape_xml(description)}</description>\n"

        # Style for restaurant markers
        kml += '    <Style id="restaurant">\n'
        kml += "      <IconStyle>\n"
        kml += "        <color>ff0000ff</color>\n"  # Red
        kml += "        <scale>1.0</scale>\n"
        kml += "        <Icon>\n"
        kml += "          <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>\n"
        kml += "        </Icon>\n"
        kml += "      </IconStyle>\n"
        kml += "    </Style>\n"

        # Style for route path
        if include_path:
            kml += '    <Style id="routePath">\n'
            kml += "      <LineStyle>\n"
            kml += "        <color>ff0000ff</color>\n"  # Red
            kml += "        <width>3</width>\n"
            kml += "      </LineStyle>\n"
            kml += "    </Style>\n"

        # Folder for restaurants
        kml += "    <Folder>\n"
        kml += "      <name>Restaurants</name>\n"

        # Add placemarks for each restaurant
        for i, restaurant in enumerate(restaurants, 1):
            kml += "      <Placemark>\n"
            kml += f"        <name>{i}. {self._escape_xml(restaurant.name)}</name>\n"

            desc = f"Stop {i}/{len(restaurants)}<br/>"
            desc += f"Address: {self._escape_xml(restaurant.address)}<br/>"
            if restaurant.rating:
                desc += f"Rating: {restaurant.rating}/5<br/>"

            kml += f"        <description><![CDATA[{desc}]]></description>\n"
            kml += '        <styleUrl>#restaurant</styleUrl>\n'
            kml += "        <Point>\n"
            kml += f"          <coordinates>{restaurant.coordinates.longitude},{restaurant.coordinates.latitude},0</coordinates>\n"
            kml += "        </Point>\n"
            kml += "      </Placemark>\n"

        kml += "    </Folder>\n"

        # Add route path if requested
        if include_path:
            kml += "    <Placemark>\n"
            kml += f"      <name>{self._escape_xml(route_name)} - Path</name>\n"
            kml += '      <styleUrl>#routePath</styleUrl>\n'
            kml += "      <LineString>\n"
            kml += "        <tessellate>1</tessellate>\n"
            kml += "        <coordinates>\n"

            # Add start location
            if route.start_location:
                kml += f"          {route.start_location[1]},{route.start_location[0]},0\n"

            # Add all restaurants
            for restaurant in restaurants:
                kml += f"          {restaurant.coordinates.longitude},{restaurant.coordinates.latitude},0\n"

            # Add end location
            if route.end_location:
                kml += f"          {route.end_location[1]},{route.end_location[0]},0\n"

            kml += "        </coordinates>\n"
            kml += "      </LineString>\n"
            kml += "    </Placemark>\n"

        kml += "  </Document>\n"
        kml += "</kml>\n"

        return kml

    def _restaurant_to_dict(self, restaurant: Restaurant) -> dict:
        """Convert restaurant to dictionary for JSON export."""
        return {
            "place_id": restaurant.place_id,
            "name": restaurant.name,
            "address": restaurant.address,
            "coordinates": {
                "latitude": restaurant.coordinates.latitude,
                "longitude": restaurant.coordinates.longitude,
            },
            "rating": restaurant.rating,
            "is_fast_food": restaurant.is_fast_food,
            "confidence_score": restaurant.confidence_score,
        }

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
