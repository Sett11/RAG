import os
from utils.mylogger import Logger

logger = Logger('CheckFile', 'logs/rag.log')

class CheckFile:
    """
    Класс для проверки существования и доступа к файлу.
    
    Этот класс предоставляет методы для проверки:
    - Существования файла по указанному пути
    - Прав доступа к файлу для чтения
    
    Attributes:
        None
    """
    def __init__(self):
        """
        Инициализация класса CheckFile.
        """
        logger.info("Инициализация класса CheckFile")

    def check_file_exists(self, file_path: str) -> bool:
        """
        Проверяет существование файла по указанному пути.

        Args:
            file_path (str): Путь к файлу для проверки

        Returns:
            bool: True если файл существует, False в противном случае
        """
        try:
            logger.debug(f"Проверка существования файла: {file_path}")
            if not os.path.exists(file_path):
                logger.error(f"Файл не существует: {file_path}")
                return False
            logger.info(f"Файл существует: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке файла {file_path}: {str(e)}")
            return False
        
    def check_file_access(self, file_path: str) -> bool:
        """
        Проверяет права доступа к файлу для чтения.

        Args:
            file_path (str): Путь к файлу для проверки прав доступа

        Returns:
            bool: True если есть права на чтение, False в противном случае
        """
        try:
            logger.debug(f"Проверка прав доступа к файлу: {file_path}")
            if not os.access(file_path, os.R_OK):
                logger.error(f"Нет прав на чтение файла: {file_path}")
                return False
            logger.info(f"Есть права на чтение файла: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к файлу {file_path}: {str(e)}")
            return False
