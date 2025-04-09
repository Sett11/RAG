import os
from utils.mylogger import Logger

logger = Logger('CheckDir', 'logs/rag.log')

class CheckDirExists:
    """
    Класс для проверки существования и доступа к директории.
    """
    def __init__(self, dir_path: str):
        # Извлекаем базовую директорию из пути с шаблоном файла
        self.dir_path = os.path.dirname(dir_path)
        if not self.dir_path:  # Если путь не содержит директорию
            self.dir_path = dir_path

    def check_directory_exists(self):
        try:
            if not os.path.exists(self.dir_path):
                logger.error(f"Директория не существует: {self.dir_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке директории {self.dir_path}: {str(e)}")
            return False
        
    def check_directory_access(self):
        try:
            if not os.access(self.dir_path, os.R_OK):
                logger.error(f"Нет прав на чтение директории: {self.dir_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к директории {self.dir_path}: {str(e)}")
            return False