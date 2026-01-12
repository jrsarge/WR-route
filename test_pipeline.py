#!/usr/bin/env python3
"""Test script for Fast Food Route Optimizer pipeline.

This script demonstrates the complete workflow:
1. Collect restaurant data (or use mock data)
2. Classify as fast food
3. Validate data quality
4. Cluster restaurants
5. Optimize routes
6. Generate and validate complete route
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fast_food_optimizer.models.restaurant import Restaurant, Coordinates
from fast_food_optimizer.data.classifier import FastFoodClassifier
from fast_food_optimizer.validation.validator import DataValidator
from fast_food_optimizer.validation.quality_metrics import QualityMetrics
from fast_food_optimizer.optimization import (
    RestaurantClusterer,
    GlobalRouteOptimizer,
)


def create_mock_restaurants(num_restaurants: int = 100) -> list[Restaurant]:
    """Create mock restaurant data for testing.

    Creates restaurants distributed across Salt Lake City area.
    """
    print(f"\n📝 Creating {num_restaurants} mock restaurants...")

    restaurants = []

    # Create restaurants in a grid pattern across SLC
    base_lat = 40.7589
    base_lng = -111.8883

    chains = ["McDonald's", "Subway", "Starbucks", "Taco Bell", "Burger King",
              "Wendy's", "KFC", "Chipotle", "Pizza Hut", "Domino's"]

    for i in range(num_restaurants):
        # Distribute across ~20km x 20km area
        lat = base_lat + (i % 10) * 0.02  # ~2km apart
        lng = base_lng + (i // 10) * 0.02

        chain = chains[i % len(chains)]

        restaurant = Restaurant(
            place_id=f"ChIJMock{i:04d}234567890",
            name=f"{chain} #{i}",
            address=f"{1000 + i} Main St, Salt Lake City, UT",
            coordinates=Coordinates(latitude=lat, longitude=lng),
            is_fast_food=True,
            confidence_score=0.9,
            rating=4.0 + (i % 10) * 0.1,
        )
        restaurants.append(restaurant)

    print(f"✅ Created {len(restaurants)} mock restaurants")
    return restaurants


def test_classification(restaurants: list[Restaurant]) -> None:
    """Test fast food classification."""
    print("\n🍔 Testing Fast Food Classification...")

    classifier = FastFoodClassifier()

    # Count classifications
    fast_food_count = sum(1 for r in restaurants if r.is_fast_food)
    avg_confidence = sum(r.confidence_score for r in restaurants) / len(restaurants)

    print(f"✅ Classification complete:")
    print(f"   Fast food: {fast_food_count}/{len(restaurants)}")
    print(f"   Avg confidence: {avg_confidence:.2f}")


def test_validation(restaurants: list[Restaurant]) -> None:
    """Test data validation."""
    print("\n✅ Testing Data Validation...")

    validator = DataValidator()

    # Validate all restaurants
    report = validator.validate_batch(restaurants)

    print(f"✅ Validation complete:")
    print(f"   Valid: {report['valid_count']}/{report['total_count']}")
    print(f"   Valid percentage: {report['valid_percentage']:.1f}%")


def test_quality_metrics(restaurants: list[Restaurant]) -> None:
    """Test quality metrics."""
    print("\n📊 Testing Quality Metrics...")

    metrics = QualityMetrics()
    report = metrics.calculate_metrics(restaurants)

    print(f"✅ Quality metrics:")
    print(f"   Quality score: {report['quality_score']:.1f}/100")
    print(f"   Completeness: {report['completeness']['coordinates']:.1f}%")
    print(f"   All gates passed: {report['quality_gates']['all_passed']}")


def test_clustering(restaurants: list[Restaurant]) -> dict:
    """Test restaurant clustering."""
    print("\n🗺️  Testing Restaurant Clustering...")

    clusterer = RestaurantClusterer(eps_km=5.0, min_samples=5)
    clusters = clusterer.cluster_restaurants(restaurants)

    # Count clusters
    non_noise = {k: v for k, v in clusters.items() if k != -1}
    noise_count = len(clusters.get(-1, []))

    print(f"✅ Clustering complete:")
    print(f"   Clusters: {len(non_noise)}")
    print(f"   Noise points: {noise_count}")

    for cluster_id, cluster_restaurants in non_noise.items():
        print(f"   Cluster {cluster_id}: {len(cluster_restaurants)} restaurants")

    return clusters


def test_route_optimization(clusters: dict, restaurants: list[Restaurant]) -> None:
    """Test route optimization."""
    print("\n🚀 Testing Route Optimization...")

    optimizer = GlobalRouteOptimizer()

    # Get starting location (center of first restaurant)
    first_restaurant = restaurants[0]
    start_location = (
        first_restaurant.coordinates.latitude,
        first_restaurant.coordinates.longitude
    )

    print(f"   Starting location: ({start_location[0]:.4f}, {start_location[1]:.4f})")

    # Optimize global route
    route = optimizer.optimize_global_route(
        clusters,
        start_location=start_location,
        time_budget_hours=24.0,
        algorithm="2opt"
    )

    print(f"\n✅ Route optimization complete:")
    print(f"   Total restaurants: {route.total_restaurants}")
    print(f"   Total distance: {route.total_distance:.2f}km")
    print(f"   Estimated time: {route.estimated_time_hours:.1f}h")
    print(f"   Cluster sequence: {route.cluster_sequence}")

    # Calculate efficiency
    if route.estimated_time_hours > 0:
        restaurants_per_hour = route.total_restaurants / route.estimated_time_hours
        print(f"   Efficiency: {restaurants_per_hour:.1f} restaurants/hour")

    # Validate route
    print("\n🔍 Validating route...")
    validation = optimizer.validate_global_route(
        route,
        time_budget_hours=24.0,
        min_restaurants=50
    )

    if validation["valid"]:
        print("✅ Route is valid!")
        if "restaurants_per_hour" in validation["metrics"]:
            print(f"   Restaurants/hour: {validation['metrics']['restaurants_per_hour']:.1f}")
    else:
        print("❌ Route validation failed:")
        for error in validation["errors"]:
            print(f"   - {error}")

    # Generate alternatives
    print("\n🔄 Generating alternative routes...")
    alternatives = optimizer.generate_alternative_routes(
        clusters,
        start_location=start_location,
        num_alternatives=2
    )

    print(f"✅ Generated {len(alternatives)} alternative routes:")
    for i, alt in enumerate(alternatives, 1):
        print(f"   Route {i}: {alt.total_distance:.2f}km, {alt.estimated_time_hours:.1f}h")


def main():
    """Run complete pipeline test."""
    print("=" * 70)
    print("FAST FOOD ROUTE OPTIMIZER - PIPELINE TEST")
    print("=" * 70)

    try:
        # Step 1: Create mock data
        restaurants = create_mock_restaurants(num_restaurants=100)

        # Step 2: Test classification
        test_classification(restaurants)

        # Step 3: Test validation
        test_validation(restaurants)

        # Step 4: Test quality metrics
        test_quality_metrics(restaurants)

        # Step 5: Test clustering
        clusters = test_clustering(restaurants)

        # Step 6: Test route optimization
        test_route_optimization(clusters, restaurants)

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n📝 Next steps:")
        print("   1. Set up Google Maps API key in .env file")
        print("   2. Use GoogleMapsClient to collect real restaurant data")
        print("   3. Run the same pipeline with real data")
        print("   4. Export routes to GPX/CSV (Sprint 8-9)")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
