"""
Точка входа в приложение LinkStorage API.
Инициализирует FastAPI, подключает роутеры, CORS и логгер.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models.base import Base
from .routers import auth, users, links, collections
from .utils.mylogger import Logger, ensure_log_directory

# Создаём все таблицы в базе данных на основе моделей (если их ещё нет)
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI-приложения с метаданными
app = FastAPI(
    title="LinkStorage API",
    description="API for storing and managing user links and collections",
    version="1.0.0",
)

# Добавляем CORS middleware для поддержки запросов с любых источников (например, для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Разрешаем все источники
    allow_credentials=True,         # Разрешаем передачу куки и авторизационных заголовков
    allow_methods=["*"],           # Разрешаем все методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],           # Разрешаем любые заголовки
)

# Подключаем роутеры для auth, users, links, collections
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(links.router)
app.include_router(collections.router)

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("main", "logs/app.log")
logger.info("Запуск приложения LinkStorage API")