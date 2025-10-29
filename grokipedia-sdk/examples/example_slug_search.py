"""Example usage of Grokipedia SDK slug search features"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError


def example_search_slugs():
    """Demonstrate searching for article slugs"""
    print("=" * 60)
    print("Example 1: Search for Article Slugs")
    print("=" * 60)
    
    with Client() as client:
        # Search for articles about "Joe Biden"
        print("\nSearching for 'joe biden'...")
        results = client.search_slug("joe biden", limit=5)
        print(f"Found {len(results)} results:")
        for i, slug in enumerate(results, 1):
            print(f"  {i}. {slug}")
        
        # Search with spaces or underscores - both work
        print("\nSearching for 'artificial intelligence'...")
        results = client.search_slug("artificial intelligence", limit=5)
        print(f"Found {len(results)} results:")
        for i, slug in enumerate(results, 1):
            print(f"  {i}. {slug}")


def example_find_best_match():
    """Demonstrate finding the best matching slug"""
    print("\n" + "=" * 60)
    print("Example 2: Find Best Match")
    print("=" * 60)
    
    with Client() as client:
        queries = ["elon musk", "donald trump", "climate change"]
        
        for query in queries:
            slug = client.find_slug(query)
            if slug:
                print(f"\n'{query}' -> {slug}")
                # Optionally fetch the article
                try:
                    summary = client.get_summary(slug)
                    print(f"  Title: {summary.title}")
                    print(f"  Summary: {summary.summary[:100]}...")
                except (ArticleNotFound, RequestError) as e:
                    print(f"  Error fetching article: {e}")
            else:
                print(f"\n'{query}' -> No match found")


def example_check_slug_exists():
    """Demonstrate checking if a slug exists"""
    print("\n" + "=" * 60)
    print("Example 3: Check if Slug Exists")
    print("=" * 60)
    
    with Client() as client:
        slugs_to_check = [
            "Joe_Biden",
            "Elon_Musk",
            "This_Article_Does_Not_Exist_12345",
            "Artificial_Intelligence"
        ]
        
        print("\nChecking slugs:")
        for slug in slugs_to_check:
            exists = client.slug_exists(slug)
            status = "✓ EXISTS" if exists else "✗ NOT FOUND"
            print(f"  {slug}: {status}")


def example_list_by_prefix():
    """Demonstrate listing articles by prefix"""
    print("\n" + "=" * 60)
    print("Example 4: List Articles by Prefix")
    print("=" * 60)
    
    with Client() as client:
        prefixes = ["Joe", "Artificial", "Climate"]
        
        for prefix in prefixes:
            results = client.list_available_articles(prefix=prefix, limit=10)
            print(f"\nArticles starting with '{prefix}' (showing {len(results)}):")
            for i, slug in enumerate(results, 1):
                print(f"  {i}. {slug}")


def example_total_count():
    """Demonstrate getting total article count"""
    print("\n" + "=" * 60)
    print("Example 5: Get Total Article Count")
    print("=" * 60)
    
    with Client() as client:
        total = client.get_total_article_count()
        print(f"\nTotal articles in index: {total:,}")


def example_random_articles():
    """Demonstrate getting random articles"""
    print("\n" + "=" * 60)
    print("Example 6: Get Random Articles")
    print("=" * 60)
    
    with Client() as client:
        print("\nFetching 5 random articles...")
        random_slugs = client.get_random_articles(5)
        
        for i, slug in enumerate(random_slugs, 1):
            try:
                summary = client.get_summary(slug)
                print(f"\n{i}. {summary.title}")
                print(f"   Slug: {slug}")
                print(f"   Summary: {summary.summary[:150]}...")
            except (ArticleNotFound, RequestError) as e:
                print(f"\n{i}. {slug}")
                print(f"   Error: {e}")


def example_workflow():
    """Demonstrate a complete workflow: search -> validate -> fetch"""
    print("\n" + "=" * 60)
    print("Example 7: Complete Workflow")
    print("=" * 60)
    
    with Client() as client:
        # Step 1: User searches for an article
        query = "machine learning"
        print(f"\nUser searches for: '{query}'")
        
        # Step 2: Find matching slugs
        matches = client.search_slug(query, limit=5)
        
        if not matches:
            print("No matches found!")
            return
        
        print(f"Found {len(matches)} matches:")
        for i, slug in enumerate(matches, 1):
            print(f"  {i}. {slug}")
        
        # Step 3: User selects first match
        selected_slug = matches[0]
        print(f"\nUser selects: {selected_slug}")
        
        # Step 4: Verify it exists (optional but good practice)
        if client.slug_exists(selected_slug):
            print("✓ Slug verified in index")
        
        # Step 5: Fetch the article
        try:
            article = client.get_article(selected_slug)
            print(f"\n✓ Successfully fetched article!")
            print(f"Title: {article.title}")
            print(f"Sections: {len(article.sections)}")
            print(f"References: {len(article.references)}")
            print(f"Word Count: {article.metadata.word_count:,}")
        except ArticleNotFound:
            print("✗ Article not found on server")
        except RequestError as e:
            print(f"✗ Error fetching article: {e}")


def example_fuzzy_search():
    """Demonstrate fuzzy search with typos"""
    print("\n" + "=" * 60)
    print("Example 8: Fuzzy Search (handles typos)")
    print("=" * 60)
    
    with Client() as client:
        # Test with typos and variations
        queries = [
            "joe bidden",  # typo
            "elon mask",   # typo
            "artifical",   # typo
            "climte",      # typo
        ]
        
        print("\nFuzzy search results:")
        for query in queries:
            results = client.search_slug(query, limit=3, fuzzy=True)
            print(f"\n'{query}':")
            if results:
                for i, slug in enumerate(results, 1):
                    print(f"  {i}. {slug}")
            else:
                print("  No matches found")


if __name__ == "__main__":
    print("\nGrokipedia SDK - Slug Search Examples")
    print("=" * 60)
    
    try:
        # Run all examples
        example_search_slugs()
        example_find_best_match()
        example_check_slug_exists()
        example_list_by_prefix()
        example_total_count()
        example_random_articles()
        example_workflow()
        example_fuzzy_search()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

