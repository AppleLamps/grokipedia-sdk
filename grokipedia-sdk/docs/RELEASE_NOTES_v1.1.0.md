# Release Notes - v1.1.0

## 🎯 Major Improvement: Relevance-Based Search

This release dramatically improves search quality by fixing overly aggressive fuzzy matching that was returning irrelevant results based on character patterns rather than semantic relevance.

### ✨ What's New

#### Smarter Substring Matching
- **Exact matches now appear first** - No more seeing `Acquisition_of_Twitter_by_Elon_Musk` before `Elon_Musk`
- **Word-boundary awareness** - Prioritizes matches at word boundaries over character-pattern matches
- **Multi-tiered scoring system** - Exact > Word-boundary > Prefix > Generic substring

#### Token-Aware Fuzzy Search
- **Semantic similarity** - Uses `token_set_ratio` and `WRatio` for multi-word queries
- **Eliminates false positives** - "Putin" no longer matches "*-bit_computing" articles
- **Re-scored BK-tree results** - All fuzzy candidates verified for actual relevance

### 🐛 Bugs Fixed

| Query | Before | After |
|-------|--------|-------|
| `"Putin"` | `1-bit_computing` ❌ | `Putin_(surname)` ✅ |
| `"lego"` | `Allegoria` ❌ | `Lego` ✅ |
| `"Elon Musk"` | `Acquisition_of_Twitter_by_Elon_Musk` ❌ | `Elon_Musk` ✅ |

### 🛠️ New Tools

**Fuzzy Search Diagnostics Script**
```bash
python scripts/fuzzy_search_diagnostics.py "your query" --limit 10
```

Displays:
- Substring vs fuzzy results
- Similarity scores (ratio, token_set, WRatio)
- Best match with metrics

### 📊 Performance

- **No regression** - Search remains fast (<500ms for fuzzy queries)
- **Minimal overhead** - Relevance ranking adds <5ms
- **Same memory footprint** - No additional overhead

### 🧪 Testing

All 68 tests passing ✅
- Unit tests for new scoring functions
- Integration tests for search behavior
- Performance benchmarks maintained

### 🔄 Upgrade Guide

**Breaking Changes:** None! API remains fully backward compatible.

**Recommended Actions:**
1. Update to v1.1.0: `pip install --upgrade grokipedia-sdk`
2. Re-run `pip install -e .` if using editable install
3. Test your search queries - you should see better results!

### 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.

### 🙏 Acknowledgments

Thanks to the community for reporting search quality issues that led to these improvements!

---

**Release Date:** January 29, 2025  
**Version:** 1.1.0  
**Status:** ✅ Production Ready

