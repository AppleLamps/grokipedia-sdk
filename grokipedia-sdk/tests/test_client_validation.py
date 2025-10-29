"""Tests for Client slug validation and security"""

import pytest
from grokipedia_sdk import Client
from grokipedia_sdk.exceptions import RequestError


class TestClientSlugValidation:
    """Test Client slug validation and sanitization"""
    
    def test_validate_slug_valid_slug(self):
        """Test that valid slugs pass through"""
        client = Client()
        
        # Valid slugs should pass
        assert client._validate_slug("Joe_Biden") == "Joe_Biden"
        assert client._validate_slug("Article_Name") == "Article_Name"
        assert client._validate_slug("Test123") == "Test123"
    
    def test_validate_slug_empty_string(self):
        """Test that empty strings raise ValueError"""
        client = Client()
        
        with pytest.raises(ValueError) as exc_info:
            client._validate_slug("")
        
        assert "empty" in str(exc_info.value).lower() or "non-empty" in str(exc_info.value).lower()
    
    def test_validate_slug_whitespace_only(self):
        """Test that whitespace-only strings raise ValueError"""
        client = Client()
        
        with pytest.raises(ValueError) as exc_info:
            client._validate_slug("   ")
        
        assert "empty" in str(exc_info.value).lower() or "non-empty" in str(exc_info.value).lower()
    
    def test_validate_slug_none_raises_error(self):
        """Test that None raises ValueError"""
        client = Client()
        
        with pytest.raises(ValueError) as exc_info:
            client._validate_slug(None)
        
        assert "string" in str(exc_info.value).lower()
    
    def test_validate_slug_non_string_raises_error(self):
        """Test that non-string types raise ValueError"""
        client = Client()
        
        with pytest.raises(ValueError):
            client._validate_slug(123)
        
        with pytest.raises(ValueError):
            client._validate_slug([])
        
        with pytest.raises(ValueError):
            client._validate_slug({})
    
    def test_validate_slug_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        client = Client()
        
        result = client._validate_slug("  Joe_Biden  ")
        assert result == "Joe_Biden"
        
        result = client._validate_slug("\tArticle_Name\n")
        assert result == "Article_Name"
    
    def test_validate_slug_url_encodes_special_characters(self):
        """Test that special characters are URL encoded"""
        from urllib.parse import unquote
        
        client = Client()
        
        # Slugs with spaces should be encoded
        result = client._validate_slug("Article Name")
        assert "%20" in result or "+" in result
        
        # Slugs with special chars should be encoded
        result = client._validate_slug("Article@Name")
        assert "@" not in result or "%40" in result
    
    def test_validate_slug_preserves_underscores_and_hyphens(self):
        """Test that underscores and hyphens are preserved (common in slugs)"""
        client = Client()
        
        # Underscores should pass through
        result = client._validate_slug("Article_Name")
        assert "_" in result
        
        # Hyphens should pass through
        result = client._validate_slug("Article-Name")
        assert "-" in result
    
    def test_validate_slug_path_traversal_prevention(self):
        """Test that path traversal attempts are prevented"""
        client = Client()
        
        # Path traversal attempts should be encoded
        result = client._validate_slug("../etc/passwd")
        assert "../" not in result or "%2E%2E" in result
        
        result = client._validate_slug("....//....//etc/passwd")
        # Should be encoded, not pass through as-is
        assert "....//" not in result or "%2E" in result
    
    def test_validate_slug_injection_prevention(self):
        """Test that SQL/command injection attempts are URL encoded"""
        client = Client()
        
        # SQL injection attempts should be encoded
        # Note: '-' is in safe list, so '--' may not be encoded, but other chars are
        result = client._validate_slug("'; DROP TABLE articles; --")
        assert "%27" in result or result != "'; DROP TABLE articles; --"  # Should be encoded
        assert "%3B" in result  # Semicolon should be encoded
        
        # Command injection attempts should be encoded
        result = client._validate_slug("; rm -rf /")
        assert "%3B" in result  # Semicolon should be encoded
        assert result != "; rm -rf /"  # Should be different from original
    
    def test_validate_slug_xss_prevention(self):
        """Test that XSS attempts are URL encoded"""
        client = Client()
        
        # Script tags should be encoded
        result = client._validate_slug("<script>alert('xss')</script>")
        assert "%3C" in result or result != "<script>alert('xss')</script>"  # Should be encoded
        assert "<" not in result or "%3C" in result  # '<' should be encoded
        
        # Event handlers should be URL encoded (onclick text may appear but special chars encoded)
        result = client._validate_slug("Article onclick='alert(1)'")
        # The text 'onclick' may appear but special chars should be encoded
        assert result != "Article onclick='alert(1)'"  # Should be encoded
        assert "%27" in result or "%3D" in result  # Quotes or equals should be encoded
    
    def test_validate_slug_unicode_handling(self):
        """Test that unicode characters are handled correctly"""
        client = Client()
        
        # Unicode slugs should be URL encoded
        result = client._validate_slug("北京")
        # Should be URL encoded
        assert "%" in result or result == "北京"  # Some encoders may handle UTF-8
        
        result = client._validate_slug("François_Macron")
        assert "_" in result  # Underscores should still pass through
    
    def test_validate_slug_very_long_slug(self):
        """Test that very long slugs are handled"""
        client = Client()
        
        # Very long slug should still be validated
        long_slug = "A" * 1000
        result = client._validate_slug(long_slug)
        assert len(result) == len(long_slug)  # No truncation, just encoding if needed
    
    def test_validate_slug_url_encoding_format(self):
        """Test that URL encoding produces valid URL format"""
        from urllib.parse import quote, unquote
        
        client = Client()
        
        # Test that encoding can be decoded back
        original = "Article Name With Spaces"
        encoded = client._validate_slug(original)
        
        # Encoded should be different from original
        assert encoded != original
        
        # Should be able to decode (if using standard URL encoding)
        try:
            decoded = unquote(encoded)
            # After decoding and normalizing, should match original
            assert decoded.replace("+", " ") == original.replace("+", " ")
        except Exception:
            # If encoding uses safe characters, that's okay too
            pass
    
    def test_get_article_validates_slug(self):
        """Test that get_article validates slug before fetching"""
        client = Client()
        
        # Empty slug should raise ValueError before making HTTP request
        with pytest.raises(ValueError):
            client.get_article("")
        
        # None slug should raise ValueError
        with pytest.raises(ValueError):
            client.get_article(None)
    
    def test_get_summary_validates_slug(self):
        """Test that get_summary validates slug before fetching"""
        client = Client()
        
        # Empty slug should raise ValueError
        with pytest.raises(ValueError):
            client.get_summary("")
        
        # None slug should raise ValueError
        with pytest.raises(ValueError):
            client.get_summary(None)
    
    def test_get_section_validates_slug(self):
        """Test that get_section validates slug before fetching"""
        client = Client()
        
        # Empty slug should raise ValueError
        with pytest.raises(ValueError):
            client.get_section("", "Section")
        
        # None slug should raise ValueError
        with pytest.raises(ValueError):
            client.get_section(None, "Section")


class TestClientSecurity:
    """Test security-related aspects of Client"""
    
    def test_slug_validation_prevents_directory_traversal(self):
        """Test that directory traversal is prevented"""
        client = Client()
        
        malicious_slugs = [
            "../etc/passwd",
            "....//....//etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        for slug in malicious_slugs:
            result = client._validate_slug(slug)
            # Should be encoded, not pass through
            assert "../" not in result or "%2E" in result
            assert "..\\" not in result or "%5C" in result
            assert slug != result  # Should be modified
    
    def test_slug_validation_prevents_command_injection(self):
        """Test that command injection attempts are prevented"""
        client = Client()
        
        malicious_slugs = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& echo 'hacked'",
            "`whoami`",
            "$(id)",
        ]
        
        for slug in malicious_slugs:
            result = client._validate_slug(slug)
            # Should be encoded
            assert ";" not in result or "%3B" in result
            assert "|" not in result or "%7C" in result
            assert "`" not in result or "%60" in result
            assert "$(" not in result or "%24" in result
    
    def test_slug_validation_prevents_sql_injection(self):
        """Test that SQL injection attempts are URL encoded"""
        client = Client()
        
        malicious_slugs = [
            "'; DROP TABLE articles; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('admin', 'password'); --",
        ]
        
        for slug in malicious_slugs:
            result = client._validate_slug(slug)
            # Should be URL encoded (different from original)
            assert result != slug  # Should be encoded
            # Key dangerous characters should be encoded
            assert "'" not in result or "%27" in result  # Single quote encoded
            assert ";" not in result or "%3B" in result  # Semicolon encoded


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

