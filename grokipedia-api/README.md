# Grokipedia API

A lightweight, deployable REST API for the Grokipedia SDK, built with FastAPI.

## Endpoints

-   `GET /`: Health check.
-   `GET /article/{slug}`: Retrieves the full content of a Grokipedia article.
-   `GET /summary/{slug}`: Retrieves the summary and table of contents for an article.
-   `GET /section/{slug}?title={section_title}`: Retrieves a specific section from an article by its title.
-   `GET /docs`: View interactive API documentation (Swagger UI).
-   `GET /redoc`: View alternative API documentation (ReDoc).

## Deployment to Railway

1.  Push this repository (including the `grokipedia-api` folder) to GitHub.
2.  Create a new project on Railway and link it to your GitHub repository.
3.  When prompted, select "Deploy from Dockerfile".
4.  Railway will automatically build the `Dockerfile` and deploy the service.
5.  A public URL will be generated for your API.

