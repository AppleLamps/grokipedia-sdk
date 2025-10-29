"""Tests for Client HTTP methods, error handling, and retry logic"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from grokipedia_sdk import Client, ArticleNotFound, RequestError
from grokipedia_sdk.models import Article, ArticleSummary, Section
import httpx


# Sample HTML for testing
SAMPLE_ARTICLE_HTML = """
<html>
<head>
    <meta property="og:description" content="Article about Joe Biden, the 46th President of the United States.">
</head>
<body>
    <h1>Joe Biden</h1>
    <p>This is a comprehensive article about Joe Biden, who served as the 46th President of the United States. The article covers his early life, political career, and presidency in detail.</p>
    
    <h2>Early Life</h2>
    <p>Joe Biden was born in Scranton, Pennsylvania in 1942.</p>
    
    <h2>Political Career</h2>
    <p>Biden served as a U.S. Senator from Delaware from 1973 to 2009.</p>
    
    <h2>References</h2>
    <ol>
        <li><a href="https://example.com/source1">Source 1</a></li>
        <li><a href="https://example.com/source2">Source 2</a></li>
    </ol>
    
    <footer>Fact-checked by John Smith</footer>
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


class TestClientHTTPMethods:
    """Test Client HTTP fetching methods"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_success(self, mock_client_class):
        """Test successful article fetch"""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_cache_size=10)
        article = client.get_article("Joe_Biden")
        
        # Verify article was fetched and parsed
        assert isinstance(article, Article)
        assert article.title == "Joe Biden"
        assert article.slug == "Joe_Biden"
        assert "Joe Biden" in article.summary
        assert len(article.sections) >= 2
        assert "Early Life" in [s.title for s in article.sections]
        assert len(article.references) == 2
        assert article.metadata.fact_checked is not None
        
        # Verify HTTP request was made
        mock_client_instance.get.assert_called_once()
        call_args = mock_client_instance.get.call_args
        assert call_args[0][0] == "https://test.com/page/Joe_Biden"
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_summary_success(self, mock_client_class):
        """Test successful summary fetch"""
        mock_response = Mock()
        mock_response.text = SAMPLE_SUMMARY_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com")
        summary = client.get_summary("Joe_Biden")
        
        assert isinstance(summary, ArticleSummary)
        assert summary.title == "Joe Biden"
        assert summary.slug == "Joe_Biden"
        assert "summary" in summary.summary.lower()
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_section_success(self, mock_client_class):
        """Test successful section fetch"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com")
        section = client.get_section("Joe_Biden", "Early Life")
        
        assert isinstance(section, Section)
        assert section.title == "Early Life"
        assert "Scranton" in section.content
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_section_not_found(self, mock_client_class):
        """Test get_section returns None when section doesn't exist"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com")
        section = client.get_section("Joe_Biden", "Nonexistent Section")
        
        assert section is None


class TestClientErrorHandling:
    """Test Client error handling and HTTP status codes"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_404_raises_article_not_found(self, mock_client_class):
        """Test that 404 raises ArticleNotFound"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=0)
        
        with pytest.raises(ArticleNotFound) as exc_info:
            client.get_article("Nonexistent_Article")
        
        assert "Nonexistent_Article" in str(exc_info.value)
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_429_rate_limit(self, mock_client_class):
        """Test that 429 rate limit error retries"""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate Limited", request=Mock(), response=mock_response_429
        )
        
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [mock_response_429, mock_response_200]
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = client.get_article("Joe_Biden")
        
        # Should retry and eventually succeed
        assert isinstance(article, Article)
        assert mock_client_instance.get.call_count == 2
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_500_server_error_retries(self, mock_client_class):
        """Test that 500 server errors retry"""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response_500
        )
        
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [mock_response_500, mock_response_200]
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = client.get_article("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_client_instance.get.call_count == 2
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_500_max_retries_exceeded(self, mock_client_class):
        """Test that RequestError is raised after max retries"""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response_500
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response_500
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=2, rate_limit=0)
        
        with pytest.raises(RequestError) as exc_info:
            client.get_article("Joe_Biden")
        
        assert "500" in str(exc_info.value) or "server error" in str(exc_info.value).lower()
        # Should have attempted max_retries + 1 times
        assert mock_client_instance.get.call_count == 3
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_connection_error_retries(self, mock_client_class):
        """Test that connection errors retry"""
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [
            httpx.ConnectError("Connection failed"),
            mock_response_200
        ]
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = client.get_article("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_client_instance.get.call_count == 2
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_timeout_retries(self, mock_client_class):
        """Test that timeout errors retry"""
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [
            httpx.TimeoutException("Request timeout"),
            mock_response_200
        ]
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = client.get_article("Joe_Biden")
        
        assert isinstance(article, Article)
        assert mock_client_instance.get.call_count == 2
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_400_client_error_no_retry(self, mock_client_class):
        """Test that 400 client errors don't retry"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        with pytest.raises(RequestError) as exc_info:
            client.get_article("Joe_Biden")
        
        assert "400" in str(exc_info.value) or "error" in str(exc_info.value).lower()
        # Should not retry for 400 errors
        assert mock_client_instance.get.call_count == 1
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_get_article_403_forbidden_no_retry(self, mock_client_class):
        """Test that 403 forbidden errors don't retry"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=Mock(), response=mock_response
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        with pytest.raises(RequestError) as exc_info:
            client.get_article("Joe_Biden")
        
        assert "403" in str(exc_info.value) or "error" in str(exc_info.value).lower()
        assert mock_client_instance.get.call_count == 1


class TestClientRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    @patch('grokipedia_sdk.client.time.sleep')
    def test_exponential_backoff_on_retries(self, mock_sleep, mock_client_class):
        """Test that retries use exponential backoff"""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response_500
        )
        
        mock_response_200 = Mock()
        mock_response_200.text = SAMPLE_ARTICLE_HTML
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [
            mock_response_500,
            mock_response_500,
            mock_response_200
        ]
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=3, rate_limit=0)
        
        article = client.get_article("Joe_Biden")
        
        assert isinstance(article, Article)
        # Should have slept between retries (exponential backoff: 2^0, 2^1)
        assert mock_sleep.call_count >= 2
        sleep_values = [call[0][0] for call in mock_sleep.call_args_list]
        # Check that sleep times follow exponential pattern (approximately)
        assert sleep_values[0] <= sleep_values[1] or sleep_values[0] == sleep_values[1]
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_no_retries_when_max_retries_zero(self, mock_client_class):
        """Test that no retries occur when max_retries=0"""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response_500
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response_500
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", max_retries=0, rate_limit=0)
        
        with pytest.raises(RequestError):
            client.get_article("Joe_Biden")
        
        # Should only try once (no retries)
        assert mock_client_instance.get.call_count == 1


class TestClientRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    @patch('grokipedia_sdk.client.time.sleep')
    @patch('grokipedia_sdk.client.time.time')
    def test_rate_limiting_enforced(self, mock_time, mock_sleep, mock_client_class):
        """Test that rate limiting delays requests"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        # Simulate time progression - return increasing values
        call_count = [0]
        def time_side_effect():
            result = call_count[0] * 0.1  # Start at 0.0, then 0.1, 0.2, etc.
            call_count[0] += 1
            return result
        
        mock_time.side_effect = time_side_effect
        
        client = Client(base_url="https://test.com", rate_limit=1.0, max_retries=0)
        
        # First request (no delay expected)
        client.get_article("Article1")
        
        # Second request immediately after (should delay because elapsed < rate_limit)
        # time.time() will be called multiple times, so we need many values
        call_count[0] = 0  # Reset to simulate immediate second call
        
        # Mock time to return same value twice (simulating immediate second call)
        def time_side_effect_immediate():
            # First call returns 0.0, subsequent calls also return 0.0 (immediate)
            return 0.0
        mock_time.side_effect = time_side_effect_immediate
        
        client.get_article("Article2")
        
        # Verify sleep was called for rate limiting
        assert mock_sleep.called
    
    @patch('grokipedia_sdk.client.httpx.Client')
    @patch('grokipedia_sdk.client.time.sleep')
    def test_rate_limiting_disabled_when_zero(self, mock_sleep, mock_client_class):
        """Test that rate limiting is disabled when rate_limit=0"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", rate_limit=0, max_retries=0)
        
        client.get_article("Article1")
        client.get_article("Article2")
        
        # Should not sleep for rate limiting (only for retries if any)
        # Mock sleep to check if it was called for rate limiting
        calls_for_rate_limit = [call for call in mock_sleep.call_args_list 
                                if len(call[0]) > 0 and call[0][0] > 0]
        # With rate_limit=0, no rate limiting sleep should occur
        assert len(calls_for_rate_limit) == 0


class TestClientURLConstruction:
    """Test URL construction and slug encoding"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_url_construction_with_base_url(self, mock_client_class):
        """Test that URLs are constructed correctly"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://example.com/api")
        client.get_article("Test_Article")
        
        call_args = mock_client_instance.get.call_args
        assert call_args[0][0] == "https://example.com/api/page/Test_Article"
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_url_construction_with_special_characters(self, mock_client_class):
        """Test that special characters in slugs are URL encoded"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com")
        
        # Slug with special characters should be URL encoded
        client.get_article("Article Name")  # Space should be encoded
        
        call_args = mock_client_instance.get.call_args
        url = call_args[0][0]
        assert "Article%20Name" in url or "Article+Name" in url


class TestClientUserAgent:
    """Test User-Agent header handling"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_default_user_agent(self, mock_client_class):
        """Test that default User-Agent is set"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com")
        client.get_article("Test")
        
        call_kwargs = mock_client_instance.get.call_args[1]
        headers = call_kwargs.get('headers', {})
        assert 'User-Agent' in headers
        assert 'GrokipediaSDK' in headers['User-Agent']
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_custom_user_agent(self, mock_client_class):
        """Test that custom User-Agent can be set"""
        mock_response = Mock()
        mock_response.text = SAMPLE_ARTICLE_HTML
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        client = Client(base_url="https://test.com", user_agent="CustomAgent/1.0")
        client.get_article("Test")
        
        call_kwargs = mock_client_instance.get.call_args[1]
        headers = call_kwargs.get('headers', {})
        assert headers['User-Agent'] == "CustomAgent/1.0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

