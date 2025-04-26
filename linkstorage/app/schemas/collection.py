"""
Pydantic-схемы для коллекций: базовая, создание, обновление, ответ.
"""
from pydantic import BaseModel
from typing import Optional
from ..utils.mylogger import Logger, ensure_log_directory

ensure_log_directory()
logger = Logger("schemas.collection", "logs/app.log")

class CollectionBase(BaseModel):
    """
    Базовая схема коллекции (имя, описание).
    """
    name: str  # Название коллекции
    description: Optional[str] = None  # Описание коллекции (необязательное поле)

    def __init__(self, **data):
        # Инициализация базовой схемы коллекции
        super().__init__(**data)
        logger.debug(f"Создана схема CollectionBase: name={self.name}")

class CollectionCreate(CollectionBase):
    """
    Схема для создания новой коллекции.
    """
    def __init__(self, **data):
        # Инициализация схемы создания коллекции
        super().__init__(**data)
        logger.debug(f"Создана схема CollectionCreate: name={self.name}")

class CollectionUpdate(BaseModel):
    """
    Схема для обновления существующей коллекции (частичное обновление).
    """
    name: Optional[str] = None  # Новое имя коллекции
    description: Optional[str] = None  # Новое описание коллекции

    def __init__(self, **data):
        # Инициализация схемы обновления коллекции
        super().__init__(**data)
        logger.debug(f"Создана схема CollectionUpdate: поля={list(data.keys())}")

class CollectionResponse(CollectionBase):
    """
    Схема ответа с данными коллекции (id, user_id и все базовые поля).
    """
    id: int  # ID коллекции
    user_id: int  # ID пользователя-владельца
    class Config:
        from_attributes = True  # Для поддержки работы с ORM-моделями

    def __init__(self, **data):
        # Инициализация схемы ответа коллекции
        super().__init__(**data)
        logger.debug(f"Создана схема CollectionResponse: id={self.id}, name={self.name}") 