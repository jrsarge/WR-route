# Fast Food Route Optimizer - Style Guide

## 1. Code Style Standards

### 1.1 Python Code Conventions

#### PEP 8 Compliance
```python
# File naming: snake_case for modules
restaurant_optimizer.py
route_calculator.py
map_visualizer.py

# Class naming: PascalCase
class RestaurantOptimizer:
class RouteCalculator:
class MapVisualizer:

# Function/variable naming: snake_case
def calculate_distance():
def optimize_route():
restaurant_count = 150
total_distance = 42.5

# Constants: UPPER_SNAKE_CASE
MAX_RESTAURANTS_PER_HOUR = 15
DEFAULT_SEARCH_RADIUS = 50000
GOOGLE_API_RATE_LIMIT = 50
```

#### Type Annotations
```python
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass

def search_restaurants(
    center_lat: float, 
    center_lng: float, 
    radius: int = 50000
) -> List[Restaurant]:
    """Search for restaurants within specified radius."""
    pass

@dataclass
class Restaurant:
    place_id: str
    name: str
    coordinates: Tuple[float, float]
    is_fast_food: bool
    operating_hours: Optional[Dict[str, str]] = None
```

#### Docstring Standards (Google Style)
```python
def optimize_cluster_route(restaurants: List[Restaurant]) -> List[Restaurant]:
    """Optimize the visiting order within a restaurant cluster.
    
    Uses a nearest neighbor heuristic to minimize total walking distance
    between restaurants within a single cluster.
    
    Args:
        restaurants: List of Restaurant objects in the cluster.
        
    Returns:
        Optimized list of restaurants in visiting order.
        
    Raises:
        ValueError: If restaurants list is empty.
        OptimizationError: If route optimization fails.
        
    Example:
        >>> cluster = [restaurant_a, restaurant_b, restaurant_c]
        >>> optimized = optimize_cluster_route(cluster)
        >>> print(f"Optimized route visits {len(optimized)} restaurants")
    """
```

### 1.2 Import Organization
```python
# Standard library imports
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

# Third-party imports
import numpy as np
import pandas as pd
import googlemaps
import folium
from geopy.distance import geodesic

# Local application imports
from src.config.settings import Config
from src.data.models import Restaurant, RouteCluster
from src.utils.logging import get_logger
```

### 1.3 Error Handling Patterns
```python
# Custom exception hierarchy
class FastFoodOptimizerError(Exception):
    """Base exception for all optimizer errors."""
    pass

class APIConnectionError(FastFoodOptimizerError):
    """Raised when Google Maps API connection fails."""
    pass

class RouteOptimizationError(FastFoodOptimizerError):
    """Raised when route optimization cannot find solution."""
    pass

# Consistent error handling
def search_restaurants(query: str) -> List[Restaurant]:
    try:
        response = gmaps_client.places_nearby(query)
        return parse_restaurants(response)
    except googlemaps.exceptions.ApiError as e:
        logger.error(f"Google Maps API error: {e}")
        raise APIConnectionError(f"Failed to search restaurants: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in restaurant search: {e}")
        raise FastFoodOptimizerError(f"Restaurant search failed: {e}")
```

## 2. User Interface Standards

### 2.1 Command Line Interface

#### Consistent Command Structure
```bash
# Primary commands follow verb-noun pattern
ffro search --area "Salt Lake City" --radius 50000
ffro optimize --restaurants restaurants.json --output route.json
ffro visualize --route route.json --format interactive
ffro export --route route.json --format gpx --output my_route.gpx

# Help and information
ffro --help
ffro search --help
ffro optimize --help
```

#### Progress Indicators
```python
# Consistent progress messaging
print("🔍 Searching for restaurants...")
print("📊 Found 847 restaurants in search area")
print("🧮 Calculating distance matrix...")
print("⚡ Optimizing route clusters...")
print("✅ Route optimization complete!")
print("📍 Generated route with 203 restaurants")
```

#### Output Formatting
```python
# Consistent result display
def display_optimization_results(route: Route) -> None:
    print("\n" + "="*60)
    print("        FAST FOOD ROUTE OPTIMIZATION RESULTS")
    print("="*60)
    print(f"Total Restaurants:     {route.total_restaurants}")
    print(f"Total Distance:        {route.total_distance_km:.1f} km")
    print(f"Estimated Time:        {route.estimated_hours:.1f} hours")
    print(f"Avg Restaurants/Hour:  {route.restaurants_per_hour:.1f}")
    print("="*60)
    
    print("\nTop 5 Clusters by Efficiency:")
    for i, cluster in enumerate(route.top_clusters[:5]):
        print(f"  {i+1}. {cluster.name}: {cluster.restaurant_count} restaurants")
```

### 2.2 Logging Standards

#### Log Levels and Format
```python
import logging

# Consistent logging format
LOGGING_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log level usage
logger.debug("Detailed diagnostic information")     # Debug only
logger.info("General workflow progress")           # User information  
logger.warning("Unexpected but handled situation") # Potential issues
logger.error("Error occurred, operation failed")   # Errors
logger.critical("System cannot continue")          # Critical failures
```

#### Structured Logging
```python
# Include context in log messages
logger.info(
    "Restaurant search completed",
    extra={
        "search_area": "Salt Lake City",
        "radius_km": 50,
        "restaurants_found": 847,
        "api_calls": 12,
        "duration_seconds": 45.2
    }
)
```

## 3. Visual Design Standards

### 3.1 Map Visualization

#### Color Palette
```python
# Consistent color scheme for maps
COLORS = {
    'clusters': {
        'high_density': '#2E8B57',      # Sea Green
        'medium_density': '#FFB347',    # Peach  
        'low_density': '#CD5C5C',       # Indian Red
    },
    'routes': {
        'primary': '#1E90FF',           # Dodge Blue
        'alternative': '#9370DB',       # Medium Purple
        'walking': '#32CD32',           # Lime Green
    },
    'restaurants': {
        'fast_food': '#FF6347',         # Tomato
        'food_court': '#4169E1',        # Royal Blue
        'drive_through': '#FF1493',     # Deep Pink
        'visited': '#228B22',           # Forest Green
    }
}
```

#### Map Icons and Markers
```python
# Consistent iconography
ICONS = {
    'restaurant': 'cutlery',
    'food_court': 'shopping-cart', 
    'drive_through': 'car',
    'cluster_center': 'star',
    'start_point': 'play',
    'end_point': 'stop'
}

# Marker sizing based on importance
MARKER_SIZES = {
    'restaurant': 8,
    'food_court': 12,
    'cluster_center': 15,
    'waypoints': 6
}
```

#### Legend and Labels
```python
def add_map_legend(map_object: folium.Map) -> None:
    """Add consistent legend to all maps."""
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 120px; 
                background-color: white; border: 2px solid grey; z-index: 9999; 
                font-size: 14px; padding: 10px">
    <p><b>Fast Food Route Legend</b></p>
    <p><i class="fa fa-circle" style="color:#FF6347"></i> Fast Food Restaurant</p>
    <p><i class="fa fa-circle" style="color:#4169E1"></i> Food Court</p>
    <p><i class="fa fa-star" style="color:#2E8B57"></i> Cluster Center</p>
    <p><i class="fa fa-line" style="color:#1E90FF"></i> Optimal Route</p>
    </div>
    '''
    map_object.get_root().html.add_child(folium.Element(legend_html))
```

### 3.2 Data Visualization

#### Chart Styling
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Consistent chart styling
plt.style.use('seaborn-v0_8')
CHART_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

def setup_chart_style():
    """Apply consistent styling to all charts."""
    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'legend.fontsize': 10,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10
    })
```

## 4. Documentation Standards

### 4.1 README Structure
```markdown
# Fast Food Route Optimizer

## Quick Start
[Installation and basic usage in under 5 minutes]

## Features
[Key capabilities with examples]

## Installation
[Detailed setup instructions]

## Usage
[Common use cases and examples]

## Configuration
[Environment variables and settings]

## API Reference
[Link to detailed API documentation]

## Contributing
[How to contribute to the project]

## License
[License information]
```

### 4.2 Code Comments

#### Inline Comments
```python
# Calculate walking distance between restaurants using haversine formula
distance_km = geodesic(restaurant_a.coordinates, restaurant_b.coordinates).kilometers

# Apply density-based clustering to group nearby restaurants  
# eps=0.5km ensures clusters are walkable, min_samples=3 avoids single outliers
clusters = DBSCAN(eps=0.5, min_samples=3).fit(coordinates)

# Convert cluster assignments to restaurant groups for route optimization
restaurant_clusters = group_by_cluster_id(restaurants, clusters.labels_)
```

#### Function Documentation
```python
def calculate_cluster_efficiency(cluster: RouteCluster) -> float:
    """Calculate restaurants per kilometer for cluster ranking.
    
    Efficiency is measured as the ratio of restaurants to the cluster's
    bounding circle radius. Higher values indicate more restaurants in
    a smaller walking area.
    
    Args:
        cluster: RouteCluster containing restaurant locations.
        
    Returns:
        Efficiency score as restaurants per kilometer.
        
    Note:
        Used for ranking clusters by visit priority during route optimization.
    """
```

### 4.3 Configuration Documentation

#### Environment Variables
```python
# .env.example with comprehensive documentation
# Google Maps API Configuration
GOOGLE_MAPS_API_KEY=your_api_key_here              # Required: Get from Google Cloud Console
GOOGLE_MAPS_RATE_LIMIT=50                          # Optional: API requests per second (default: 50)

# Search Configuration  
DEFAULT_SEARCH_RADIUS=50000                        # Optional: Search radius in meters (default: 50km)
MAX_RESTAURANTS=1000                               # Optional: Maximum restaurants to process (default: 1000)

# Optimization Settings
CLUSTER_MIN_RESTAURANTS=3                          # Optional: Minimum restaurants per cluster (default: 3)
WALKING_SPEED_KMH=5.0                             # Optional: Average walking speed (default: 5.0 km/h)

# Output Configuration
EXPORT_DIRECTORY=./exports                         # Optional: Output directory (default: ./exports)
MAP_OUTPUT_FORMAT=html                             # Optional: html|png|svg (default: html)
```

## 5. Testing Standards

### 5.1 Test Naming Conventions
```python
class TestRestaurantOptimizer:
    def test_search_returns_expected_restaurant_count(self):
        """Test that restaurant search returns reasonable number of results."""
        
    def test_search_handles_invalid_coordinates_gracefully(self):
        """Test error handling for invalid latitude/longitude input."""
        
    def test_optimization_produces_valid_route_sequence(self):
        """Test that route optimization returns valid visiting order."""
        
    def test_optimization_respects_walking_distance_constraints(self):
        """Test that optimized routes stay within walkable distances."""
```

### 5.2 Mock Data Standards
```python
# Consistent test data creation
@pytest.fixture
def sample_restaurants():
    """Create consistent test restaurant data."""
    return [
        Restaurant(
            place_id="test_001",
            name="McDonald's Downtown",
            coordinates=(40.7589, -111.8883),
            is_fast_food=True,
            operating_hours={"monday": {"open": "06:00", "close": "23:00"}}
        ),
        Restaurant(
            place_id="test_002", 
            name="Subway City Creek",
            coordinates=(40.7614, -111.8910),
            is_fast_food=True,
            operating_hours={"monday": {"open": "07:00", "close": "22:00"}}
        )
    ]
```

## 6. Performance Standards

### 6.1 Response Time Targets
```python
# Performance benchmarks for different operations
PERFORMANCE_TARGETS = {
    'restaurant_search': 30,      # seconds for 1000+ restaurants
    'distance_matrix': 60,        # seconds for 500x500 calculations
    'route_optimization': 120,    # seconds for 200+ restaurants
    'map_generation': 10,         # seconds for interactive map
    'export_generation': 5        # seconds for all formats
}
```

### 6.2 Memory Usage Standards
```python
# Memory efficiency guidelines
import psutil
import functools

def monitor_memory_usage(func):
    """Decorator to monitor memory usage of functions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        if memory_used > 100:  # Alert if using more than 100MB
            logger.warning(f"{func.__name__} used {memory_used:.1f}MB memory")
            
        return result
    return wrapper
```

## 7. Security Standards

### 7.1 API Key Management
```python
# Secure configuration loading
import os
from cryptography.fernet import Fernet

def load_secure_config():
    """Load configuration with encrypted API keys."""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable required")
        
    if len(api_key) < 20:
        raise ValueError("Invalid API key format")
        
    return api_key

# Never log API keys
def safe_log_api_call(endpoint: str, params: dict):
    """Log API calls without exposing sensitive data."""
    safe_params = {k: v for k, v in params.items() if k != 'key'}
    logger.info(f"API call to {endpoint} with params: {safe_params}")
```

### 7.2 Input Validation
```python
from typing import Union
import re

def validate_coordinates(lat: float, lng: float) -> bool:
    """Validate latitude and longitude values."""
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        raise ValueError("Coordinates must be numeric")
        
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90")
        
    if not (-180 <= lng <= 180):
        raise ValueError("Longitude must be between -180 and 180")
        
    return True

def sanitize_search_query(query: str) -> str:
    """Sanitize user input for restaurant searches."""
    if not isinstance(query, str):
        raise ValueError("Search query must be a string")
        
    # Remove special characters that could be used for injection
    sanitized = re.sub(r'[<>"\';]', '', query)
    
    # Limit length to prevent DoS
    if len(sanitized) > 100:
        raise ValueError("Search query too long")
        
    return sanitized.strip()
```

---

**Style Guide Compliance**: All code must pass automated style checks before commit  
**Review Process**: Style guide adherence verified in all pull requests  
**Updates**: Style guide updated quarterly or when new patterns emerge

**Document Version**: 1.0  
**Last Updated**: January 11, 2026  
**Next Review**: Upon completion of Sprint Breakdown Document