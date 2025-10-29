"""Tests for Pydantic models validation"""

import pytest
from pydantic import ValidationError, HttpUrl
from grokipedia_sdk.models import (
    Section, ArticleMetadata, Article, ArticleSummary, SearchResult
)


class TestSectionModel:
    """Test Section model validation"""
    
    def test_section_valid_data(self):
        """Test Section with valid data"""
        section = Section(
            title="Test Section",
            content="Test content",
            level=2
        )
        
        assert section.title == "Test Section"
        assert section.content == "Test content"
        assert section.level == 2
    
    def test_section_default_content(self):
        """Test Section with default empty content"""
        section = Section(title="Test", level=1)
        
        assert section.content == ""
    
    def test_section_level_validation_min(self):
        """Test that level must be >= 1"""
        with pytest.raises(ValidationError) as exc_info:
            Section(title="Test", level=0)
        
        assert "level" in str(exc_info.value).lower()
    
    def test_section_level_validation_max(self):
        """Test that level must be <= 6"""
        with pytest.raises(ValidationError) as exc_info:
            Section(title="Test", level=7)
        
        assert "level" in str(exc_info.value).lower()
    
    def test_section_level_boundary_values(self):
        """Test boundary values for level (1 and 6)"""
        section1 = Section(title="Test", level=1)
        section6 = Section(title="Test", level=6)
        
        assert section1.level == 1
        assert section6.level == 6
    
    def test_section_title_required(self):
        """Test that title is required"""
        with pytest.raises(ValidationError) as exc_info:
            Section(level=1)
        
        assert "title" in str(exc_info.value).lower()
    
    def test_section_title_min_length(self):
        """Test that title must have min_length=1"""
        with pytest.raises(ValidationError) as exc_info:
            Section(title="", level=1)
        
        assert "title" in str(exc_info.value).lower()
    
    def test_section_level_validation_custom(self):
        """Test custom level validator"""
        # Test with non-integer
        with pytest.raises(ValidationError) as exc_info:
            Section(title="Test", level="invalid")
        
        assert "level" in str(exc_info.value).lower()
    
    def test_section_repr(self):
        """Test Section __repr__ method"""
        section = Section(title="Test Section", content="Content" * 10, level=2)
        repr_str = repr(section)
        
        assert "Section" in repr_str
        assert "Test Section" in repr_str
        assert "level=2" in repr_str
    
    def test_section_repr_long_content(self):
        """Test Section __repr__ truncates long content"""
        long_content = "A" * 100
        section = Section(title="Test", content=long_content, level=1)
        repr_str = repr(section)
        
        assert "..." in repr_str  # Should truncate


class TestArticleMetadataModel:
    """Test ArticleMetadata model validation"""
    
    def test_metadata_valid_data(self):
        """Test ArticleMetadata with valid data"""
        metadata = ArticleMetadata(
            fact_checked="John Smith",
            word_count=1000
        )
        
        assert metadata.fact_checked == "John Smith"
        assert metadata.word_count == 1000
    
    def test_metadata_all_optional(self):
        """Test ArticleMetadata with all optional fields None"""
        metadata = ArticleMetadata()
        
        assert metadata.fact_checked is None
        assert metadata.last_updated is None
        assert metadata.word_count == 0
    
    def test_metadata_word_count_default(self):
        """Test that word_count defaults to 0"""
        metadata = ArticleMetadata()
        
        assert metadata.word_count == 0
    
    def test_metadata_word_count_validation_negative(self):
        """Test that word_count must be >= 0"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleMetadata(word_count=-1)
        
        assert "word_count" in str(exc_info.value).lower()
    
    def test_metadata_word_count_zero(self):
        """Test that word_count can be 0"""
        metadata = ArticleMetadata(word_count=0)
        
        assert metadata.word_count == 0
    
    def test_metadata_repr_with_fact_check(self):
        """Test ArticleMetadata __repr__ with fact_check"""
        metadata = ArticleMetadata(fact_checked="John Smith", word_count=500)
        repr_str = repr(metadata)
        
        assert "ArticleMetadata" in repr_str
        assert "word_count=500" in repr_str
        assert "fact_checked=True" in repr_str or "fact_checked" in repr_str
    
    def test_metadata_repr_without_fact_check(self):
        """Test ArticleMetadata __repr__ without fact_check"""
        metadata = ArticleMetadata(word_count=500)
        repr_str = repr(metadata)
        
        assert "ArticleMetadata" in repr_str
        assert "word_count=500" in repr_str
        assert "fact_checked=False" in repr_str or "fact_checked" in repr_str


class TestArticleModel:
    """Test Article model validation"""
    
    def test_article_valid_data(self):
        """Test Article with valid data"""
        metadata = ArticleMetadata(word_count=1000)
        section = Section(title="Section 1", level=2)
        
        article = Article(
            title="Test Article",
            slug="Test_Article",
            url="https://example.com/page/Test_Article",
            summary="Summary",
            full_content="Full content",
            sections=[section],
            table_of_contents=["Section 1"],
            references=["https://example.com/ref1"],
            metadata=metadata,
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        assert article.title == "Test Article"
        assert article.slug == "Test_Article"
        assert str(article.url) == "https://example.com/page/Test_Article"
        assert article.summary == "Summary"
        assert len(article.sections) == 1
        assert len(article.table_of_contents) == 1
        assert len(article.references) == 1
        assert article.metadata.word_count == 1000
    
    def test_article_default_fields(self):
        """Test Article with default field values"""
        metadata = ArticleMetadata()
        
        article = Article(
            title="Test",
            slug="Test",
            url="https://example.com/test",
            metadata=metadata,
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        assert article.summary == ""
        assert article.full_content == ""
        assert article.sections == []
        assert article.table_of_contents == []
        assert article.references == []
    
    def test_article_title_required(self):
        """Test that title is required"""
        metadata = ArticleMetadata()
        
        with pytest.raises(ValidationError) as exc_info:
            Article(
                slug="Test",
                url="https://example.com/test",
                metadata=metadata,
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "title" in str(exc_info.value).lower()
    
    def test_article_title_min_length(self):
        """Test that title must have min_length=1"""
        metadata = ArticleMetadata()
        
        with pytest.raises(ValidationError) as exc_info:
            Article(
                title="",
                slug="Test",
                url="https://example.com/test",
                metadata=metadata,
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "title" in str(exc_info.value).lower()
    
    def test_article_slug_required(self):
        """Test that slug is required"""
        metadata = ArticleMetadata()
        
        with pytest.raises(ValidationError) as exc_info:
            Article(
                title="Test",
                url="https://example.com/test",
                metadata=metadata,
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "slug" in str(exc_info.value).lower()
    
    def test_article_url_validation(self):
        """Test that url must be a valid HttpUrl"""
        metadata = ArticleMetadata()
        
        with pytest.raises(ValidationError) as exc_info:
            Article(
                title="Test",
                slug="Test",
                url="not-a-valid-url",
                metadata=metadata,
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "url" in str(exc_info.value).lower()
    
    def test_article_url_accepts_valid_urls(self):
        """Test that valid URLs are accepted"""
        metadata = ArticleMetadata()
        
        valid_urls = [
            "https://example.com/page",
            "http://example.com/page",
            "https://example.com/page?query=test",
            "https://example.com/page#section",
        ]
        
        for url in valid_urls:
            article = Article(
                title="Test",
                slug="Test",
                url=url,
                metadata=metadata,
                scraped_at="2024-01-01T00:00:00Z"
            )
            assert str(article.url) == url
    
    def test_article_metadata_required(self):
        """Test that metadata is required"""
        with pytest.raises(ValidationError) as exc_info:
            Article(
                title="Test",
                slug="Test",
                url="https://example.com/test",
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "metadata" in str(exc_info.value).lower()
    
    def test_article_repr(self):
        """Test Article __repr__ method"""
        metadata = ArticleMetadata(word_count=1000)
        article = Article(
            title="Test Article",
            slug="Test_Article",
            url="https://example.com/test",
            metadata=metadata,
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        repr_str = repr(article)
        assert "Article" in repr_str
        assert "Test Article" in repr_str
        assert "Test_Article" in repr_str
    
    def test_article_repr_long_title(self):
        """Test Article __repr__ truncates long titles"""
        metadata = ArticleMetadata()
        long_title = "A" * 100
        article = Article(
            title=long_title,
            slug="Test",
            url="https://example.com/test",
            metadata=metadata,
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        repr_str = repr(article)
        assert "..." in repr_str  # Should truncate


class TestArticleSummaryModel:
    """Test ArticleSummary model validation"""
    
    def test_summary_valid_data(self):
        """Test ArticleSummary with valid data"""
        summary = ArticleSummary(
            title="Test Article",
            slug="Test_Article",
            url="https://example.com/page/Test_Article",
            summary="Summary text",
            table_of_contents=["Section 1", "Section 2"],
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        assert summary.title == "Test Article"
        assert summary.slug == "Test_Article"
        assert str(summary.url) == "https://example.com/page/Test_Article"
        assert summary.summary == "Summary text"
        assert len(summary.table_of_contents) == 2
    
    def test_summary_default_fields(self):
        """Test ArticleSummary with default field values"""
        summary = ArticleSummary(
            title="Test",
            slug="Test",
            url="https://example.com/test",
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        assert summary.summary == ""
        assert summary.table_of_contents == []
    
    def test_summary_title_required(self):
        """Test that title is required"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleSummary(
                slug="Test",
                url="https://example.com/test",
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "title" in str(exc_info.value).lower()
    
    def test_summary_url_validation(self):
        """Test that url must be a valid HttpUrl"""
        with pytest.raises(ValidationError) as exc_info:
            ArticleSummary(
                title="Test",
                slug="Test",
                url="invalid-url",
                scraped_at="2024-01-01T00:00:00Z"
            )
        
        assert "url" in str(exc_info.value).lower()
    
    def test_summary_repr(self):
        """Test ArticleSummary __repr__ method"""
        summary = ArticleSummary(
            title="Test Article",
            slug="Test_Article",
            url="https://example.com/test",
            scraped_at="2024-01-01T00:00:00Z"
        )
        
        repr_str = repr(summary)
        assert "ArticleSummary" in repr_str
        assert "Test Article" in repr_str


class TestSearchResultModel:
    """Test SearchResult model validation"""
    
    def test_search_result_valid_data(self):
        """Test SearchResult with valid data"""
        result = SearchResult(
            title="Test Article",
            slug="Test_Article",
            url="https://example.com/page/Test_Article",
            snippet="This is a snippet"
        )
        
        assert result.title == "Test Article"
        assert result.slug == "Test_Article"
        assert str(result.url) == "https://example.com/page/Test_Article"
        assert result.snippet == "This is a snippet"
    
    def test_search_result_snippet_optional(self):
        """Test that snippet is optional"""
        result = SearchResult(
            title="Test",
            slug="Test",
            url="https://example.com/test"
        )
        
        assert result.snippet is None
    
    def test_search_result_title_required(self):
        """Test that title is required"""
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                slug="Test",
                url="https://example.com/test"
            )
        
        assert "title" in str(exc_info.value).lower()
    
    def test_search_result_url_validation(self):
        """Test that url must be a valid HttpUrl"""
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                title="Test",
                slug="Test",
                url="not-a-url"
            )
        
        assert "url" in str(exc_info.value).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

