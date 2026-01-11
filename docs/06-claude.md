# CLAUDE.md - Project Instructions for Fast Food Route Optimizer

## Project Overview

You are working on the **Fast Food Route Optimizer**, a specialized routing system designed to help an ultramarathon runner break the world record for "Most fast food restaurants visited in 24 hours" (current record: 150, target: 202+).

### Core Objective
Generate optimal walking routes through Salt Lake City metropolitan area to visit 200+ fast food restaurants within 24 hours, prioritizing high-density clusters and efficient inter-cluster travel.

---

## Project Context & Requirements

### Business Requirements
- **Primary Goal**: Route optimization for 200+ restaurant visits in 24 hours
- **Travel Method**: On-foot (running/walking) - no private vehicles allowed
- **Definition**: "Fast food" = over-counter service (includes food courts, coffee shops, frozen yogurt)
- **Documentation**: GPS coordinates and receipts required for each visit
- **Target Efficiency**: 15+ restaurants/hour in dense areas, 9/hour minimum overall

### Technical Constraints
- **API Limitations**: Google Maps API rate limits (manage carefully)
- **Performance**: Complete optimization in under 2 minutes for full dataset
- **Memory**: Efficient handling of 1000+ restaurant datasets
- **Export Formats**: GPX, CSV, KML, JSON for various GPS devices and analysis

### User Profile
- **User**: Jacob - ultramarathon runner, product manager, technically skilled
- **Location**: Salt Lake City, Utah area
- **Experience**: Comfortable with APIs, data analysis, command-line tools
- **Needs**: Accurate, flexible routing with manual override capabilities

---

## Architecture & Design Patterns

### Project Structure
```
fast_food_optimizer/
├── src/fast_food_optimizer/
│   ├── config/           # Settings and API configuration
│   ├── data/            # Data collection and storage
│   ├── models/          # Data models and validation
│   ├── optimization/    # Clustering and routing algorithms
│   ├── visualization/   # Map generation and exports
│   ├── validation/      # Data quality and route validation
│   └── utils/           # Logging, exceptions, helpers
├── tests/               # Comprehensive test suite
├── exports/             # Generated routes and visualizations
└── data/                # Cached restaurant datasets
```

### Key Design Patterns
- **Strategy Pattern**: Multiple optimization algorithms (TSP, genetic, heuristic)
- **Observer Pattern**: Progress reporting during long-running operations
- **Factory Pattern**: Export format generation (GPX, CSV, KML, JSON)
- **Cache Pattern**: API response caching and distance matrix persistence

---

## Development Standards

### Code Quality Requirements
```python
# Always use type hints and dataclasses
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Restaurant:
    place_id: str
    name: str
    coordinates: Tuple[float, float]
    is_fast_food: bool
    operating_hours: Optional[Dict[str, str]] = None

# Always include comprehensive docstrings
def optimize_cluster_route(restaurants: List[Restaurant]) -> List[Restaurant]:
    """Optimize visiting order within a restaurant cluster.
    
    Uses nearest neighbor heuristic with 2-opt improvement to minimize
    total walking distance between restaurants within a single cluster.
    
    Args:
        restaurants: List of Restaurant objects in the cluster.
        
    Returns:
        Optimized list of restaurants in visiting order.
        
    Raises:
        ValueError: If restaurants list is empty.
        OptimizationError: If route optimization fails.
    """
```

### Error Handling Standards
```python
# Use custom exception hierarchy
class FastFoodOptimizerError(Exception):
    """Base exception for all optimizer errors."""

class APIConnectionError(FastFoodOptimizerError):
    """Google Maps API connection issues."""

class RouteOptimizationError(FastFoodOptimizerError):
    """Route optimization algorithm failures."""

# Always provide context and recovery suggestions
try:
    route = optimize_route(clusters)
except RouteOptimizationError as e:
    logger.error(f"Route optimization failed: {e}")
    logger.info("Trying fallback algorithm...")
    route = fallback_optimize_route(clusters)
```

### Performance Requirements
- **Distance Matrix**: 500x500 calculations in <60 seconds
- **Clustering**: 1000 restaurants in <30 seconds
- **Route Optimization**: 200+ restaurants in <2 minutes
- **Memory Usage**: <512MB for full dataset processing

---

## API Integration Guidelines

### Google Maps API Best Practices
```python
# Always implement rate limiting
import time
from functools import wraps

def rate_limit(calls_per_second: int = 10):
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 1.0 / calls_per_second - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

# Always cache API responses
import json
from pathlib import Path

class APICache:
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cached_response(self, key: str) -> Optional[Dict]:
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None
```

### Required API Integrations
1. **Places Nearby API**: Restaurant discovery within geographic bounds
2. **Place Details API**: Operating hours and detailed information
3. **Distance Matrix API**: Backup for complex distance calculations
4. **Geocoding API**: Address resolution and validation

---

## Algorithm Implementation Guidelines

### Clustering Requirements
```python
# Use DBSCAN for density-based clustering
from sklearn.cluster import DBSCAN
import numpy as np

def cluster_restaurants(restaurants: List[Restaurant], 
                       eps_km: float = 0.5, 
                       min_samples: int = 3) -> List[List[Restaurant]]:
    """Cluster restaurants using DBSCAN algorithm.
    
    Args:
        restaurants: List of restaurants to cluster
        eps_km: Maximum distance between restaurants in same cluster (km)
        min_samples: Minimum restaurants required to form a cluster
    
    Returns:
        List of restaurant clusters, excluding noise points
    """
    coordinates = np.array([r.coordinates for r in restaurants])
    
    # Convert eps from km to degrees (approximate)
    eps_degrees = eps_km / 111.0  # 1 degree ≈ 111km
    
    clustering = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit(coordinates)
    
    # Group restaurants by cluster
    clusters = {}
    for i, label in enumerate(clustering.labels_):
        if label != -1:  # Exclude noise points
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(restaurants[i])
    
    return list(clusters.values())
```

### TSP Implementation Guidelines
```python
# Use multiple TSP algorithms based on problem size
def optimize_route(restaurants: List[Restaurant]) -> List[Restaurant]:
    """Choose optimal TSP algorithm based on problem size."""
    n = len(restaurants)
    
    if n <= 10:
        return exact_tsp_solver(restaurants)  # Branch and bound
    elif n <= 20:
        return genetic_algorithm_tsp(restaurants)  # GA with 2-opt
    else:
        return nearest_neighbor_with_2opt(restaurants)  # Fast heuristic
```

---

## Data Quality & Validation

### Restaurant Classification Rules
```python
# Fast food classification criteria
FAST_FOOD_INDICATORS = {
    'chain_names': [
        'mcdonalds', 'subway', 'burger king', 'kfc', 'taco bell',
        'pizza hut', 'dominos', 'papa johns', 'starbucks', 'dunkin'
        # ... comprehensive list
    ],
    'service_keywords': [
        'fast food', 'quick service', 'counter service', 'drive thru',
        'takeaway', 'grab and go', 'food court'
    ],
    'excluded_types': [
        'bar', 'night_club', 'liquor_store', 'casino',
        'fine_dining', 'table_service'
    ]
}

def classify_fast_food(restaurant: Restaurant) -> Tuple[bool, float]:
    """Classify restaurant as fast food with confidence score.
    
    Returns:
        Tuple of (is_fast_food: bool, confidence: float)
    """
    confidence = 0.0
    
    # Chain name matching (high confidence)
    name_lower = restaurant.name.lower()
    for chain in FAST_FOOD_INDICATORS['chain_names']:
        if chain in name_lower:
            confidence += 0.8
            break
    
    # Service type indicators
    for keyword in FAST_FOOD_INDICATORS['service_keywords']:
        if keyword in ' '.join(restaurant.place_types):
            confidence += 0.3
    
    # Google place type analysis
    if 'meal_takeaway' in restaurant.place_types:
        confidence += 0.4
    if 'restaurant' in restaurant.place_types:
        confidence += 0.2
    
    return confidence >= 0.5, min(confidence, 1.0)
```

### Data Validation Requirements
```python
# Always validate critical data
def validate_restaurant_data(restaurant: Restaurant) -> List[str]:
    """Validate restaurant data and return list of issues."""
    issues = []
    
    # Coordinate validation
    lat, lng = restaurant.coordinates
    if not (-90 <= lat <= 90):
        issues.append(f"Invalid latitude: {lat}")
    if not (-180 <= lng <= 180):
        issues.append(f"Invalid longitude: {lng}")
    
    # Required fields
    if not restaurant.name or len(restaurant.name.strip()) < 2:
        issues.append("Restaurant name missing or too short")
    
    if not restaurant.place_id:
        issues.append("Place ID missing")
    
    return issues
```

---

## Visualization & Export Standards

### Map Visualization Requirements
```python
# Use consistent color scheme and styling
VISUALIZATION_CONFIG = {
    'colors': {
        'fast_food': '#FF6347',      # Tomato red
        'food_court': '#4169E1',     # Royal blue
        'cluster_high': '#2E8B57',   # Sea green
        'cluster_med': '#FFB347',    # Peach
        'cluster_low': '#CD5C5C',    # Indian red
        'route_primary': '#1E90FF',  # Dodge blue
        'route_alt': '#9370DB'       # Medium purple
    },
    'markers': {
        'restaurant': {'icon': 'cutlery', 'size': 8},
        'food_court': {'icon': 'shopping-cart', 'size': 12},
        'cluster_center': {'icon': 'star', 'size': 15}
    }
}
```

### Export Format Standards
```python
# Support multiple export formats
class RouteExporter:
    def export_gpx(self, route: Route, filename: str) -> None:
        """Export route as GPX file for GPS devices."""
        
    def export_csv(self, route: Route, filename: str) -> None:
        """Export route data as CSV for analysis."""
        
    def export_kml(self, route: Route, filename: str) -> None:
        """Export route as KML for Google Earth."""
        
    def export_json(self, route: Route, filename: str) -> None:
        """Export route as JSON for API integration."""
```

---

## Testing Requirements

### Test Coverage Standards
- **Unit Tests**: 90%+ coverage for all business logic
- **Integration Tests**: Google Maps API interaction validation
- **Performance Tests**: Benchmark against specified targets
- **End-to-End Tests**: Complete workflow validation

### Critical Test Scenarios
```python
# Always test with realistic data sizes
def test_clustering_performance():
    """Test clustering with 1000+ restaurants completes in <30 seconds."""
    restaurants = generate_test_restaurants(1000)
    start_time = time.time()
    clusters = cluster_restaurants(restaurants)
    duration = time.time() - start_time
    
    assert duration < 30, f"Clustering took {duration:.1f}s, should be <30s"
    assert len(clusters) >= 20, "Should generate reasonable number of clusters"
    assert sum(len(c) for c in clusters) >= 800, "Should cluster most restaurants"
```

---

## Deployment & Distribution

### Environment Configuration
```bash
# Required environment variables
GOOGLE_MAPS_API_KEY=your_api_key_here
GOOGLE_MAPS_RATE_LIMIT=50
DEFAULT_SEARCH_RADIUS=50000
MAX_RESTAURANTS=1000
EXPORT_DIRECTORY=./exports
```

### CLI Interface Standards
```python
# Use Click for consistent CLI interface
import click

@click.group()
@click.version_option()
def cli():
    """Fast Food Route Optimizer - World Record Route Planning"""
    pass

@cli.command()
@click.option('--area', default='Salt Lake City, UT', help='Search area')
@click.option('--radius', default=50000, help='Search radius in meters')
@click.option('--output', default='route.json', help='Output file')
def search(area, radius, output):
    """Search for restaurants and generate route."""
    # Implementation
```

---

## Troubleshooting & Common Issues

### Google Maps API Issues
- **Rate Limiting**: Implement exponential backoff, cache aggressively
- **Quota Exceeded**: Provide clear error messages and usage tracking
- **Invalid Responses**: Validate all API responses, handle partial data

### Performance Issues
- **Large Datasets**: Use chunked processing and progress reporting
- **Memory Usage**: Monitor memory consumption, implement streaming where possible
- **Slow Optimization**: Provide time estimates and cancellation options

### Data Quality Issues
- **Missing Data**: Implement graceful degradation and fallback strategies
- **Incorrect Classifications**: Provide manual override and learning capabilities
- **Coordinate Accuracy**: Validate against known landmarks and addresses

---

## Success Criteria

### Final Deliverable Requirements
- [ ] Generate routes with 200+ restaurants in Salt Lake area
- [ ] Complete optimization in under 2 minutes
- [ ] Export routes compatible with GPS devices
- [ ] Interactive map visualization for route validation
- [ ] Manual route modification capabilities
- [ ] Comprehensive validation and quality reporting

### Performance Benchmarks
- [ ] Process 1000+ restaurants without memory issues
- [ ] Generate 3+ alternative routes for contingency planning
- [ ] Achieve 15+ restaurants/hour clusters in dense areas
- [ ] Provide clear error messages and recovery guidance

---

This project requires careful balance between optimization performance and real-world practicality. Always consider the end user (ultramarathon runner) who needs reliable, actionable route data for a world record attempt.

**Document Version**: 1.0  
**Last Updated**: January 11, 2026  
**Priority**: Use this document as the authoritative reference for all implementation decisions