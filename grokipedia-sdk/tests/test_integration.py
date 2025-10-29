"""Integration test: Search for slug, then fetch article"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError

def test_integration():
    """Test the complete workflow: search -> find -> fetch"""
    
    with Client() as client:
        print("Integration Test: Search + Fetch Article")
        print("=" * 60)
        
        # Step 1: Search for an article
        query = "donald trump"
        print(f"\n1. Searching for '{query}'...")
        results = client.search_slug(query, limit=5)
        print(f"   Found {len(results)} results:")
        for i, slug in enumerate(results[:3], 1):
            print(f"   {i}. {slug}")
        
        # Step 2: Find best match
        print(f"\n2. Finding best match...")
        best_slug = client.find_slug(query)
        print(f"   Best match: {best_slug}")
        
        # Step 3: Verify it exists
        print(f"\n3. Verifying slug exists...")
        exists = client.slug_exists(best_slug)
        print(f"   Exists in index: {exists}")
        
        # Step 4: Fetch the article summary
        print(f"\n4. Fetching article summary...")
        try:
            summary = client.get_summary(best_slug)
            print(f"   Title: {summary.title}")
            print(f"   URL: {summary.url}")
            print(f"   Sections: {len(summary.table_of_contents)}")
            print(f"   Summary (first 150 chars): {summary.summary[:150]}...")
            print("\n   SUCCESS: Article fetched successfully!")
        except ArticleNotFound:
            print("   ERROR: Article not found on server (but exists in index)")
        except RequestError as e:
            print(f"   ERROR: {e}")
        
        print("\n" + "=" * 60)
        print("Integration test completed!")

if __name__ == '__main__':
    test_integration()

