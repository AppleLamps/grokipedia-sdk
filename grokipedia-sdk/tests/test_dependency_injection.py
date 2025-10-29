"""Tests for dependency injection of SlugIndex into Client"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from grokipedia_sdk import Client, SlugIndex


class MockSlugIndex:
    """Mock implementation of SlugIndex for testing"""
    
    def __init__(self, articles=None):
        """
        Initialize mock slug index with optional predefined articles.
        
        Args:
            articles: Dict of article names to slugs, or list of slugs
        """
        if articles is None:
            articles = {
                'Joe Biden': 'Joe_Biden',
                'Donald Trump': 'Donald_Trump',
                'Artificial Intelligence': 'Artificial_Intelligence',
            }
        
        if isinstance(articles, list):
            self.articles = {slug.replace('_', ' '): slug for slug in articles}
        else:
            self.articles = articles
    
    def search(self, query, limit=10, fuzzy=True):
        """Search for matching slugs"""
        query_lower = query.lower()
        matches = []
        for name, slug in self.articles.items():
            if query_lower in name.lower():
                matches.append(slug)
                if len(matches) >= limit:
                    break
        return matches
    
    def find_best_match(self, query):
        """Find best matching slug"""
        results = self.search(query, limit=1)
        return results[0] if results else None
    
    def exists(self, slug):
        """Check if slug exists"""
        return slug in self.articles.values()
    
    def list_by_prefix(self, prefix="", limit=100):
        """List articles by prefix"""
        matches = []
        for slug in self.articles.values():
            if slug.lower().startswith(prefix.lower()):
                matches.append(slug)
                if len(matches) >= limit:
                    break
        return matches
    
    def get_total_count(self):
        """Get total article count"""
        return len(self.articles)
    
    def random_slugs(self, count=10):
        """Get random slugs"""
        import random
        slugs = list(self.articles.values())
        return random.sample(slugs, min(count, len(slugs)))


class TestClientDependencyInjection:
    """Test suite for Client dependency injection"""
    
    def test_client_with_default_slug_index(self):
        """Test that Client creates default SlugIndex when not provided"""
        client = Client()
        
        assert client._slug_index is not None
        assert isinstance(client._slug_index, SlugIndex)
    
    def test_client_with_custom_slug_index(self):
        """Test that Client accepts custom SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        assert client._slug_index is mock_index
    
    def test_client_with_none_creates_default(self):
        """Test that passing None explicitly creates default SlugIndex"""
        client = Client(slug_index=None)
        
        assert client._slug_index is not None
        assert isinstance(client._slug_index, SlugIndex)
    
    def test_search_slug_uses_injected_index(self):
        """Test that search_slug uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        results = client.search_slug("Joe")
        
        assert "Joe_Biden" in results
    
    def test_find_slug_uses_injected_index(self):
        """Test that find_slug uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        result = client.find_slug("artificial")
        
        assert result == "Artificial_Intelligence"
    
    def test_slug_exists_uses_injected_index(self):
        """Test that slug_exists uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        assert client.slug_exists("Joe_Biden")
        assert not client.slug_exists("Nonexistent_Article")
    
    def test_list_available_articles_uses_injected_index(self):
        """Test that list_available_articles uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        articles = client.list_available_articles(prefix="Artificial", limit=10)
        
        assert "Artificial_Intelligence" in articles
    
    def test_get_total_article_count_uses_injected_index(self):
        """Test that get_total_article_count uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        count = client.get_total_article_count()
        
        assert count == 3  # MockSlugIndex has 3 articles
    
    def test_get_random_articles_uses_injected_index(self):
        """Test that get_random_articles uses the injected SlugIndex"""
        mock_index = MockSlugIndex()
        client = Client(slug_index=mock_index)
        
        articles = client.get_random_articles(count=2)
        
        assert len(articles) == 2
        assert all(article in list(mock_index.articles.values()) for article in articles)


class TestClientWithMockSlugIndex:
    """Test Client methods with mocked SlugIndex"""
    
    def test_client_initialization_with_mock(self):
        """Test Client initializes properly with mock SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        client = Client(slug_index=mock_index)
        
        assert client._slug_index is mock_index
    
    def test_search_slug_with_mock(self):
        """Test search_slug delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.search.return_value = ['Article1', 'Article2']
        
        client = Client(slug_index=mock_index)
        result = client.search_slug("test", limit=5, fuzzy=True)
        
        mock_index.search.assert_called_once_with("test", limit=5, fuzzy=True)
        assert result == ['Article1', 'Article2']
    
    def test_find_slug_with_mock(self):
        """Test find_slug delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.find_best_match.return_value = 'Best_Match'
        
        client = Client(slug_index=mock_index)
        result = client.find_slug("query")
        
        mock_index.find_best_match.assert_called_once_with("query")
        assert result == 'Best_Match'
    
    def test_slug_exists_with_mock(self):
        """Test slug_exists delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.exists.return_value = True
        
        client = Client(slug_index=mock_index)
        result = client.slug_exists("Some_Slug")
        
        mock_index.exists.assert_called_once_with("Some_Slug")
        assert result is True
    
    def test_list_available_articles_with_mock(self):
        """Test list_available_articles delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.list_by_prefix.return_value = ['Article1', 'Article2']
        
        client = Client(slug_index=mock_index)
        result = client.list_available_articles(prefix="A", limit=50)
        
        mock_index.list_by_prefix.assert_called_once_with(prefix="A", limit=50)
        assert result == ['Article1', 'Article2']
    
    def test_get_total_article_count_with_mock(self):
        """Test get_total_article_count delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.get_total_count.return_value = 1000
        
        client = Client(slug_index=mock_index)
        result = client.get_total_article_count()
        
        mock_index.get_total_count.assert_called_once()
        assert result == 1000
    
    def test_get_random_articles_with_mock(self):
        """Test get_random_articles delegates to injected SlugIndex"""
        mock_index = Mock(spec=SlugIndex)
        mock_index.random_slugs.return_value = ['Random1', 'Random2', 'Random3']
        
        client = Client(slug_index=mock_index)
        result = client.get_random_articles(count=3)
        
        mock_index.random_slugs.assert_called_once_with(count=3)
        assert result == ['Random1', 'Random2', 'Random3']


class TestBackwardCompatibility:
    """Test backward compatibility - existing code should work unchanged"""
    
    def test_client_default_constructor_still_works(self):
        """Test that old constructor calls still work"""
        # Old way: no slug_index parameter
        client = Client()
        assert client._slug_index is not None
        
        client = Client(base_url="https://example.com")
        assert client._slug_index is not None
        
        client = Client(timeout=60.0)
        assert client._slug_index is not None
        
        client = Client(base_url="https://example.com", timeout=60.0)
        assert client._slug_index is not None
    
    def test_client_slug_methods_work_with_default_index(self):
        """Test that slug methods work without explicitly passing slug_index"""
        client = Client()
        
        # These should work with default SlugIndex
        # (may return empty results if links not loaded, but shouldn't error)
        try:
            results = client.search_slug("test")
            assert isinstance(results, list)
        except Exception as e:
            pytest.fail(f"search_slug failed with default index: {e}")
        
        try:
            count = client.get_total_article_count()
            assert isinstance(count, int)
        except Exception as e:
            pytest.fail(f"get_total_article_count failed with default index: {e}")


class TestRealWorldUseCases:
    """Test real-world usage patterns"""
    
    def test_testing_with_mock_index(self):
        """Test pattern: using mock index for unit testing"""
        # Setup: Create a mock index with known articles
        mock_index = MockSlugIndex(['Test_Article_1', 'Test_Article_2'])
        client = Client(slug_index=mock_index)
        
        # Test: Client methods work predictably with mock
        assert client.slug_exists('Test_Article_1')
        assert not client.slug_exists('Nonexistent')
        
        results = client.search_slug('Test')
        assert len(results) >= 1
    
    def test_custom_slug_index_implementation(self):
        """Test pattern: using custom SlugIndex implementation"""
        # Setup: Create a custom index with different behavior
        custom_articles = {
            'Custom Article': 'Custom_Article',
            'Another Article': 'Another_Article',
        }
        custom_index = MockSlugIndex(custom_articles)
        client = Client(slug_index=custom_index)
        
        # Test: Client works with custom implementation
        assert client.get_total_article_count() == 2
        assert client.slug_exists('Custom_Article')
    
    def test_switching_indexes_at_runtime(self):
        """Test pattern: switching between different indexes"""
        # Setup: Create multiple indexes
        index1 = MockSlugIndex(['Article_A', 'Article_B'])
        index2 = MockSlugIndex(['Article_C', 'Article_D'])
        
        # Create client with first index
        client = Client(slug_index=index1)
        assert client.slug_exists('Article_A')
        assert not client.slug_exists('Article_C')
        
        # Switch to second index
        client._slug_index = index2
        assert not client.slug_exists('Article_A')
        assert client.slug_exists('Article_C')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
