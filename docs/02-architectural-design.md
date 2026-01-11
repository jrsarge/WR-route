# Fast Food Route Optimizer - Architecture Design Document

## 1. System Overview

### Architecture Philosophy
The Fast Food Route Optimizer follows a modular, data-driven architecture designed for:
- **Separation of Concerns**: Data collection, processing, optimization, and visualization as distinct modules
- **Extensibility**: Plugin-based approach for new optimization algorithms and data sources
- **Testability**: Each component can be unit tested independently
- **Performance**: Efficient algorithms for large-scale route optimization

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │────│  Business Logic │────│   Presentation  │
│                 │    │                 │    │                 │
│ • Google APIs   │    │ • Route Optimizer│    │ • CLI Interface │
│ • Local Cache   │    │ • Clustering     │    │ • Web Visualizer│
│ • Config Files  │    │ • Distance Calc  │    │ • Export Utils  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. System Components

### 2.1 Data Layer

#### Google Maps API Client
```python
class GoogleMapsClient:
    - places_search()      # Restaurant discovery
    - distance_matrix()    # Travel calculations  
    - geocoding()         # Address resolution
    - place_details()     # Operating hours, ratings
```

#### Data Models
```python
@dataclass
class Restaurant:
    place_id: str           # UNIQUE identifier - Google Places ID
    name: str               # Chain/restaurant name (CAN be duplicate)
    address: str            # Physical address (should be unique)
    coordinates: Tuple[float, float]  # GPS coordinates
    place_types: List[str]
    operating_hours: Dict
    is_fast_food: bool
    cluster_id: Optional[int]

    # NOTE: Multiple restaurants can share the same 'name' (e.g., "McDonald's")
    # Each unique place_id represents a distinct physical location
    # This is intentional and valuable for route optimization

@dataclass  
class RouteCluster:
    cluster_id: int
    restaurants: List[Restaurant]
    centroid: Tuple[float, float]
    density_score: float
    estimated_time: int
```

#### Cache Management
```python
class DataCache:
    - save_restaurants()   # Persist API results (by place_id, not name)
    - load_restaurants()   # Resume from cache
    - invalidate()        # Force refresh
    - is_valid()         # Check freshness
    - deduplicate_by_place_id()  # Remove duplicate place_ids ONLY (not names)
```

### 2.2 Business Logic Layer

#### Restaurant Discovery Engine
```python
class RestaurantDiscovery:
    - search_by_location()     # Geographic search
    - filter_fast_food()       # Apply criteria
    - enrich_with_details()    # Add metadata
    - validate_data()          # Quality checks
```

#### Clustering Algorithm
```python
class RestaurantClusterer:
    - density_clustering()     # DBSCAN-based grouping
    - calculate_centroids()    # Cluster centers
    - rank_by_efficiency()     # Density scoring
    - merge_nearby_clusters()  # Optimization
```

#### Route Optimization Engine
```python
class RouteOptimizer:
    - calculate_distances()        # Build distance matrix
    - optimize_cluster_sequence()  # Inter-cluster routing
    - optimize_intra_cluster()     # Within cluster routing
    - generate_alternatives()      # Backup routes
```

#### Geographic Calculator
```python
class GeoCalculator:
    - haversine_distance()     # Great circle distance
    - walking_time()           # Pace-based timing
    - bearing_calculation()    # Direction finding
    - bounds_checking()        # Area validation
```

### 2.3 Presentation Layer

#### Command Line Interface
```python
class CLI:
    - configure_search()       # Set parameters
    - run_discovery()         # Execute search
    - show_progress()         # Status updates
    - export_results()        # Output generation
```

#### Web Visualizer
```python
class WebVisualizer:
    - render_map()            # Interactive mapping
    - highlight_clusters()     # Color-coded regions  
    - show_route_options()    # Multiple paths
    - export_to_formats()     # GPX, KML, CSV
```

#### Export Utilities
```python
class ExportManager:
    - to_csv()               # Spreadsheet format
    - to_gpx()              # GPS device format
    - to_json()             # API integration
    - to_kml()              # Google Earth format
```

## 3. Data Flow Architecture

### 3.1 Primary Data Flow
```
Input Parameters → Restaurant Discovery → Data Enrichment → 
Clustering Analysis → Route Optimization → Visualization → Export
```

### 3.2 Detailed Flow Diagram
```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ User Config │──▶│Google Places│──▶│   Filter    │
│• Search Area│   │   Search    │   │ Fast Food   │
│• Preferences│   │             │   │  Criteria   │
└─────────────┘   └─────────────┘   └─────────────┘
                                            │
                                            ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Export    │◀──│    Route    │◀──│  Clustering │
│  Results    │   │Optimization │   │  Analysis   │
│• GPS Files  │   │             │   │             │
│• Maps       │   │             │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
```

## 4. Technology Stack

### 4.1 Core Technologies

#### Backend Framework
- **Language**: Python 3.9+
- **Rationale**: Excellent geospatial libraries, rapid prototyping, strong data science ecosystem

#### Key Libraries
```python
# API Integration
googlemaps==4.10.0           # Google Maps API client
requests==2.31.0             # HTTP requests with retry

# Data Processing  
pandas==2.0.3                # Data manipulation
numpy==1.24.3                # Numerical computing
scipy==1.11.1                # Scientific computing

# Geospatial Analysis
geopy==2.3.0                 # Distance calculations
shapely==2.0.1               # Geometric operations
geopandas==0.13.2            # Geospatial dataframes

# Clustering & Optimization
scikit-learn==1.3.0          # Machine learning algorithms
ortools==9.7.2996            # Route optimization (TSP)

# Visualization
folium==0.14.0               # Interactive maps
matplotlib==3.7.2            # Static plotting
plotly==5.15.0               # Interactive plotting

# CLI & Configuration
click==8.1.6                 # Command line interface
python-dotenv==1.0.0         # Environment management
pydantic==2.1.1              # Data validation
```

### 4.2 External Services

#### Google Cloud Platform
- **Places API**: Restaurant discovery and details
- **Distance Matrix API**: Travel time/distance calculations  
- **Geocoding API**: Address resolution and validation
- **Rate Limits**: 1000 requests/day (free), 100 requests/second

#### Alternative Data Sources (Backup)
- **OpenStreetMap**: Overpass API for restaurant data
- **Yelp API**: Business details and ratings
- **Foursquare**: Location data and operating hours

## 5. Database Design

### 5.1 Data Storage Strategy
**Primary**: File-based storage (JSON, CSV, Pickle)
- Simple deployment without database dependencies
- Version control friendly for route iterations
- Fast read/write for moderate data volumes (<10k restaurants)

### 5.2 Data Schema

#### Restaurants Table (JSON)
```json
{
  "place_id": "string",
  "name": "string", 
  "address": "string",
  "latitude": "float",
  "longitude": "float",
  "place_types": ["array"],
  "operating_hours": {
    "monday": {"open": "06:00", "close": "23:00"},
    "tuesday": {"open": "06:00", "close": "23:00"}
  },
  "is_fast_food": "boolean",
  "confidence_score": "float",
  "last_updated": "datetime"
}
```

#### Clusters Table (JSON)
```json
{
  "cluster_id": "integer",
  "restaurants": ["array of place_ids"],
  "centroid_lat": "float",
  "centroid_lng": "float", 
  "restaurant_count": "integer",
  "density_score": "float",
  "estimated_walking_time": "integer"
}
```

#### Routes Table (JSON)
```json
{
  "route_id": "string",
  "cluster_sequence": ["array of cluster_ids"],
  "total_restaurants": "integer",
  "total_distance_km": "float",
  "estimated_total_time": "integer",
  "created_at": "datetime"
}
```

## 6. API Design

### 6.1 Internal API Structure

#### Configuration API
```python
class Config:
    def load_config(config_path: str) -> Dict
    def validate_api_key() -> bool
    def set_search_parameters(**kwargs) -> None
```

#### Discovery API
```python
class RestaurantAPI:
    def search_area(lat: float, lng: float, radius: int) -> List[Restaurant]
    def get_place_details(place_id: str) -> Restaurant
    def batch_distance_matrix(origins: List, destinations: List) -> Matrix
```

#### Optimization API  
```python
class OptimizationAPI:
    def cluster_restaurants(restaurants: List[Restaurant]) -> List[RouteCluster]
    def optimize_route(clusters: List[RouteCluster]) -> Route
    def calculate_alternatives(route: Route, count: int) -> List[Route]
```

### 6.2 External API Integration

#### Google Maps API Wrapper
```python
class GoogleMapsWrapper:
    def __init__(self, api_key: str, rate_limit: int = 50)
    
    @retry(max_attempts=3)
    def places_nearby(self, location: str, radius: int) -> Dict
    
    @rate_limited  
    def distance_matrix(self, origins: List, destinations: List) -> Dict
    
    def handle_api_errors(self, response: requests.Response) -> None
```

## 7. Performance Considerations

### 7.1 Optimization Strategies

#### Caching Strategy
- **API Response Caching**: 24-hour TTL for restaurant data
- **Distance Matrix Caching**: Persistent storage for calculated distances  
- **Route Caching**: Save optimized routes for reuse

#### Algorithmic Optimizations
- **Spatial Indexing**: KD-tree for efficient nearest neighbor searches
- **Clustering Optimization**: DBSCAN with optimized epsilon values
- **TSP Approximation**: Christofides algorithm for route optimization
- **Parallel Processing**: Multi-threaded API requests where possible

### 7.2 Scalability Considerations

#### Memory Management
- **Streaming Processing**: Process large datasets in chunks
- **Lazy Loading**: Load restaurant details on-demand
- **Memory Monitoring**: Track usage during optimization

#### API Rate Limiting
```python
class RateLimiter:
    def __init__(self, requests_per_second: int = 10)
    def wait_if_needed(self) -> None
    def track_usage(self) -> Dict[str, int]
```

## 8. Security Architecture

### 8.1 API Key Management
```python
# Environment variable loading
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Validation
if not GOOGLE_MAPS_API_KEY:
    raise ConfigurationError("Google Maps API key required")
```

### 8.2 Data Privacy
- No storage of user location data beyond session
- Restaurant data considered public information
- Export files contain no personally identifiable information

### 8.3 Input Validation
```python
class LocationValidator:
    @staticmethod
    def validate_coordinates(lat: float, lng: float) -> bool
    
    @staticmethod  
    def validate_search_radius(radius: int) -> bool
    
    @staticmethod
    def sanitize_search_query(query: str) -> str
```

## 9. Testing Strategy

### 9.1 Unit Testing
```python
# Test coverage for each component
class TestRestaurantDiscovery:
    def test_search_by_location()
    def test_filter_fast_food() 
    def test_validate_data()

class TestRouteOptimizer:
    def test_distance_calculation()
    def test_cluster_optimization()
    def test_route_generation()
```

### 9.2 Integration Testing
- Google Maps API response handling
- End-to-end route generation workflow
- Export format validation

### 9.3 Performance Testing
- Large dataset processing (1000+ restaurants)
- API rate limit compliance
- Memory usage monitoring

## 10. Deployment Architecture

### 10.1 Local Development
```bash
# Development environment setup
python -m venv fast_food_optimizer
source fast_food_optimizer/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure API keys in .env
```

### 10.2 Production Considerations
- **Containerization**: Docker for consistent environments
- **CI/CD**: GitHub Actions for testing and deployment
- **Monitoring**: Basic logging and error tracking
- **Backup**: Route data versioning and recovery

---

**Document Version**: 1.0  
**Last Updated**: January 11, 2026  
**Next Review**: Upon completion of Development Phases Document