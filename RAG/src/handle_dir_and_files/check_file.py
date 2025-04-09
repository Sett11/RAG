import os
from utils.mylogger import Logger

logger = Logger('CheckFile', 'logs/rag.log')

class CheckFile:
    """
    Класс для проверки существования и доступа к файлу.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def check_file_exists(self):
        try:
            if not os.path.exists(self.file_path):
                logger.error(f"Файл не существует: {self.file_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке файла {self.file_path}: {str(e)}")
            return False
        
    def check_file_access(self):
        try:
            if not os.access(self.file_path, os.R_OK):
                logger.error(f"Нет прав на чтение файла: {self.file_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к файлу {self.file_path}: {str(e)}")
            return False
