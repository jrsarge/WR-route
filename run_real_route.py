#!/usr/bin/env python3
"""Run the Fast Food Route Optimizer with real Google Maps data.

This script:
1. Collects real restaurant data from Google Maps API
2. Classifies and validates restaurants
3. Clusters restaurants geographically
4. Optimizes the complete route
5. Visualizes on interactive maps
6. Exports to GPS formats (GPX, CSV, KML, JSON)

Usage:
    python3 run_real_route.py

Requirements:
    - Google Maps API key in .env file
    - Target city coordinates configured below
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fast_food_optimizer.config.settings import get_config
from fast_food_optimizer.data.osm_client import OpenStreetMapClient
from fast_food_optimizer.data.classifier import FastFoodClassifier
from fast_food_optimizer.data.persistence import DataPersistence
from fast_food_optimizer.validation.validator import DataValidator
from fast_food_optimizer.optimization import (
    RestaurantClusterer,
    GlobalRouteOptimizer,
)
from fast_food_optimizer.visualization import MapVisualizer, RouteExporter
from fast_food_optimizer.models.restaurant import Restaurant, Coordinates


# ============================================================================
# CONFIGURATION - MODIFY THESE FOR YOUR CITY
# ============================================================================

# Target city coordinates (Salt Lake City, UT by default)
TARGET_LATITUDE = 40.719493
TARGET_LONGITUDE = -111.888749

# Search radius in meters (20km = 20000m)
SEARCH_RADIUS = 25000

# Route parameters
TIME_BUDGET_HOURS = 24.0
MIN_RESTAURANTS = 250  # Target exactly 250 densest restaurants
MAX_RESTAURANTS = 250  # Cap at 250 for efficiency

# Clustering parameters - TIGHT for maximum density
CLUSTER_EPS_KM = 0.8  # Max 800m between restaurants in a cluster (very tight)
CLUSTER_MIN_SAMPLES = 8  # Only include dense clusters with 8+ restaurants

# Output directory
OUTPUT_DIR = "data/world_record_route"

# Route name for exports
ROUTE_NAME = "Fast Food World Record Attempt"


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run complete pipeline with real data."""

    print("=" * 70)
    print("FAST FOOD ROUTE OPTIMIZER - REAL DATA RUN")
    print("=" * 70)
    print()

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    try:
        # ====================================================================
        # STEP 1: Initialize OpenStreetMap Client
        # ====================================================================
        print("📝 Step 1: Initializing OpenStreetMap client...")
        print("   ✅ No API key required - using free OpenStreetMap data")
        print(f"   Target: ({TARGET_LATITUDE}, {TARGET_LONGITUDE})")
        print(f"   Radius: {SEARCH_RADIUS/1000:.1f}km")
        print()

        # ====================================================================
        # STEP 2: Collect Restaurant Data from OpenStreetMap
        # ====================================================================
        print("📍 Step 2: Collecting restaurants from OpenStreetMap...")
        print("   This may take 30-60 seconds for large areas...")

        client = OpenStreetMapClient(timeout=90)

        # Search for all restaurants in the area
        results = client.search_restaurants(
            latitude=TARGET_LATITUDE,
            longitude=TARGET_LONGITUDE,
            radius=SEARCH_RADIUS,
        )

        print(f"✅ Found {len(results)} total restaurants from OpenStreetMap")
        print(f"   Cost: $0.00 (OpenStreetMap is free!)")
        print()

        # ====================================================================
        # STEP 3: Classify as Fast Food
        # ====================================================================
        print("🍔 Step 3: Classifying fast food restaurants...")

        classifier = FastFoodClassifier()
        restaurants = []

        for place in results:
            # Classify
            is_ff, confidence = classifier.classify(
                name=place.get("name", ""),
                place_types=place.get("types", []),
            )

            # Create Restaurant object
            location = place.get("geometry", {}).get("location", {})
            restaurant = Restaurant(
                place_id=place["place_id"],
                name=place.get("name", ""),
                address=place.get("vicinity", ""),
                coordinates=Coordinates(
                    latitude=location.get("lat", 0),
                    longitude=location.get("lng", 0)
                ),
                is_fast_food=is_ff,
                confidence_score=confidence,
                rating=place.get("rating"),
                place_types=place.get("types", [])
            )
            restaurants.append(restaurant)

        # Filter to fast food only
        fast_food = [r for r in restaurants if r.is_fast_food]
        print(f"✅ Classified {len(fast_food)} as fast food restaurants")

        # Show top chains
        chain_counts = {}
        for r in fast_food:
            # Simple chain detection (first word of name)
            chain = r.name.split()[0] if r.name else "Unknown"
            chain_counts[chain] = chain_counts.get(chain, 0) + 1

        top_chains = sorted(chain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"\n   Top chains found:")
        for chain, count in top_chains:
            print(f"   - {chain}: {count} locations")
        print()

        # ====================================================================
        # STEP 4: Validate Data
        # ====================================================================
        print("✅ Step 4: Validating data quality...")

        validator = DataValidator()
        report = validator.validate_batch(fast_food)

        print(f"✅ Validation complete:")
        print(f"   Valid: {report['valid_count']}/{report['total_count']} ({report['valid_percentage']:.1f}%)")

        if report['valid_percentage'] < 90:
            print(f"   ⚠️  Warning: Only {report['valid_percentage']:.1f}% of restaurants are valid")
            print(f"   You may want to check for data quality issues")
        print()

        # ====================================================================
        # STEP 5: Save Raw Data
        # ====================================================================
        print("💾 Step 5: Saving raw data...")

        persistence = DataPersistence()
        saved_path = persistence.save_json(
            fast_food,
            "raw_restaurants"
        )
        print(f"✅ Saved to {saved_path}")
        print()

        # ====================================================================
        # STEP 6: Cluster Restaurants
        # ====================================================================
        print("🗺️  Step 6: Clustering restaurants...")

        clusterer = RestaurantClusterer(
            eps_km=CLUSTER_EPS_KM,
            min_samples=CLUSTER_MIN_SAMPLES
        )
        clusters = clusterer.cluster_restaurants(fast_food)

        # Filter out noise
        valid_clusters = {k: v for k, v in clusters.items() if k != -1}
        noise_count = len(clusters.get(-1, []))

        print(f"✅ Created {len(valid_clusters)} clusters")
        print(f"   Noise points: {noise_count}")

        for cluster_id in sorted(valid_clusters.keys()):
            count = len(valid_clusters[cluster_id])
            print(f"   Cluster {cluster_id}: {count} restaurants")
        print()

        # ====================================================================
        # STEP 6.5: Find Tightest Geographic Circle with 250 Restaurants
        # ====================================================================
        print(f"📍 Step 6.5: Finding tightest geographic area with {MAX_RESTAURANTS} restaurants...")
        print(f"   Analyzing all {len(fast_food)} restaurants...")

        import math

        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate distance in km between two points."""
            R = 6371  # Earth radius in km
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c

        # For each restaurant, find the radius needed to capture 250 restaurants
        best_center = None
        best_radius_km = float('inf')
        best_restaurants = []

        # Sample every Nth restaurant to speed up (or all if dataset is small)
        sample_step = max(1, len(fast_food) // 100)  # Check ~100 potential centers

        for i, center_restaurant in enumerate(fast_food[::sample_step]):
            center_lat = center_restaurant.coordinates.latitude
            center_lon = center_restaurant.coordinates.longitude

            # Calculate distance from this center to all restaurants
            distances = []
            for restaurant in fast_food:
                dist = haversine_distance(
                    center_lat, center_lon,
                    restaurant.coordinates.latitude,
                    restaurant.coordinates.longitude
                )
                distances.append((dist, restaurant))

            # Sort by distance and take closest 250
            distances.sort(key=lambda x: x[0])
            closest_250 = distances[:MAX_RESTAURANTS]
            radius_needed = closest_250[-1][0]  # Distance to 250th restaurant

            # Track the best (smallest radius) center
            if radius_needed < best_radius_km:
                best_radius_km = radius_needed
                best_center = (center_lat, center_lon, center_restaurant.name)
                best_restaurants = [r for _, r in closest_250]

            if (i + 1) % 10 == 0:
                print(f"   Checked {(i + 1) * sample_step}/{len(fast_food)} potential centers... (best so far: {best_radius_km:.2f}km radius)")

        print(f"\n✅ Found tightest geographic area!")
        print(f"   Center: {best_center[2]}")
        print(f"   Location: ({best_center[0]:.6f}, {best_center[1]:.6f})")
        print(f"   Radius: {best_radius_km:.2f}km")
        print(f"   Contains: {len(best_restaurants)} restaurants")
        print(f"   Diameter: {best_radius_km * 2:.2f}km")

        # Calculate approximate area
        area_km2 = math.pi * (best_radius_km ** 2)
        density = len(best_restaurants) / area_km2
        print(f"   Area: {area_km2:.2f}km²")
        print(f"   Density: {density:.1f} restaurants/km²")
        print()

        selected_restaurants = best_restaurants

        # Create clusters for visualization - group nearby restaurants
        # We'll recreate clusters just for the selected 250
        from sklearn.cluster import DBSCAN
        import numpy as np

        coords = np.array([
            [r.coordinates.latitude, r.coordinates.longitude]
            for r in selected_restaurants
        ])

        # Use tight clustering for visualization
        clustering = DBSCAN(eps=0.008, min_samples=3).fit(coords)  # ~0.8km

        filtered_clusters = {}
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:
                continue  # Skip noise
            mask = clustering.labels_ == cluster_id
            cluster_restaurants = [selected_restaurants[i] for i, m in enumerate(mask) if m]
            filtered_clusters[cluster_id] = cluster_restaurants

        print(f"   Visualization: {len(filtered_clusters)} micro-clusters within this area")
        print()

        # ====================================================================
        # STEP 7: Optimize Global Route
        # ====================================================================
        print("🚀 Step 7: Optimizing global route...")
        print("   This may take 30-60 seconds...")

        optimizer = GlobalRouteOptimizer()

        route = optimizer.optimize_global_route(
            filtered_clusters,  # Use filtered clusters instead of all clusters
            start_location=(TARGET_LATITUDE, TARGET_LONGITUDE),
            time_budget_hours=TIME_BUDGET_HOURS,
            algorithm="2opt"
        )

        print(f"✅ Route optimized!")
        print(f"   Total restaurants: {route.total_restaurants}")
        print(f"   Total distance: {route.total_distance:.2f}km")
        print(f"   Estimated time: {route.estimated_time_hours:.1f}h")
        print(f"   Cluster sequence: {route.cluster_sequence}")

        if route.estimated_time_hours > 0:
            efficiency = route.total_restaurants / route.estimated_time_hours
            print(f"   Efficiency: {efficiency:.1f} restaurants/hour")
        print()

        # ====================================================================
        # STEP 8: Validate Route
        # ====================================================================
        print("🔍 Step 8: Validating route...")

        validation = optimizer.validate_global_route(
            route,
            time_budget_hours=TIME_BUDGET_HOURS,
            min_restaurants=MIN_RESTAURANTS
        )

        if validation["valid"]:
            print("✅ Route is valid!")
            if "restaurants_per_hour" in validation["metrics"]:
                print(f"   Restaurants/hour: {validation['metrics']['restaurants_per_hour']:.1f}")
        else:
            print("❌ Route validation failed:")
            for error in validation["errors"]:
                print(f"   - {error}")

        if validation["warnings"]:
            print("   Warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        print()

        # ====================================================================
        # STEP 9: Generate Alternative Routes
        # ====================================================================
        print("🔄 Step 9: Generating alternative routes...")

        alternatives = optimizer.generate_alternative_routes(
            filtered_clusters,  # Use filtered clusters
            start_location=(TARGET_LATITUDE, TARGET_LONGITUDE),
            num_alternatives=2
        )

        print(f"✅ Generated {len(alternatives)} alternative routes:")
        for i, alt in enumerate(alternatives, 1):
            print(f"   Route {i}: {alt.total_distance:.2f}km, {alt.estimated_time_hours:.1f}h, {alt.total_restaurants} restaurants")
        print()

        # ====================================================================
        # STEP 10: Create Visualizations
        # ====================================================================
        print("🗺️  Step 10: Creating interactive maps...")

        visualizer = MapVisualizer()

        # Clusters map (showing only selected dense clusters)
        print("   Creating clusters map...")
        clusters_map = visualizer.visualize_clusters(
            filtered_clusters,  # Show only selected clusters
            center=(TARGET_LATITUDE, TARGET_LONGITUDE),
            show_noise=False
        )
        visualizer.save_map(clusters_map, f"{OUTPUT_DIR}/clusters_map.html")

        # Route map
        print("   Creating route map...")
        route_map = visualizer.visualize_route(
            route,
            show_route_lines=True
        )
        visualizer.save_map(route_map, f"{OUTPUT_DIR}/route_map.html")

        # Alternatives comparison
        print("   Creating alternatives comparison map...")
        all_routes = [route] + alternatives
        comparison_map = visualizer.visualize_alternative_routes(
            all_routes,
            center=(TARGET_LATITUDE, TARGET_LONGITUDE)
        )
        visualizer.save_map(comparison_map, f"{OUTPUT_DIR}/alternatives_map.html")

        print(f"✅ Maps saved to {OUTPUT_DIR}/")
        print()

        # ====================================================================
        # STEP 11: Export Route Files
        # ====================================================================
        print("📤 Step 11: Exporting route files...")

        exporter = RouteExporter()

        # Export all formats
        files = exporter.export_all_formats(
            route,
            output_dir=f"{OUTPUT_DIR}/exports",
            base_filename="world_record_route",
            route_name=ROUTE_NAME
        )

        print(f"✅ Exported route files:")
        print(f"   📍 GPX (GPS Device): {files['gpx']}")
        print(f"   📊 CSV (Analysis): {files['csv']}")
        print(f"   🌍 KML (Google Earth): {files['kml']}")
        print(f"   📱 JSON (Mobile App): {files['json']}")
        print()

        # ====================================================================
        # STEP 12: Summary and Next Steps
        # ====================================================================
        print("=" * 70)
        print("✅ ALL STEPS COMPLETE!")
        print("=" * 70)
        print()
        print("📊 ROUTE SUMMARY:")
        print(f"   Total Restaurants: {route.total_restaurants}")
        print(f"   Total Distance: {route.total_distance:.2f}km")
        print(f"   Estimated Time: {route.estimated_time_hours:.1f}h")
        print(f"   Number of Clusters: {len(route.cluster_sequence)}")
        print()

        print("📁 OUTPUT FILES:")
        print(f"   Raw Data: data/raw_restaurants.json")
        print(f"   Maps: {OUTPUT_DIR}/*.html")
        print(f"   GPS Files: {OUTPUT_DIR}/exports/")
        print()

        print("🎯 NEXT STEPS:")
        print()
        print("1. REVIEW THE ROUTE:")
        print(f"   - Open {OUTPUT_DIR}/route_map.html in your browser")
        print("   - Verify the route makes sense geographically")
        print("   - Check for any obvious issues")
        print()

        print("2. COMPARE ALTERNATIVES:")
        print(f"   - Open {OUTPUT_DIR}/alternatives_map.html")
        print("   - See if any alternative is better")
        print("   - Choose the best route for your attempt")
        print()

        print("3. LOAD ONTO GPS DEVICE:")
        print(f"   - Copy {OUTPUT_DIR}/exports/world_record_route.gpx")
        print("   - Transfer to your Garmin or phone")
        print("   - Test navigation before the actual attempt")
        print()

        print("4. PREPARE FOR ATTEMPT:")
        print(f"   - Print {OUTPUT_DIR}/exports/world_record_route.csv as backup")
        print("   - Download offline maps for the area")
        print("   - Charge all devices")
        print("   - Bring portable chargers")
        print()

        print("🚀 YOU'RE READY TO BREAK THE WORLD RECORD!")
        print()

        # Show first 10 restaurants
        all_restaurants = route.get_all_restaurants()
        print("📍 First 10 Stops:")
        for i, r in enumerate(all_restaurants[:10], 1):
            print(f"   {i}. {r.name} - {r.address}")

        if len(all_restaurants) > 10:
            print(f"   ... and {len(all_restaurants) - 10} more")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
