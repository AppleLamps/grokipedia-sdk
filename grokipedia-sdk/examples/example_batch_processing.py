"""Batch processing examples for Grokipedia SDK"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError
from typing import List, Dict
import time


def example_batch_summaries():
    """Fetch summaries for multiple articles"""
    print("=" * 60)
    print("Example 1: Batch Fetch Summaries")
    print("=" * 60)
    
    slugs = [
        "Joe_Biden",
        "Elon_Musk",
        "Artificial_Intelligence",
        "Python_(programming_language)",
        "Machine_learning"
    ]
    
    results = []
    
    with Client() as client:
        print(f"\nFetching summaries for {len(slugs)} articles...")
        
        for slug in slugs:
            try:
                summary = client.get_summary(slug)
                results.append({
                    'slug': slug,
                    'title': summary.title,
                    'success': True,
                    'sections': len(summary.table_of_contents)
                })
                print(f"✓ {summary.title}")
            except (ArticleNotFound, RequestError) as e:
                results.append({
                    'slug': slug,
                    'success': False,
                    'error': str(e)
                })
                print(f"✗ {slug}: {e}")
        
        print(f"\n✓ Successfully fetched {sum(r['success'] for r in results)}/{len(slugs)} articles")


def example_batch_with_error_handling():
    """Batch processing with comprehensive error handling"""
    print("\n" + "=" * 60)
    print("Example 2: Batch Processing with Error Handling")
    print("=" * 60)
    
    slugs = [
        "Joe_Biden",
        "NonExistent_Article_123",
        "Elon_Musk",
        "Invalid-Slug-Format",
        "Artificial_Intelligence"
    ]
    
    successful = []
    failed = []
    
    with Client() as client:
        for slug in slugs:
            try:
                article = client.get_article(slug)
                successful.append({
                    'slug': slug,
                    'title': article.title,
                    'word_count': article.metadata.word_count
                })
            except ArticleNotFound:
                failed.append({'slug': slug, 'reason': 'Article not found'})
            except ValueError as e:
                failed.append({'slug': slug, 'reason': f'Invalid slug: {e}'})
            except RequestError as e:
                failed.append({'slug': slug, 'reason': f'Request error: {e}'})
            except Exception as e:
                failed.append({'slug': slug, 'reason': f'Unexpected error: {e}'})
        
        print(f"\n✓ Successful: {len(successful)}")
        for item in successful:
            print(f"  - {item['title']} ({item['word_count']:,} words)")
        
        print(f"\n✗ Failed: {len(failed)}")
        for item in failed:
            print(f"  - {item['slug']}: {item['reason']}")


def example_filter_articles_by_criteria():
    """Filter articles by specific criteria"""
    print("\n" + "=" * 60)
    print("Example 3: Filter Articles by Criteria")
    print("=" * 60)
    
    # Find articles about a topic
    with Client() as client:
        # Search for articles about "climate"
        climate_articles = client.search_slug("climate", limit=20)
        
        print(f"\nFound {len(climate_articles)} climate-related articles")
        print("\nFetching summaries to filter by word count...")
        
        # Filter articles with substantial content (word count > threshold)
        substantial_articles = []
        for slug in climate_articles[:10]:  # Limit to first 10 for demo
            try:
                article = client.get_article(slug)
                if article.metadata.word_count > 500:
                    substantial_articles.append({
                        'title': article.title,
                        'word_count': article.metadata.word_count,
                        'sections': len(article.sections)
                    })
            except Exception as e:
                continue
        
        print(f"\nFound {len(substantial_articles)} articles with >500 words:")
        for item in sorted(substantial_articles, key=lambda x: x['word_count'], reverse=True):
            print(f"  - {item['title']}: {item['word_count']:,} words, {item['sections']} sections")


def example_collect_statistics():
    """Collect statistics from multiple articles"""
    print("\n" + "=" * 60)
    print("Example 4: Collect Statistics")
    print("=" * 60)
    
    slugs = [
        "Joe_Biden",
        "Elon_Musk",
        "Artificial_Intelligence",
        "Python_(programming_language)",
        "Machine_learning"
    ]
    
    stats = {
        'total_articles': 0,
        'total_words': 0,
        'total_sections': 0,
        'total_references': 0,
        'fact_checked_count': 0,
        'articles': []
    }
    
    with Client() as client:
        for slug in slugs:
            try:
                article = client.get_article(slug)
                stats['total_articles'] += 1
                stats['total_words'] += article.metadata.word_count
                stats['total_sections'] += len(article.sections)
                stats['total_references'] += len(article.references)
                
                if article.metadata.fact_checked:
                    stats['fact_checked_count'] += 1
                
                stats['articles'].append({
                    'title': article.title,
                    'word_count': article.metadata.word_count,
                    'sections': len(article.sections),
                    'references': len(article.references)
                })
            except Exception as e:
                print(f"✗ Error fetching {slug}: {e}")
        
        print(f"\nStatistics for {stats['total_articles']} articles:")
        print(f"  Total words: {stats['total_words']:,}")
        print(f"  Total sections: {stats['total_sections']}")
        print(f"  Total references: {stats['total_references']}")
        print(f"  Fact-checked articles: {stats['fact_checked_count']}")
        print(f"  Average words per article: {stats['total_words'] // stats['total_articles']:,}")
        
        print("\nArticle breakdown:")
        for article in stats['articles']:
            print(f"  - {article['title']}: {article['word_count']:,} words, "
                  f"{article['sections']} sections, {article['references']} references")


def example_extract_specific_sections():
    """Extract specific sections from multiple articles"""
    print("\n" + "=" * 60)
    print("Example 5: Extract Specific Sections")
    print("=" * 60)
    
    articles_to_extract = [
        ("Joe_Biden", "Early Life"),
        ("Elon_Musk", "Education"),
        ("Artificial_Intelligence", "History")
    ]
    
    with Client() as client:
        for slug, section_title in articles_to_extract:
            try:
                section = client.get_section(slug, section_title)
                if section:
                    print(f"\n✓ {slug} - {section.title}:")
                    print(f"  {section.content[:200]}...")
                else:
                    print(f"\n✗ {slug} - Section '{section_title}' not found")
            except ArticleNotFound:
                print(f"\n✗ {slug} - Article not found")
            except Exception as e:
                print(f"\n✗ {slug} - Error: {e}")


def example_progressive_loading():
    """Progressive loading with user feedback"""
    print("\n" + "=" * 60)
    print("Example 6: Progressive Loading")
    print("=" * 60)
    
    slugs = [
        "Joe_Biden",
        "Elon_Musk",
        "Artificial_Intelligence"
    ]
    
    with Client() as client:
        print(f"\nLoading {len(slugs)} articles with progress updates...")
        
        for i, slug in enumerate(slugs, 1):
            print(f"\n[{i}/{len(slugs)}] Fetching {slug}...", end=" ", flush=True)
            try:
                article = client.get_article(slug)
                print(f"✓ Done ({article.metadata.word_count:,} words)")
            except Exception as e:
                print(f"✗ Failed: {e}")
        
        print("\n✓ Batch processing complete!")


if __name__ == "__main__":
    print("\nGrokipedia SDK - Batch Processing Examples")
    print("=" * 60)
    
    try:
        example_batch_summaries()
        example_batch_with_error_handling()
        example_filter_articles_by_criteria()
        example_collect_statistics()
        example_extract_specific_sections()
        example_progressive_loading()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

