"""
Pydantic-схемы для пользователя: базовая, создание, ответ, токен.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..utils.mylogger import Logger, ensure_log_directory

ensure_log_directory()
logger = Logger("schemas.user", "logs/app.log")

class UserBase(BaseModel):
    """
    Базовая схема пользователя (email, активность).
    """
    email: EmailStr  # Email пользователя
    is_active: Optional[bool] = True  # Флаг активности

    def __init__(self, **data):
        # Инициализация базовой схемы пользователя
        super().__init__(**data)
        logger.debug(f"Создана схема UserBase: email={self.email}")

class UserCreate(UserBase):
    """
    Схема для создания пользователя (email, пароль).
    """
    password: str  # Пароль пользователя

    def __init__(self, **data):
        # Инициализация схемы создания пользователя
        super().__init__(**data)
        logger.debug(f"Создана схема UserCreate: email={self.email}")

class UserResponse(UserBase):
    """
    Схема ответа с данными пользователя (id, email, активность).
    """
    id: int  # ID пользователя
    class Config:
        from_attributes = True  # Для поддержки работы с ORM-моделями

    def __init__(self, **data):
        # Инициализация схемы ответа пользователя
        super().__init__(**data)
        logger.debug(f"Создана схема UserResponse: id={self.id}, email={self.email}")

class Token(BaseModel):
    """
    Схема для JWT-токена (access_token, token_type).
    """
    access_token: str  # JWT-токен
    token_type: str    # Тип токена (обычно 'bearer')

    def __init__(self, **data):
        # Инициализация схемы токена
        super().__init__(**data)
        logger.debug(f"Создана схема Token: тип={self.token_type}") 