"""
Модели коллекций и связей коллекция-ссылка для хранения пользовательских коллекций и их содержимого.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("models.collection", "logs/app.log")

class Collection(Base):
    """
    Класс Collection описывает таблицу коллекций пользователя.
    Содержит имя, описание, временные метки и связь с пользователем.
    """
    __tablename__ = "collections"

    # Уникальный идентификатор коллекции (первичный ключ)
    id = Column(Integer, primary_key=True, index=True)
    # Название коллекции (обязательное поле)
    name = Column(String, nullable=False)
    # Описание коллекции (необязательное поле)
    description = Column(String)
    # Дата и время создания коллекции (устанавливается автоматически)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Дата и время последнего обновления коллекции (обновляется автоматически)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # ID пользователя-владельца (внешний ключ)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __init__(self, *args, **kwargs):
        # Инициализация экземпляра коллекции через родительский конструктор
        super().__init__(*args, **kwargs)
        logger.info(f"Создана коллекция: {self.name if hasattr(self, 'name') else 'без имени'}")

class CollectionLink(Base):
    """
    Класс CollectionLink описывает связь между коллекцией и ссылкой (многие ко многим).
    """
    __tablename__ = "collection_links"

    # Уникальный идентификатор связи (первичный ключ)
    id = Column(Integer, primary_key=True, index=True)
    # ID коллекции (внешний ключ)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    # ID ссылки (внешний ключ)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)

    def __init__(self, *args, **kwargs):
        # Инициализация экземпляра связи через родительский конструктор
        super().__init__(*args, **kwargs)
        logger.info(f"Создана связь коллекция-ссылка: collection_id={getattr(self, 'collection_id', None)}, link_id={getattr(self, 'link_id', None)}")