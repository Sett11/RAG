"""
Базовый класс для всех моделей SQLAlchemy в проекте.
"""
from sqlalchemy.orm import declarative_base
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("models.base", "logs/app.log")

# Создаём базовый класс для всех моделей SQLAlchemy
Base = declarative_base()
logger.info("Базовый класс моделей SQLAlchemy инициализирован (Base)") 