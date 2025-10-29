"""Comprehensive tests for SlugIndex with edge case coverage"""

import pytest
import tempfile
from pathlib import Path
from grokipedia_sdk.slug_index import SlugIndex


class TestNormalizationFunction:
    """Test the _normalize_name() static method"""
    
    def test_normalize_basic(self):
        """Test basic normalization (lowercase + underscore to space)"""
        assert SlugIndex._normalize_name("Joe_Biden") == "joe biden"
        assert SlugIndex._normalize_name("HELLO_WORLD") == "hello world"
    
    def test_normalize_already_normalized(self):
        """Test idempotency of normalization"""
        normalized = SlugIndex._normalize_name("joe biden")
        assert SlugIndex._normalize_name(normalized) == normalized
    
    def test_normalize_mixed_case(self):
        """Test with mixed case"""
        assert SlugIndex._normalize_name("CamelCase_WithUnderscores") == "camelcase withunderscores"
    
    def test_normalize_empty_string(self):
        """Test normalization of empty string"""
        assert SlugIndex._normalize_name("") == ""
    
    def test_normalize_unicode(self):
        """Test normalization with unicode characters"""
        assert SlugIndex._normalize_name("François_Macron") == "françois macron"
        assert SlugIndex._normalize_name("José_María") == "josé maría"
        assert SlugIndex._normalize_name("北京") == "北京"  # Chinese characters


class TestEmptyDirectory:
    """Test SlugIndex behavior with empty directory"""
    
    def test_load_empty_directory(self):
        """Test loading from an empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "links"
            empty_dir.mkdir()
            
            index = SlugIndex(links_dir=empty_dir)
            result = index.load()
            
            assert result == {}
            assert index.get_total_count() == 0
    
    def test_load_no_sitemaps(self):
        """Test loading from directory with no sitemap subdirectories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            # Create some random files but no sitemap-* directories
            (links_dir / "random_file.txt").write_text("content")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert result == {}
    
    def test_load_missing_directory(self):
        """Test loading from non-existent directory"""
        index = SlugIndex(links_dir=Path("/nonexistent/path"))
        result = index.load()
        
        assert result == {}
        assert index.get_total_count() == 0
    
    def test_search_empty_index(self):
        """Test search on empty index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "links"
            empty_dir.mkdir()
            
            index = SlugIndex(links_dir=empty_dir)
            results = index.search("anything")
            
            assert results == []
            assert index.find_best_match("anything") is None


class TestMalformedNames:
    """Test SlugIndex with malformed or edge case names.txt files"""
    
    def test_empty_names_file(self):
        """Test loading from empty names.txt"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert result == {}
    
    def test_whitespace_only_lines(self):
        """Test names.txt with only whitespace lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("   \n\t\n  \n")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert result == {}
    
    def test_duplicate_slugs(self):
        """Test handling of duplicate slugs in the index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Joe_Biden\nJoe_Biden\nJoe_Biden\n")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            # Should only appear once in the count
            assert index.get_total_count() == 1
            assert "joe biden" in result
            assert result["joe biden"] == "Joe_Biden"
    
    def test_invalid_utf8_file(self):
        """Test handling of file with invalid UTF-8 encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            
            # Write binary data that's not valid UTF-8
            names_file = sitemap_dir / "names.txt"
            with open(names_file, 'wb') as f:
                f.write(b'Valid_Slug\n\xFF\xFE\nAnother_Slug\n')
            
            index = SlugIndex(links_dir=links_dir)
            # Should handle gracefully (skip the file or continue)
            result = index.load()
            
            # Either recovers some items or returns empty - both are acceptable
            assert isinstance(result, dict)
    
    def test_lines_with_extra_whitespace(self):
        """Test lines with leading/trailing whitespace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("  Joe_Biden  \n\tArtificial_Intelligence\t\n")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            # Should strip whitespace properly
            assert "joe biden" in result
            assert result["joe biden"] == "Joe_Biden"
            assert "artificial intelligence" in result
            assert result["artificial intelligence"] == "Artificial_Intelligence"


class TestUnicodeSlugHandling:
    """Test SlugIndex with unicode slugs"""
    
    def test_chinese_characters(self):
        """Test with Chinese character slugs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("北京\n上海\n深圳\n", encoding='utf-8')
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert index.get_total_count() == 3
            assert "北京" in result
    
    def test_accented_characters(self):
        """Test with accented Latin characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("François_Macron\nJosé_María_García\nÜber_Äpfel\n", encoding='utf-8')
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert index.get_total_count() == 3
            assert "françois macron" in result
            assert "josé maría garcía" in result
    
    def test_emoji_in_slugs(self):
        """Test with emoji characters in slugs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Climate_🌍\nPython_🐍\n", encoding='utf-8')
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            assert index.get_total_count() == 2
            assert "climate 🌍" in result
    
    def test_mixed_unicode_and_ascii(self):
        """Test with mixed unicode and ASCII slugs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Joe_Biden\nFrançois_Macron\nArtificial_Intelligence\n北京\n", encoding='utf-8')
            
            index = SlugIndex(links_dir=links_dir)
            results = index.search("joe", limit=10)
            
            assert "Joe_Biden" in results
            assert index.get_total_count() == 4


class TestMultipleSitemapDirectories:
    """Test SlugIndex with multiple sitemap directories"""
    
    def test_multiple_sitemaps_consolidation(self):
        """Test that slugs from multiple sitemaps are properly consolidated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            
            # Create multiple sitemap directories
            for i in range(3):
                sitemap_dir = links_dir / f"sitemap-{i}"
                sitemap_dir.mkdir()
                (sitemap_dir / "names.txt").write_text(f"Article_{i}\nShared_Article\n")
            
            index = SlugIndex(links_dir=links_dir)
            result = index.load()
            
            # Should have Article_0, Article_1, Article_2, and Shared_Article
            assert index.get_total_count() == 4
            
            # Search should work across all sitemaps
            shared_results = index.search("shared")
            assert "Shared_Article" in shared_results


class TestCaching:
    """Test that the index is properly cached"""
    
    def test_index_caching(self):
        """Test that load() returns cached index on second call"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Article_1\nArticle_2\n")
            
            index = SlugIndex(links_dir=links_dir)
            
            # First load
            result1 = index.load()
            
            # Modify the file
            (sitemap_dir / "names.txt").write_text("Article_3\n")
            
            # Second load should return cached version
            result2 = index.load()
            
            assert result1 is result2  # Same object
            assert len(result2) == 4  # Original items, not new ones


class TestAsyncLoad:
    """Test the async load_async() method"""
    
    @pytest.mark.asyncio
    async def test_load_async_basic(self):
        """Test basic async loading"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Article_1\nArticle_2\nArticle_3\n")
            
            index = SlugIndex(links_dir=links_dir)
            result = await index.load_async()
            
            assert len(result) >= 3  # At least 3 articles
            assert index.get_total_count() == 3
    
    @pytest.mark.asyncio
    async def test_load_async_empty_directory(self):
        """Test async loading with empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "links"
            empty_dir.mkdir()
            
            index = SlugIndex(links_dir=empty_dir)
            result = await index.load_async()
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_load_async_caching(self):
        """Test that async load also uses caching"""
        with tempfile.TemporaryDirectory() as tmpdir:
            links_dir = Path(tmpdir) / "links"
            links_dir.mkdir()
            sitemap_dir = links_dir / "sitemap-0"
            sitemap_dir.mkdir()
            (sitemap_dir / "names.txt").write_text("Article_1\nArticle_2\n")
            
            index = SlugIndex(links_dir=links_dir)
            
            # First async load
            result1 = await index.load_async()
            
            # Second async load should return same cached object
            result2 = await index.load_async()
            
            assert result1 is result2

