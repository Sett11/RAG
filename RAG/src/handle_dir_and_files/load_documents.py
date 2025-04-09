from typing import List
import os
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

from utils.mylogger import Logger
from src.handle_dir_and_files.check_dir import CheckDirExists
from src.handle_dir_and_files.check_file import CheckFile

logger = Logger('LoadDocuments', 'logs/rag.log')

class LoadDocuments:
    def __init__(self, file_patterns: List[str]) -> None:
        self.file_patterns = file_patterns
        self.check_dir = CheckDirExists(file_patterns[0])
        self.check_file = CheckFile()

    def _get_supported_formats(self) -> List[str]:
        """
        Возвращает список поддерживаемых форматов файлов.

        Returns:
            List[str]: Список расширений файлов
        """
        return ['.pdf', '.txt', '.docx']

    def _is_supported_format(self, file_path: str) -> bool:
        """
        Проверяет, поддерживается ли формат файла.

        Args:
            file_path (str): Путь к файлу

        Returns:
            bool: True, если формат поддерживается, иначе False
        """
        return any(file_path.lower().endswith(fmt) for fmt in self._get_supported_formats())

    def load_documents(self) -> List[Document]:
        """
        Загрузка документов из указанных файловых паттернов.

        Args:
            file_patterns (List[str]): Список паттернов для поиска файлов

        Returns:
            List[Document]: Список загруженных документов

        Raises:
            ValueError: Если список паттернов пуст
            FileNotFoundError: Если не найдено ни одного файла
            Exception: При ошибках загрузки документов
        """
        if not self.file_patterns:
            raise ValueError("Список паттернов файлов не может быть пустым")
        documents = []
        loaded_files = 0
        skipped_files = 0
        try:
            # Извлекаем расширения файлов из паттернов
            extensions = []
            for pattern in self.file_patterns:
                # Получаем расширение из паттерна
                if not self._is_supported_format(pattern):
                    logger.warning(f"Неподдерживаемый формат файла: {pattern}")
                    skipped_files += 1
                    continue
                ext = os.path.splitext(pattern)[1].lower()
                if ext:
                    extensions.append(ext)
            # Получаем базовую директорию из первого паттерна
            base_dir = os.path.dirname(self.file_patterns[0])
            # Проверяем существование и доступ к директории
            if not self.check_dir.check_directory_exists():
                logger.warning(f"Пропускаем директорию {base_dir}: директория не существует")
                return documents
            if not self.check_dir.check_directory_access():
                logger.warning(f"Пропускаем директорию {base_dir}: нет доступа к директории")
                return documents
            # Рекурсивно ищем файлы с указанными расширениями
            for root, _, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file_path)[1].lower()
                    # Проверяем, соответствует ли расширение файла одному из искомых
                    if file_ext in extensions:
                        try:
                            # Проверяем права доступа к файлу
                            if not self.check_file.check_file_access(file_path):
                                logger.warning(f"Пропускаем файл без прав доступа: {file_path}")
                                skipped_files += 1
                                continue
                            # Загружаем документ в зависимости от формата
                            if file_path.lower().endswith('.pdf'):
                                loader = PyPDFLoader(file_path)
                            elif file_path.lower().endswith('.txt'):
                                loader = TextLoader(file_path)
                            elif file_path.lower().endswith('.docx'):
                                loader = Docx2txtLoader(file_path)
                            else:
                                logger.warning(f"Неподдерживаемый формат файла: {file_path}")
                                skipped_files += 1
                                continue
                            # Загружаем документ
                            docs = loader.load()
                            if docs:
                                documents.extend(docs)
                                loaded_files += 1
                                logger.info(f"Успешно загружен файл: {file_path}")
                            else:
                                logger.warning(f"Файл не содержит текста: {file_path}")
                                skipped_files += 1
                        except Exception as e:
                            logger.error(f"Ошибка при загрузке файла {file_path}: {str(e)}")
                            skipped_files += 1
                            continue
            if not documents:
                raise FileNotFoundError("Не удалось загрузить ни одного документа")
            logger.info(f"Загрузка завершена. Загружено: {loaded_files}, пропущено: {skipped_files}")
            return documents
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке документов: {str(e)}")
            raise