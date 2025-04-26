"""
Модель ссылки для хранения информации о пользовательских ссылках в базе данных.
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("models.link", "logs/app.log")

class LinkType(str, Enum):
    """
    Перечисление типов ссылок для классификации контента.
    """
    WEBSITE = "website"  # Веб-сайт
    BOOK = "book"        # Книга
    ARTICLE = "article"  # Статья
    MUSIC = "music"      # Музыка
    VIDEO = "video"      # Видео

class Link(Base):
    """
    Класс Link описывает таблицу ссылок.
    Содержит заголовок, описание, url, изображение, тип, временные метки и связь с пользователем.
    """
    __tablename__ = "links"

    # Уникальный идентификатор ссылки (первичный ключ)
    id = Column(Integer, primary_key=True, index=True)
    # Заголовок ссылки (обязательное поле)
    title = Column(String, nullable=False)
    # Описание ссылки (необязательное поле)
    description = Column(String)
    # URL ссылки (уникальный, обязательный)
    url = Column(String, nullable=False, unique=True)
    # Ссылка на изображение (если есть)
    image = Column(String)
    # Тип ссылки (по умолчанию - сайт)
    link_type = Column(String, default=LinkType.WEBSITE)
    # Дата и время создания ссылки (устанавливается автоматически)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Дата и время последнего обновления ссылки (обновляется автоматически)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # ID пользователя-владельца (внешний ключ)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __init__(self, *args, **kwargs):
        # Инициализация экземпляра ссылки через родительский конструктор
        super().__init__(*args, **kwargs)
        logger.info(f"Создан экземпляр ссылки: {self.url if hasattr(self, 'url') else 'без url'}")