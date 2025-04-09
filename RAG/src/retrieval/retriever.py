from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from src.embedded.custom_embeddings import CustomEmbeddings
from utils.mylogger import Logger
from config import RAG_CONFIG

logger = Logger('Retriever', 'logs/rag.log')

class Retriever:
    """
    Класс для настройки и использования системы ретриверов для LLM.
    """
    def __init__(self, llm) -> None:
        """
        Инициализация класса.
        
        Args:
        LLM: Объект класса LLM.
        """
        self.llm = llm
        self.vectorstore = llm.vectorstore
        self.embedding_model = CustomEmbeddings(llm.sentence_transformer)

    def setup_retrievers(self) -> None:
        """
        Настройка системы ретриверов для поиска документов.

        Raises:
            ValueError: Если векторное хранилище не инициализировано
            Exception: При ошибках настройки ретриверов
        """
        if not self.vectorstore:
            raise ValueError("Векторное хранилище не инициализировано")
        try:
            # Настраиваем базовый ретривер для LLM
            try:
                self.llm.base_retriever = self.vectorstore.llm.vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs=RAG_CONFIG["search_kwargs"]
                )
                logger.info("Базовый ретривер успешно настроен")
            except Exception as e:
                logger.warning(f"Не удалось настроить базовый ретривер стандартным методом: {str(e)}")
                logger.info("Пробуем настроить базовый ретривер вручную")
                try:
                    # Используем FAISSRetriever
                    self.llm.base_retriever = self.llm.vectorstore.FAISSRetriever(
                        vectorstore=self.vectorstore.llm.vectorstore,
                        search_kwargs=RAG_CONFIG["search_kwargs"]
                    )
                    logger.info("Базовый ретривер успешно настроен вручную")
                except Exception as e:
                    logger.error(f"Ошибка при настройке базового ретривера вручную: {str(e)}")
                    raise
            # Настраиваем фильтр по эмбеддингам для LLM
            try:
                embeddings_filter = EmbeddingsFilter(
                    embeddings=self.embedding_model,
                    similarity_threshold=RAG_CONFIG["similarity_threshold"]
                )
                logger.info("Фильтр по эмбеддингам успешно настроен")
            except Exception as e:
                logger.warning(f"Не удалось настроить фильтр по эмбеддингам: {str(e)}")
                logger.info("Продолжаем работу без фильтра по эмбеддингам")
                embeddings_filter = None
            # Создаем компресионный ретривер для LLM
            try:
                if embeddings_filter:
                    self.llm.retriever = ContextualCompressionRetriever(
                        base_compressor=embeddings_filter,
                        base_retriever=self.llm.base_retriever
                    )
                    logger.info("Компресионный ретривер успешно настроен")
                else:
                    self.llm.retriever = self.llm.base_retriever
                    logger.info("Используется базовый ретривер без фильтрации")
            except Exception as e:
                logger.warning(f"Не удалось создать компресионный ретривер: {str(e)}")
                logger.info("Используем базовый ретривер")
                self.llm.retriever = self.llm.base_retriever
        except Exception as e:
            logger.error(f"Критическая ошибка при настройке ретриверов: {str(e)}")
            raise

