"""
Модель пользователя для хранения информации о пользователях в базе данных.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("models.user", "logs/app.log")

class User(Base):
    """
    Класс User описывает таблицу пользователей.
    Содержит email, хэш пароля, статус активности и временные метки.
    """
    __tablename__ = "users"

    # Уникальный идентификатор пользователя (первичный ключ)
    id = Column(Integer, primary_key=True, index=True)
    # Email пользователя (уникальный, не может быть null)
    email = Column(String, unique=True, index=True, nullable=False)
    # Хэш пароля пользователя (не может быть null)
    hashed_password = Column(String, nullable=False)
    # Флаг активности пользователя (по умолчанию True)
    is_active = Column(Boolean, default=True)
    # Дата и время создания пользователя (устанавливается автоматически)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Дата и время последнего обновления пользователя (обновляется автоматически)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Токен для сброса пароля (может быть null)
    reset_password_token = Column(String, nullable=True)
    # Срок действия токена сброса пароля (может быть null)
    reset_password_token_expiration = Column(DateTime(timezone=True), nullable=True)

    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, *args, **kwargs):
        # Инициализация экземпляра пользователя через родительский конструктор
        super().__init__(*args, **kwargs)
        logger.info(f"Создан экземпляр пользователя: {self.email if hasattr(self, 'email') else 'без email'}")