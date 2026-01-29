"""Testing website for Grokipedia SDK"""

import sys
from pathlib import Path

# Add parent directory to path to import the SDK
sdk_path = Path(__file__).parent.parent
sys.path.insert(0, str(sdk_path))

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional, List
import json

from grokipedia_sdk import Client, SlugIndex, ArticleNotFound, RequestError

app = FastAPI(title="Grokipedia SDK Testing", version="1.0.0")

# Initialize SDK client (lazy loaded)
_client: Optional[Client] = None
_slug_index: Optional[SlugIndex] = None


def get_client() -> Client:
    """Get or create SDK client"""
    global _client
    if _client is None:
        _client = Client(rate_limit=0.1)  # Lower rate limit for testing
    return _client


def get_slug_index() -> SlugIndex:
    """Get or create slug index"""
    global _slug_index
    if _slug_index is None:
        _slug_index = SlugIndex()
        _slug_index.load()
    return _slug_index


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the testing frontend"""
    html_path = Path(__file__).parent / "index.html"
    return FileResponse(html_path)


@app.get("/api/search")
async def search_articles(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    fuzzy: bool = Query(True, description="Enable fuzzy matching"),
):
    """
    Search for articles matching the query.
    Returns list of matching slugs with their display names.
    """
    try:
        index = get_slug_index()
        slugs = index.search(q, limit=limit, fuzzy=fuzzy)
        
        # Convert slugs to display format
        results = []
        for slug in slugs:
            display_name = slug.replace("_", " ")
            results.append({
                "slug": slug,
                "title": display_name,
                "url": f"https://grokipedia.com/page/{slug}"
            })
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/article/{slug}")
async def get_article(slug: str):
    """
    Fetch a complete article by slug.
    """
    try:
        client = get_client()
        article = client.get_article(slug)
        
        return {
            "title": article.title,
            "slug": article.slug,
            "url": str(article.url),
            "summary": article.summary,
            "sections": [
                {"title": s.title, "level": s.level, "content": s.content[:500] + "..." if len(s.content) > 500 else s.content}
                for s in article.sections[:10]  # Limit sections for response size
            ],
            "table_of_contents": article.table_of_contents[:20],
            "word_count": article.metadata.word_count,
            "scraped_at": article.scraped_at
        }
    except ArticleNotFound as e:
        raise HTTPException(status_code=404, detail=f"Article not found: {slug}")
    except RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch article: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary/{slug}")
async def get_summary(slug: str):
    """
    Fetch article summary by slug (faster, less data).
    """
    try:
        client = get_client()
        summary = client.get_summary(slug)
        
        return {
            "title": summary.title,
            "slug": summary.slug,
            "url": str(summary.url),
            "summary": summary.summary,
            "table_of_contents": summary.table_of_contents,
            "scraped_at": summary.scraped_at
        }
    except ArticleNotFound as e:
        raise HTTPException(status_code=404, detail=f"Article not found: {slug}")
    except RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch article: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """
    Get index statistics.
    """
    try:
        index = get_slug_index()
        return {
            "total_articles": index.get_total_count(),
            "load_errors": len(index.get_load_errors())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/random")
async def get_random_articles(count: int = Query(5, ge=1, le=20)):
    """
    Get random article slugs.
    """
    try:
        index = get_slug_index()
        slugs = index.random_slugs(count)
        
        results = []
        for slug in slugs:
            display_name = slug.replace("_", " ")
            results.append({
                "slug": slug,
                "title": display_name,
                "url": f"https://grokipedia.com/page/{slug}"
            })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
