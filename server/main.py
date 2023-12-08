import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

server_path = os.path.join(os.getcwd(), "server")
sys.path.insert(0, server_path)

from config import settings

from router import router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)

app.include_router(router)

if __name__ == '__main__':
    directory = 'server.' if settings.NODE_ENV != 'production' and \
                             os.path.dirname(os.path.abspath(__file__)).split('/')[-1] != 'server' else ''
    os.system(f"gunicorn {directory}"
              f"main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8077")
