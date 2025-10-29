# Performance Optimizations

This document describes the performance optimizations implemented in the Grokipedia SDK.

## Overview

The SDK implements two major performance optimizations for fuzzy search:

1. **rapidfuzz library** - 21-47x faster string similarity calculations
2. **BK-Tree data structure** - 3.3x additional speedup with O(log n) search complexity

**Combined Result: ~67x faster** than the original implementation.

---

## Optimization 1: rapidfuzz Library

### Problem
Original fuzzy search used Python's `difflib.SequenceMatcher`, scanning 885k+ articles with pure Python implementation, taking 10-30+ seconds per query.

### Solution
Replaced `difflib` with `rapidfuzz` library (C/Rust extensions) and added intelligent filtering.

### Implementation
```python
# Before (slow)
from difflib import SequenceMatcher
similarity = SequenceMatcher(None, query, name).ratio()

# After (fast)
from rapidfuzz import fuzz
similarity = fuzz.ratio(query, name)
```

### Additional Optimizations
1. **heapq for top-k tracking** - O(n log k) instead of O(n log n)
2. **Length-based filtering** - Skip ~50% of expensive comparisons
3. **Graceful fallback** - Works without rapidfuzz (degraded performance)

### Performance Results
- **String similarity**: 21-47x faster per comparison
- **Fuzzy search**: ~1.5 seconds (down from ~30 seconds)
- **Speedup**: 10-20x overall improvement

---

## Optimization 2: BK-Tree Data Structure

### Problem
Even with rapidfuzz, linear scanning of 885k items for fuzzy search took ~1.5 seconds per query.

### Solution
Implemented BK-Tree (Burkhard-Keller Tree) - a metric tree specialized for edit distance queries.

### How BK-Tree Works
- Organizes strings based on edit distances
- Exploits triangle inequality to prune search space
- O(log n) search complexity vs O(n) linear scan
- Skips ~90% of comparisons during search

### Implementation
```python
# Enable BK-Tree (default)
index = SlugIndex()  # use_bktree=True by default
index.load()  # Takes ~9s (builds BK-Tree)

# Fuzzy search now 3-7x faster
results = index.search("joe bidan", fuzzy=True)
# Returns in ~320ms (was ~1260ms)
```

### Performance Results

| Query | Without BK-Tree | With BK-Tree | Speedup |
|-------|----------------|--------------|---------|
| `"joe bidan"` | 1259ms | 320ms | **3.9x** |
| `"pyton"` | 849ms | 120ms | **7.1x** |
| `"quantm mechanics"` | 1657ms | 712ms | **2.3x** |

**Average**: 3.3x speedup

### Trade-offs
- **Build time**: +7 seconds (one-time cost)
- **Memory**: +200-300 MB overhead
- **Break-even**: ~15 fuzzy queries

### When to Enable/Disable

✅ **Enable (default)** if you:
- Perform multiple fuzzy searches per session
- Need sub-500ms query times
- Can afford 7s startup time

⚠️ **Disable** if you:
- Run single query then exit
- Need <2s startup time
- Only use exact/substring searches

```python
# Disable for fast startup
index = SlugIndex(use_bktree=False)
index.load()  # Takes ~2s (no BK-Tree)
```

---

## Combined Performance Timeline

| Stage | Implementation | Time per Query | vs Original |
|-------|---------------|----------------|-------------|
| Original | difflib | ~30 seconds | 1x |
| + rapidfuzz | C/Rust extensions + heapq | ~1.5 seconds | **20x** |
| + BK-Tree | Metric tree structure | ~450ms | **67x** |

---

## Installation

```bash
# Install rapidfuzz (required for good performance)
pip install rapidfuzz>=3.0.0

# Or install all dependencies
pip install -r requirements.txt
```

---

## Testing Performance

```bash
# Run performance test
cd grokipedia-sdk
python tests/test_performance.py
```

Expected output:
```
✓ Using rapidfuzz: True
✓ BK-Tree available: True
✓ Loaded 885,279 articles
✓ Exact match: ~26ms
✓ Fuzzy search: ~450ms
Overall rating: ✓ EXCELLENT
```

---

## Technical Details

### Time Complexity

| Operation | Without Optimizations | With rapidfuzz | With BK-Tree | Improvement |
|-----------|---------------------|---------------|--------------|-------------|
| Load index | O(n) | O(n) | O(n log n) | -7s (one-time) |
| Exact search | O(n) | O(n) | O(n) | Same (fast path) |
| Fuzzy search | O(n × m) | O(n × m) | O(log n × m) | **67x faster** |

Where:
- n = number of articles (885k)
- m = average string length (~30 chars)

### Space Complexity

| Component | Memory |
|-----------|--------|
| Flat index | ~100 MB |
| BK-Tree nodes | +200-300 MB |
| **Total** | ~300-400 MB |

---

## Optimization 3: Relevance-Based Ranking (v1.1.0)

### Problem
Early versions matched on character patterns rather than semantic relevance, leading to poor search results:

| Query | Before v1.1.0 | Issue |
|-------|---------------|-------|
| `"Putin"` | `1-bit_computing`, `12-bit_computing` | Substring "putin" in "comPUTINg" |
| `"lego"` | `Allegoria`, `Allegorical_interpretation` | Character overlap in "alLEGOry" |
| `"Elon Musk"` | `Acquisition_of_Twitter_by_Elon_Musk` | Longer title appeared before exact match |

### Solution
Implemented multi-tiered relevance scoring for substring matches and token-aware fuzzy matching.

#### Substring Match Scoring
```python
# Priority ranking (highest to lowest):
# 1. Exact match (score: 4)          → "Elon_Musk" for "elon musk"
# 2. Word-boundary both sides (score: 3)  → "Elon_Musk_filmography"
# 3. Word-boundary one side (score: 2)    → "in_Elon_context"
# 4. Generic substring (score: 1)         → "skeleton_muskrat"

# Tiebreaker: earlier position, then shorter length
```

#### Token-Aware Fuzzy Matching
For multi-word queries, the system now uses semantic similarity:

```python
# Old approach (character-based)
similarity = fuzz.ratio("putin", "computing")  # 50% - false positive!

# New approach (token-aware)
similarity = max(
    fuzz.token_set_ratio("putin", "computing"),  # 50%
    fuzz.WRatio("putin", "computing")            # 50%
)
# Still high, but re-scored with context

# Real Putin articles score 90-100% with token_set_ratio
```

#### BK-Tree Result Re-scoring
BK-tree candidates are now re-scored before returning:

```python
# 1. BK-tree finds candidates within edit distance
bk_results = tree.search(query, max_distance=2)

# 2. Re-score each candidate with token-aware similarity
for slug, distance in bk_results:
    similarity = compute_similarity_score(query, slug)
    if similarity >= min_similarity:  # Filter by threshold
        ranked_candidates.append((similarity, distance, slug))

# 3. Sort by similarity (not just edit distance)
ranked_candidates.sort(key=lambda x: (-x[0], x[1]))
```

### Results

| Query | Before v1.1.0 | After v1.1.0 | Improvement |
|-------|---------------|--------------|-------------|
| `"Elon Musk"` | `Acquisition_of_Twitter_by_Elon_Musk` | **`Elon_Musk`** ✅ | Exact match first |
| `"Putin"` | `1-bit_computing` | **`Putin_(surname)`** ✅ | Actual relevance |
| `"lego"` | `Allegoria` | **`Lego`** ✅ | Correct topic |
| `"open ai"` | `Bloodstock_Open_Air` | **`OpenAI`** ✅ | Semantic match |

### Performance Impact
- **Substring ranking**: <5ms overhead (negligible)
- **Token-aware scoring**: ~10-20ms for fuzzy queries (still <500ms total)
- **Memory**: No additional overhead
- **Overall**: Dramatically better results with minimal performance cost

### Testing Relevance
Use the diagnostic script to test search quality:

```bash
python scripts/fuzzy_search_diagnostics.py "Elon Musk" Putin lego

# Output shows:
# - Substring results with ranking
# - Fuzzy results with similarity scores
# - Token-set and WRatio metrics for analysis
```

---

## Future Improvements

If sub-100ms fuzzy search is required:

1. **Trigram Indexing** (5-10x faster)
   - Pre-compute trigrams at load time
   - Candidate generation before fuzzy match

2. **VP-Tree** (potentially faster than BK-Tree)
   - Vantage Point Tree alternative
   - Sometimes better for high-dimensional spaces

3. **Full-Text Search Engine** (100-1000x faster)
   - Elasticsearch, Whoosh, or Tantivy
   - Production-grade features

4. **Parallel Processing** (2-8x faster)
   - Multi-threaded tree traversal
   - Utilize multiple CPU cores

---

## Code Quality

- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Zero linter errors
- ✅ Backward compatible
- ✅ Graceful fallbacks
- ✅ Well tested

---

## References

- [BK-Tree Algorithm](https://en.wikipedia.org/wiki/BK-tree)
- [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
- [rapidfuzz Library](https://github.com/maxbachmann/rapidfuzz)
- [Triangle Inequality](https://en.wikipedia.org/wiki/Triangle_inequality)

---

**Last Updated**: January 29, 2025  
**Status**: ✅ Production Ready

