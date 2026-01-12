# Testing the Fast Food Route Optimizer

This guide explains how to test the complete system.

---

## Quick Test (No API Key Required)

Run the test pipeline with mock data:

```bash
python3 test_pipeline.py
```

This will:
1. Create 100 mock restaurants
2. Test classification
3. Test validation
4. Test clustering
5. Test route optimization
6. Generate alternative routes

**Expected output:**
```
✅ ALL TESTS PASSED!
Total restaurants: 100
Total distance: XX.XXkm
Estimated time: X.Xh
```

---

## Unit Tests

Run all unit tests:

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=src/fast_food_optimizer

# Run specific sprint tests
python3 -m pytest tests/unit/test_global_optimizer.py -v
python3 -m pytest tests/unit/test_route_optimizer.py -v
python3 -m pytest tests/unit/test_clusterer.py -v
```

**Expected:** 270 tests passing

---

## Testing with Real Google Maps Data

### Step 1: Set Up API Key

Create `.env` file in project root:

```bash
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### Step 2: Create Test Script

```python
#!/usr/bin/env python3
"""Test with real Google Maps data."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fast_food_optimizer.config.settings import get_config
from fast_food_optimizer.data.google_client import GoogleMapsClient
from fast_food_optimizer.data.classifier import FastFoodClassifier
from fast_food_optimizer.data.persistence import DataPersistence
from fast_food_optimizer.optimization import RestaurantClusterer, GlobalRouteOptimizer
from fast_food_optimizer.models.restaurant import Restaurant, Coordinates

def main():
    # Load config
    config = get_config()

    # Initialize Google Maps client
    client = GoogleMapsClient(
        api_key=config.google_maps_api_key,
        rate_limit=config.google_maps_rate_limit
    )

    # Search for restaurants in Salt Lake City
    print("🔍 Searching for restaurants...")
    results = client.search_nearby_restaurants(
        latitude=40.7589,
        longitude=-111.8883,
        radius=5000,  # 5km radius
        place_type="restaurant"
    )

    print(f"Found {len(results)} restaurants")

    # Convert to Restaurant objects
    restaurants = []
    classifier = FastFoodClassifier()

    for place in results:
        # Classify as fast food
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
    print(f"✅ Found {len(fast_food)} fast food restaurants")

    # Save data
    persistence = DataPersistence()
    persistence.save_restaurants(fast_food, "slc_restaurants", format="json")
    print("💾 Saved to data/slc_restaurants.json")

    # Cluster restaurants
    print("\n🗺️  Clustering restaurants...")
    clusterer = RestaurantClusterer(eps_km=3.0, min_samples=3)
    clusters = clusterer.cluster_restaurants(fast_food)

    non_noise = {k: v for k, v in clusters.items() if k != -1}
    print(f"Created {len(non_noise)} clusters")

    # Optimize route
    print("\n🚀 Optimizing route...")
    optimizer = GlobalRouteOptimizer()

    route = optimizer.optimize_global_route(
        clusters,
        start_location=(40.7589, -111.8883),
        time_budget_hours=24.0,
        algorithm="2opt"
    )

    print(f"\n✅ Route created:")
    print(f"   {route.total_restaurants} restaurants")
    print(f"   {route.total_distance:.2f}km")
    print(f"   {route.estimated_time_hours:.1f}h")

    # Show first 10 restaurants in order
    all_restaurants = route.get_all_restaurants()
    print(f"\n📍 First 10 restaurants:")
    for i, r in enumerate(all_restaurants[:10], 1):
        print(f"   {i}. {r.name} - {r.address}")

if __name__ == "__main__":
    main()
```

Save as `test_real_data.py` and run:

```bash
python3 test_real_data.py
```

---

## Testing Individual Components

### Test Clustering

```python
from fast_food_optimizer.optimization import RestaurantClusterer

clusterer = RestaurantClusterer(eps_km=5.0, min_samples=5)
clusters = clusterer.cluster_restaurants(restaurants)

print(f"Created {len(clusters)} clusters")
```

### Test Route Optimization

```python
from fast_food_optimizer.optimization import GlobalRouteOptimizer

optimizer = GlobalRouteOptimizer()
route = optimizer.optimize_global_route(
    clusters,
    start_location=(40.7589, -111.8883)
)

print(f"Route: {route.total_restaurants} restaurants, {route.total_distance:.2f}km")
```

### Test Data Validation

```python
from fast_food_optimizer.validation.validator import DataValidator

validator = DataValidator()
report = validator.validate_batch(restaurants)

print(f"Valid: {report['valid_percentage']:.1f}%")
```

---

## Performance Testing

### Test with Different Dataset Sizes

```python
# Test with 50 restaurants
restaurants_50 = create_mock_restaurants(50)
test_optimization(restaurants_50)

# Test with 200 restaurants
restaurants_200 = create_mock_restaurants(200)
test_optimization(restaurants_200)

# Test with 500 restaurants
restaurants_500 = create_mock_restaurants(500)
test_optimization(restaurants_500)
```

### Benchmark Clustering

```python
import time

start = time.time()
clusters = clusterer.cluster_restaurants(restaurants)
elapsed = time.time() - start

print(f"Clustering took {elapsed:.2f}s for {len(restaurants)} restaurants")
```

### Benchmark Route Optimization

```python
import time

start = time.time()
route = optimizer.optimize_global_route(clusters)
elapsed = time.time() - start

print(f"Route optimization took {elapsed:.2f}s")
```

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution:** Install package in editable mode:

```bash
pip3 install --user -e .
```

### Issue: Google Maps API errors

**Solution:** Check your API key:

```python
from fast_food_optimizer.config.settings import get_config

config = get_config()
print(f"API key configured: {bool(config.google_maps_api_key)}")
```

### Issue: No clusters created

**Solution:** Adjust clustering parameters:

```python
# Try smaller eps or min_samples
clusterer = RestaurantClusterer(eps_km=3.0, min_samples=3)
```

### Issue: Route validation fails

**Solution:** Check time budget and restaurant count:

```python
validation = optimizer.validate_global_route(
    route,
    time_budget_hours=48.0,  # Increase time budget
    min_restaurants=50  # Lower minimum
)
```

---

## Expected Performance

| Dataset Size | Clustering | Optimization | Total |
|--------------|------------|--------------|-------|
| 50 restaurants | < 1s | < 2s | < 3s |
| 100 restaurants | < 2s | < 5s | < 7s |
| 200 restaurants | < 5s | < 15s | < 20s |
| 500 restaurants | < 15s | < 60s | < 75s |

---

## Next Steps After Testing

1. **Collect Real Data:**
   - Set up Google Maps API key
   - Run data collection for your city
   - Enrich with Place Details API

2. **Optimize for Your Area:**
   - Adjust clustering parameters (eps_km, min_samples)
   - Set realistic time budgets
   - Generate multiple alternative routes

3. **Export Routes (Sprint 8-9):**
   - GPX for GPS devices
   - CSV for analysis
   - KML for Google Earth
   - Mobile app integration

4. **Customize (Sprint 10-11):**
   - Add operating hours constraints
   - Exclude specific chains
   - Manual route adjustments

---

## Questions?

- Check `SPRINT_X_COMPLETE.md` files for detailed documentation
- Run `pytest tests/unit/test_*.py -v` to see example usage
- Review code in `src/fast_food_optimizer/` for API details
