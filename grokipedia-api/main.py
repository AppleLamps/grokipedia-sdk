import contextlib
import os
import secrets  # Import secrets for key comparison
from typing import List, Set
from fastapi import FastAPI, HTTPException, Query, Security  # Import Security
from fastapi.security import APIKeyHeader  # Import APIKeyHeader

from grokipedia_sdk import (
    Client,
    Article,
    ArticleSummary,
    Section,
    SearchResult,
    ArticleNotFound,
    RequestError
)

# --- Authentication Setup ---
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

# Load valid API keys from environment variable (comma-separated)
VALID_API_KEYS_STR = os.getenv("GROKIPEDIA_API_KEYS", "")  # Default to empty string
VALID_API_KEYS: Set[str] = set(VALID_API_KEYS_STR.split(",")) if VALID_API_KEYS_STR else set()


async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """Dependency to validate the API key from the X-API-Key header."""
    if not VALID_API_KEYS:
        # If no keys are configured, maybe allow access or raise an internal error
        # For now, let's raise an error indicating it's not configured
        raise HTTPException(status_code=500, detail="API Key authentication is not configured on the server.")

    # Use secrets.compare_digest for secure comparison against timing attacks
    is_valid = any(secrets.compare_digest(api_key_header, valid_key) for valid_key in VALID_API_KEYS)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key_header
# --- End Authentication Setup ---

# Dictionary to hold our SDK client instance
client_state = {}

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, initialize the client
    client_state["client"] = Client()
    yield
    # On shutdown, close the client
    client_state["client"].close()


app = FastAPI(
    title="Grokipedia API",
    description="A REST API wrapper for the Grokipedia SDK. Requires an API key via the 'X-API-Key' header.",
    version="1.0.0",
    lifespan=lifespan
)

def get_client() -> Client:
    """Helper to get the initialized client."""
    return client_state["client"]

@app.get("/", summary="Health Check")
def read_root():
    """Returns a welcome message, indicating the API is operational."""
    return {"message": "Grokipedia API is running"}

@app.get(
    "/article/{slug}",
    response_model=Article,
    summary="Get Full Article",
    tags=["Grokipedia"],
    dependencies=[Security(get_api_key)])  # Add dependency here
async def get_full_article(slug: str):
    """
    Retrieves a complete article from Grokipedia by its slug. Requires API Key.
    """
    try:
        client = get_client()
        article = client.get_article(slug)
        return article
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")
    except RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get(
    "/summary/{slug}",
    response_model=ArticleSummary,
    summary="Get Article Summary",
    tags=["Grokipedia"],
    dependencies=[Security(get_api_key)])  # Add dependency here
async def get_article_summary(slug: str):
    """
    Retrieves just the summary and table of contents for an article. Requires API Key.
    """
    try:
        client = get_client()
        summary = client.get_summary(slug)
        return summary
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")
    except RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get(
    "/section/{slug}",
    response_model=Section,
    summary="Get Specific Section",
    tags=["Grokipedia"],
    dependencies=[Security(get_api_key)])  # Add dependency here
async def get_article_section(
    slug: str,
    title: str = Query(..., description="The title of the section to retrieve (case-insensitive search).")
):
    """
    Retrieves a specific section from an article by its title. Requires API Key.
    """
    try:
        client = get_client()
        section = client.get_section(slug, title)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found with that title")
        return section
    except ArticleNotFound:
        raise HTTPException(status_code=404, detail="Article not found")
    except RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get(
    "/search",
    response_model=List[SearchResult],
    summary="Search Grokipedia Articles",
    tags=["Grokipedia"],
    dependencies=[Security(get_api_key)])
async def search_articles(q: str = Query(..., description="The search query term.")):
    """
    Searches for articles matching the query term. Requires API Key.
    """
    try:
        client = get_client()
        results = client.search(q)
        return results
    except RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

