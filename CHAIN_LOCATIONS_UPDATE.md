# Chain Locations Policy - Documentation Update Summary

**Date**: January 11, 2026
**Priority**: CRITICAL
**Impact**: All sprints (data collection, validation, optimization, visualization)

---

## What Was Updated

This update clarifies a **critical business rule** that affects the entire project:

**RULE**: Each unique physical location counts as a separate restaurant visit, regardless of chain or brand name. Multiple locations of the same chain (e.g., two McDonald's one block apart) are valid and highly desirable targets.

---

## Files Updated (8 files)

### 1. ✅ `docs/01-prd.md` - Product Requirements Document

**Section 4.1 - Restaurant Discovery**
- Added prominent note explaining the rule
- Added FR-006: "Preserve all locations regardless of chain name duplication"

**Section 4.2 - Route Optimization**
- Renumbered FRs (now FR-007 through FR-012)
- Added FR-012: "Optimize for chain density"

**Section 4.3 - Data Analysis & Clustering**
- Renumbered FRs (now FR-013 through FR-015)
- Added FR-015: "Identify high-value clusters with multiple chain locations"

### 2. ✅ `docs/00-project-summary.md` - Project Summary

**Core Challenge Section**
- Added critical detail paragraph explaining chain locations rule
- Emphasized that goal is maximizing physical locations, not unique brands

**Key Algorithms Section**
- Updated DBSCAN description: "DO NOT filter duplicate chain names"
- Added algorithm: "Chain Density Recognition"

**Complete Documentation Set**
- Added new doc: "9. Chain Locations Policy (CRITICAL)"

### 3. ✅ `docs/06-claude.md` - Claude Implementation Guide

**Business Requirements Section**
- Added CRITICAL line about unique physical locations
- Clarified that multiple chain locations are valid targets

**Restaurant Classification Rules**
- Added CRITICAL note at top: "DO NOT filter out duplicate chain names"
- Added explanation of chain density advantage with example
- Updated `classify_fast_food()` docstring to clarify it classifies by TYPE not uniqueness
- Added code comment: "Finding a known chain name is GOOD, even if we've seen it before"

**Data Validation Requirements**
- Updated `validate_restaurant_data()` docstring
- Added explicit note: "DO NOT flag duplicate chain names as an issue"
- Added comment: "Multiple 'McDonald's' locations are VALID and DESIRED"

### 4. ✅ `docs/02-architectural-design.md` - Architecture Design

**Data Models Section**
- Added detailed comments to Restaurant dataclass:
  - `place_id`: "UNIQUE identifier - Google Places ID"
  - `name`: "Chain/restaurant name (CAN be duplicate)"
  - `address`: "Physical address (should be unique)"
- Added multi-line comment explaining that duplicate names are intentional and valuable

**Cache Management Section**
- Updated comment: "Persist API results (by place_id, not name)"
- Added method: `deduplicate_by_place_id()` - Remove duplicate place_ids ONLY (not names)

### 5. ✅ `docs/09-chain-locations-policy.md` - NEW MASTER REFERENCE

Created comprehensive new document (400+ lines) with:

**Core Policy**
- Clear statement of the rule
- Examples of valid and invalid scenarios
- Why this matters strategically

**Implementation Requirements**
- Detailed DO/DON'T lists for each sprint phase
- Data collection guidelines (Sprint 2)
- Validation rules (Sprint 4)
- Optimization considerations (Sprints 5-7)
- Visualization requirements (Sprints 8-9)

**Code Examples**
- ✅ CORRECT: Preserve all locations by place_id
- ❌ INCORRECT: Filtering by chain name (what NOT to do)
- ✅ CORRECT: Validation that allows duplicate names
- ✅ CORRECT: Cluster analysis with chain density bonus

**Testing Requirements**
- Unit test examples for multiple chain locations
- Cluster value testing with chain density
- Validation testing that allows duplicate names

**Quick Reference Card**
- Common questions with clear yes/no answers

### 6. ✅ `README.md` - Project README

**Overview Section**
- Added prominent CRITICAL RULE note at top
- Explains multiple chain locations are valid and desirable

### 7. ✅ Documentation Index Updated

All doc references now point to the new chain locations policy document

---

## Key Messages Added

### Strategic Advantages Highlighted

1. **Urban Density Goldmine**
   - Downtown areas may have 2-3 Starbucks within 2 blocks
   - Shopping districts often have multiple Subway, McDonald's locations
   - This is exactly what we want for maximizing restaurants/hour

2. **Route Efficiency**
   - Three locations of same chain in 0.2 km = ultra-efficient
   - Better than three different brands spread over 1 km

3. **Predictable Quality**
   - Known chains = reliable fast service
   - Same ordering process at each location
   - Minimal time per visit

### Real-World Example Added

```
Salt Lake City Downtown Example:
Block 1: Starbucks A, Subway A, McDonald's A
Block 2: Starbucks B, McDonald's B, Panda Express
Block 3: Starbucks C, Subway B, Taco Bell

Result: 9 restaurants, 3 blocks
- 3 Starbucks (valid)
- 2 Subways (valid)
- 2 McDonald's (valid)
- 1 Panda Express (valid)
- 1 Taco Bell (valid)

This is ideal - high density, walkable, and efficient.
```

---

## Implementation Impact by Sprint

### Sprint 2: Data Models & Collection
- **DO**: Keep all locations regardless of chain name
- **DON'T**: Filter by unique names
- **Action**: Use `place_id` as unique identifier

### Sprint 4: Data Quality & Validation
- **DO**: Check for duplicate `place_id` (data error)
- **DON'T**: Flag duplicate chain names as errors
- **Action**: Update validation to allow duplicate names

### Sprints 5-7: Optimization
- **DO**: Recognize chain density as valuable
- **DON'T**: Skip locations because "we already have that chain"
- **Action**: Add chain density bonus to cluster scoring

### Sprints 8-9: Visualization
- **DO**: Show all locations with unique labels
- **DON'T**: Collapse multiple locations into one marker
- **Action**: Label with address/identifier, not just chain name

---

## Code Pattern Changes

### Before (INCORRECT) ❌
```python
# DON'T DO THIS - filters out valuable locations
seen_names = set()
unique = [r for r in restaurants if r.name not in seen_names and not seen_names.add(r.name)]
```

### After (CORRECT) ✅
```python
# Deduplicate by place_id ONLY
seen_place_ids = set()
unique = [r for r in restaurants if r.place_id not in seen_place_ids and not seen_place_ids.add(r.place_id)]
```

---

## Testing Requirements Added

All future tests must include:

1. **Multiple chain locations preserved**
   ```python
   def test_multiple_mcdonalds_all_preserved():
       # 3 McDonald's with different place_ids
       assert len(result) == 3
   ```

2. **Chain density valued in clustering**
   ```python
   def test_cluster_values_chain_density():
       # Cluster with 3 Starbucks scores high
       assert high_density_score > low_density_score
   ```

3. **Validation allows duplicate names**
   ```python
   def test_validation_allows_duplicate_names():
       # Two Subways with different place_ids
       assert len(validation_errors) == 0
   ```

---

## Documentation Cross-References

The chain locations policy is now documented in:

- ✅ `00-project-summary.md` - Core Challenge + Key Algorithms
- ✅ `01-prd.md` - Functional Requirements (FR-006, FR-012, FR-015)
- ✅ `02-architectural-design.md` - Data Models + Cache Management
- ✅ `06-claude.md` - Business Requirements + Classification + Validation
- ✅ `09-chain-locations-policy.md` - **Master Reference** (NEW)
- ✅ `README.md` - Project overview

---

## Quick Reference for Developers

**Q**: Two McDonald's one block apart - valid?
**A**: ✅ YES - Each physical location counts

**Q**: Should we filter to one per chain?
**A**: ❌ NO - Keep all locations

**Q**: Is chain density good or bad?
**A**: ✅ GOOD - More restaurants per walking distance

**Q**: What makes locations unique?
**A**: `place_id` only, never name

**Q**: Food court with duplicate chains?
**A**: Each vendor location counts if unique `place_id`

---

## Impact on Sprint 1 (Already Complete)

Sprint 1 components are already compatible:
- ✅ Configuration system: No changes needed
- ✅ API Client: Uses place_id correctly
- ✅ Exceptions: No changes needed
- ✅ Logging: No changes needed

**No Sprint 1 rework required** - foundation supports this correctly!

---

## Next Steps

### For Sprint 2 (Data Models & Collection):
1. Implement Restaurant dataclass with `place_id` as primary key
2. Ensure search results preserve all locations
3. Add dedupe logic by `place_id` ONLY (not name)
4. Test with real data that has chain duplicates

### For Future Sprints:
1. Add chain density metrics to cluster analysis
2. Bonus scoring for high chain density clusters
3. Visualization labels that distinguish same-chain locations
4. Documentation examples using real chain data

---

## Summary

This update clarifies a fundamental business rule that was implicit but not explicitly documented. It ensures that:

1. **Development teams** understand the rule and implement correctly
2. **Validation logic** doesn't incorrectly flag duplicate chains
3. **Optimization algorithms** recognize chain density as valuable
4. **Testing** includes scenarios with multiple chain locations
5. **Documentation** provides clear guidance and examples

**Impact**: HIGH - Affects all data processing, validation, optimization, and visualization
**Risk of not updating**: Would have incorrectly filtered out valuable high-density chain locations
**Status**: ✅ COMPLETE - All documentation updated and new master reference created

---

**Document Version**: 1.0
**Created**: January 11, 2026
**Purpose**: Track chain locations policy documentation updates
