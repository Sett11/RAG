from langchain_core.documents import Document
from typing import List
from utils.mylogger import Logger

logger = Logger('ProcessDocuments', 'logs/rag.log')

class ProcessDocuments:
    def __init__(self, documents: List[Document]) -> None:
        self.documents = documents

    def process_documents(self) -> List[Document]:
        """
        Обработка и подготовка документов для индексации.

        Args:
            documents (List[Document]): Список документов для обработки

        Returns:
            List[Document]: Список обработанных документов

        Raises:
            ValueError: Если список документов пуст
            Exception: При ошибках обработки документов
        """
        if not self.documents:
            raise ValueError("Список документов не может быть пустым")
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
                except Exception as e:
                    logger.error(f"Ошибка при обработке документа: {str(e)}")
                    skipped_docs += 1
                    continue
            if not processed_docs:
                raise ValueError("Не удалось обработать ни одного документа")
            logger.info(f"Обработка завершена. Обработано: {len(processed_docs)}, пропущено: {skipped_docs}")
            return processed_docs
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке документов: {str(e)}")
            raise