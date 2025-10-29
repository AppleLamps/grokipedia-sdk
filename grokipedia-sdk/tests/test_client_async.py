"""Tests for Client async methods"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from grokipedia_sdk import Client, ArticleNotFound, RequestError
from grokipedia_sdk.models import Article, ArticleSummary


SAMPLE_ARTICLE_HTML = """
<html>
<head>
    <meta property="og:description" content="Article about Joe Biden.">
</head>
<body>
    <h1>Joe Biden</h1>
    <p>This is a comprehensive article about Joe Biden, who served as the 46th President of the United States.</p>
    
    <h2>Early Life</h2>
    <p>Joe Biden was born in Scranton, Pennsylvania in 1942.</p>
    
    <h2>References</h2>
    <ol>
        <li><a href="https://example.com/source1">Source 1</a></li>
    </ol>
</body>
</html>
"""

SAMPLE_SUMMARY_HTML = """
<html>
<head>
    <meta property="og:description" content="Summary about Joe Biden.">
</head>
<body>
    <h1>Joe Biden</h1>
    <p>This is a summary paragraph about Joe Biden.</p>
</body>
</html>
"""


class TestClientAsyncMethods:
    """Test Client async methods"""
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_success(self, mock_async_client_class):
        """Test successful async article fetch"""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com")
        article = await client.get_article_async("Joe_Biden")
        
        assert isinstance(article, Article)
        assert article.title == "Joe Biden"
        assert article.slug == "Joe_Biden"
        assert len(article.sections) >= 1
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_summary_async_success(self, mock_async_client_class):
        """Test successful async summary fetch"""
        mock_response = Mock()
        mock_response.text = SAMPLE_SUMMARY_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com")
        summary = await client.get_summary_async("Joe_Biden")
        
        assert isinstance(summary, ArticleSummary)
        assert summary.title == "Joe Biden"
        assert summary.slug == "Joe_Biden"
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_caching(self, mock_async_client_class):
        """Test that async articles are cached"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", max_cache_size=10)
        
        # First fetch
        article1 = await client.get_article_async("Joe_Biden")
        
        # Second fetch - should use cache
        article2 = await client.get_article_async("Joe_Biden")
        
        # Should only call get once (cached)
        assert mock_async_client.get.call_count == 1
        assert article1 is article2


class TestClientAsyncErrorHandling:
    """Test async error handling"""
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_404_raises_article_not_found(self, mock_async_client_class):
        """Test that async 404 raises ArticleNotFound"""
        import httpx
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        ))
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", max_retries=0)
        
        with pytest.raises(ArticleNotFound):
            await client.get_article_async("Nonexistent_Article")
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_retries_on_500(self, mock_async_client_class):
        """Test that async methods retry on server errors"""
        import httpx
        
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response_500
        ))
        
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(side_effect=[mock_response_500, mock_response_200])
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = await client.get_article_async("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_async_client.get.call_count == 2
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_connection_error_retries(self, mock_async_client_class):
        """Test that async connection errors retry"""
        import httpx
        
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(side_effect=[
            httpx.ConnectError("Connection failed"),
            mock_response
        ])
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = await client.get_article_async("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_async_client.get.call_count == 2
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_get_article_async_timeout_retries(self, mock_async_client_class):
        """Test that async timeout errors retry"""
        import httpx
        
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(side_effect=[
            httpx.TimeoutException("Request timeout"),
            mock_response
        ])
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = await client.get_article_async("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_async_client.get.call_count == 2


class TestClientAsyncRateLimiting:
    """Test async rate limiting"""
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    @patch('grokipedia_sdk.client.asyncio.sleep')
    @patch('grokipedia_sdk.client.time.time')
    async def test_async_rate_limiting_enforced(self, mock_time, mock_sleep, mock_async_client_class):
        """Test that async rate limiting delays requests"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        # Mock time to return same value (simulating immediate second call)
        def time_side_effect():
            return 0.0
        mock_time.side_effect = time_side_effect
        
        client = Client(base_url="https://test.com", rate_limit=1.0, max_retries=0)
        
        # First request
        await client.get_article_async("Article1")
        
        # Second request (should delay because elapsed < rate_limit)
        await client.get_article_async("Article2")
        
        # Verify sleep was called
        assert mock_sleep.called


class TestClientConcurrentAsyncRequests:
    """Test concurrent async requests"""
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_concurrent_async_requests(self, mock_async_client_class):
        """Test that multiple async requests can run concurrently"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", rate_limit=0, max_retries=0)
        
        # Make concurrent requests
        articles = await asyncio.gather(
            client.get_article_async("Article1"),
            client.get_article_async("Article2"),
            client.get_article_async("Article3"),
        )
        
        assert len(articles) == 3
        assert all(isinstance(article, Article) for article in articles)
        assert mock_async_client.get.call_count == 3
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_concurrent_async_summaries(self, mock_async_client_class):
        """Test concurrent async summary requests"""
        mock_response = Mock()
        mock_response.text = SAMPLE_SUMMARY_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(return_value=mock_response)
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", rate_limit=0, max_retries=0)
        
        # Make concurrent requests
        summaries = await asyncio.gather(
            client.get_summary_async("Article1"),
            client.get_summary_async("Article2"),
            client.get_summary_async("Article3"),
        )
        
        assert len(summaries) == 3
        assert all(isinstance(summary, ArticleSummary) for summary in summaries)
        assert mock_async_client.get.call_count == 3
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_concurrent_mixed_async_requests(self, mock_async_client_class):
        """Test concurrent mixed article and summary requests"""
        mock_article_response = Mock()
        mock_article_response.text = SAMPLE_ARTICLE_HTML
        mock_article_response.status_code = 200
        mock_article_response.raise_for_status = Mock()
        
        mock_summary_response = Mock()
        mock_summary_response.text = SAMPLE_SUMMARY_HTML
        mock_summary_response.status_code = 200
        mock_summary_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        
        # Alternate between article and summary responses
        mock_async_client.get = AsyncMock(side_effect=[
            mock_article_response,
            mock_summary_response,
            mock_article_response,
        ])
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", rate_limit=0, max_retries=0)
        
        # Make concurrent mixed requests
        results = await asyncio.gather(
            client.get_article_async("Article1"),
            client.get_summary_async("Article2"),
            client.get_article_async("Article3"),
        )
        
        assert isinstance(results[0], Article)
        assert isinstance(results[1], ArticleSummary)
        assert isinstance(results[2], Article)
        assert mock_async_client.get.call_count == 3


class TestClientAsyncIntegration:
    """Integration tests for async methods"""
    
    @pytest.mark.asyncio
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    async def test_async_article_then_summary(self, mock_async_client_class):
        """Test fetching article then summary async"""
        mock_article_response = Mock()
        mock_article_response.text = SAMPLE_ARTICLE_HTML
        mock_article_response.status_code = 200
        mock_article_response.raise_for_status = Mock()
        
        mock_summary_response = Mock()
        mock_summary_response.text = SAMPLE_SUMMARY_HTML
        mock_summary_response.status_code = 200
        mock_summary_response.raise_for_status = Mock()
        
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.get = AsyncMock(side_effect=[
            mock_article_response,
            mock_summary_response,
        ])
        mock_async_client_class.return_value = mock_async_client
        
        client = Client(base_url="https://test.com", rate_limit=0, max_retries=0)
        
        article = await client.get_article_async("Joe_Biden")
        summary = await client.get_summary_async("Joe_Biden")
        
        assert isinstance(article, Article)
        assert isinstance(summary, ArticleSummary)
        assert article.title == summary.title


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

