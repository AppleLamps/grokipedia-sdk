"""Example CLI tool using Grokipedia SDK"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError
import argparse
import sys


def search_articles(query: str, limit: int = 10):
    """Search for articles matching a query"""
    with Client() as client:
        print(f"\nSearching for '{query}'...")
        results = client.search_slug(query, limit=limit)
        
        if results:
            print(f"\nFound {len(results)} results:\n")
            for i, slug in enumerate(results, 1):
                print(f"  {i}. {slug}")
        else:
            print("\nNo results found.")


def show_article_summary(slug: str):
    """Show summary of an article"""
    with Client() as client:
        try:
            summary = client.get_summary(slug)
            
            print(f"\n{'=' * 60}")
            print(f"Title: {summary.title}")
            print(f"URL: {summary.url}")
            print(f"{'=' * 60}\n")
            print(f"Summary:\n{summary.summary}\n")
            
            if summary.table_of_contents:
                print("Table of Contents:")
                for i, section in enumerate(summary.table_of_contents[:10], 1):
                    print(f"  {i}. {section}")
                if len(summary.table_of_contents) > 10:
                    print(f"  ... and {len(summary.table_of_contents) - 10} more sections")
        
        except ArticleNotFound:
            print(f"\n✗ Article '{slug}' not found.")
            print("  Tip: Use 'search' command to find the correct slug")
        except RequestError as e:
            print(f"\n✗ Error fetching article: {e}")


def show_full_article(slug: str):
    """Show full article content"""
    with Client() as client:
        try:
            article = client.get_article(slug)
            
            print(f"\n{'=' * 60}")
            print(f"Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"{'=' * 60}\n")
            
            print(f"Summary:\n{article.summary}\n")
            
            print(f"Full Content:\n{article.full_content[:1000]}...")
            print(f"\n[... {article.metadata.word_count - len(article.full_content[:1000].split()):,} more words ...]\n")
            
            print(f"Metadata:")
            print(f"  Word count: {article.metadata.word_count:,}")
            print(f"  Sections: {len(article.sections)}")
            print(f"  References: {len(article.references)}")
            if article.metadata.fact_checked:
                print(f"  Fact-checked: {article.metadata.fact_checked}")
        
        except ArticleNotFound:
            print(f"\n✗ Article '{slug}' not found.")
        except RequestError as e:
            print(f"\n✗ Error fetching article: {e}")


def show_section(slug: str, section_title: str):
    """Show a specific section of an article"""
    with Client() as client:
        try:
            section = client.get_section(slug, section_title)
            
            if section:
                print(f"\n{'=' * 60}")
                print(f"Article: {slug}")
                print(f"Section: {section.title}")
                print(f"{'=' * 60}\n")
                print(section.content)
            else:
                print(f"\n✗ Section '{section_title}' not found in article '{slug}'")
                print("\nAvailable sections:")
                try:
                    article = client.get_article(slug)
                    for s in article.sections[:10]:
                        print(f"  - {s.title}")
                except:
                    pass
        
        except ArticleNotFound:
            print(f"\n✗ Article '{slug}' not found.")
        except RequestError as e:
            print(f"\n✗ Error: {e}")


def list_articles(prefix: str = "", limit: int = 20):
    """List available articles"""
    with Client() as client:
        print(f"\nListing articles{' starting with ' + prefix if prefix else ''}...\n")
        
        articles = client.list_available_articles(prefix=prefix, limit=limit)
        
        if articles:
            for i, slug in enumerate(articles, 1):
                print(f"  {i}. {slug}")
        else:
            print("No articles found.")


def show_stats():
    """Show statistics about available articles"""
    with Client() as client:
        total = client.get_total_article_count()
        print(f"\n{'=' * 60}")
        print(f"Grokipedia Statistics")
        print(f"{'=' * 60}")
        print(f"\nTotal articles in index: {total:,}")
        print(f"\nExample: Use 'search <query>' to find articles")
        print(f"         Use 'summary <slug>' to view article summary")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Grokipedia SDK CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "joe biden"
  %(prog)s summary Joe_Biden
  %(prog)s article Joe_Biden
  %(prog)s section Joe_Biden "Early Life"
  %(prog)s list --prefix "Python"
  %(prog)s stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for articles')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum results (default: 10)')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show article summary')
    summary_parser.add_argument('slug', help='Article slug (e.g., Joe_Biden)')
    
    # Article command
    article_parser = subparsers.add_parser('article', help='Show full article')
    article_parser.add_argument('slug', help='Article slug (e.g., Joe_Biden)')
    
    # Section command
    section_parser = subparsers.add_parser('section', help='Show article section')
    section_parser.add_argument('slug', help='Article slug')
    section_parser.add_argument('section_title', help='Section title')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List articles')
    list_parser.add_argument('--prefix', default='', help='Filter by prefix')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum results (default: 20)')
    
    # Stats command
    subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'search':
            search_articles(args.query, args.limit)
        elif args.command == 'summary':
            show_article_summary(args.slug)
        elif args.command == 'article':
            show_full_article(args.slug)
        elif args.command == 'section':
            show_section(args.slug, args.section_title)
        elif args.command == 'list':
            list_articles(args.prefix, args.limit)
        elif args.command == 'stats':
            show_stats()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

