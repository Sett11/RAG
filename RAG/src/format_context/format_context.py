from typing import List
from langchain.schema import Document
from utils.mylogger import Logger
from config import RAG_CONFIG

logger = Logger('FormatContext', 'logs/rag.log')

class FormatContext:
    def __init__(self, llm) -> None:
        self.llm = llm
        # Максимальная длина контекста в символах (примерно 4000 токенов)
        self.max_context_length = int(RAG_CONFIG.get("max_context_length", 16000))

    def format_context(self, docs: List[Document]) -> str:
        """
        Форматирование контекста из документов для LLM.

        Args:
            docs (List[Document]): Список документов

        Returns:
            str: Отформатированный контекст

        Raises:
            ValueError: Если список документов пуст
            Exception: При ошибках форматирования
        """
        if not docs:
            raise ValueError("Список документов не может быть пустым")
        try:
            # Подготавливаем контекст
            try:
                context_parts = []
                total_length = 0
                for i, doc in enumerate(docs, 1):
                    # Очищаем текст от лишних пробелов и переносов строк
                    cleaned_text = ' '.join(doc.page_content.split())
                    # Добавляем метаданные, если они есть
                    metadata_str = ""
                    if doc.metadata:
                        source = doc.metadata.get('source', 'Неизвестный источник')
                        page = doc.metadata.get('page', '')
                        metadata_str = f" [Источник: {source}"
                        if page:
                            metadata_str += f", Страница: {page}"
                        metadata_str += "]"
                    # Форматируем часть контекста
                    context_part = f"Документ {i}{metadata_str}:\n{cleaned_text}\n"
                    
                    # Проверяем, не превысит ли добавление этой части максимальную длину
                    if total_length + len(context_part) > self.max_context_length:
                        logger.warning(f"Достигнута максимальная длина контекста ({self.max_context_length} символов)")
                        break
                    
                    context_parts.append(context_part)
                    total_length += len(context_part)
                
                # Объединяем все части
                context = "\n".join(context_parts)
                logger.info(f"Контекст успешно отформатирован, длина: {len(context)} символов")
                return context
            except Exception as e:
                logger.error(f"Ошибка при форматировании контекста: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Критическая ошибка при форматировании контекста: {str(e)}")
            raise