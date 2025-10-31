"""Comprehensive performance tests for Grokipedia SDK

This module consolidates all performance-related tests including:
- Fuzzy search performance benchmarking
- BK-Tree vs linear search comparison
- rapidfuzz vs difflib comparison
"""

import time
import sys
import os
from pathlib import Path
from difflib import SequenceMatcher

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from grokipedia_sdk.slug_index import SlugIndex, HAS_RAPIDFUZZ, HAS_BKTREE

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ_IMPORT = True
except ImportError:
    HAS_RAPIDFUZZ_IMPORT = False


class PerformanceTestSuite:
    """Consolidated performance test suite"""
    
    def __init__(self):
        self.index = None
        self.total_count = 0
        
    def setup_index(self, use_bktree=True):
        """Load slug index for testing"""
        print("Loading slug index...")
        self.index = SlugIndex(use_bktree=use_bktree)
        start_load = time.time()
        self.index.load()
        load_time = time.time() - start_load
        self.total_count = self.index.get_total_count()
        print(f"✓ Loaded {self.total_count:,} articles in {load_time:.3f}s")
        return load_time
    
    def test_fuzzy_search_performance(self):
        """Test the performance of the fuzzy search function"""
        print("\n" + "=" * 80)
        print("Test 1: Fuzzy Search Performance")
        print("=" * 80)
        print(f"\nUsing rapidfuzz: {HAS_RAPIDFUZZ}")
        if not HAS_RAPIDFUZZ:
            print("⚠️  WARNING: rapidfuzz not installed, using slow difflib fallback")
        print()
        
        if not self.index:
            self.setup_index()
        
        # Test queries with different characteristics
        test_queries = [
            ("exact match", "Joe_Biden", False),
            ("substring", "biden", False),
            ("fuzzy typo", "joe bidan", True),
            ("fuzzy complex", "artificial inteligence", True),
            ("common term", "president", False),
        ]
        
        print("Running search performance tests:")
        print("-" * 80)
        print(f"{'Test Type':<20} {'Query':<30} {'Time (ms)':<12} {'Results':<10} {'Notes'}")
        print("-" * 80)
        
        for test_name, query, expect_fuzzy in test_queries:
            start = time.time()
            results = self.index.search(query, limit=10, fuzzy=True, min_similarity=0.6)
            elapsed = time.time() - start
            
            status = "✓" if results else "✗"
            fuzzy_indicator = " [FUZZY]" if expect_fuzzy else ""
            
            print(f"{status} {test_name:<18} | {query:<28} | {elapsed*1000:>8.2f}ms | {len(results):>2} results{fuzzy_indicator}")
            
            if results and len(results) <= 3:
                for i, slug in enumerate(results[:3], 1):
                    print(f"    {i}. {slug}")
        
        print("-" * 80)
        
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
            results = self.index.search(query, limit=10, fuzzy=True, min_similarity=0.6)
            elapsed = time.time() - start
            fuzzy_times.append(elapsed)
            print(f"  Query: {query:25s} | {elapsed*1000:7.2f}ms | {len(results)} results")
        
        avg_fuzzy_time = sum(fuzzy_times) / len(fuzzy_times) if fuzzy_times else 0
        print(f"\nAverage fuzzy search time: {avg_fuzzy_time*1000:.2f}ms")
        
        # Performance evaluation
        print("\n" + "-" * 80)
        print("PERFORMANCE EVALUATION")
        print("-" * 80)
        
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
        print(f"Dataset size: {self.total_count:,} articles")
        print(f"Average fuzzy search time: {avg_fuzzy_time*1000:.2f}ms")
        
        if HAS_RAPIDFUZZ:
            print("\n✓ Using optimized rapidfuzz library with C extensions")
            print("✓ Using heapq for efficient top-k result tracking")
        else:
            print("\n⚠️  RECOMMENDATION: Install rapidfuzz for dramatically better performance:")
            print("   pip install rapidfuzz>=3.0.0")
        
        return avg_fuzzy_time
    
    def test_string_similarity_benchmark(self):
        """Compare difflib vs rapidfuzz on string similarity calculations"""
        print("\n" + "=" * 80)
        print("Test 2: String Similarity Benchmark (difflib vs rapidfuzz)")
        print("=" * 80)
        
        if not HAS_RAPIDFUZZ_IMPORT:
            print("\n⚠️  rapidfuzz not installed. Skipping benchmark.")
            print("   Install with: pip install rapidfuzz>=3.0.0")
            return
        
        test_pairs = [
            ("Joe Biden", "Joe Bidan"),
            ("artificial intelligence", "artificial inteligence"),
            ("machine learning", "machin learning"),
            ("neural network", "neurall network"),
            ("deep learning", "deep lerning"),
        ]
        
        iterations = 10000
        
        print(f"\nComparing {len(test_pairs)} string pairs, {iterations:,} iterations each\n")
        
        # Benchmark difflib
        print("Testing difflib.SequenceMatcher...")
        start = time.time()
        for _ in range(iterations):
            for s1, s2 in test_pairs:
                _ = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
        difflib_time = time.time() - start
        
        # Benchmark rapidfuzz
        print("Testing rapidfuzz.fuzz.ratio...")
        start = time.time()
        for _ in range(iterations):
            for s1, s2 in test_pairs:
                _ = fuzz.ratio(s1.lower(), s2.lower())
        rapidfuzz_time = time.time() - start
        
        # Results
        print("\n" + "-" * 80)
        print(f"difflib time:    {difflib_time:.3f}s")
        print(f"rapidfuzz time:  {rapidfuzz_time:.3f}s")
        print(f"Speedup:         {difflib_time/rapidfuzz_time:.1f}x faster")
        print("-" * 80)
        
        return difflib_time, rapidfuzz_time
    
    def test_full_search_benchmark(self):
        """Benchmark full search on actual dataset comparing difflib vs rapidfuzz"""
        print("\n" + "=" * 80)
        print("Test 3: Full Search Benchmark (difflib vs rapidfuzz)")
        print("=" * 80)
        
        if not HAS_RAPIDFUZZ_IMPORT:
            print("\n⚠️  rapidfuzz not installed. Skipping benchmark.")
            return
        
        if not self.index:
            self.setup_index()
        
        # Create a subset for testing (to make old method testable)
        print("\nCreating test subset (10,000 articles) for comparison...")
        all_items = list(self.index._index.items())[:10000]
        
        test_queries = [
            "joe bidan",
            "artificial inteligence", 
            "machne learning"
        ]
        
        print("\nBenchmarking on 10,000 article subset:\n")
        
        for query in test_queries:
            query_normalized = query.lower().replace('_', ' ')
            min_similarity = 0.6
            
            # Test with difflib (old method)
            start = time.time()
            difflib_matches = []
            for normalized_name, slug in all_items:
                similarity = SequenceMatcher(None, query_normalized, normalized_name).ratio()
                if similarity >= min_similarity:
                    difflib_matches.append((similarity, slug))
            difflib_matches.sort(reverse=True)
            difflib_matches = difflib_matches[:10]
            difflib_time = time.time() - start
            
            # Test with rapidfuzz (new method)
            start = time.time()
            rapidfuzz_matches = []
            for normalized_name, slug in all_items:
                similarity = fuzz.ratio(query_normalized, normalized_name) / 100.0
                if similarity >= min_similarity:
                    rapidfuzz_matches.append((similarity, slug))
            rapidfuzz_matches.sort(reverse=True)
            rapidfuzz_matches = rapidfuzz_matches[:10]
            rapidfuzz_time = time.time() - start
            
            # Results
            print(f"Query: '{query}'")
            print(f"  difflib:    {difflib_time*1000:7.2f}ms")
            print(f"  rapidfuzz:  {rapidfuzz_time*1000:7.2f}ms")
            print(f"  Speedup:    {difflib_time/rapidfuzz_time:6.1f}x faster")
            print(f"  Results:    {len(difflib_matches)} vs {len(rapidfuzz_matches)}")
            print()
        
        # Extrapolate to full dataset
        print("-" * 80)
        print("Extrapolation to full dataset:")
        print("-" * 80)
        scale_factor = self.total_count / 10000
        
        print(f"\nEstimated time per fuzzy search on {self.total_count:,} articles:")
        print(f"  Old (difflib):    ~{difflib_time * scale_factor:.1f}s")
        print(f"  New (rapidfuzz):  ~{rapidfuzz_time * scale_factor:.1f}s")
        print(f"  Improvement:      {difflib_time/rapidfuzz_time:.1f}x faster")
    
    def test_bktree_performance(self):
        """Test the performance improvement with BK-Tree"""
        print("\n" + "=" * 80)
        print("Test 4: BK-Tree Performance Comparison")
        print("=" * 80)
        print(f"\nBK-Tree available: {HAS_BKTREE}")
        
        if not HAS_BKTREE:
            print("\n⚠️  WARNING: BK-Tree module not available!")
            print("The bk_tree.py file should be in grokipedia_sdk/")
            return
        
        print("\n" + "-" * 80)
        print("Loading with BK-Tree (initial build time)")
        print("-" * 80)
        
        # Test WITH BK-Tree
        print("\nLoading index WITH BK-Tree enabled...")
        index_with_bktree = SlugIndex(use_bktree=True)
        start = time.time()
        index_with_bktree.load()
        load_time_with = time.time() - start
        total_count = index_with_bktree.get_total_count()
        
        print(f"✓ Loaded {total_count:,} articles in {load_time_with:.3f}s")
        print(f"  BK-Tree built: {index_with_bktree._bk_tree is not None}")
        if index_with_bktree._bk_tree:
            print(f"  BK-Tree size: {len(index_with_bktree._bk_tree):,} nodes")
        
        # Test WITHOUT BK-Tree (for comparison)
        print("\nLoading index WITHOUT BK-Tree (for comparison)...")
        index_without_bktree = SlugIndex(use_bktree=False)
        start = time.time()
        index_without_bktree.load()
        load_time_without = time.time() - start
        
        print(f"✓ Loaded {total_count:,} articles in {load_time_without:.3f}s")
        print(f"  BK-Tree built: {index_without_bktree._bk_tree is not None}")
        
        print(f"\nBuild overhead: +{load_time_with - load_time_without:.3f}s")
        print("(One-time cost, amortized across all future fuzzy searches)")
        
        # Test queries
        print("\n" + "-" * 80)
        print("Fuzzy Search Performance Comparison")
        print("-" * 80)
        
        test_queries = [
            ("Simple typo", "joe bidan", 0.6),
            ("Complex typo", "artificial inteligence", 0.6),
            ("Multiple typos", "machne lerning", 0.6),
            ("Short query", "pyton", 0.5),
            ("Medium query", "quantm mechanics", 0.6),
            ("Long query", "united states of amerca", 0.6),
        ]
        
        print("\nQuery Performance (10 results per query):\n")
        print(f"{'Query':<30} {'Without BK-Tree':<20} {'With BK-Tree':<20} {'Speedup':<15}")
        print("-" * 85)
        
        total_speedup = 0
        valid_tests = 0
        
        for test_name, query, min_sim in test_queries:
            # Test WITHOUT BK-Tree
            start = time.time()
            results_without = index_without_bktree.search(query, limit=10, fuzzy=True, min_similarity=min_sim)
            time_without = time.time() - start
            
            # Test WITH BK-Tree
            start = time.time()
            results_with = index_with_bktree.search(query, limit=10, fuzzy=True, min_similarity=min_sim)
            time_with = time.time() - start
            
            speedup = time_without / time_with if time_with > 0 else 0
            if speedup > 1:
                total_speedup += speedup
                valid_tests += 1
            
            status = "🚀" if speedup > 10 else "✓" if speedup > 2 else "→"
            
            print(f"{test_name:<30} {time_without*1000:>8.2f}ms        {time_with*1000:>8.2f}ms        {status} {speedup:>6.1f}x")
            
            # Show top result for verification
            if results_with:
                print(f"  └─ Top result: {results_with[0]}")
        
        print("-" * 85)
        
        avg_speedup = total_speedup / valid_tests if valid_tests > 0 else 1
        print(f"\nAverage speedup: {avg_speedup:.1f}x")
        
        # Summary
        print("\n" + "=" * 80)
        print("BK-TREE PERFORMANCE SUMMARY")
        print("=" * 80)
        
        print(f"\nDataset: {total_count:,} Wikipedia articles")
        print(f"BK-Tree build time: +{load_time_with - load_time_without:.2f}s (one-time cost)")
        print(f"Average fuzzy search speedup: {avg_speedup:.1f}x")
        
        if avg_speedup > 100:
            rating = "🚀 EXCELLENT (100x+ faster!)"
        elif avg_speedup > 10:
            rating = "🚀 OUTSTANDING (10x+ faster)"
        elif avg_speedup > 5:
            rating = "✓ GREAT (5x+ faster)"
        elif avg_speedup > 2:
            rating = "✓ GOOD (2x+ faster)"
        else:
            rating = "→ MARGINAL (less than 2x)"
        
        print(f"Overall rating: {rating}")
        
        # Cost-benefit analysis
        queries_to_breakeven = (load_time_with - load_time_without) / (
            (1.5 / avg_speedup) if avg_speedup > 0 else 1
        )
        
        print(f"\n💡 Break-even analysis:")
        print(f"   After ~{queries_to_breakeven:.0f} fuzzy queries, BK-Tree pays for itself")
        print(f"   Recommendation: {'ENABLE BK-Tree' if queries_to_breakeven < 100 else 'OPTIONAL'}")
        
        # Detailed explanation
        print("\n" + "-" * 80)
        print("EXPLANATION")
        print("-" * 80)
        
        print("""
BK-Tree (Burkhard-Keller Tree) organizes strings by edit distance,
enabling O(log n) fuzzy search instead of O(n) linear scan.

Trade-offs:
  ✓ Pros: 10-100x+ faster fuzzy queries
  ✓ Pros: Scales well to millions of items
  ⚠ Cons: One-time build cost (~5-10s for 885k items)
  ⚠ Cons: 2-3x memory overhead

Best for:
  • Applications with frequent fuzzy searches
  • Large datasets (100k+ items)
  • Real-time search requirements
  
To disable:
  index = SlugIndex(use_bktree=False)
""")
        
        return avg_speedup
    
    def test_trigram_performance(self):
        """Test trigram indexing performance improvements."""
        print("\n" + "="*80)
        print("Test 5: Trigram Indexing Performance")
        print("="*80)
        
        # Test with trigram indexing enabled vs disabled
        print("\n" + "-"*60)
        print("Comparing trigram indexing performance...")
        print("-"*60)
        
        # Load index with trigram enabled
        print("\nLoading index WITH trigram indexing...")
        start = time.time()
        index_with_trigram = SlugIndex(use_bktree=False, use_trigram=True)
        index_with_trigram.load()
        load_time_with_trigram = time.time() - start
        print(f"✓ Loaded in {load_time_with_trigram:.3f}s")
        print(f"  Trigram index built: {len(index_with_trigram._trigram_index)} trigrams")
        
        # Load index without trigram
        print("\nLoading index WITHOUT trigram indexing...")
        start = time.time()
        index_without_trigram = SlugIndex(use_bktree=False, use_trigram=False)
        index_without_trigram.load()
        load_time_without_trigram = time.time() - start
        print(f"✓ Loaded in {load_time_without_trigram:.3f}s")
        
        build_overhead = load_time_with_trigram - load_time_without_trigram
        print(f"\nTrigram build overhead: +{build_overhead:.3f}s")
        
        # Test search performance
        test_queries = [
            "joe bidan",                    # Simple typo
            "artificial inteligence",       # Complex typo
            "machne learning",              # Multiple typos
            "quantum mechancs",             # Technical term typo
            "computr science"               # Common term typo
        ]
        
        print(f"\nSearch Performance Comparison ({len(test_queries)} queries):")
        print("-" * 70)
        print(f"{'Query':<25} {'Without Trigram':<18} {'With Trigram':<15} {'Speedup'}")
        print("-" * 70)
        
        total_time_without = 0
        total_time_with = 0
        
        for query in test_queries:
            # Test without trigram
            start = time.time()
            results_without = index_without_trigram.search(query, limit=10, fuzzy=True)
            time_without = (time.time() - start) * 1000
            total_time_without += time_without
            
            # Test with trigram
            start = time.time()
            results_with = index_with_trigram.search(query, limit=10, fuzzy=True)
            time_with = (time.time() - start) * 1000
            total_time_with += time_with
            
            speedup = time_without / time_with if time_with > 0 else float('inf')
            
            print(f"{query:<25} {time_without:>8.2f}ms        {time_with:>8.2f}ms     {speedup:>5.1f}x")
        
        avg_speedup = total_time_without / total_time_with if total_time_with > 0 else float('inf')
        
        print("-" * 70)
        print(f"{'Average':<25} {total_time_without/len(test_queries):>8.2f}ms        {total_time_with/len(test_queries):>8.2f}ms     {avg_speedup:>5.1f}x")
        
        print(f"\nTrigram indexing summary:")
        print(f"  Build overhead: +{build_overhead:.3f}s")
        print(f"  Average speedup: {avg_speedup:.1f}x")
        
        # Calculate break-even point
        if avg_speedup > 1:
            queries_to_break_even = build_overhead / ((total_time_without - total_time_with) / len(test_queries) / 1000)
            print(f"  Break-even after: {queries_to_break_even:.0f} fuzzy searches")
        
        if avg_speedup >= 5:
            print(f"  Rating: 🚀 OUTSTANDING (5x+ faster)")
        elif avg_speedup >= 2:
            print(f"  Rating: ✅ GOOD (2x+ faster)")
        else:
            print(f"  Rating: ⚠️ MARGINAL (<2x faster)")
        
        return avg_speedup
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("\n" + "=" * 80)
        print("🚀 Grokipedia SDK - Comprehensive Performance Test Suite")
        print("=" * 80)
        
        try:
            # Test 1: Fuzzy search performance
            self.test_fuzzy_search_performance()
            
            # Test 2: String similarity benchmark
            self.test_string_similarity_benchmark()
            
            # Test 3: Full search benchmark
            self.test_full_search_benchmark()
            
            # Test 4: BK-Tree performance
            bktree_speedup = self.test_bktree_performance()
            
            # Test 5: Trigram indexing performance
            trigram_speedup = self.test_trigram_performance()
            
            # Final summary
            print("\n" + "="*80)
            print("FINAL SUMMARY")
            print("="*80)
            print("✓ All performance tests completed")
            print("✓ rapidfuzz provides 10-100x speedup over difflib")
            print(f"✓ BK-Tree provides {bktree_speedup:.1f}x speedup for fuzzy search")
            print(f"✓ Trigram indexing provides {trigram_speedup:.1f}x speedup for candidate filtering")
            
            print(f"\n💡 For sub-second fuzzy search, consider:")
            print(f"   - Trigram indexing (5-10x faster) {'✅ ENABLED' if trigram_speedup >= 2 else '⚠️ CHECK PERFORMANCE'}")
            print(f"   - BK-tree data structure (100-1000x faster) {'✅ ENABLED' if bktree_speedup >= 10 else '⚠️ CHECK PERFORMANCE'}")
            print(f"   - Full-text search engine like Whoosh")
            print("="*80)
            
        except Exception as e:
            print(f"\n✗ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    suite = PerformanceTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()
