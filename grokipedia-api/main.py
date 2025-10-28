import contextlib
from fastapi import FastAPI, HTTPException, Query
from grokipedia_sdk import (
    Client,
    Article,
    ArticleSummary,
    Section,
    ArticleNotFound,
    RequestError
)

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
    description="A REST API wrapper for the Grokipedia SDK.",
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
    tags=["Grokipedia"])
async def get_full_article(slug: str):
    """
    Retrieves a complete article from Grokipedia by its slug.
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
    tags=["Grokipedia"])
async def get_article_summary(slug: str):
    """
    Retrieves just the summary and table of contents for an article.
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
    tags=["Grokipedia"])
async def get_article_section(
    slug: str,
    title: str = Query(..., description="The title of the section to retrieve (case-insensitive search).")
):
    """
    Retrieves a specific section from an article by its title.
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

