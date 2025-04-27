"""
CRUD-операции для ссылок: создание, получение, обновление, удаление.
"""
from sqlalchemy.orm import Session
from ..models.link import Link
from ..schemas.link import LinkCreate, LinkUpdate
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("crud.link", "logs/app.log")

def create_link(db: Session, link: LinkCreate, user_id: int):
    """
    Создаёт новую ссылку для пользователя.
    :param db: Сессия БД.
    :param link: Данные новой ссылки.
    :param user_id: ID пользователя.
    :return: Объект созданной ссылки.
    """
    # Преобразуем url в строку, если это HttpUrl
    link_data = link.model_dump()
    link_data['url'] = str(link_data['url'])
    db_link = Link(**link_data, user_id=user_id)
    # Добавляем ссылку в сессию
    db.add(db_link)
    # Фиксируем изменения в базе данных
    db.commit()
    # Обновляем объект ссылки из базы (получаем id и другие поля)
    db.refresh(db_link)
    # Логируем успешное создание ссылки
    logger.info(f"Создана ссылка: {db_link.url} для пользователя {user_id}")
    return db_link

def get_links(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Получает список ссылок пользователя.
    :param db: Сессия БД.
    :param user_id: ID пользователя.
    :param skip: Сколько пропустить (пагинация).
    :param limit: Сколько вернуть (пагинация).
    :return: Список ссылок.
    """
    # Логируем получение списка ссылок
    logger.info(f"Получение ссылок для пользователя {user_id}")
    # Возвращаем список ссылок с поддержкой пагинации
    return db.query(Link).filter(Link.user_id == user_id).offset(skip).limit(limit).all()

def get_link(db: Session, link_id: int, user_id: int):
    """
    Получает одну ссылку пользователя по её ID.
    :param db: Сессия БД.
    :param link_id: ID ссылки.
    :param user_id: ID пользователя.
    :return: Объект ссылки или None.
    """
    # Логируем попытку получения ссылки
    logger.info(f"Получение ссылки {link_id} для пользователя {user_id}")
    # Ищем ссылку по id и user_id
    return db.query(Link).filter(Link.id == link_id, Link.user_id == user_id).first()

def update_link(db: Session, db_link: Link, link: LinkUpdate):
    """
    Обновляет существующую ссылку.
    :param db: Сессия БД.
    :param db_link: Объект ссылки из БД.
    :param link: Новые данные ссылки.
    :return: Обновлённая ссылка.
    """
    # Обновляем только те поля, которые были переданы (partial update)
    for key, value in link.model_dump(exclude_unset=True).items():
        setattr(db_link, key, value)
    # Фиксируем изменения в базе данных
    db.commit()
    # Обновляем объект ссылки из базы
    db.refresh(db_link)
    # Логируем успешное обновление ссылки
    logger.info(f"Обновлена ссылка: {db_link.id}")
    return db_link

def delete_link(db: Session, db_link: Link):
    """
    Удаляет ссылку из базы данных.
    :param db: Сессия БД.
    :param db_link: Объект ссылки из БД.
    """
    # Логируем удаление ссылки
    logger.info(f"Удалена ссылка: {db_link.id}")
    # Удаляем ссылку из базы данных
    db.delete(db_link)
    db.commit() 