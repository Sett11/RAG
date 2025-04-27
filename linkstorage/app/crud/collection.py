"""
CRUD-операции для коллекций: создание, получение, обновление, удаление.
"""
from sqlalchemy.orm import Session
from ..models.collection import Collection
from ..schemas.collection import CollectionCreate, CollectionUpdate
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("crud.collection", "logs/app.log")

def create_collection(db: Session, collection: CollectionCreate, user_id: int):
    """
    Создаёт новую коллекцию для пользователя.
    :param db: Сессия БД.
    :param collection: Данные новой коллекции.
    :param user_id: ID пользователя.
    :return: Объект созданной коллекции.
    """
    # Формируем объект коллекции на основе данных и ID пользователя
    db_collection = Collection(**collection.model_dump(), user_id=user_id)
    # Добавляем коллекцию в сессию
    db.add(db_collection)
    # Фиксируем изменения в базе данных
    db.commit()
    # Обновляем объект коллекции из базы (получаем id и другие поля)
    db.refresh(db_collection)
    # Логируем успешное создание коллекции
    logger.info(f"Создана коллекция: {db_collection.name} для пользователя {user_id}")
    return db_collection

def get_collections(db: Session, user_id: int):
    """
    Получает список коллекций пользователя.
    :param db: Сессия БД.
    :param user_id: ID пользователя.
    :return: Список коллекций.
    """
    # Логируем получение списка коллекций
    logger.info(f"Получение коллекций для пользователя {user_id}")
    # Возвращаем все коллекции пользователя
    return db.query(Collection).filter(Collection.user_id == user_id).all()

def get_collection(db: Session, collection_id: int, user_id: int):
    """
    Получает одну коллекцию пользователя по её ID.
    :param db: Сессия БД.
    :param collection_id: ID коллекции.
    :param user_id: ID пользователя.
    :return: Объект коллекции или None.
    """
    # Логируем попытку получения коллекции
    logger.info(f"Получение коллекции {collection_id} для пользователя {user_id}")
    # Ищем коллекцию по id и user_id
    return db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == user_id).first()

def update_collection(db: Session, db_collection: Collection, collection: CollectionUpdate):
    """
    Обновляет существующую коллекцию.
    :param db: Сессия БД.
    :param db_collection: Объект коллекции из БД.
    :param collection: Новые данные коллекции.
    :return: Обновлённая коллекция.
    """
    # Обновляем только те поля, которые были переданы (partial update)
    for key, value in collection.model_dump(exclude_unset=True).items():
        setattr(db_collection, key, value)
    # Фиксируем изменения в базе данных
    db.commit()
    # Обновляем объект коллекции из базы
    db.refresh(db_collection)
    # Логируем успешное обновление коллекции
    logger.info(f"Обновлена коллекция: {db_collection.id}")
    return db_collection

def delete_collection(db: Session, db_collection: Collection):
    """
    Удаляет коллекцию из базы данных.
    :param db: Сессия БД.
    :param db_collection: Объект коллекции из БД.
    """
    # Логируем удаление коллекции
    logger.info(f"Удалена коллекция: {db_collection.id}")
    # Удаляем коллекцию из базы данных
    db.delete(db_collection)
    db.commit() 