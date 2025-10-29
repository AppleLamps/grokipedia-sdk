"""Grokipedia SDK - A Python SDK for accessing Grokipedia content"""

from .client import Client
from .exceptions import GrokipediaError, ArticleNotFound, RequestError
from .models import Article, ArticleSummary, Section, ArticleMetadata, SearchResult
from .slug_index import SlugIndex
from . import parsers

__version__ = "1.1.0"
__all__ = [
    "Client",
    "GrokipediaError",
    "ArticleNotFound",
    "RequestError",
    "Article",
    "ArticleSummary",
    "Section",
    "ArticleMetadata",
    "SearchResult",
    "SlugIndex",
    "parsers",
]

