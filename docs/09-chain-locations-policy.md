# Chain Locations Policy - CRITICAL RULE

**Document Version**: 1.0
**Last Updated**: January 11, 2026
**Priority**: CRITICAL - This affects all search, validation, and optimization logic

---

## The Rule

**Each unique physical location counts as a separate restaurant visit, regardless of chain or brand name.**

Multiple locations of the same chain (e.g., two McDonald's, three Starbucks, four Subways) are **valid, desirable, and strategically valuable** targets.

---

## Examples

### ✅ VALID Scenarios

**Scenario 1: Multiple McDonald's**
- McDonald's at 123 Main St → Valid restaurant #1
- McDonald's at 456 Oak Ave → Valid restaurant #2
- McDonald's at 789 Pine Rd → Valid restaurant #3
- **Result**: 3 separate restaurant visits

**Scenario 2: Starbucks Cluster**
- Starbucks - Downtown (place_id: abc123)
- Starbucks - City Creek (place_id: def456)
- Starbucks - Library Square (place_id: ghi789)
- **Result**: 3 separate restaurant visits in high-density cluster

**Scenario 3: Food Court with Duplicates**
- Subway - Mall Food Court → Valid
- Subway - Street Level → Valid (even in same mall)
- **Result**: 2 separate visits

### ❌ INVALID Scenarios

**Scenario 1: Same Physical Location, Different Entrance**
- Taco Bell - North entrance (place_id: xyz123)
- Taco Bell - South entrance (place_id: xyz123)
- **Result**: Only 1 visit (same place_id)

**Scenario 2: Moved Location**
- Old restaurant data with outdated coordinates
- **Result**: Invalid - location must be current

---

## Why This Matters

### Strategic Advantages

1. **Urban Density Goldmine**: Major chains cluster in high-traffic areas
   - Downtown areas may have 2-3 Starbucks within 2 blocks
   - Shopping districts often have multiple Subway, McDonald's locations
   - This is exactly what we want for maximizing restaurants/hour

2. **Route Efficiency**: Chain density = shorter walking distances
   - Three locations of same chain in 0.2 km radius = ultra-efficient
   - Better than three different brands spread over 1 km

3. **Predictable Quality**: Known chains = reliable fast service
   - Same ordering process at each location
   - Minimal time per visit

### Real-World Example: Salt Lake City Downtown

```
Block 1: Starbucks A, Subway A, McDonald's A
Block 2: Starbucks B, McDonald's B, Panda Express
Block 3: Starbucks C, Subway B, Taco Bell

Result: 9 restaurants, 3 blocks
- 3 Starbucks (valid)
- 2 Subways (valid)
- 2 McDonald's (valid)
- 1 Panda Express (valid)
- 1 Taco Bell (valid)
```

**This is ideal** - high density, walkable, and efficient.

---

## Implementation Requirements

### 1. Data Collection (Sprint 2)

**DO**:
- ✅ Collect ALL locations from Google Places API
- ✅ Preserve all results regardless of chain name
- ✅ Use `place_id` as unique identifier
- ✅ Keep duplicate chain names in dataset

**DON'T**:
- ❌ Filter by unique chain names
- ❌ Remove "duplicate" restaurants with same name
- ❌ Assume same brand = same location

### 2. Data Validation (Sprint 4)

**DO**:
- ✅ Validate `place_id` uniqueness (remove duplicate place_ids)
- ✅ Validate coordinates are different
- ✅ Check that addresses are distinct

**DON'T**:
- ❌ Flag duplicate chain names as errors
- ❌ Warn about "too many McDonald's"
- ❌ Filter to "one per chain"

### 3. Route Optimization (Sprints 5-7)

**DO**:
- ✅ Recognize chain density as valuable
- ✅ Prioritize clusters with multiple chain locations
- ✅ Calculate efficiency including all locations
- ✅ Optimize paths through chain-dense areas

**DON'T**:
- ❌ Skip locations because "we already have a McDonald's"
- ❌ Treat chain locations as less valuable
- ❌ Reduce cluster score due to "duplicates"

### 4. Visualization (Sprints 8-9)

**DO**:
- ✅ Show all locations on map
- ✅ Label each with address/identifier (not just chain name)
- ✅ Highlight chain-dense clusters
- ✅ Display total count including all locations

**DON'T**:
- ❌ Collapse multiple locations into one marker
- ❌ Hide "duplicate" chains
- ❌ Use generic "McDonald's" labels without location info

---

## Code Examples

### ✅ CORRECT: Preserve All Locations

```python
def collect_restaurants(api_client, center, radius):
    """Collect all restaurant locations from API."""
    all_restaurants = api_client.search_nearby(center, radius)

    # Filter by fast food type (service style)
    fast_food = [r for r in all_restaurants if is_fast_food(r)]

    # Deduplicate ONLY by place_id (not by name)
    seen_place_ids = set()
    unique_locations = []
    for restaurant in fast_food:
        if restaurant.place_id not in seen_place_ids:
            unique_locations.append(restaurant)
            seen_place_ids.add(restaurant.place_id)

    # Result: Multiple "McDonald's" in list is CORRECT
    return unique_locations
```

### ❌ INCORRECT: Filtering by Chain Name

```python
# DON'T DO THIS!
def collect_restaurants_WRONG(api_client, center, radius):
    """WRONG: This filters out valuable chain locations."""
    all_restaurants = api_client.search_nearby(center, radius)

    # Filter by fast food type
    fast_food = [r for r in all_restaurants if is_fast_food(r)]

    # WRONG: Deduplicating by name loses valuable locations
    seen_names = set()
    unique_restaurants = []
    for restaurant in fast_food:
        if restaurant.name not in seen_names:  # ❌ WRONG!
            unique_restaurants.append(restaurant)
            seen_names.add(restaurant.name)

    # Result: Only ONE McDonald's when there might be 5 nearby
    return unique_restaurants
```

### ✅ CORRECT: Validation

```python
def validate_restaurant_dataset(restaurants):
    """Validate collected restaurant data."""
    errors = []

    # Check for duplicate place_ids (indicates data error)
    place_ids = [r.place_id for r in restaurants]
    if len(place_ids) != len(set(place_ids)):
        errors.append("Duplicate place_ids found - API data error")

    # Check for duplicate coordinates (might be data error)
    coords = [r.coordinates for r in restaurants]
    if len(coords) - len(set(coords)) > 5:  # Allow some duplicates (buildings)
        errors.append("Suspicious number of identical coordinates")

    # DO NOT check for duplicate names - this is expected and good!

    return errors
```

### ✅ CORRECT: Cluster Analysis

```python
def analyze_cluster_value(cluster):
    """Calculate cluster value score."""
    total_restaurants = len(cluster.restaurants)
    cluster_area = calculate_area(cluster.restaurants)

    # Density = restaurants per square km
    density = total_restaurants / cluster_area

    # Bonus for chain density (multiple locations of same chains)
    chain_counts = {}
    for restaurant in cluster.restaurants:
        chain = extract_chain_name(restaurant.name)
        chain_counts[chain] = chain_counts.get(chain, 0) + 1

    # Multiple locations of popular chains = BONUS points
    chain_density_bonus = sum(count - 1 for count in chain_counts.values() if count > 1)

    # Higher score = better cluster
    return density + (chain_density_bonus * 0.5)
```

---

## Testing Requirements

### Unit Tests Must Include:

1. **Test Multiple Chain Locations**
   ```python
   def test_multiple_mcdonalds_all_preserved():
       restaurants = [
           Restaurant(place_id="abc", name="McDonald's", lat=40.1, lng=-111.1),
           Restaurant(place_id="def", name="McDonald's", lat=40.2, lng=-111.2),
           Restaurant(place_id="ghi", name="McDonald's", lat=40.3, lng=-111.3),
       ]
       result = process_restaurants(restaurants)
       assert len(result) == 3  # All three preserved
   ```

2. **Test Cluster with Chain Density**
   ```python
   def test_cluster_values_chain_density():
       # Cluster with multiple Starbucks should score higher
       cluster_a = create_cluster_with_chain_duplicates("Starbucks", count=3)
       cluster_b = create_cluster_with_unique_chains(count=3)

       assert cluster_value(cluster_a) >= cluster_value(cluster_b)
   ```

3. **Test Validation Doesn't Flag Chain Names**
   ```python
   def test_validation_allows_duplicate_names():
       restaurants = [
           Restaurant(place_id="abc", name="Subway"),
           Restaurant(place_id="def", name="Subway"),  # Different location
       ]
       errors = validate_restaurants(restaurants)
       assert len(errors) == 0  # No errors for duplicate names
   ```

---

## Documentation References

This policy is documented in:
- ✅ `00-project-summary.md` - Core Challenge section
- ✅ `01-prd.md` - Functional Requirements (FR-006)
- ✅ `02-architectural-design.md` - Data Models comments
- ✅ `06-claude.md` - Business Requirements and Classification Rules
- ✅ `09-chain-locations-policy.md` - This document (master reference)

---

## Quick Reference Card

**Question**: Two McDonald's one block apart - are they both valid?
**Answer**: ✅ YES - Each physical location counts

**Question**: Should we filter to one location per chain?
**Answer**: ❌ NO - Keep all locations

**Question**: Is chain density good or bad?
**Answer**: ✅ GOOD - More restaurants per walking distance

**Question**: How do we identify duplicates?
**Answer**: Only by `place_id`, never by name

**Question**: What about food courts with same chains?
**Answer**: Each vendor location is separate if it has unique place_id

---

**REMEMBER**: The goal is maximizing PHYSICAL LOCATIONS visited, not unique brand count. Chain density is a strategic advantage, not a problem to solve.

**Document Version**: 1.0
**Status**: ACTIVE - All developers must follow this policy
**Next Review**: After Sprint 2 (Data Collection) validation
