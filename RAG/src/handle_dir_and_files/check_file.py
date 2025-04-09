import os
from utils.mylogger import Logger

logger = Logger('CheckFile', 'logs/rag.log')

class CheckFile:
    """
    Класс для проверки существования и доступа к файлу.
    """
    def __init__(self):
        pass

    def check_file_exists(self, file_path: str):
        try:
            if not os.path.exists(file_path):
                logger.error(f"Файл не существует: {file_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке файла {file_path}: {str(e)}")
            return False
        
    def check_file_access(self, file_path: str):
        try:
            if not os.access(file_path, os.R_OK):
                logger.error(f"Нет прав на чтение файла: {file_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к файлу {file_path}: {str(e)}")
            return False
