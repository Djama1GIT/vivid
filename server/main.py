import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

server_path = os.path.join(os.getcwd(), "server")
sys.path.insert(0, server_path)

from config import settings

from router import router

app = FastAPI(
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)

app.include_router(router)
app.mount("/books", StaticFiles(directory="books"), name="books")

if __name__ == '__main__':
    directory = 'server.' if settings.NODE_ENV != 'production' and \
                             os.path.dirname(os.path.abspath(__file__)).split('/')[-1] != 'server' else ''
    os.system(
        f"gunicorn "
        f"{directory}main:app "
        f"--workers {settings.WORKERS} "
        f"--worker-class uvicorn.workers.UvicornWorker "
        f"--bind=0.0.0.0:{settings.SERVER_PORT} "
        f"--timeout {settings.WORKER_TIMEOUT}"
    )
