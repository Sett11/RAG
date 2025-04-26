"""
Модуль безопасности: хэширование паролей, JWT, аутентификация, смена пароля.
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.user import User
from datetime import datetime, timedelta
from typing import Optional
from .mylogger import Logger, ensure_log_directory

# Секретный ключ для подписи JWT-токенов (в реальном проекте хранить в переменных окружения!)
SECRET_KEY = "supersecretkey"
# Алгоритм шифрования для JWT
ALGORITHM = "HS256"
# Время жизни токена (в минутах)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 схема для авторизации через Bearer-токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("security", "logs/app.log")

def get_password_hash(password: str) -> str:
    """
    Хэширует пароль пользователя.
    :param password: Обычный пароль.
    :return: Хэш пароля.
    """
    # Хэшируем пароль с помощью bcrypt
    hash_ = pwd_context.hash(password)
    logger.debug("Пароль захеширован")
    return hash_

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля и его хэша.
    :param plain_password: Обычный пароль.
    :param hashed_password: Хэш пароля.
    :return: True, если пароль совпадает, иначе False.
    """
    # Проверяем, соответствует ли переданный пароль хэшу
    result = pwd_context.verify(plain_password, hashed_password)
    logger.debug(f"Проверка пароля: {'успех' if result else 'неудача'}")
    return result

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создаёт JWT-токен для пользователя.
    :param data: Данные для кодирования (например, email).
    :param expires_delta: Время жизни токена.
    :return: JWT-токен.
    """
    # Копируем данные для токена
    to_encode = data.copy()
    # Устанавливаем время истечения токена
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # Кодируем JWT-токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Создан JWT для {data.get('sub')}")
    return encoded_jwt

def get_db():
    """
    Генератор для получения сессии БД.
    """
    db = SessionLocal()
    try:
        # Возвращаем сессию для работы с БД
        yield db
    finally:
        # Закрываем сессию после использования
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Получает текущего пользователя по JWT-токену.
    :param token: JWT-токен.
    :param db: Сессия БД.
    :return: Объект пользователя.
    :raises HTTPException: Если токен невалиден или пользователь не найден.
    """
    # Исключение для невалидных токенов
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем JWT-токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        # Проверяем, что email присутствует в токене
        if email is None:
            logger.warning("JWT не содержит email (sub)")
            raise credentials_exception
    except JWTError:
        # Логируем ошибку декодирования токена
        logger.warning("Ошибка декодирования JWT")
        raise credentials_exception
    # Ищем пользователя по email в базе данных
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"Пользователь не найден по email из JWT: {email}")
        raise credentials_exception
    logger.info(f"Аутентифицирован пользователь по JWT: {email}")
    return user

def change_password(db: Session, user: User, new_password: str):
    """
    Меняет пароль пользователя.
    :param db: Сессия БД.
    :param user: Объект пользователя.
    :param new_password: Новый пароль.
    """
    # Хэшируем новый пароль и сохраняем его в БД
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    logger.info(f"Пользователь сменил пароль: {user.email}") 