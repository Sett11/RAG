from langchain_core.documents import Document
from typing import List
from utils.mylogger import Logger

logger = Logger('ProcessDocuments', 'logs/rag.log')

class ProcessDocuments:
    """
    Класс для обработки и подготовки документов перед индексацией.
    
    Этот класс предоставляет функциональность для:
    - Валидации содержимого документов
    - Очистки текста от лишних пробелов и переносов строк
    - Фильтрации документов с недостаточным количеством текста
    - Сохранения метаданных документов
    
    Attributes:
        documents (List[Document]): Список документов для обработки
    """
    def __init__(self, documents: List[Document]) -> None:
        """
        Инициализация класса ProcessDocuments.
        
        Args:
            documents (List[Document]): Список документов для обработки
        """
        logger.info("Инициализация класса ProcessDocuments")
        self.documents = documents
        logger.debug(f"Получено документов для обработки: {len(documents)}")

    def process_documents(self) -> List[Document]:
        """
        Обработка и подготовка документов для индексации.
        
        Процесс обработки:
        1. Проверка наличия текста в документе
        2. Очистка текста от лишних пробелов и переносов строк
        3. Проверка минимальной длины текста
        4. Создание нового документа с очищенным текстом
        
        Returns:
            List[Document]: Список обработанных документов
            
        Raises:
            ValueError: Если список документов пуст или не удалось обработать ни одного документа
            Exception: При ошибках обработки документов
        """
        logger.info("Начало обработки документов")
        
        if not self.documents:
            error_msg = "Список документов не может быть пустым"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            processed_docs = []
            skipped_docs = 0
            
            for doc in self.documents:
                try:
                    # Проверяем наличие текста
                    if not doc.page_content or not doc.page_content.strip():
                        logger.warning("Пропускаем документ без текста")
                        skipped_docs += 1
                        continue
                        
                    # Очищаем текст от лишних пробелов и переносов строк
                    cleaned_text = ' '.join(doc.page_content.split())
                    
                    # Проверяем длину текста после очистки
                    if len(cleaned_text) < 10:  # Минимальная длина текста
                        logger.warning("Пропускаем документ с недостаточным количеством текста")
                        skipped_docs += 1
                        continue
                        
                    # Создаем новый документ с очищенным текстом
                    processed_doc = Document(
                        page_content=cleaned_text,
                        metadata=doc.metadata
                    )
                    processed_docs.append(processed_doc)
                    logger.debug(f"Документ успешно обработан: {doc.metadata.get('source', 'unknown')}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке документа: {str(e)}")
                    skipped_docs += 1
                    continue
                    
            if not processed_docs:
                error_msg = "Не удалось обработать ни одного документа"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            logger.info(f"Обработка завершена. Обработано: {len(processed_docs)}, пропущено: {skipped_docs}")
            return processed_docs
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке документов: {str(e)}")
            raise