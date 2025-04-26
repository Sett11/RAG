"""
Роутер для работы с пользователями: получение информации о себе и смена пароля.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import UserResponse
from ..utils.security import get_current_user, change_password
from ..models.user import User
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("users", "logs/app.log")

# Создаём роутер с тегом "users" для группировки эндпоинтов
router = APIRouter(tags=["users"])

@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Возвращает информацию о текущем пользователе.
    :param current_user: Объект пользователя, полученный из токена.
    :return: Данные пользователя.
    """
    # Возвращаем объект текущего пользователя (данные берутся из токена)
    logger.info(f"Получена информация о пользователе: {current_user.email}")
    return current_user

@router.put("/users/me/password")
def update_password(new_password: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Смена пароля текущего пользователя.
    :param new_password: Новый пароль.
    :param db: Сессия БД.
    :param current_user: Объект пользователя, полученный из токена.
    :return: Сообщение об успешной смене пароля.
    """
    # Вызываем функцию смены пароля (пароль будет захеширован и сохранён в БД)
    change_password(db, current_user, new_password)
    logger.info(f"Пользователь сменил пароль: {current_user.email}")
    # Возвращаем сообщение об успешной смене пароля
    return {"message": "Password updated successfully"} 