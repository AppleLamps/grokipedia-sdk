"""Tests for exception hierarchy"""

import pytest
from grokipedia_sdk.exceptions import (
    GrokipediaError,
    ArticleNotFound,
    RequestError
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy"""
    
    def test_grokipedia_error_is_base_exception(self):
        """Test that GrokipediaError is base exception"""
        assert issubclass(GrokipediaError, Exception)
    
    def test_article_not_found_inherits_from_grokipedia_error(self):
        """Test that ArticleNotFound inherits from GrokipediaError"""
        assert issubclass(ArticleNotFound, GrokipediaError)
        assert issubclass(ArticleNotFound, Exception)
    
    def test_request_error_inherits_from_grokipedia_error(self):
        """Test that RequestError inherits from GrokipediaError"""
        assert issubclass(RequestError, GrokipediaError)
        assert issubclass(RequestError, Exception)
    
    def test_exceptions_are_not_siblings(self):
        """Test that ArticleNotFound and RequestError are not related"""
        assert not issubclass(ArticleNotFound, RequestError)
        assert not issubclass(RequestError, ArticleNotFound)


class TestGrokipediaError:
    """Test GrokipediaError base exception"""
    
    def test_grokipedia_error_can_be_raised(self):
        """Test that GrokipediaError can be raised"""
        with pytest.raises(GrokipediaError):
            raise GrokipediaError("Test error")
    
    def test_grokipedia_error_with_message(self):
        """Test GrokipediaError with custom message"""
        error = GrokipediaError("Custom error message")
        
        assert str(error) == "Custom error message"
    
    def test_grokipedia_error_can_be_caught_by_exception(self):
        """Test that GrokipediaError can be caught by Exception"""
        try:
            raise GrokipediaError("Test")
        except Exception as e:
            assert isinstance(e, GrokipediaError)


class TestArticleNotFound:
    """Test ArticleNotFound exception"""
    
    def test_article_not_found_can_be_raised(self):
        """Test that ArticleNotFound can be raised"""
        with pytest.raises(ArticleNotFound):
            raise ArticleNotFound("Article not found")
    
    def test_article_not_found_with_message(self):
        """Test ArticleNotFound with custom message"""
        error = ArticleNotFound("Article 'Test' not found")
        
        assert str(error) == "Article 'Test' not found"
    
    def test_article_not_found_can_be_caught_by_grokipedia_error(self):
        """Test that ArticleNotFound can be caught by GrokipediaError"""
        try:
            raise ArticleNotFound("Not found")
        except GrokipediaError as e:
            assert isinstance(e, ArticleNotFound)
    
    def test_article_not_found_can_be_caught_by_exception(self):
        """Test that ArticleNotFound can be caught by Exception"""
        try:
            raise ArticleNotFound("Not found")
        except Exception as e:
            assert isinstance(e, ArticleNotFound)
    
    def test_article_not_found_not_caught_by_request_error(self):
        """Test that ArticleNotFound is NOT caught by RequestError"""
        try:
            raise ArticleNotFound("Not found")
        except RequestError:
            pytest.fail("ArticleNotFound should not be caught by RequestError")
        except ArticleNotFound:
            pass  # Expected


class TestRequestError:
    """Test RequestError exception"""
    
    def test_request_error_can_be_raised(self):
        """Test that RequestError can be raised"""
        with pytest.raises(RequestError):
            raise RequestError("Request failed")
    
    def test_request_error_with_message(self):
        """Test RequestError with custom message"""
        error = RequestError("Network error occurred")
        
        assert str(error) == "Network error occurred"
    
    def test_request_error_can_be_caught_by_grokipedia_error(self):
        """Test that RequestError can be caught by GrokipediaError"""
        try:
            raise RequestError("Request failed")
        except GrokipediaError as e:
            assert isinstance(e, RequestError)
    
    def test_request_error_can_be_caught_by_exception(self):
        """Test that RequestError can be caught by Exception"""
        try:
            raise RequestError("Request failed")
        except Exception as e:
            assert isinstance(e, RequestError)
    
    def test_request_error_not_caught_by_article_not_found(self):
        """Test that RequestError is NOT caught by ArticleNotFound"""
        try:
            raise RequestError("Request failed")
        except ArticleNotFound:
            pytest.fail("RequestError should not be caught by ArticleNotFound")
        except RequestError:
            pass  # Expected


class TestExceptionUsage:
    """Test exception usage patterns"""
    
    def test_catching_base_exception_catches_all(self):
        """Test that catching GrokipediaError catches all SDK exceptions"""
        exceptions = [
            GrokipediaError("Base error"),
            ArticleNotFound("Article not found"),
            RequestError("Request failed"),
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except GrokipediaError:
                pass  # Should catch all
            except Exception:
                pytest.fail(f"GrokipediaError should catch {type(exc)}")
    
    def test_catching_exception_catches_all(self):
        """Test that catching Exception catches all SDK exceptions"""
        exceptions = [
            GrokipediaError("Base error"),
            ArticleNotFound("Article not found"),
            RequestError("Request failed"),
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except Exception:
                pass  # Should catch all
    
    def test_specific_exception_catching(self):
        """Test catching specific exceptions"""
        # Test catching ArticleNotFound specifically
        try:
            raise ArticleNotFound("Not found")
        except ArticleNotFound:
            pass  # Should catch
        except RequestError:
            pytest.fail("Should not catch ArticleNotFound")
        except GrokipediaError:
            pytest.fail("Should catch ArticleNotFound specifically first")
    
    def test_exception_chaining(self):
        """Test exception chaining"""
        try:
            try:
                raise RequestError("Inner error")
            except RequestError as e:
                raise ArticleNotFound("Outer error") from e
        except ArticleNotFound as e:
            assert isinstance(e.__cause__, RequestError)
            assert "Inner error" in str(e.__cause__)


class TestExceptionMessages:
    """Test exception message formatting"""
    
    def test_exception_with_detailed_message(self):
        """Test exception with detailed error message"""
        error = ArticleNotFound(
            "Article 'Joe_Biden' not found at https://example.com/page/Joe_Biden. Status: 404"
        )
        
        assert "Joe_Biden" in str(error)
        assert "404" in str(error)
    
    def test_exception_message_formatting(self):
        """Test that exceptions can have formatted messages"""
        slug = "Test_Article"
        url = "https://example.com/page/Test_Article"
        error = ArticleNotFound(f"Article '{slug}' not found at {url}. Status: 404")
        
        assert slug in str(error)
        assert url in str(error)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

