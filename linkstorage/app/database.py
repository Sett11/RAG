"""
Модуль для настройки подключения к базе данных PostgreSQL через SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.base import Base
from .utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("database", "logs/app.log")

# URL подключения к базе данных (используется в docker-compose)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db/postgres"

# Создаём движок SQLAlchemy для работы с PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
logger.info(f"Создан движок SQLAlchemy для подключения к БД: {SQLALCHEMY_DATABASE_URL}")

# Создаём фабрику сессий для работы с БД (SessionLocal)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("Инициализирована фабрика сессий SQLAlchemy (SessionLocal)")

# Функция зависимости для получения сессии БД (используется в Depends)
def get_db():
    """
    Генерирует сессию БД для запроса и корректно её закрывает после использования.
    Используется как зависимость в роутерах FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()