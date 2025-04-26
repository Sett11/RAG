"""
Роутер для управления ссылками пользователя: создание, получение, обновление, удаление.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.link import LinkCreate, LinkResponse, LinkUpdate
from ..crud.link import create_link, get_links, get_link, update_link, delete_link
from ..utils.security import get_current_user
from ..models.user import User
from ..utils.mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("links", "logs/app.log")

# Создаём роутер с тегом "links" для группировки эндпоинтов
router = APIRouter(tags=["links"])

@router.post("/links/", response_model=LinkResponse)
def create_user_link(
    link: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт новую ссылку для пользователя.
    :param link: Данные новой ссылки.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Данные созданной ссылки.
    """
    # Создаём новую ссылку через функцию crud, передаём id пользователя
    logger.info(f"Создание ссылки пользователем {current_user.email}: {link.url}")
    return create_link(db, link, current_user.id)

@router.get("/links/", response_model=list[LinkResponse])
def read_user_links(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получает список ссылок пользователя.
    :param skip: Сколько пропустить (пагинация).
    :param limit: Сколько вернуть (пагинация).
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Список ссылок.
    """
    # Получаем список ссылок пользователя с поддержкой пагинации
    logger.info(f"Получение ссылок пользователя: {current_user.email}")
    return get_links(db, current_user.id, skip, limit)

@router.put("/links/{link_id}", response_model=LinkResponse)
def update_user_link(
    link_id: int,
    link: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновляет существующую ссылку пользователя.
    :param link_id: ID ссылки.
    :param link: Новые данные ссылки.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Обновлённая ссылка.
    """
    # Получаем ссылку по id и id пользователя
    db_link = get_link(db, link_id, current_user.id)
    # Если ссылка не найдена — выбрасываем исключение
    if not db_link:
        logger.warning(f"Попытка обновить несуществующую ссылку: {link_id} пользователем {current_user.email}")
        raise HTTPException(status_code=404, detail="Link not found")
    # Обновляем ссылку через функцию crud
    logger.info(f"Обновление ссылки {link_id} пользователем {current_user.email}")
    return update_link(db, db_link, link)

@router.delete("/links/{link_id}")
def delete_user_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет ссылку пользователя.
    :param link_id: ID ссылки.
    :param db: Сессия БД.
    :param current_user: Текущий пользователь.
    :return: Сообщение об успешном удалении.
    """
    # Получаем ссылку по id и id пользователя
    db_link = get_link(db, link_id, current_user.id)
    # Если ссылка не найдена — выбрасываем исключение
    if not db_link:
        logger.warning(f"Попытка удалить несуществующую ссылку: {link_id} пользователем {current_user.email}")
        raise HTTPException(status_code=404, detail="Link not found")
    # Удаляем ссылку через функцию crud
    delete_link(db, db_link)
    logger.info(f"Удалена ссылка {link_id} пользователем {current_user.email}")
    # Возвращаем сообщение об успешном удалении
    return {"message": "Link deleted successfully"}