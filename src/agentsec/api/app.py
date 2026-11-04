"""The FastAPI application. Milestone 1 serves only a health check."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    # /health must not need the model config: the app has to start on a clean checkout.
    api = FastAPI(title="agentsec", docs_url=None, redoc_url=None, openapi_url=None)

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return api
