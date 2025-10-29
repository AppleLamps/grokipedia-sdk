"""Pydantic models for the Grokipedia SDK"""

from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional


class Section(BaseModel):
    """Represents a section in an article"""
    title: str = Field(..., min_length=1, description="Section title")
    content: str = Field(default="", description="Section content")
    level: int = Field(..., ge=1, le=6, description="Heading level (1-6)")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v: int) -> int:
        """Validate heading level is between 1 and 6"""
        if not isinstance(v, int) or not (1 <= v <= 6):
            raise ValueError('Level must be between 1 and 6')
        return v
    
    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Section title='{self.title}' level={self.level} content='{content_preview}'>"


class ArticleMetadata(BaseModel):
    """Metadata about the article"""
    fact_checked: Optional[str] = Field(None, description="Fact-checker information")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    word_count: int = Field(ge=0, default=0, description="Word count in article")
    
    def __repr__(self) -> str:
        fact_checked_str = f"fact_checked={bool(self.fact_checked)}" if self.fact_checked else "fact_checked=False"
        return f"<ArticleMetadata word_count={self.word_count} {fact_checked_str}>"


class Article(BaseModel):
    """Complete article response"""
    title: str = Field(..., min_length=1, description="Article title")
    slug: str = Field(..., min_length=1, description="Article slug")
    url: HttpUrl = Field(..., description="Article URL")
    summary: str = Field(default="", description="First paragraph or intro text")
    full_content: str = Field(default="", description="Complete article text")
    sections: List[Section] = Field(default_factory=list, description="Article sections")
    table_of_contents: List[str] = Field(default_factory=list, description="Table of contents")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    metadata: ArticleMetadata = Field(..., description="Article metadata")
    scraped_at: str = Field(..., description="ISO timestamp when article was scraped")
    
    def __repr__(self) -> str:
        title_preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return f"<Article title='{title_preview}' slug='{self.slug}' sections={len(self.sections)} word_count={self.metadata.word_count}>"


class ArticleSummary(BaseModel):
    """Summary response for an article"""
    title: str = Field(..., min_length=1, description="Article title")
    slug: str = Field(..., min_length=1, description="Article slug")
    url: HttpUrl = Field(..., description="Article URL")
    summary: str = Field(default="", description="Article summary")
    table_of_contents: List[str] = Field(default_factory=list, description="Table of contents")
    scraped_at: str = Field(..., description="ISO timestamp when article was scraped")
    
    def __repr__(self) -> str:
        title_preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return f"<ArticleSummary title='{title_preview}' slug='{self.slug}' toc_sections={len(self.table_of_contents)}>"


class SearchResult(BaseModel):
    """Search result item"""
    title: str = Field(..., min_length=1, description="Article title")
    slug: str = Field(..., min_length=1, description="Article slug")
    url: HttpUrl = Field(..., description="Article URL")
    snippet: Optional[str] = Field(None, description="Text snippet from article")

