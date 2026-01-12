# Quick Start Guide: Running for Real

This guide will walk you through running the system with real Google Maps data to generate an actual route for your world record attempt.

---

## Prerequisites

Before you start, make sure you have:

1. **Python 3.9+** installed
2. **All dependencies** installed: `pip3 install -r requirements.txt`
3. **Google Maps API key** (see instructions below)

---

## Step 1: Get Google Maps API Key

### Create API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the following APIs:
   - **Places API (New)**
   - **Maps JavaScript API** (optional, for visualization)
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy your API key

### Enable Billing

**IMPORTANT:** You must enable billing, but you won't be charged much:
- Google gives $200/month free credits
- Places API costs ~$32/1000 requests
- Typical usage: 5-10 requests for 200 restaurants = **$0.16 - $0.32**

**You won't be charged unless you exceed $200/month**

### Restrict API Key (Optional but Recommended)

1. Click "Restrict Key"
2. Under "API restrictions":
   - Select "Restrict key"
   - Choose "Places API (New)"
3. Save

---

## Step 2: Configure API Key

Create a `.env` file in the project root:

```bash
# In the project directory
cd /Users/jacobsargent/Desktop/git/WR-route

# Create .env file
echo "GOOGLE_MAPS_API_KEY=your_api_key_here" > .env
```

Replace `your_api_key_here` with your actual API key.

**Example `.env` file:**
```
GOOGLE_MAPS_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuv
```

---

## Step 3: Configure Target City

Edit `run_real_route.py` to set your target city coordinates:

```python
# CONFIGURATION - MODIFY THESE FOR YOUR CITY
# ============================================================================

# Target city coordinates (Salt Lake City, UT by default)
TARGET_LATITUDE = 40.7589   # Change to your city
TARGET_LONGITUDE = -111.8883  # Change to your city

# Search radius in meters (20km = 20000m)
SEARCH_RADIUS = 20000  # Adjust as needed

# Route parameters
TIME_BUDGET_HOURS = 24.0  # How many hours you have
MIN_RESTAURANTS = 150  # Minimum target
```

### Finding Your City Coordinates

**Method 1: Google Maps**
1. Go to [Google Maps](https://maps.google.com)
2. Right-click on your city center
3. Click coordinates (e.g., "40.7589, -111.8883")
4. Copy the numbers

**Method 2: GPS Device**
- Use your phone's GPS to get current location coordinates

**Method 3: Online Tool**
- Use [LatLong.net](https://www.latlong.net/)

---

## Step 4: Run the Script

```bash
cd /Users/jacobsargent/Desktop/git/WR-route

# Make script executable
chmod +x run_real_route.py

# Run it!
python3 run_real_route.py
```

**Expected Output:**
```
======================================================================
FAST FOOD ROUTE OPTIMIZER - REAL DATA RUN
======================================================================

📝 Step 1: Loading configuration...
✅ API key configured
   Target: (40.7589, -111.8883)
   Radius: 20.0km

📍 Step 2: Collecting restaurants from Google Maps...
   This may take a few minutes depending on search radius...
✅ Found 847 total restaurants

🍔 Step 3: Classifying fast food restaurants...
✅ Classified 312 as fast food restaurants

   Top chains found:
   - McDonald's: 28 locations
   - Subway: 24 locations
   - Starbucks: 22 locations
   ...

🗺️  Step 6: Clustering restaurants...
✅ Created 8 clusters
   Cluster 0: 45 restaurants
   Cluster 1: 38 restaurants
   ...

🚀 Step 7: Optimizing global route...
✅ Route optimized!
   Total restaurants: 312
   Total distance: 125.34km
   Estimated time: 21.8h
   Efficiency: 14.3 restaurants/hour

✅ ALL STEPS COMPLETE!
```

---

## Step 5: Review Your Route

The script creates these files in `data/world_record_route/`:

### Maps (Open in Browser)
1. **`route_map.html`** - Your optimized route with numbered stops
2. **`clusters_map.html`** - See how restaurants are grouped
3. **`alternatives_map.html`** - Compare different route options

**To view:**
```bash
# Open route map
open data/world_record_route/route_map.html

# Or double-click the file in Finder
```

### GPS Files (In `exports/` folder)
1. **`world_record_route.gpx`** - For GPS devices
2. **`world_record_route.csv`** - For spreadsheet analysis
3. **`world_record_route.kml`** - For Google Earth
4. **`world_record_route.json`** - For mobile apps

---

## Step 6: Load onto GPS Device

### Option A: Garmin GPS Device

1. Connect Garmin to computer via USB
2. Copy `world_record_route.gpx` to `Garmin/GPX/` folder
3. Safely eject device
4. On device: Menu → Saved Routes → Select route

### Option B: Phone (Google Maps)

1. Go to [My Maps](https://mymaps.google.com)
2. Create new map
3. Click "Import"
4. Upload `world_record_route.gpx`
5. Access on phone via Google Maps app

### Option C: Phone (Dedicated GPS App)

**Recommended: Gaia GPS (free version works)**

1. Install Gaia GPS app
2. Open app → Import → Select GPX file
3. Download offline maps for area
4. Enable offline mode

---

## Step 7: Verify and Test

### Before the Actual Attempt

1. **Check the route visually:**
   - Open `route_map.html`
   - Does the route make geographic sense?
   - Any obvious backtracking?
   - Any long distances between stops?

2. **Test with first 5 restaurants:**
   - Visit the first 5 on the list
   - Make sure GPS navigation works
   - Verify restaurants are actually there
   - Check operating hours

3. **Print backup:**
   - Open `world_record_route.csv` in Excel
   - Print with large font
   - Laminate for weather protection

---

## Troubleshooting

### "No API key found"
- Make sure `.env` file exists in project root
- Check file has `GOOGLE_MAPS_API_KEY=...` with your actual key
- No quotes needed around the key

### "API key not valid"
- Verify you enabled "Places API (New)" in Google Cloud Console
- Check you copied the entire key (usually starts with "AIza")
- Make sure billing is enabled

### "Not enough restaurants found"
- Increase `SEARCH_RADIUS` (try 30000 for 30km)
- Check your target coordinates are correct
- Some cities have fewer fast food chains

### "Route validation failed"
- Increase `TIME_BUDGET_HOURS` (try 30 or 48)
- Decrease `MIN_RESTAURANTS` requirement
- Route may be too ambitious for time budget

### "Clustering creates too many clusters"
- Increase `CLUSTER_EPS_KM` (try 7.0 or 10.0)
- Decrease `CLUSTER_MIN_SAMPLES` (try 3)

---

## Customizing for Your Needs

### Different City

Edit these in `run_real_route.py`:
```python
TARGET_LATITUDE = 34.0522    # Los Angeles
TARGET_LONGITUDE = -118.2437
SEARCH_RADIUS = 25000         # 25km
```

### Longer Route

```python
TIME_BUDGET_HOURS = 48.0      # 2 days
MIN_RESTAURANTS = 300         # Higher target
```

### Tighter Clusters

```python
CLUSTER_EPS_KM = 3.0          # Smaller clusters
CLUSTER_MIN_SAMPLES = 8       # More restaurants per cluster
```

---

## Output Files Explained

### `raw_restaurants.json`
- All restaurants collected from Google Maps
- Includes coordinates, ratings, types
- Use for analysis or reprocessing

### `route_map.html`
- Interactive map with your optimized route
- Click markers to see restaurant details
- Sequential numbering shows visit order

### `world_record_route.gpx`
- **THIS IS YOUR NAVIGATION FILE**
- Load onto GPS device
- Contains waypoints in order
- Works with Garmin, phone apps

### `world_record_route.csv`
- Spreadsheet with all stops in order
- Coordinates, addresses, ratings
- Print as backup checklist
- Track progress during attempt

### `world_record_route.kml`
- Open in Google Earth
- See route in 3D
- Great for planning and visualization

### `world_record_route.json`
- Complete route data
- For custom apps or processing
- Includes all metadata

---

## Cost Estimate

Typical cost for 200-restaurant route:

| API Calls | Cost per 1000 | Total Cost |
|-----------|---------------|------------|
| Nearby Search: 8 requests | $32/1000 | $0.26 |
| (No Place Details needed) | - | - |
| **TOTAL** | | **$0.26** |

**Your $200/month free credit covers ~750,000 restaurants!**

---

## Ready to Go!

You now have:
- ✅ Real restaurant data from Google Maps
- ✅ Optimized route covering 200+ restaurants
- ✅ Interactive maps for review
- ✅ GPS file ready for your device
- ✅ Backup CSV checklist

**Next:** Load the GPX file onto your GPS device and GO BREAK THAT RECORD! 🚀

---

## Need Help?

Common issues and solutions in `TESTING.md`

Questions? Check the sprint documentation:
- `SPRINT_7_COMPLETE.md` - Route optimization
- `SPRINT_8_COMPLETE.md` - Visualization
- `SPRINT_9_COMPLETE.md` - Export formats
