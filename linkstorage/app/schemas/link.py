"""
Pydantic-схемы для ссылок: базовая, создание, обновление, ответ.
"""
from pydantic import BaseModel, HttpUrl, validator, field_validator
from typing import Optional
from ..utils.mylogger import Logger, ensure_log_directory

ensure_log_directory()
logger = Logger("schemas.link", "logs/app.log")

class LinkBase(BaseModel):
    """
    Базовая схема ссылки (заголовок, описание, url, изображение, тип).
    """
    title: str  # Заголовок ссылки
    description: Optional[str] = None  # Описание ссылки (необязательное поле)
    url: HttpUrl  # URL ссылки
    image: Optional[str] = None  # Ссылка на изображение (необязательное поле)
    link_type: Optional[str] = "website"  # Тип ссылки (по умолчанию - сайт)

    def __init__(self, **data):
        # Инициализация базовой схемы ссылки
        super().__init__(**data)
        logger.debug(f"Создана схема LinkBase: url={self.url}")

    @field_validator("url", mode="before")
    @classmethod
    def url_no_xss(cls, v):
        url_str = str(v)
        forbidden = ['<', '>', '"', "'", ' ']
        if any(char in url_str for char in forbidden):
            raise ValueError("URL содержит недопустимые символы (XSS/SQL injection protection)")
        return v

class LinkCreate(LinkBase):
    """
    Схема для создания новой ссылки.
    """
    def __init__(self, **data):
        # Инициализация схемы создания ссылки
        super().__init__(**data)
        logger.debug(f"Создана схема LinkCreate: url={self.url}")

class LinkUpdate(BaseModel):
    """
    Схема для обновления существующей ссылки (частичное обновление).
    """
    title: Optional[str] = None  # Новый заголовок
    description: Optional[str] = None  # Новое описание
    image: Optional[str] = None  # Новое изображение
    link_type: Optional[str] = None  # Новый тип ссылки

    def __init__(self, **data):
        # Инициализация схемы обновления ссылки
        super().__init__(**data)
        logger.debug(f"Создана схема LinkUpdate: поля={list(data.keys())}")

class LinkResponse(LinkBase):
    """
    Схема ответа с данными ссылки (id, user_id и все базовые поля).
    """
    id: int  # ID ссылки
    user_id: int  # ID пользователя-владельца
    class Config:
        from_attributes = True  # Для поддержки работы с ORM-моделями

    def __init__(self, **data):
        # Инициализация схемы ответа ссылки
        super().__init__(**data)
        logger.debug(f"Создана схема LinkResponse: id={self.id}, url={self.url}") 