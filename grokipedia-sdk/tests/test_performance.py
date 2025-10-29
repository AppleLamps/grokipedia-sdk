"""Performance test for optimized fuzzy search"""

import time
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from grokipedia_sdk.slug_index import SlugIndex, HAS_RAPIDFUZZ

def test_search_performance():
    """Test the performance of the search function"""
    
    print("=" * 70)
    print("Grokipedia SDK - Fuzzy Search Performance Test")
    print("=" * 70)
    print(f"\nUsing rapidfuzz: {HAS_RAPIDFUZZ}")
    if not HAS_RAPIDFUZZ:
        print("⚠️  WARNING: rapidfuzz not installed, using slow difflib fallback")
    print()
    
    # Initialize index
    print("Loading slug index...")
    index = SlugIndex()
    start_load = time.time()
    index.load()
    load_time = time.time() - start_load
    
    total_count = index.get_total_count()
    print(f"✓ Loaded {total_count:,} articles in {load_time:.3f}s")
    print()
    
    # Test queries with different characteristics
    test_queries = [
        ("exact match", "Joe_Biden", False),  # Exact match, no fuzzy needed
        ("substring", "biden", False),  # Simple substring
        ("fuzzy typo", "joe bidan", True),  # Typo requiring fuzzy match
        ("fuzzy complex", "artificial inteligence", True),  # Complex typo
        ("common term", "president", False),  # Common term, many matches
    ]
    
    print("Running search performance tests:")
    print("-" * 70)
    
    for test_name, query, expect_fuzzy in test_queries:
        start = time.time()
        results = index.search(query, limit=10, fuzzy=True, min_similarity=0.6)
        elapsed = time.time() - start
        
        status = "✓" if results else "✗"
        fuzzy_indicator = " [FUZZY]" if expect_fuzzy else ""
        
        print(f"{status} {test_name:20s} | {query:30s} | {elapsed*1000:7.2f}ms | {len(results):2d} results{fuzzy_indicator}")
        
        if results and len(results) <= 3:
            for i, slug in enumerate(results[:3], 1):
                print(f"    {i}. {slug}")
    
    print("-" * 70)
    
    # Benchmark worst-case fuzzy search
    print("\nBenchmarking worst-case fuzzy search (no substring matches)...")
    worst_case_queries = [
        "zzzzunknownzzzz",
        "xqwertasdfg",
        "notarealwikipage123"
    ]
    
    fuzzy_times = []
    for query in worst_case_queries:
        start = time.time()
        results = index.search(query, limit=10, fuzzy=True, min_similarity=0.6)
        elapsed = time.time() - start
        fuzzy_times.append(elapsed)
        print(f"  Query: {query:25s} | {elapsed*1000:7.2f}ms | {len(results)} results")
    
    avg_fuzzy_time = sum(fuzzy_times) / len(fuzzy_times)
    print(f"\nAverage fuzzy search time: {avg_fuzzy_time*1000:.2f}ms")
    
    # Performance evaluation
    print("\n" + "=" * 70)
    print("PERFORMANCE EVALUATION")
    print("=" * 70)
    
    if HAS_RAPIDFUZZ:
        if avg_fuzzy_time < 0.1:
            rating = "🚀 EXCELLENT"
        elif avg_fuzzy_time < 0.5:
            rating = "✓ GOOD"
        elif avg_fuzzy_time < 2.0:
            rating = "⚠️  ACCEPTABLE"
        else:
            rating = "✗ SLOW"
    else:
        if avg_fuzzy_time < 1.0:
            rating = "⚠️  OK (but install rapidfuzz for 10-100x speedup!)"
        else:
            rating = "✗ VERY SLOW - Install rapidfuzz immediately!"
    
    print(f"Overall rating: {rating}")
    print(f"Dataset size: {total_count:,} articles")
    print(f"Average fuzzy search time: {avg_fuzzy_time*1000:.2f}ms")
    
    if HAS_RAPIDFUZZ:
        print("\n✓ Using optimized rapidfuzz library with C extensions")
        print("✓ Using heapq for efficient top-k result tracking")
    else:
        print("\n⚠️  RECOMMENDATION: Install rapidfuzz for dramatically better performance:")
        print("   pip install rapidfuzz>=3.0.0")
    
    print("\n" + "=" * 70)
    
    return avg_fuzzy_time

if __name__ == "__main__":
    try:
        test_search_performance()
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

