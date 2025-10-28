# Grokipedia API

A lightweight, deployable REST API for the Grokipedia SDK, built with FastAPI.

## Authentication

This API requires an API key for access to most endpoints. Provide your key in the `X-API-Key` header with each request.

Example using `curl`:

```bash
curl -X 'GET' \
  'YOUR_API_URL/article/Joe_Biden' \
  -H 'accept: application/json' \
  -H 'X-API-Key: YOUR_SECRET_API_KEY'
```

The API administrator sets the valid API keys via the `GROKIPEDIA_API_KEYS` environment variable (comma-separated).

## Endpoints

-   `GET /`: Health check (No API Key required).
-   `GET /article/{slug}`: Retrieves the full content of a Grokipedia article (Requires API Key).
-   `GET /summary/{slug}`: Retrieves the summary and table of contents for an article (Requires API Key).
-   `GET /section/{slug}?title={section_title}`: Retrieves a specific section from an article by its title (Requires API Key).
-   `GET /search?q={query}`: Searches for articles matching the query (Requires API Key). Returns a list of potential matches with titles and slugs.
-   `GET /docs`: View interactive API documentation (Swagger UI). You can authorize using the lock icon here.
-   `GET /redoc`: View alternative API documentation (ReDoc).

## Deployment to Railway

1.  Push this repository (including the `grokipedia-api` folder) to GitHub.
2.  Create a new project on Railway and link it to your GitHub repository.
3.  When prompted, select "Deploy from Dockerfile".
4.  Railway will automatically build the `Dockerfile` and deploy the service.
5.  A public URL will be generated for your API.

