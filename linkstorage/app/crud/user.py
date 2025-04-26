"""
CRUD-операции для пользователей: создание и аутентификация.
"""
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate
from ..utils.security import get_password_hash, verify_password
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("crud.user", "logs/app.log")

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