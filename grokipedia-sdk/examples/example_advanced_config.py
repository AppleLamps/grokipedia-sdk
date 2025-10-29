"""Advanced configuration examples for Grokipedia SDK"""

from grokipedia_sdk import Client, SlugIndex
import os


def example_custom_cache_size():
    """Demonstrate custom cache size configuration"""
    print("=" * 60)
    print("Example 1: Custom Cache Size")
    print("=" * 60)
    
    # Use smaller cache for memory-constrained environments
    with Client(max_cache_size=100) as client:
        print(f"Client initialized with max_cache_size=100")
        
        # Fetch some articles - cache will be limited to 100 articles
        articles = ["Joe_Biden", "Elon_Musk", "Artificial_Intelligence"]
        for slug in articles:
            try:
                article = client.get_article(slug)
                print(f"✓ Fetched and cached: {article.title}")
            except Exception as e:
                print(f"✗ Error fetching {slug}: {e}")


def example_rate_limiting():
    """Demonstrate rate limiting configuration"""
    print("\n" + "=" * 60)
    print("Example 2: Rate Limiting")
    print("=" * 60)
    
    # Set rate limit to 2 seconds between requests (be respectful!)
    with Client(rate_limit=2.0) as client:
        print("Client configured with rate_limit=2.0 seconds")
        print("This ensures at least 2 seconds between requests")
        
        slugs = ["Joe_Biden", "Elon_Musk"]
        for slug in slugs:
            try:
                summary = client.get_summary(slug)
                print(f"✓ Fetched: {summary.title}")
            except Exception as e:
                print(f"✗ Error: {e}")


def example_custom_timeout():
    """Demonstrate custom timeout configuration"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Timeout")
    print("=" * 60)
    
    # Use longer timeout for slow connections
    with Client(timeout=60.0) as client:
        print("Client configured with timeout=60.0 seconds")
        
        try:
            article = client.get_article("Joe_Biden")
            print(f"✓ Successfully fetched with custom timeout")
            print(f"Title: {article.title}")
        except Exception as e:
            print(f"✗ Error: {e}")


def example_custom_slug_index():
    """Demonstrate using a custom SlugIndex"""
    print("\n" + "=" * 60)
    print("Example 4: Custom SlugIndex")
    print("=" * 60)
    
    # Create a custom SlugIndex with specific configuration
    # This is useful if you have your own sitemap data or want to customize
    # the index location
    links_dir = os.path.join(os.path.dirname(__file__), "..", "grokipedia_sdk", "links")
    
    if os.path.exists(links_dir):
        custom_index = SlugIndex(links_dir=links_dir)
        
        with Client(slug_index=custom_index) as client:
            print("Client initialized with custom SlugIndex")
            print(f"Total articles: {client.get_total_article_count():,}")
            
            # Use the client as normal
            results = client.search_slug("python", limit=3)
            print(f"\nSearch results for 'python':")
            for i, slug in enumerate(results, 1):
                print(f"  {i}. {slug}")
    else:
        print("Custom links directory not found, skipping example")


def example_retry_configuration():
    """Demonstrate custom retry configuration"""
    print("\n" + "=" * 60)
    print("Example 5: Retry Configuration")
    print("=" * 60)
    
    # Configure more retries for unreliable networks
    with Client(max_retries=5) as client:
        print("Client configured with max_retries=5")
        print("Will retry up to 5 times on transient failures")
        
        try:
            article = client.get_article("Joe_Biden")
            print(f"✓ Successfully fetched: {article.title}")
        except Exception as e:
            print(f"✗ Error after retries: {e}")


def example_environment_variable():
    """Demonstrate using environment variable for base URL"""
    print("\n" + "=" * 60)
    print("Example 6: Environment Variable Configuration")
    print("=" * 60)
    
    # You can set GROKIPEDIA_BASE_URL environment variable
    # to use a custom base URL without modifying code
    base_url = os.environ.get("GROKIPEDIA_BASE_URL")
    
    if base_url:
        print(f"Using base URL from environment: {base_url}")
        with Client(base_url=base_url) as client:
            print("Client initialized with environment variable base URL")
    else:
        print("GROKIPEDIA_BASE_URL not set, using default")
        print("To use this feature, set: export GROKIPEDIA_BASE_URL=https://your-grokipedia.com")
        
        with Client() as client:
            print("Client using default base URL")


def example_custom_user_agent():
    """Demonstrate custom user agent"""
    print("\n" + "=" * 60)
    print("Example 7: Custom User Agent")
    print("=" * 60)
    
    # Set a custom User-Agent string
    custom_ua = "MyApp/1.0 (Research Project; contact@example.com)"
    
    with Client(user_agent=custom_ua) as client:
        print(f"Client configured with custom User-Agent:")
        print(f"  {custom_ua}")
        
        try:
            article = client.get_article("Joe_Biden")
            print(f"\n✓ Successfully fetched: {article.title}")
        except Exception as e:
            print(f"✗ Error: {e}")


def example_combined_configuration():
    """Demonstrate combining multiple configuration options"""
    print("\n" + "=" * 60)
    print("Example 8: Combined Configuration")
    print("=" * 60)
    
    # Combine multiple configuration options for production use
    with Client(
        timeout=45.0,
        max_cache_size=500,
        rate_limit=1.5,
        max_retries=3,
        user_agent="ProductionApp/2.0 (Production; support@example.com)"
    ) as client:
        print("Client configured with production settings:")
        print("  - Timeout: 45 seconds")
        print("  - Cache size: 500 articles")
        print("  - Rate limit: 1.5 seconds")
        print("  - Max retries: 3")
        print("  - Custom User-Agent")
        
        try:
            article = client.get_article("Joe_Biden")
            print(f"\n✓ Successfully fetched: {article.title}")
            print(f"  Word count: {article.metadata.word_count:,}")
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("\nGrokipedia SDK - Advanced Configuration Examples")
    print("=" * 60)
    
    try:
        example_custom_cache_size()
        example_rate_limiting()
        example_custom_timeout()
        example_custom_slug_index()
        example_retry_configuration()
        example_environment_variable()
        example_custom_user_agent()
        example_combined_configuration()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

