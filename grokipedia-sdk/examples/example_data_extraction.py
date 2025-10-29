"""Data extraction and analysis examples"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError
from typing import List, Dict, Set
import re


def example_extract_all_references():
    """Extract and analyze all references from an article"""
    print("=" * 60)
    print("Example 1: Extract References")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Joe_Biden")
            
            print(f"\nArticle: {article.title}")
            print(f"Total references: {len(article.references)}\n")
            
            print("References:")
            for i, ref in enumerate(article.references[:10], 1):  # Show first 10
                print(f"  {i}. {ref}")
            
            if len(article.references) > 10:
                print(f"\n  ... and {len(article.references) - 10} more")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_extract_keywords():
    """Extract keywords and key phrases from article content"""
    print("\n" + "=" * 60)
    print("Example 2: Extract Keywords")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Artificial_Intelligence")
            
            # Simple keyword extraction (capitalized words, important terms)
            content = article.full_content.lower()
            words = re.findall(r'\b[a-z]{4,}\b', content)
            
            # Count word frequencies
            word_freq = {}
            for word in words:
                # Skip common words
                common_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 
                               'were', 'been', 'would', 'there', 'their', 'which', 'these'}
                if word not in common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
            
            print(f"\nArticle: {article.title}")
            print(f"Total words: {len(article.full_content.split()):,}")
            print("\nTop keywords:")
            for word, count in top_keywords:
                print(f"  {word}: {count}")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_extract_dates():
    """Extract dates mentioned in article"""
    print("\n" + "=" * 60)
    print("Example 3: Extract Dates")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Joe_Biden")
            
            # Simple date pattern matching
            date_patterns = [
                r'\b\d{4}\b',  # Years
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
            ]
            
            dates = set()
            for pattern in date_patterns:
                matches = re.findall(pattern, article.full_content, re.IGNORECASE)
                dates.update(matches)
            
            print(f"\nArticle: {article.title}")
            print(f"\nFound {len(dates)} dates:")
            for date in sorted(dates)[:20]:  # Show first 20
                print(f"  - {date}")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_extract_links_to_other_articles():
    """Extract potential links to other articles (wiki-style links)"""
    print("\n" + "=" * 60)
    print("Example 4: Extract Article Links")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Artificial_Intelligence")
            
            # Look for capitalized word sequences (potential article titles)
            # This is a simple heuristic - real implementation would parse HTML links
            pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
            potential_articles = re.findall(pattern, article.full_content)
            
            # Filter and deduplicate
            unique_articles = list(set(potential_articles))
            
            print(f"\nArticle: {article.title}")
            print(f"\nFound {len(unique_articles)} potential article references:")
            for ref in sorted(unique_articles)[:20]:  # Show first 20
                # Check if it exists as a slug
                slug = ref.replace(' ', '_')
                if client.slug_exists(slug):
                    print(f"  ✓ {ref} ({slug})")
                else:
                    print(f"  ? {ref}")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_build_article_graph():
    """Build a graph of related articles"""
    print("\n" + "=" * 60)
    print("Example 5: Build Article Graph")
    print("=" * 60)
    
    with Client() as client:
        seed_article = "Artificial_Intelligence"
        
        try:
            article = client.get_article(seed_article)
            print(f"\nSeed article: {article.title}")
            
            # Find related articles by searching for terms in the article
            # Extract key terms from title and summary
            terms = article.title.split() + article.summary.split()[:20]
            
            related_articles = set()
            for term in terms[:10]:  # Use first 10 terms
                if len(term) > 4:  # Skip short words
                    matches = client.search_slug(term, limit=5)
                    related_articles.update(matches)
            
            # Remove the seed article itself
            related_articles.discard(seed_article.replace(' ', '_'))
            
            print(f"\nFound {len(related_articles)} related articles:")
            for slug in sorted(list(related_articles))[:15]:
                try:
                    summary = client.get_summary(slug)
                    print(f"  - {summary.title}")
                except:
                    print(f"  - {slug}")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_extract_statistics():
    """Extract various statistics from articles"""
    print("\n" + "=" * 60)
    print("Example 6: Extract Statistics")
    print("=" * 60)
    
    articles = ["Joe_Biden", "Elon_Musk", "Artificial_Intelligence"]
    
    with Client() as client:
        all_stats = []
        
        for slug in articles:
            try:
                article = client.get_article(slug)
                
                stats = {
                    'title': article.title,
                    'word_count': article.metadata.word_count,
                    'section_count': len(article.sections),
                    'reference_count': len(article.references),
                    'toc_count': len(article.table_of_contents),
                    'has_fact_check': bool(article.metadata.fact_checked),
                    'avg_words_per_section': article.metadata.word_count / len(article.sections) if article.sections else 0
                }
                
                all_stats.append(stats)
                
                print(f"\n{stats['title']}:")
                print(f"  Words: {stats['word_count']:,}")
                print(f"  Sections: {stats['section_count']}")
                print(f"  References: {stats['reference_count']}")
                print(f"  Avg words/section: {stats['avg_words_per_section']:.0f}")
                print(f"  Fact-checked: {'Yes' if stats['has_fact_check'] else 'No'}")
            
            except Exception as e:
                print(f"\n✗ Error fetching {slug}: {e}")
        
        # Summary statistics
        if all_stats:
            print("\n" + "=" * 60)
            print("Summary Statistics:")
            print(f"  Total articles analyzed: {len(all_stats)}")
            print(f"  Average word count: {sum(s['word_count'] for s in all_stats) / len(all_stats):,.0f}")
            print(f"  Average sections: {sum(s['section_count'] for s in all_stats) / len(all_stats):.1f}")
            print(f"  Average references: {sum(s['reference_count'] for s in all_stats) / len(all_stats):.1f}")


def example_extract_section_statistics():
    """Extract statistics for each section"""
    print("\n" + "=" * 60)
    print("Example 7: Section Statistics")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Artificial_Intelligence")
            
            print(f"\nArticle: {article.title}")
            print("\nSection Statistics:")
            print("-" * 60)
            
            for section in article.sections[:15]:  # First 15 sections
                word_count = len(section.content.split())
                char_count = len(section.content)
                sentence_count = len(re.findall(r'[.!?]+', section.content))
                
                print(f"\n{section.title} (Level {section.level}):")
                print(f"  Words: {word_count}")
                print(f"  Characters: {char_count:,}")
                print(f"  Sentences: {sentence_count}")
                if sentence_count > 0:
                    print(f"  Avg words/sentence: {word_count / sentence_count:.1f}")
            
            print("-" * 60)
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


def example_export_article_data():
    """Export article data in structured format"""
    print("\n" + "=" * 60)
    print("Example 8: Export Article Data")
    print("=" * 60)
    
    with Client() as client:
        try:
            article = client.get_article("Joe_Biden")
            
            # Structure data for export
            export_data = {
                'title': article.title,
                'slug': article.slug,
                'url': str(article.url),
                'metadata': {
                    'word_count': article.metadata.word_count,
                    'fact_checked': article.metadata.fact_checked,
                    'last_updated': article.metadata.last_updated,
                    'scraped_at': article.scraped_at
                },
                'summary': article.summary,
                'sections': [
                    {
                        'title': s.title,
                        'level': s.level,
                        'word_count': len(s.content.split())
                    }
                    for s in article.sections
                ],
                'table_of_contents': article.table_of_contents,
                'reference_count': len(article.references),
                'references': article.references[:10]  # First 10
            }
            
            print(f"\nArticle: {article.title}")
            print(f"\nExport Data Structure:")
            print(f"  Title: {export_data['title']}")
            print(f"  Slug: {export_data['slug']}")
            print(f"  Metadata keys: {list(export_data['metadata'].keys())}")
            print(f"  Sections: {len(export_data['sections'])}")
            print(f"  References: {export_data['reference_count']}")
            print(f"\nThis data can be exported to JSON, CSV, or database")
        
        except (ArticleNotFound, RequestError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("\nGrokipedia SDK - Data Extraction Examples")
    print("=" * 60)
    
    try:
        example_extract_all_references()
        example_extract_keywords()
        example_extract_dates()
        example_extract_links_to_other_articles()
        example_build_article_graph()
        example_extract_statistics()
        example_extract_section_statistics()
        example_export_article_data()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

