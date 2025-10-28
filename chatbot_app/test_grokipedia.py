"""Test script to verify Grokipedia SDK functionality"""

import sys
import os

# Add parent directory to path to import grokipedia_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'grokipedia-sdk'))

try:
    from grokipedia_sdk import Client, ArticleNotFound
    print("[OK] Successfully imported grokipedia_sdk")
except ImportError as e:
    print(f"[ERROR] Failed to import grokipedia_sdk: {e}")
    sys.exit(1)


def test_comcast_article():
    """Test fetching the Comcast article from Grokipedia"""
    print("\n" + "="*60)
    print("Testing Grokipedia SDK - Comcast Article")
    print("="*60)
    
    client = Client()
    
    try:
        print("\nFetching article summary for 'Comcast'...")
        summary = client.get_summary("Comcast")
        
        print("\n[OK] Successfully fetched article summary!")
        print(f"\nTitle: {summary.title}")
        print(f"URL: {summary.url}")
        print(f"\nSummary ({len(summary.summary)} characters):")
        print("-" * 60)
        print(summary.summary[:500] + "..." if len(summary.summary) > 500 else summary.summary)
        print("-" * 60)
        
        print(f"\nTable of Contents ({len(summary.table_of_contents)} sections):")
        for i, section in enumerate(summary.table_of_contents[:10], 1):
            print(f"  {i}. {section}")
        
        if len(summary.table_of_contents) > 10:
            print(f"  ... and {len(summary.table_of_contents) - 10} more sections")
        
        print(f"\nArticle scraped at: {summary.scraped_at}")
        
        return True
        
    except ArticleNotFound:
        print("\n[ERROR] Article 'Comcast' not found")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error fetching article: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


def test_full_article():
    """Test fetching the full Comcast article"""
    print("\n" + "="*60)
    print("Testing Full Article Fetch")
    print("="*60)
    
    client = Client()
    
    try:
        print("\nFetching full article for 'Comcast'...")
        article = client.get_article("Comcast")
        
        print("\n[OK] Successfully fetched full article!")
        print(f"\nTitle: {article.title}")
        print(f"Slug: {article.slug}")
        print(f"URL: {article.url}")
        print(f"Word Count: {article.metadata.word_count}")
        
        if article.metadata.fact_checked:
            print(f"Fact-checked by: {article.metadata.fact_checked}")
        
        print(f"\nNumber of sections: {len(article.sections)}")
        print(f"Number of references: {len(article.references)}")
        
        print(f"\nFirst few sections:")
        for i, section in enumerate(article.sections[:3], 1):
            print(f"\n{i}. {section.title} (Level {section.level})")
            print(f"   Content preview: {section.content[:150]}...")
        
        return True
        
    except ArticleNotFound:
        print("\n[ERROR] Article 'Comcast' not found")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error fetching full article: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


def test_client_functionality():
    """Test various client methods"""
    print("\n" + "="*60)
    print("Testing Additional SDK Functionality")
    print("="*60)
    
    client = Client()
    
    try:
        # Test get_section
        print("\nTesting get_section('Comcast', 'Corporate Profile')...")
        section = client.get_section("Comcast", "Corporate Profile")
        
        if section:
            print(f"[OK] Found section: {section.title}")
            print(f"  Level: {section.level}")
            print(f"  Content preview: {section.content[:200]}...")
        else:
            print("[ERROR] Section not found")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


if __name__ == "__main__":
    print("\nGrokipedia SDK Test Script")
    print("Testing with article: Comcast")
    print("URL: https://grokipedia.com/page/Comcast")
    
    results = []
    
    # Test 1: Fetch summary
    results.append(("Summary Test", test_comcast_article()))
    
    # Test 2: Fetch full article
    results.append(("Full Article Test", test_full_article()))
    
    # Test 3: Fetch specific section
    results.append(("Section Test", test_client_functionality()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{test_name}: {status}")
    
    print("\n" + "="*60)
    
    if all(passed for _, passed in results):
        print("All tests passed!")
    else:
        print("Some tests failed.")
    
    print("="*60 + "\n")

