"""
Роутер для управления коллекциями пользователя: создание, получение, обновление, удаление.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.collection import CollectionCreate, CollectionResponse, CollectionUpdate
from ..crud.collection import create_collection, get_collections, get_collection, update_collection, delete_collection
from ..utils.security import get_current_user
from ..models.user import User
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("collections", "logs/app.log")

# Создаём роутер с тегом "collections" для группировки эндпоинтов
router = APIRouter(tags=["collections"])

@router.post("/collections/", response_model=CollectionResponse)
def create_user_collection(collection: CollectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Создаёт новую коллекцию для пользователя.
    :param collection: Данные новой коллекции.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Данные созданной коллекции.
    """
    # Создаём новую коллекцию через функцию crud, передаём id пользователя
    logger.info(f"Создание коллекции пользователем {current_user.email}: {collection.name}")
    return create_collection(db, collection, current_user.id)

@router.get("/collections/", response_model=list[CollectionResponse])
def read_user_collections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получает список коллекций пользователя.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Список коллекций.
    """
    # Получаем список коллекций пользователя
    logger.info(f"Получение коллекций пользователя: {current_user.email}")
    return get_collections(db, current_user.id)

@router.put("/collections/{collection_id}", response_model=CollectionResponse)
def update_user_collection(collection_id: int, collection: CollectionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Обновляет существующую коллекцию пользователя.
    :param collection_id: ID коллекции.
    :param collection: Новые данные коллекции.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Обновлённая коллекция.
    """
    # Получаем коллекцию по id и id пользователя
    db_collection = get_collection(db, collection_id, current_user.id)
    # Если коллекция не найдена — выбрасываем исключение
    if not db_collection:
        logger.warning(f"Попытка обновить несуществующую коллекцию: {collection_id} пользователем {current_user.email}")
        raise HTTPException(status_code=404, detail="Collection not found")
    # Обновляем коллекцию через функцию crud
    logger.info(f"Обновление коллекции {collection_id} пользователем {current_user.email}")
    return update_collection(db, db_collection, collection)

@router.delete("/collections/{collection_id}")
def delete_user_collection(collection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Удаляет коллекцию пользователя.
    :param collection_id: ID коллекции.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Сообщение об успешном удалении.
    """
    # Получаем коллекцию по id и id пользователя
    db_collection = get_collection(db, collection_id, current_user.id)
    # Если коллекция не найдена — выбрасываем исключение
    if not db_collection:
        logger.warning(f"Попытка удалить несуществующую коллекцию: {collection_id} пользователем {current_user.email}")
        raise HTTPException(status_code=404, detail="Collection not found")
    # Удаляем коллекцию через функцию crud
    delete_collection(db, db_collection)
    logger.info(f"Удалена коллекция {collection_id} пользователем {current_user.email}")
    # Возвращаем сообщение об успешном удалении
    return {"message": "Collection deleted successfully"} 