# Fast Food Route Optimizer

A specialized routing system designed to help ultramarathon runner Jacob break the world record for "Most fast food restaurants visited in 24 hours." Current record: 150 restaurants. Target: 202+.

**CRITICAL RULE**: Each unique physical location counts as a separate restaurant, regardless of chain/brand name. Multiple locations of the same chain (e.g., two McDonald's one block apart) are valid and highly desirable targets for route efficiency.

## Overview

The Fast Food Route Optimizer generates optimal walking/running routes through metropolitan areas (starting with Salt Lake City) to visit the maximum number of fast food restaurants within 24 hours. It prioritizes high-density clusters (food courts, shopping centers) and efficient inter-cluster travel.

### Key Features

- **Restaurant Discovery**: Automated search using Google Maps Places API with fast food filtering
- **Intelligent Clustering**: Density-based grouping (DBSCAN) for walkable restaurant clusters
- **Route Optimization**: TSP-based algorithms for optimal visiting sequences
- **Interactive Maps**: Web-based visualization with Folium for route validation
- **Multi-Format Export**: GPX, KML, CSV, and JSON exports for GPS devices
- **Performance Focused**: Process 1000+ restaurants, optimize 200+ location routes in under 2 minutes

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Maps API key with Places, Distance Matrix, and Geocoding APIs enabled
- Get your API key at: https://console.cloud.google.com/

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/WR-route.git
cd WR-route

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your Google Maps API key
```

### Basic Usage

```python
from fast_food_optimizer.config.settings import get_config
from fast_food_optimizer.data.google_client import GoogleMapsClient

# Initialize configuration
config = get_config()

# Test API connection
client = GoogleMapsClient(
    api_key=config.google_maps_api_key,
    rate_limit=config.google_maps_rate_limit
)

if client.test_connection():
    print("✅ Google Maps API connection successful!")
```

## Project Structure

```
WR-route/
├── src/fast_food_optimizer/     # Main source code
│   ├── config/                  # Configuration management
│   ├── data/                    # Data collection and API clients
│   ├── models/                  # Data models (Restaurant, Cluster, Route)
│   ├── optimization/            # Route optimization algorithms
│   ├── visualization/           # Map generation and exports
│   ├── validation/              # Data quality and validation
│   └── utils/                   # Logging, exceptions, helpers
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docs/                        # Project documentation
├── exports/                     # Generated routes and maps
└── data/                        # Cached restaurant data
```

## Configuration

All configuration is managed through environment variables. Copy `.env.example` to `.env` and customize:

```bash
# Required
GOOGLE_MAPS_API_KEY=your_api_key_here

# Optional (with defaults)
GOOGLE_MAPS_RATE_LIMIT=50
DEFAULT_SEARCH_RADIUS=50000
MAX_RESTAURANTS=1000
CLUSTER_MIN_RESTAURANTS=3
WALKING_SPEED_KMH=5.0
EXPORT_DIRECTORY=./exports
DATA_DIRECTORY=./data
LOG_LEVEL=INFO
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fast_food_optimizer --cov-report=html

# Run specific test categories
pytest tests/unit                    # Unit tests only
pytest -m integration                # Integration tests only
pytest tests/unit/test_config.py     # Specific test file
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[00-project-summary.md](docs/00-project-summary.md)**: Project overview and master reference
- **[01-prd.md](docs/01-prd.md)**: Product requirements and specifications
- **[02-architectural-design.md](docs/02-architectural-design.md)**: System architecture and design
- **[03-development-phases.md](docs/03-development-phases.md)**: 4-phase development plan (5-8 weeks)
- **[04-style-guide.md](docs/04-style-guide.md)**: Code style and conventions
- **[05-sprint-breakdown.md](docs/05-sprint-breakdown.md)**: 11 sprints with detailed deliverables
- **[06-claude.md](docs/06-claude.md)**: Claude Code implementation guidelines
- **[07-user-stories.md](docs/07-user-stories.md)**: User stories with acceptance criteria
- **[08-product-backlog.md](docs/08-product-backlog.md)**: Future enhancements and roadmap

## Performance Targets

- **Restaurant Search**: 1000+ restaurants in <60 seconds
- **Distance Matrix**: 500×500 calculations in <60 seconds
- **Route Optimization**: 200+ restaurants in <2 minutes
- **Memory Usage**: <512MB for full dataset
- **Route Quality**: 15+ restaurants/hour in dense clusters

## Technology Stack

- **Language**: Python 3.9+
- **APIs**: Google Maps (Places, Distance Matrix, Geocoding)
- **Data Processing**: pandas, numpy, scipy
- **Geospatial**: geopy, shapely, geopandas
- **Clustering**: scikit-learn (DBSCAN)
- **Optimization**: OR-Tools (TSP)
- **Visualization**: Folium, matplotlib, plotly
- **CLI**: Click

## Development Status

**Current Sprint**: Sprint 1 - Project Setup & Infrastructure ✅

**Completed**:
- [x] Project structure and packaging
- [x] Configuration management system
- [x] Google Maps API client with authentication
- [x] Logging framework
- [x] Custom exception hierarchy
- [x] Unit test suite

**Next Sprint**: Sprint 2 - Data Models & Basic Collection

See [05-sprint-breakdown.md](docs/05-sprint-breakdown.md) for detailed sprint planning.

## License

MIT License - See LICENSE file for details

## Author

Jacob Sargent - Ultramarathon runner, product manager, and world record aspirant

## Acknowledgments

- Current world record holder for inspiration
- Google Maps Platform for location data
- Open source Python geospatial community

---

**Project Goal**: Enable Jacob to break the world record for most fast food restaurants visited in 24 hours by providing optimal, data-driven route planning.

**Target**: 202+ restaurants in 24 hours (current record: 150)

**Timeline**: 5-8 weeks development across 11 sprints
