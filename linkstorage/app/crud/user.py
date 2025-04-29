"""
CRUD-операции для пользователей: создание и аутентификация.
"""
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate
from ..utils.security import get_password_hash, verify_password
from ..utils.mylogger import Logger, ensure_log_directory
import secrets
from datetime import datetime, timedelta, UTC

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("crud.user", "logs/app.log")

RESET_TOKEN_EXPIRE_HOURS = 1

def create_user(db: Session, user: UserCreate):
    """
    Создаёт нового пользователя в базе данных.
    :param db: Сессия БД.
    :param user: Данные пользователя для создания.
    :return: Объект пользователя.
    """
    # Формируем объект пользователя с email и хэшированным паролем
    db_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    # Добавляем пользователя в сессию
    db.add(db_user)
    # Фиксируем изменения в базе данных
    db.commit()
    # Обновляем объект пользователя из базы (получаем id и другие поля)
    db.refresh(db_user)
    # Логируем успешное создание пользователя
    logger.info(f"Пользователь создан: {db_user.email}")
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    """
    Аутентифицирует пользователя по email и паролю.
    :param db: Сессия БД.
    :param email: Email пользователя.
    :param password: Пароль пользователя.
    :return: Объект пользователя или None, если аутентификация не удалась.
    """
    # Ищем пользователя по email в базе данных
    user = db.query(User).filter(User.email == email).first()
    # Проверяем, найден ли пользователь и совпадает ли пароль
    if not user or not verify_password(password, user.hashed_password):
        # Если пользователь не найден или пароль неверный — логируем и возвращаем None
        logger.warning(f"Неудачная попытка аутентификации: {email}")
        return None
    # Если всё успешно — логируем вход пользователя
    logger.info(f"Пользователь аутентифицирован: {email}")
    return user 

def generate_reset_token():
    """
    Генерирует криптостойкий токен для сброса пароля.
    """
    return secrets.token_urlsafe(32)

def set_reset_token(db: Session, user: User):
    """
    Устанавливает токен и срок действия для сброса пароля пользователю.
    :param db: Сессия БД.
    :param user: Объект пользователя.
    :return: Токен сброса пароля.
    """
    token = generate_reset_token()
    expiration = datetime.now(UTC) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    user.reset_password_token = token
    user.reset_password_token_expiration = expiration
    db.commit()
    db.refresh(user)
    logger.info(f"Установлен токен сброса пароля для пользователя: {user.email}")
    return token

def verify_reset_token(db: Session, token: str):
    """
    Проверяет валидность токена сброса пароля и возвращает пользователя.
    :param db: Сессия БД.
    :param token: Токен сброса пароля.
    :return: Объект пользователя или None.
    """
    user = db.query(User).filter(User.reset_password_token == token).first()
    if not user:
        logger.warning(f"Токен сброса пароля не найден: {token}")
        return None
    if not user.reset_password_token_expiration or user.reset_password_token_expiration < datetime.now(UTC):
        logger.warning(f"Токен сброса пароля истёк для пользователя: {user.email}")
        return None
    return user

def reset_password(db: Session, user: User, new_password: str):
    """
    Сбрасывает пароль пользователя и удаляет токен сброса.
    :param db: Сессия БД.
    :param user: Объект пользователя.
    :param new_password: Новый пароль.
    """
    user.hashed_password = get_password_hash(new_password)
    user.reset_password_token = None
    user.reset_password_token_expiration = None
    db.commit()
    db.refresh(user)
    logger.info(f"Пользователь сбросил пароль: {user.email}") 