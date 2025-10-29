# Changelog

All notable changes to the Grokipedia SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-29

### Changed
- **BREAKING IMPROVEMENT**: Substring matching now ranks by relevance instead of dictionary order
  - Exact matches now appear first, followed by word-boundary matches, then prefix matches
  - Eliminates cases where longer irrelevant titles appeared before exact matches
- Fuzzy search now uses token-aware scoring (`token_set_ratio`, `WRatio`) for multi-word queries
  - Dramatically reduces false positives from shared character patterns
  - Better semantic matching for natural language queries
- BK-tree fuzzy candidates are now re-scored with similarity metrics before returning
  - Ensures all returned results meet the minimum similarity threshold
  - Improves relevance of fuzzy match results

### Fixed
- Fixed "Putin" returning computing-related articles (`*-bit_computing`) due to substring "putin" in "computing"
- Fixed "lego" matching "allegory" articles instead of actual Lego content
- Fixed best match returning less relevant longer titles before exact matches (e.g., `Acquisition_of_Twitter_by_Elon_Musk` before `Elon_Musk`)
- Fixed overly aggressive character-pattern matching that ignored semantic relevance

### Added
- New `scripts/fuzzy_search_diagnostics.py` utility for testing and diagnosing search quality
  - Displays substring vs fuzzy results with similarity scores
  - Helps developers understand search behavior and tune parameters
- Substring match scoring system with configurable priorities:
  - Exact match (score: 4)
  - Word-boundary match both sides (score: 3)
  - Word-boundary match one side (score: 2)
  - Generic substring match (score: 1)
- Token-based similarity computation for multi-word queries

### Performance
- No performance regression despite improved accuracy
- BK-tree optimization still provides 3-7x speedup for fuzzy queries
- Substring ranking adds negligible overhead (<5ms for typical queries)

## [1.0.0] - 2025-01-XX

### Added
- Initial release of Grokipedia SDK
- Full article retrieval with metadata
- Summary extraction and table of contents
- Smart article search with fuzzy matching
- BK-Tree implementation for O(log n) fuzzy search
- Support for 885,000+ Wikipedia articles
- Type-safe models using Pydantic
- Context manager support for resource management
- Section navigation and extraction
- Comprehensive test suite with 68+ test cases
- Performance optimizations (rapidfuzz + BK-Tree for 67x speedup)

### Features
- `Client` class for accessing Grokipedia content
- `SlugIndex` for fast article lookup and search
- Async support via `load_async()`
- Dependency injection for testing
- Graceful fallbacks when optional dependencies missing
- Unicode and emoji support in article slugs

[1.1.0]: https://github.com/AppleLamps/grokipedia-sdk/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AppleLamps/grokipedia-sdk/releases/tag/v1.0.0

