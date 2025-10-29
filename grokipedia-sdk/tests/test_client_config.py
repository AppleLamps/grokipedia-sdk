"""Tests for Client configuration, initialization, and context manager"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from grokipedia_sdk import Client, SlugIndex
from grokipedia_sdk.models import Article


SAMPLE_ARTICLE_HTML = """
<html>
<head>
    <meta property="og:description" content="Test article.">
</head>
<body>
    <h1>Test Article</h1>
    <p>Test content.</p>
</body>
</html>
"""


class TestClientInitialization:
    """Test Client initialization with various parameters"""
    
    def test_default_initialization(self):
        """Test Client with default parameters"""
        client = Client()
        
        assert client.base_url == "https://grokipedia.com"
        assert client.timeout == 30.0
        assert client.max_cache_size == 1000
        assert client._rate_limit == 1.0
        assert client.max_retries == 3
        assert client._verify is True
        assert client._cert is None
        assert "GrokipediaSDK" in client.user_agent
        assert isinstance(client._slug_index, SlugIndex)
    
    def test_custom_base_url(self):
        """Test Client with custom base_url"""
        client = Client(base_url="https://custom.example.com")
        
        assert client.base_url == "https://custom.example.com"
    
    def test_base_url_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base_url"""
        client = Client(base_url="https://example.com/")
        
        assert client.base_url == "https://example.com"
    
    def test_custom_timeout(self):
        """Test Client with custom timeout"""
        client = Client(timeout=60.0)
        
        assert client.timeout == 60.0
    
    def test_custom_max_cache_size(self):
        """Test Client with custom cache size"""
        client = Client(max_cache_size=500)
        
        assert client.max_cache_size == 500
    
    def test_custom_rate_limit(self):
        """Test Client with custom rate limit"""
        client = Client(rate_limit=0.5)
        
        assert client._rate_limit == 0.5
    
    def test_rate_limit_zero_disables_rate_limiting(self):
        """Test that rate_limit=0 disables rate limiting"""
        client = Client(rate_limit=0)
        
        assert client._rate_limit == 0
    
    def test_custom_max_retries(self):
        """Test Client with custom max retries"""
        client = Client(max_retries=5)
        
        assert client.max_retries == 5
    
    def test_max_retries_zero_disables_retries(self):
        """Test that max_retries=0 disables retries"""
        client = Client(max_retries=0)
        
        assert client.max_retries == 0
    
    def test_custom_verify(self):
        """Test Client with custom SSL verification"""
        client = Client(verify=False)
        
        assert client._verify is False
    
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_custom_cert(self, mock_client_class, mock_async_client_class):
        """Test Client with custom certificate"""
        mock_client_class.return_value = Mock()
        mock_async_client_class.return_value = Mock()
        
        client = Client(cert="/path/to/cert.pem")
        
        assert client._cert == "/path/to/cert.pem"
        # Verify httpx.Client was called with cert parameter
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs['cert'] == "/path/to/cert.pem"
    
    def test_custom_cert_tuple(self):
        """Test Client with certificate tuple"""
        with patch('grokipedia_sdk.client.httpx.Client') as mock_client_class, \
             patch('grokipedia_sdk.client.httpx.AsyncClient') as mock_async_client_class:
            mock_client_class.return_value = Mock()
            mock_async_client_class.return_value = Mock()
            
            client = Client(cert=("/path/to/cert.pem", "/path/to/key.pem"))
            
            assert client._cert == ("/path/to/cert.pem", "/path/to/key.pem")
            # Verify httpx.Client was called with cert parameter
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs['cert'] == ("/path/to/cert.pem", "/path/to/key.pem")
    
    def test_custom_user_agent(self):
        """Test Client with custom User-Agent"""
        client = Client(user_agent="CustomAgent/1.0")
        
        assert client.user_agent == "CustomAgent/1.0"
    
    def test_custom_slug_index(self):
        """Test Client with custom SlugIndex"""
        custom_index = SlugIndex()
        client = Client(slug_index=custom_index)
        
        assert client._slug_index is custom_index
    
    def test_default_slug_index_created(self):
        """Test that default SlugIndex is created when not provided"""
        client = Client()
        
        assert client._slug_index is not None
        assert isinstance(client._slug_index, SlugIndex)
    
    @patch.dict(os.environ, {'GROKIPEDIA_BASE_URL': 'https://env.example.com'})
    def test_base_url_from_environment_variable(self):
        """Test that base_url is read from environment variable"""
        client = Client()
        
        assert client.base_url == "https://env.example.com"
    
    @patch.dict(os.environ, {'GROKIPEDIA_BASE_URL': 'https://env.example.com/'})
    def test_base_url_from_env_strips_trailing_slash(self):
        """Test that env var base_url has trailing slash stripped"""
        client = Client()
        
        assert client.base_url == "https://env.example.com"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_base_url_defaults_when_env_not_set(self):
        """Test that base_url defaults when env var not set"""
        client = Client()
        
        assert client.base_url == "https://grokipedia.com"
    
    def test_base_url_explicit_overrides_env(self):
        """Test that explicit base_url overrides environment variable"""
        with patch.dict(os.environ, {'GROKIPEDIA_BASE_URL': 'https://env.example.com'}):
            client = Client(base_url="https://explicit.example.com")
        
        assert client.base_url == "https://explicit.example.com"
    
    @patch('grokipedia_sdk.client.httpx.AsyncClient')
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_httpx_client_initialized_with_params(self, mock_client_class, mock_async_client_class):
        """Test that httpx.Client is initialized with correct parameters"""
        mock_client_class.return_value = Mock()
        mock_async_client_class.return_value = Mock()
        
        client = Client(
            base_url="https://test.com",
            timeout=60.0,
            verify=False,
            cert="/path/to/cert.pem"
        )
        
        # Verify httpx.Client was called with correct parameters
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args[1]
        
        assert call_kwargs['timeout'] == 60.0
        assert call_kwargs['verify'] is False
        assert call_kwargs['cert'] == "/path/to/cert.pem"
        assert call_kwargs['follow_redirects'] is True


class TestClientContextManager:
    """Test Client context manager functionality"""
    
    def test_context_manager_enter(self):
        """Test that Client can be used as context manager"""
        with Client() as client:
            assert client is not None
            assert hasattr(client, '_client')
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_context_manager_exit_closes_client(self, mock_client_class):
        """Test that exiting context manager closes HTTP client"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        with Client() as client:
            assert client._client is not None
        
        # Verify close was called
        mock_client_instance.close.assert_called_once()
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_context_manager_exit_on_exception(self, mock_client_class):
        """Test that client is closed even when exception occurs"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        try:
            with Client() as client:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify close was called even though exception occurred
        mock_client_instance.close.assert_called_once()
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_multiple_context_managers(self, mock_client_class):
        """Test using multiple context managers"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        with Client() as client1:
            with Client() as client2:
                assert client1 is not client2
        
        # Both should be closed
        assert mock_client_instance.close.call_count == 2


class TestClientCleanup:
    """Test Client cleanup and resource management"""
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_close_closes_http_client(self, mock_client_class):
        """Test that close() closes HTTP client"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        client = Client()
        assert client._client is not None
        
        client.close()
        
        mock_client_instance.close.assert_called_once()
        assert client._client is None
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_close_idempotent(self, mock_client_class):
        """Test that close() can be called multiple times safely"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        client = Client()
        
        client.close()
        client.close()
        client.close()
        
        # Should only close once
        assert mock_client_instance.close.call_count == 1
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_close_after_context_manager(self, mock_client_class):
        """Test that close() works after context manager"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        with Client() as client:
            pass
        
        # Already closed by context manager
        assert mock_client_instance.close.call_count == 1
        
        # Calling close again should be safe
        client.close()
        assert mock_client_instance.close.call_count == 1
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_destructor_closes_client(self, mock_client_class):
        """Test that __del__ closes client if not already closed"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        client = Client()
        client._client = mock_client_instance
        
        # Delete client object
        del client
        
        # Verify close was called
        mock_client_instance.close.assert_called_once()
    
    @patch('grokipedia_sdk.client.httpx.Client')
    def test_destructor_handles_already_closed(self, mock_client_class):
        """Test that __del__ handles already-closed client gracefully"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        client = Client()
        client.close()  # Explicitly close
        
        # Delete client object
        del client
        
        # Should not raise exception


class TestClientConfigurationDefaults:
    """Test default configuration values"""
    
    def test_default_timeout_value(self):
        """Test default timeout is 30.0 seconds"""
        client = Client()
        assert client.timeout == 30.0
    
    def test_default_max_cache_size(self):
        """Test default max_cache_size is 1000"""
        client = Client()
        assert client.max_cache_size == 1000
    
    def test_default_rate_limit(self):
        """Test default rate_limit is 1.0 seconds"""
        client = Client()
        assert client._rate_limit == 1.0
    
    def test_default_max_retries(self):
        """Test default max_retries is 3"""
        client = Client()
        assert client.max_retries == 3
    
    def test_default_verify(self):
        """Test default verify is True"""
        client = Client()
        assert client._verify is True
    
    def test_default_cert_is_none(self):
        """Test default cert is None"""
        client = Client()
        assert client._cert is None
    
    def test_default_user_agent_contains_sdk_name(self):
        """Test default User-Agent contains SDK name"""
        client = Client()
        assert "GrokipediaSDK" in client.user_agent
        assert "Python SDK" in client.user_agent


class TestClientWithMockSlugIndex:
    """Test Client initialization with mocked SlugIndex"""
    
    def test_client_with_mock_slug_index(self):
        """Test Client works with mocked SlugIndex"""
        from unittest.mock import Mock
        mock_index = Mock(spec=SlugIndex)
        
        client = Client(slug_index=mock_index)
        
        assert client._slug_index is mock_index
    
    def test_client_slug_methods_use_mock_index(self):
        """Test that slug methods use the provided mock index"""
        from unittest.mock import Mock
        mock_index = Mock(spec=SlugIndex)
        mock_index.search.return_value = ['Article1', 'Article2']
        mock_index.find_best_match.return_value = 'Article1'
        mock_index.exists.return_value = True
        mock_index.list_by_prefix.return_value = ['Article1']
        mock_index.get_total_count.return_value = 100
        mock_index.random_slugs.return_value = ['Random1']
        
        client = Client(slug_index=mock_index)
        
        assert client.search_slug("test") == ['Article1', 'Article2']
        assert client.find_slug("test") == 'Article1'
        assert client.slug_exists("Article1") is True
        assert client.list_available_articles() == ['Article1']
        assert client.get_total_article_count() == 100
        assert client.get_random_articles() == ['Random1']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

