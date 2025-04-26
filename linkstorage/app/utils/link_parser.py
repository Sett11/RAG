"""
Модуль для парсинга метаданных ссылок (title, description, image, type).
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ..models.link import LinkType
from .mylogger import Logger, ensure_log_directory

# Гарантируем наличие директории для логов и инициализируем логгер
ensure_log_directory()
logger = Logger("link_parser", "logs/app.log")

def parse_link_metadata(url: str):
    """
    Извлекает метаданные из переданной ссылки (title, description, image, type).
    :param url: URL для парсинга.
    :return: Словарь с метаданными или None при ошибке.
    """
    try:
        logger.info(f"Парсинг метаданных для ссылки: {url}")
        # Отправляем HTTP-запрос к переданному URL
        response = requests.get(url, timeout=10)
        # Проверяем успешность ответа (код 200)
        response.raise_for_status()
    except Exception as e:
        # В случае ошибки логируем и возвращаем None
        logger.warning(f"Ошибка при получении ссылки {url}: {e}")
        return None

    # Создаём объект BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Словарь для хранения метаданных ссылки
    metadata = {
        "title": None,         # Заголовок страницы
        "description": None,   # Описание страницы
        "image": None,        # Картинка-превью
        "link_type": LinkType.WEBSITE  # Тип ссылки (по умолчанию - сайт)
    }
    
    # Сначала ищем Open Graph теги (og:title, og:description, og:image, og:type)
    og_title = soup.find("meta", property="og:title")
    og_description = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    og_type = soup.find("meta", property="og:type")
    
    # Если найден og:title, используем его, иначе ищем обычный <title>
    if og_title:
        metadata["title"] = og_title.get("content")
    else:
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.text
    
    # Если найден og:description, используем его, иначе ищем <meta name="description">
    if og_description:
        metadata["description"] = og_description.get("content")
    else:
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description:
            metadata["description"] = meta_description.get("content")
    
    # Если найден og:image, используем его
    if og_image:
        metadata["image"] = og_image.get("content")
    
    # Если найден og:type, используем его, если он есть в LinkType
    if og_type:
        og_type_content = og_type.get("content", "").lower()
        if og_type_content in LinkType.__members__:
            metadata["link_type"] = og_type_content
    
    logger.info(f"Метаданные успешно извлечены для {url}")
    return metadata