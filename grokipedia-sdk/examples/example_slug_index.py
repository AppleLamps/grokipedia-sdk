"""Examples for using SlugIndex directly"""

from grokipedia_sdk import SlugIndex
import os


def example_create_slug_index():
    """Create and use a SlugIndex directly"""
    print("=" * 60)
    print("Example 1: Create SlugIndex Directly")
    print("=" * 60)
    
    # Create a SlugIndex instance
    # Uses default links directory in the package
    index = SlugIndex()
    
    print(f"\nSlugIndex created")
    print(f"Total articles: {index.get_total_count():,}")
    
    # Search for articles
    results = index.search("python", limit=5)
    print(f"\nSearch results for 'python':")
    for i, slug in enumerate(results, 1):
        print(f"  {i}. {slug}")


def example_custom_links_directory():
    """Use SlugIndex with custom links directory"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Links Directory")
    print("=" * 60)
    
    # Use a custom directory for sitemap data
    links_dir = os.path.join(os.path.dirname(__file__), "..", "grokipedia_sdk", "links")
    
    if os.path.exists(links_dir):
        index = SlugIndex(links_dir=links_dir)
        
        print(f"\nUsing custom links directory: {links_dir}")
        print(f"Total articles: {index.get_total_count():,}")
    else:
        print(f"Links directory not found: {links_dir}")


def example_slug_index_methods():
    """Demonstrate SlugIndex methods"""
    print("\n" + "=" * 60)
    print("Example 3: SlugIndex Methods")
    print("=" * 60)
    
    index = SlugIndex()
    
    # Check if slug exists
    print("\nChecking if slugs exist:")
    for slug in ["Joe_Biden", "Elon_Musk", "NonExistent_Article"]:
        exists = index.exists(slug)
        status = "✓ EXISTS" if exists else "✗ NOT FOUND"
        print(f"  {slug}: {status}")
    
    # Find best match
    print("\nFinding best matches:")
    queries = ["joe biden", "elon musk", "artificial intelligence"]
    for query in queries:
        best = index.find_best_match(query)
        print(f"  '{query}' -> {best}")
    
    # List by prefix
    print("\nListing articles by prefix:")
    prefixes = ["Python", "Java"]
    for prefix in prefixes:
        articles = index.list_by_prefix(prefix=prefix, limit=5)
        print(f"  '{prefix}': {len(articles)} articles")
        for article in articles[:3]:
            print(f"    - {article}")


def example_fuzzy_search():
    """Demonstrate fuzzy search with SlugIndex"""
    print("\n" + "=" * 60)
    print("Example 4: Fuzzy Search")
    print("=" * 60)
    
    index = SlugIndex()
    
    # Test fuzzy search with typos
    queries = [
        "joe bidden",  # typo
        "elon mask",   # typo
        "artifical",   # typo
    ]
    
    print("\nFuzzy search (handles typos):")
    for query in queries:
        results = index.search(query, limit=3, fuzzy=True)
        print(f"  '{query}':")
        for slug in results:
            print(f"    - {slug}")
    
    # Compare with fuzzy disabled
    print("\nExact search (no fuzzy):")
    for query in queries:
        results = index.search(query, limit=3, fuzzy=False)
        print(f"  '{query}': {len(results)} results")


def example_get_random_articles():
    """Get random articles using SlugIndex"""
    print("\n" + "=" * 60)
    print("Example 5: Random Articles")
    print("=" * 60)
    
    index = SlugIndex()
    
    print("\nGetting random articles:")
    random_slugs = index.random_slugs(count=5)
    
    for i, slug in enumerate(random_slugs, 1):
        print(f"  {i}. {slug}")


def example_statistics():
    """Get statistics from SlugIndex"""
    print("\n" + "=" * 60)
    print("Example 6: Statistics")
    print("=" * 60)
    
    index = SlugIndex()
    
    total = index.get_total_count()
    print(f"\nTotal articles in index: {total:,}")
    
    # Get some sample articles
    sample = index.list_by_prefix(prefix="", limit=10)
    print(f"\nSample articles: {len(sample)}")
    
    # Analyze prefixes
    print("\nAnalyzing article prefixes:")
    prefixes = ["A", "B", "C", "Python", "Java"]
    for prefix in prefixes:
        count = len(index.list_by_prefix(prefix=prefix, limit=1000))
        print(f"  '{prefix}': {count} articles")


def example_batch_operations():
    """Demonstrate batch operations with SlugIndex"""
    print("\n" + "=" * 60)
    print("Example 7: Batch Operations")
    print("=" * 60)
    
    index = SlugIndex()
    
    # Batch check multiple slugs
    slugs_to_check = [
        "Joe_Biden",
        "Elon_Musk",
        "Artificial_Intelligence",
        "Python_(programming_language)",
        "NonExistent_Article_123"
    ]
    
    print("\nBatch checking slugs:")
    existing = []
    missing = []
    
    for slug in slugs_to_check:
        if index.exists(slug):
            existing.append(slug)
        else:
            missing.append(slug)
    
    print(f"  Existing: {len(existing)}")
    for slug in existing:
        print(f"    ✓ {slug}")
    
    print(f"\n  Missing: {len(missing)}")
    for slug in missing:
        print(f"    ✗ {slug}")


def example_search_comparison():
    """Compare different search strategies"""
    print("\n" + "=" * 60)
    print("Example 8: Search Comparison")
    print("=" * 60)
    
    index = SlugIndex()
    query = "python programming"
    
    print(f"\nSearch query: '{query}'\n")
    
    # Fuzzy search
    fuzzy_results = index.search(query, limit=5, fuzzy=True)
    print(f"Fuzzy search ({len(fuzzy_results)} results):")
    for slug in fuzzy_results:
        print(f"  - {slug}")
    
    # Exact search
    exact_results = index.search(query, limit=5, fuzzy=False)
    print(f"\nExact search ({len(exact_results)} results):")
    for slug in exact_results:
        print(f"  - {slug}")
    
    # Best match
    best = index.find_best_match(query)
    print(f"\nBest match: {best}")


if __name__ == "__main__":
    print("\nGrokipedia SDK - SlugIndex Examples")
    print("=" * 60)
    
    try:
        example_create_slug_index()
        example_custom_links_directory()
        example_slug_index_methods()
        example_fuzzy_search()
        example_get_random_articles()
        example_statistics()
        example_batch_operations()
        example_search_comparison()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

