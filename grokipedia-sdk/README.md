# Grokipedia SDK

A professional Python SDK for accessing Grokipedia content programmatically. This SDK provides a clean, simple interface to fetch articles, summaries, and sections from Grokipedia without needing to implement web scraping yourself.

**Created by [Apple Lamps](https://github.com/AppleLamps)**

## Features

- **Full Article Retrieval** - Fetch complete articles with all sections, references, and metadata
- **Summary Extraction** - Get quick summaries and table of contents
- **Smart Article Search** - Built-in search with fuzzy matching across 885,000+ articles
- **Ultra-Fast Search** - Trigram indexing (45x speedup) + BK-Tree (10x speedup) for sub-second fuzzy queries
- **Fast Slug Lookup** - Optimized BK-Tree implementation for O(log n) search performance
- **Type Safety** - Built with Pydantic for robust data validation
- **Context Manager Support** - Proper resource management with context managers
- **Section Navigation** - Fetch specific sections by title

## Installation

### From PyPI (when available)

```bash
pip install grokipedia-sdk
```

### From Source

```bash
git clone https://github.com/AppleLamps/grokipedia-sdk.git
cd grokipedia-sdk
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/AppleLamps/grokipedia-sdk.git
cd grokipedia-sdk
pip install -e ".[dev]"
```

## Requirements

- Python 3.8+
- httpx >= 0.25.0
- beautifulsoup4 >= 4.12.0
- pydantic >= 2.0.0
- lxml >= 4.9.0
- rapidfuzz >= 3.0.0

## Project Structure

```text
grokipedia-sdk/
├── grokipedia_sdk/              # Main SDK package
│   ├── __init__.py              # Package exports and version
│   ├── client.py                # Main Client class
│   ├── models.py                # Pydantic models (Article, Section, SearchResult, etc.)
│   ├── exceptions.py            # Custom exceptions
│   ├── parsers.py               # HTML parsing utilities
│   ├── slug_index.py            # Article slug indexing with BK-Tree support
│   ├── bk_tree.py               # BK-Tree implementation for fast fuzzy search
│   └── links/                   # Sitemap data files
│       └── sitemap-*/           # Multiple sitemap directories
│           ├── names.txt        # Article names
│           └── urls.txt         # Article URLs
├── tests/                       # Comprehensive test suite
│   ├── test_bk_tree.py
│   ├── test_client_async.py
│   ├── test_client_caching.py
│   ├── test_client_config.py
│   ├── test_client_http.py
│   ├── test_client_validation.py
│   ├── test_dependency_injection.py
│   ├── test_exceptions.py
│   ├── test_integration.py
│   ├── test_models.py
│   ├── test_parsers.py
│   ├── test_performance.py
│   └── test_slug_search.py
├── examples/                    # Example scripts
│   ├── example.py               # Basic usage examples
│   ├── example_slug_search.py   # Slug search examples
│   ├── example_advanced_config.py # Advanced configuration examples
│   ├── example_batch_processing.py # Batch processing examples
│   ├── example_working_with_sections.py # Working with sections examples
│   ├── example_data_extraction.py # Data extraction examples
│   ├── example_cli_tool.py      # CLI tool example
│   ├── example_slug_index.py    # SlugIndex usage examples
│   └── demo.py                  # Quick demo script
├── docs/                        # Documentation
│   ├── OPTIMIZATION.md          # Performance optimization details
│   ├── RELEASE_NOTES_v1.1.0.md  # Release notes for v1.1.0
│   └── SLUG_SEARCH_FEATURE.md   # Slug search feature documentation
├── scripts/                     # Utility scripts
│   └── fuzzy_search_diagnostics.py
├── README.md                    # This file
├── CHANGELOG.md                 # Project changelog
├── setup.py                     # Package configuration
└── pytest.ini                   # Pytest configuration
```

## Quick Start

### Basic Usage

```python
from grokipedia_sdk import Client, ArticleNotFound, RequestError

# Create a client instance
client = Client()

# Fetch a full article
try:
    article = client.get_article("Joe_Biden")
    print(f"Title: {article.title}")
    print(f"Summary: {article.summary}")
    print(f"Sections: {len(article.sections)}")
    print(f"References: {len(article.references)}")
except ArticleNotFound:
    print("Article not found")
except RequestError as e:
    print(f"Error: {e}")
finally:
    client.close()
```

### Using Context Manager (Recommended)

```python
from grokipedia_sdk import Client

# Using context manager (recommended)
with Client() as client:
    # Get article summary (faster, less data)
    summary = client.get_summary("Joe_Biden")
    print(f"Title: {summary.title}")
    print(f"Summary: {summary.summary}")
    print(f"Table of Contents: {summary.table_of_contents}")
```

### Fetching Specific Sections

```python
from grokipedia_sdk import Client

with Client() as client:
    # Get a specific section
    section = client.get_section("Joe_Biden", "Early Life")
    if section:
        print(f"Section: {section.title}")
        print(f"Content: {section.content}")
    else:
        print("Section not found")
```

### Searching for Articles

The SDK includes a local sitemap index with **885,000+ articles** and ultra-fast fuzzy search capabilities:

```python
from grokipedia_sdk import Client

with Client() as client:
    # Search for articles (fuzzy matching enabled by default)
    results = client.search_slug("joe biden")
    print(f"Found {len(results)} matches:")
    for slug in results[:5]:
        print(f"  - {slug}")
    
    # Search with typos (works great with trigram indexing!)
    typo_results = client.search_slug("artficial intel")
    print(f"\nTypo search results: {typo_results[:3]}")
    
    # Find the best match
    best_match = client.find_slug("elon musk")
    print(f"\nBest match for 'elon musk': {best_match}")
    
    # Check if an article exists
    exists = client.slug_exists("Python_(programming_language)")
    print(f"\nPython article exists: {exists}")
```

**Performance:** ~200ms for fuzzy search with trigram indexing (45x faster than baseline)

### Performance Optimizations

The SDK includes multiple performance optimization layers:

```python
from grokipedia_sdk import SlugIndex

# Ultra-fast configuration (default) - Best for production
fast_index = SlugIndex(use_trigram=True, use_bktree=True)
# Load time: ~12s, Search speed: 45x faster, Memory: 3x overhead

# Memory-efficient configuration - Good for resource-constrained environments
light_index = SlugIndex(use_trigram=True, use_bktree=False)
# Load time: ~3s, Search speed: 25x faster, Memory: 2x overhead

# Minimal configuration - Lowest memory usage
minimal_index = SlugIndex(use_trigram=False, use_bktree=False)
# Load time: ~2s, Search speed: baseline, Memory: base
```

**Performance Benchmarks (885,000+ articles):**

| Query Type | Without Optimizations | With Trigram + BK-Tree | Speedup |
|------------|----------------------|------------------------|---------|
| "joe bidan" | 5,795ms | 142ms | **40.9x** |
| "artficial intel" | 10,577ms | 204ms | **51.9x** |
| "machne learning" | 10,812ms | 419ms | **25.8x** |
| Average | 9,891ms | 216ms | **45.7x** |

> 💡 **Tip:** The default configuration (trigram + BK-Tree) provides the best performance for most use cases and pays for itself after just 1-2 fuzzy searches.

### Complete Workflow: Search -> Fetch

```python
from grokipedia_sdk import Client

with Client() as client:
    # 1. Search for an article
    query = "artificial intelligence"
    results = client.search_slug(query, limit=5)
    print(f"Found {len(results)} matches")
    
    # 2. Get the best match
    slug = client.find_slug(query)
    
    # 3. Fetch the article
    if slug:
        article = client.get_article(slug)
        print(f"Title: {article.title}")
        print(f"Content: {article.summary}")
```

## API Reference

### Client

#### `Client(base_url: str = "https://grokipedia.com", timeout: float = 30.0, slug_index: Optional[SlugIndex] = None)`

Initialize the Grokipedia SDK client.

**Parameters:**

- `base_url` (str): Base URL for Grokipedia (default: `"https://grokipedia.com"`)
- `timeout` (float): Request timeout in seconds (default: `30.0`)
- `slug_index` (Optional[SlugIndex]): Optional SlugIndex instance for article lookup. If `None`, a default SlugIndex will be created.

**Example:**

```python
# Default usage (auto-creates SlugIndex with trigram + BK-Tree)
client = Client()

# With custom SlugIndex
from grokipedia_sdk import SlugIndex
custom_index = SlugIndex(links_dir="/custom/path")
client = Client(slug_index=custom_index)

# With performance optimizations
fast_index = SlugIndex(use_trigram=True, use_bktree=True)  # Default - fastest
client = Client(slug_index=fast_index)

# Disable optimizations for minimal memory usage
minimal_index = SlugIndex(use_trigram=False, use_bktree=False)
client = Client(slug_index=minimal_index)
```

#### `get_article(slug: str) -> Article`

Get a complete article from Grokipedia by slug.

**Parameters:**

- `slug` (str): Article slug (e.g., `"Joe_Biden"`)

**Returns:**

- `Article`: Complete article object with full content, sections, references, and metadata

**Raises:**

- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

#### `get_summary(slug: str) -> ArticleSummary`

Get just the summary/intro of an article (faster, less data).

**Parameters:**

- `slug` (str): Article slug (e.g., `"Joe_Biden"`)

**Returns:**

- `ArticleSummary`: Article summary with table of contents

**Raises:**

- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

#### `get_section(slug: str, section_title: str) -> Optional[Section]`

Get a specific section of an article by title.

**Parameters:**

- `slug` (str): Article slug (e.g., `"Joe_Biden"`)
- `section_title` (str): Section title to search for

**Returns:**

- `Optional[Section]`: Section object if found, `None` otherwise

**Raises:**

- `ArticleNotFound`: If the article doesn't exist
- `RequestError`: For network or HTTP errors

#### `search_slug(query: str, limit: int = 10, fuzzy: bool = True) -> List[str]`

Search for article slugs matching a query using the local sitemap index with optimized fuzzy matching.

**Parameters:**

- `query` (str): Search query (partial name or slug, case-insensitive)
- `limit` (int): Maximum number of results to return (default: `10`)
- `fuzzy` (bool): Enable fuzzy matching for approximate matches (default: `True`)

**Returns:**

- `List[str]`: List of matching slugs ordered by relevance

#### `find_slug(query: str) -> Optional[str]`

Find the best matching slug for a query.

**Parameters:**

- `query` (str): Article name or partial slug (case-insensitive)

**Returns:**

- `Optional[str]`: Best matching slug or `None` if not found

#### `slug_exists(slug: str) -> bool`

Check if a slug exists in the sitemap index.

**Parameters:**

- `slug` (str): Slug to check

**Returns:**

- `bool`: `True` if slug exists, `False` otherwise

#### `list_available_articles(prefix: str = "", limit: int = 100) -> List[str]`

List available articles, optionally filtered by prefix.

**Parameters:**

- `prefix` (str): Filter articles starting with this prefix (case-insensitive, default: `""`)
- `limit` (int): Maximum number of results (default: `100`)

**Returns:**

- `List[str]`: List of article slugs matching the prefix

#### `get_total_article_count() -> int`

Get the total number of articles available in the index.

**Returns:**

- `int`: Total number of unique articles

#### `get_random_articles(count: int = 10) -> List[str]`

Get random article slugs from the index.

**Parameters:**

- `count` (int): Number of random slugs to return (default: `10`)

**Returns:**

- `List[str]`: List of random article slugs

### SlugIndex

#### `SlugIndex(links_dir: Optional[Path] = None, use_bktree: bool = True, use_trigram: bool = True)`

High-performance article search index with multiple optimization layers.

**Parameters:**

- `links_dir` (Optional[Path]): Path to links directory (default: auto-detect)
- `use_bktree` (bool): Enable BK-Tree for O(log n) fuzzy search (default: `True`)
  - Provides 10-100x speedup for fuzzy queries
  - Adds ~5-10 seconds to initial load time for large datasets
- `use_trigram` (bool): Enable trigram indexing for candidate filtering (default: `True`)
  - Provides 5-45x speedup by reducing search space
  - Adds ~1-2 seconds to initial load time

**Performance Characteristics:**

| Configuration | Load Time | Memory Usage | Search Speed | Best For |
|---------------|-----------|--------------|--------------|----------|
| Default (both enabled) | ~12s | 3x base | **45x faster** | Production use |
| Trigram only | ~3s | 2x base | 25x faster | Memory-constrained |
| BK-Tree only | ~10s | 3x base | 10x faster | CPU-constrained |
| Both disabled | ~2s | Base | Baseline | Minimal resources |

#### `search(query: str, limit: int = 10, fuzzy: bool = True, min_similarity: float = 0.6) -> List[str]`

Search for matching slugs with optimized fuzzy matching.

**Parameters:**

- `query` (str): Search query (can use spaces or underscores)
- `limit` (int): Maximum number of results to return (default: `10`)
- `fuzzy` (bool): Enable fuzzy matching if no exact matches found (default: `True`)
- `min_similarity` (float): Minimum similarity score for fuzzy matching (default: `0.6`)

**Returns:**

- `List[str]`: List of matching slugs, ordered by relevance

**Performance:** ~200ms for fuzzy search with 885,000+ articles (45x faster than baseline)

#### `find_best_match(query: str, min_similarity: float = 0.6) -> Optional[str]`

Find the single best matching slug for a query.

**Parameters:**

- `query` (str): Article name or partial slug
- `min_similarity` (float): Minimum similarity score for fuzzy matching

**Returns:**

- `Optional[str]`: Best matching slug or `None` if not found

#### `exists(slug: str) -> bool`

Check if a slug exists in the index.

**Parameters:**

- `slug` (str): Slug to check

**Returns:**

- `bool`: `True` if slug exists, `False` otherwise

#### `list_by_prefix(prefix: str = "", limit: int = 100) -> List[str]`

List available articles, optionally filtered by prefix.

**Parameters:**

- `prefix` (str): Filter articles starting with this prefix (case-insensitive)
- `limit` (int): Maximum number of results

**Returns:**

- `List[str]`: List of article slugs matching the prefix

#### `get_total_count() -> int`

Get the total number of articles in the index.

**Returns:**

- `int`: Total number of unique articles

#### `get_random_articles(count: int = 10) -> List[str]`

Get random article slugs from the index.

**Parameters:**

- `count` (int): Number of random slugs to return

**Returns:**

- `List[str]`: List of random article slugs

### Models

#### `Article`

Complete article response with full content:

- `title` (str): Article title
- `slug` (str): Article slug
- `url` (str): Full URL to the article
- `summary` (str): First paragraph or intro text
- `full_content` (str): Complete article text
- `sections` (List[Section]): List of article sections
- `table_of_contents` (List[str]): Table of contents
- `references` (List[str]): List of reference URLs
- `metadata` (ArticleMetadata): Article metadata
- `scraped_at` (str): ISO timestamp of when content was scraped

#### `ArticleSummary`

Summary response with essential information:

- `title` (str): Article title
- `slug` (str): Article slug
- `url` (str): Full URL to the article
- `summary` (str): Article summary
- `table_of_contents` (List[str]): Table of contents
- `scraped_at` (str): ISO timestamp

#### `Section`

Represents a section in an article:

- `title` (str): Section title
- `content` (str): Section content
- `level` (int): Heading level (1-6)

#### `SearchResult`

Search result item:

- `title` (str): Article title
- `slug` (str): Article slug
- `url` (str): Full URL to the article
- `snippet` (Optional[str]): Optional content snippet

#### `ArticleMetadata`

Metadata about the article:

- `fact_checked` (Optional[str]): Fact-check information
- `last_updated` (Optional[str]): Last update date
- `word_count` (int): Word count

### Exceptions

#### `GrokipediaError`

Base exception for the SDK. All other exceptions inherit from this.

#### `ArticleNotFound`

Raised when an article (slug) does not exist.

#### `RequestError`

Raised for network or HTTP errors.

## Custom Configuration

```python
from grokipedia_sdk import Client, SlugIndex

# Use custom base URL
client = Client(base_url="https://custom-grokipedia.com")

# Set custom timeout
client = Client(timeout=60.0)

# Combine both
client = Client(base_url="https://custom-grokipedia.com", timeout=60.0)

# With custom SlugIndex and performance optimizations
from grokipedia_sdk import SlugIndex

# Ultra-fast configuration (default)
fast_index = SlugIndex(
    links_dir="/custom/path", 
    use_trigram=True,   # 45x faster fuzzy search
    use_bktree=True     # 10x faster fuzzy search
)
client = Client(slug_index=fast_index)

# Memory-efficient configuration
minimal_index = SlugIndex(
    links_dir="/custom/path",
    use_trigram=False,  # Slower but less memory
    use_bktree=False    # Slower but less memory
)
client = Client(slug_index=minimal_index)

# Balanced configuration
balanced_index = SlugIndex(
    links_dir="/custom/path",
    use_trigram=True,   # Keep trigram for speed
    use_bktree=False    # Disable BK-Tree to save memory
)
client = Client(slug_index=balanced_index)
```

## Error Handling

```python
from grokipedia_sdk import Client, ArticleNotFound, RequestError

client = Client()

try:
    article = client.get_article("NonExistent_Article")
except ArticleNotFound:
    print("Article not found on Grokipedia")
except RequestError as e:
    print(f"Network or HTTP error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    client.close()
```

## Examples

The SDK includes comprehensive examples in the `examples/` directory:

- `examples/example.py` - Comprehensive examples of basic SDK usage
- `examples/example_slug_search.py` - Detailed examples of slug search features
- `examples/demo.py` - Quick demo script for slug search functionality
- `examples/example_advanced_config.py` - Advanced configuration options (caching, rate limiting, custom SSL, etc.)
- `examples/example_batch_processing.py` - Batch processing multiple articles with error handling
- `examples/example_working_with_sections.py` - Working with article sections and hierarchies
- `examples/example_data_extraction.py` - Data extraction and analysis examples
- `examples/example_cli_tool.py` - Example CLI tool implementation
- `examples/example_slug_index.py` - Using SlugIndex directly for article discovery

### Running Examples

```bash
# Run basic usage examples
python examples/example.py

# Run slug search examples
python examples/example_slug_search.py

# Run quick demo
python examples/demo.py

# Run advanced configuration examples
python examples/example_advanced_config.py

# Run batch processing examples
python examples/example_batch_processing.py

# Run section examples
python examples/example_working_with_sections.py

# Run data extraction examples
python examples/example_data_extraction.py

# Run CLI tool example
python examples/example_cli_tool.py --help
python examples/example_cli_tool.py search "artificial intelligence"
python examples/example_cli_tool.py summary Joe_Biden

# Run SlugIndex examples
python examples/example_slug_index.py

# Run performance benchmarks (tests trigram indexing, BK-Tree, etc.)
python tests/test_performance.py
```

## Testing

The project includes a comprehensive test suite covering all major functionality:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_slug_search.py -v

# Run with coverage
python -m pytest tests/ --cov=grokipedia_sdk --cov-report=html
```

## Performance

The SDK is optimized for performance with multiple optimization layers:

- **Trigram Indexing**: 45x faster fuzzy search by reducing search space before matching
- **BK-Tree Implementation**: O(log n) fuzzy search performance for article lookups (10x speedup)
- **Efficient Caching**: Built-in caching for frequently accessed articles
- **Optimized Parsing**: Fast HTML parsing with BeautifulSoup4 and lxml
- **Async Support**: Ready for future async/await implementations

**Benchmark Results (885,000+ articles):**
- Average fuzzy search time: **216ms** (45x faster than baseline)
- Trigram indexing reduces search space by 70-90%
- BK-Tree provides O(log n) search complexity
- Combined optimizations achieve sub-second fuzzy queries

See `docs/OPTIMIZATION.md` for detailed performance benchmarks and optimization strategies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This SDK is provided as-is for educational and development purposes. Please review Grokipedia's Terms of Service before heavy usage.

## Acknowledgments

- Created by **Apple Lamps**
- Built with modern Python best practices
- Uses [rapidfuzz](https://github.com/rapidfuzz/rapidfuzz) for fast fuzzy string matching
- Powered by [httpx](https://www.python-httpx.org/) for reliable HTTP requests

## Important Notes

- This SDK scrapes content from Grokipedia's website
- Please respect rate limits and robots.txt guidelines
- This SDK is not affiliated with Grokipedia
- Cache your results appropriately for production use
- The sitemap index includes 885,000+ articles for fast local search

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/AppleLamps/grokipedia-sdk).
