"""
Роутер для аутентификации пользователей: регистрация и вход.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..schemas.user import UserCreate, UserResponse, Token, PasswordResetRequest, PasswordResetConfirm, MessageResponse
from ..crud.user import create_user, authenticate_user, set_reset_token, verify_reset_token, reset_password
from ..utils.security import create_access_token
from ..utils.mylogger import Logger, ensure_log_directory
from app.models.user import User

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("auth", "logs/app.log")

# Создаём роутер с тегом "auth" для группировки эндпоинтов
router = APIRouter(tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрирует нового пользователя.
    :param user: Данные для регистрации (email, пароль).
    :param db: Сессия БД.
    :return: Данные зарегистрированного пользователя.
    """
    try:
        db_user = create_user(db, user)
    except IntegrityError:
        db.rollback()
        logger.warning(f"Попытка регистрации с уже существующим email: {user.email}")
        raise HTTPException(status_code=409, detail="User with this email already exists")
    logger.info(f"Зарегистрирован пользователь: {db_user.email}")
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Аутентификация пользователя по email и паролю.
    :param form_data: Данные формы (username/email, password).
    :param db: Сессия БД.
    :return: JWT-токен доступа.
    """
    # Проверяем, существует ли пользователь и совпадает ли пароль
    user = authenticate_user(db, form_data.username, form_data.password)
    # Если пользователь не найден или пароль неверный — выбрасываем исключение
    if not user:
        logger.warning(f"Неудачная попытка входа: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    # Генерируем JWT-токен для пользователя
    access_token = create_access_token(data={"sub": user.email})
    logger.info(f"Пользователь вошёл: {user.email}")
    # Возвращаем токен доступа
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset-password/request", response_model=MessageResponse)
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Запрос на сброс пароля: генерирует токен и "отправляет" его пользователю (для теста — возвращает в ответе).
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        logger.warning(f"Попытка сброса пароля для несуществующего email: {data.email}")
        # Не раскрываем, что пользователя нет — возвращаем успешный ответ
        return {"message": "Если email зарегистрирован, инструкция отправлена"}
    token = set_reset_token(db, user)
    # В реальном проекте здесь отправляется email с токеном
    logger.info(f"Токен сброса пароля сгенерирован для: {user.email}")
    return {"message": f"Токен для сброса пароля: {token}"}

@router.post("/reset-password/confirm", response_model=MessageResponse)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Подтверждение сброса пароля: проверяет токен и устанавливает новый пароль.
    """
    user = verify_reset_token(db, data.token)
    if not user:
        logger.warning(f"Попытка сброса пароля с невалидным или истёкшим токеном: {data.token}")
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    reset_password(db, user, data.new_password)
    logger.info(f"Пароль успешно сброшен для пользователя: {user.email}")
    return {"message": "Пароль успешно сброшен"}