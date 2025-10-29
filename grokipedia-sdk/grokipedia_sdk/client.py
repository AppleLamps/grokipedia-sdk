"""Core SDK client for interacting with Grokipedia"""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List
from urllib.parse import urljoin

from .models import Article, ArticleSummary, Section, ArticleMetadata
from .exceptions import ArticleNotFound, RequestError
from .slug_index import SlugIndex
from . import parsers


class Client:
    """Client for accessing Grokipedia content"""
    
    def __init__(
        self, 
        base_url: str = "https://grokipedia.com", 
        timeout: float = 30.0,
        slug_index: Optional[SlugIndex] = None
    ):
        """
        Initialize the Grokipedia SDK client.
        
        Args:
            base_url: Base URL for Grokipedia (default: https://grokipedia.com)
            timeout: Request timeout in seconds (default: 30.0)
            slug_index: Optional SlugIndex instance for article lookup. 
                       If None, a default SlugIndex will be created.
                       
        Example:
            >>> # Default usage (auto-creates SlugIndex)
            >>> client = Client()
            
            >>> # With custom SlugIndex
            >>> from grokipedia_sdk import SlugIndex
            >>> custom_index = SlugIndex(links_dir="/custom/path")
            >>> client = Client(slug_index=custom_index)
            
            >>> # For testing with mock
            >>> mock_index = MockSlugIndex()
            >>> client = Client(slug_index=mock_index)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout, follow_redirects=True)
        self._slug_index = slug_index if slug_index is not None else SlugIndex()
        self._article_cache = {}
    
    def __enter__(self):
        """Support for context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up httpx client on exit"""
        self.close()
    
    def close(self):
        """Close the HTTP client"""
        if self._client:
            self._client.close()
    
    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            ArticleNotFound: If the article is not found (404)
            RequestError: For other HTTP errors or network issues
        """
        try:
            headers = {
                "User-Agent": "GrokipediaSDK/1.0 (Python SDK; +https://github.com/AppleLamps/grokipedia-sdk)"
            }
            response = self._client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ArticleNotFound(f"Article not found: {url}")
            raise RequestError(f"HTTP error {e.response.status_code} fetching {url}: {str(e)}")
        except httpx.TimeoutException:
            raise RequestError(f"Request timeout - Grokipedia took too long to respond")
        except Exception as e:
            raise RequestError(f"Error fetching {url}: {str(e)}")
    
    def get_article(self, slug: str) -> Article:
        """
        Get a complete article from Grokipedia by slug.
        
        Articles are automatically cached after the first fetch to improve
        performance for subsequent requests.
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            
        Returns:
            Article object with full content
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        # Check cache first
        if slug in self._article_cache:
            return self._article_cache[slug]
        
        # Not in cache, fetch from network
        url = f"{self.base_url}/page/{slug}"
        html = self._fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title first
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
        
        # Extract summary
        summary = parsers.extract_summary(soup, title_tag)
        
        # Extract references BEFORE modifying soup
        references = parsers.extract_references(soup)
        
        # Extract metadata BEFORE modifying soup
        fact_checked = parsers.extract_fact_check_info(soup)
        
        # NOW remove unwanted elements for clean text
        parsers.clean_html_for_text_extraction(soup)
        
        # Get full text content
        full_content = soup.get_text(separator='\n', strip=True)
        
        # Extract sections and TOC
        sections, toc = parsers.extract_sections(soup)
        
        # Calculate word count
        word_count = len(full_content.split())
        
        metadata = ArticleMetadata(
            fact_checked=fact_checked,
            word_count=word_count
        )
        
        article = Article(
            title=title,
            slug=slug,
            url=url,
            summary=summary,
            full_content=full_content,
            sections=sections,
            table_of_contents=toc,
            references=references,
            metadata=metadata,
            scraped_at=datetime.utcnow().isoformat()
        )
        
        # Cache the article for future use
        self._article_cache[slug] = article
        
        return article
    
    def get_summary(self, slug: str) -> ArticleSummary:
        """
        Get just the summary/intro of an article (faster, less data).
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            
        Returns:
            ArticleSummary object with summary and TOC
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        url = f"{self.base_url}/page/{slug}"
        html = self._fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else slug.replace('_', ' ')
        
        # Extract summary
        summary = parsers.extract_summary(soup, title_tag)
        
        # Extract TOC using the same parser as get_article for consistency
        _, toc = parsers.extract_sections(soup)
        
        return ArticleSummary(
            title=title,
            slug=slug,
            url=url,
            summary=summary,
            table_of_contents=toc[:10],  # Limit to first 10 for quick overview
            scraped_at=datetime.utcnow().isoformat()
        )
    
    def get_section(self, slug: str, section_title: str) -> Optional[Section]:
        """
        Get a specific section of an article by title.
        
        Args:
            slug: Article slug (e.g., "Joe_Biden")
            section_title: Section title to search for
            
        Returns:
            Section object if found, None otherwise
            
        Raises:
            ArticleNotFound: If the article doesn't exist
            RequestError: For network or HTTP errors
        """
        article = self.get_article(slug)
        
        # Find matching section (case-insensitive, partial match)
        section_title_lower = section_title.lower().replace('_', ' ')
        
        for section in article.sections:
            if section_title_lower in section.title.lower():
                return section
        
        return None
    
    # Slug search and discovery methods
    
    def search_slug(self, query: str, limit: int = 10, fuzzy: bool = True) -> List[str]:
        """
        Search for article slugs matching a query.
        
        This method searches through the local sitemap index to find articles
        matching your query. It's fast and doesn't require network requests.
        
        Args:
            query: Search query (partial name or slug, case-insensitive)
            limit: Maximum number of results to return (default: 10)
            fuzzy: Enable fuzzy matching for approximate matches (default: True)
            
        Returns:
            List of matching slugs ordered by relevance
            
        Example:
            >>> client = Client()
            >>> client.search_slug("joe biden")
            ['Joe_Biden', 'Joe_Biden_presidential_campaign', ...]
            >>> client.search_slug("artificial intelligence", limit=5)
            ['Artificial_Intelligence', 'Artificial_Neural_Network', ...]
        """
        return self._slug_index.search(query, limit=limit, fuzzy=fuzzy)
    
    def find_slug(self, query: str) -> Optional[str]:
        """
        Find the best matching slug for a query.
        
        This is a convenience method that returns the single best match
        for your query. Useful when you want to quickly find one article.
        
        Args:
            query: Article name or partial slug (case-insensitive)
            
        Returns:
            Best matching slug or None if not found
            
        Example:
            >>> client = Client()
            >>> slug = client.find_slug("elon musk")
            >>> print(slug)
            'Elon_Musk'
            >>> article = client.get_article(slug)
        """
        return self._slug_index.find_best_match(query)
    
    def slug_exists(self, slug: str) -> bool:
        """
        Check if a slug exists in the sitemap index.
        
        Args:
            slug: Slug to check
            
        Returns:
            True if slug exists, False otherwise
            
        Example:
            >>> client = Client()
            >>> client.slug_exists("Joe_Biden")
            True
            >>> client.slug_exists("Nonexistent_Article")
            False
        """
        return self._slug_index.exists(slug)
    
    def list_available_articles(self, prefix: str = "", limit: int = 100) -> List[str]:
        """
        List available articles, optionally filtered by prefix.
        
        Args:
            prefix: Filter articles starting with this prefix (case-insensitive)
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of article slugs matching the prefix
            
        Example:
            >>> client = Client()
            >>> articles = client.list_available_articles(prefix="Artificial", limit=20)
            >>> print(articles)
            ['Artificial_Intelligence', 'Artificial_Neural_Network', ...]
            >>> all_articles = client.list_available_articles(limit=50)
        """
        return self._slug_index.list_by_prefix(prefix=prefix, limit=limit)
    
    def get_total_article_count(self) -> int:
        """
        Get the total number of articles available in the index.
        
        Returns:
            Total number of unique articles
            
        Example:
            >>> client = Client()
            >>> total = client.get_total_article_count()
            >>> print(f"Total articles available: {total}")
            Total articles available: 50000
        """
        return self._slug_index.get_total_count()
    
    def get_random_articles(self, count: int = 10) -> List[str]:
        """
        Get random article slugs from the index.
        
        Useful for exploring the content or building sample datasets.
        
        Args:
            count: Number of random slugs to return (default: 10)
            
        Returns:
            List of random article slugs
            
        Example:
            >>> client = Client()
            >>> random_slugs = client.get_random_articles(5)
            >>> for slug in random_slugs:
            ...     article = client.get_summary(slug)
            ...     print(article.title)
        """
        return self._slug_index.random_slugs(count=count)

