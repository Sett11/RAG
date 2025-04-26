import logging
from logging.handlers import TimedRotatingFileHandler
import os

def ensure_log_directory():
    """
    Проверяет наличие директории для логов и создаёт её, если она отсутствует.
    Это необходимо для корректной работы файлового логгера.
    """
    log_dir = "logs"
    # Проверяем, существует ли директория для логов
    if not os.path.exists(log_dir):
        # Если директории нет — создаём её
        os.makedirs(log_dir)

class Logger(logging.Logger):
    """
    Кастомный логгер с ротацией логов по времени (раз в сутки).
    Используется для записи логов приложения в файл с автоматическим созданием новой версии каждый день.
    """
    def __init__(self, name, log_file, level=logging.INFO):
        """
        Инициализация класса Logger.

        :param name: Имя логгера (обычно имя файла, где используется логгер).
        :param log_file: Путь к файлу для сохранения логов.
        :param level: Уровень логгирования (по умолчанию INFO).
        """
        super().__init__(name, level)

        # Форматтер для логов: время, имя логгера, уровень, сообщение
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Обработчик для ротации файлов по времени (раз в сутки)
        handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, encoding='utf-8')
        handler.suffix = "%Y-%m-%d"
        handler.setFormatter(formatter)

        # Добавление обработчика в логгер
        self.addHandler(handler)