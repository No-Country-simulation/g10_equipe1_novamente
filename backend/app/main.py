import logging
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.storage import StorageError

FRONTEND_DIR = Path(__file__).parent / "frontend"

app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)
if not app_logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    app_logger.addHandler(handler)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.FASTAPI_ENV != "development":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StorageError)
def storage_error_handler(_request: Request, exc: StorageError) -> JSONResponse:
    logging.error("Erro de armazenamento: %s", type(exc).__name__)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "O armazenamento de arquivos não está disponível. Tente novamente mais tarde."
        },
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
app.frontend("/", directory=FRONTEND_DIR)
