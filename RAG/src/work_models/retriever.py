from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.embeddings.base import Embeddings
from src.rag import AdvancedRAG
from src.work_models.custom_embeddings import CustomEmbeddings
from utils.mylogger import Logger

logger = Logger('Retriever', 'logs/rag.log')

class Retriever:
    def __init__(self, llm: AdvancedRAG) -> None:
        self.llm = llm
        self.vectorstore = self.llm.vectorstore
        self.embedding_model = CustomEmbeddings(Embeddings)

    def setup_retrievers(self) -> None:
        """
        Настройка системы ретриверов для поиска документов.

        Raises:
            ValueError: Если векторное хранилище не инициализировано
            Exception: При ошибках настройки ретриверов
        """
        if not self.vectorstore:
            raise ValueError("Векторное хранилище не инициализировано")
        search_kwargs = {
            "k": 20,
            "score_threshold": 0.5
        }
        try:
            # Настраиваем базовый ретривер
            try:
                self.base_retriever = self.vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs=search_kwargs
                )
                logger.info("Базовый ретривер успешно настроен")
            except Exception as e:
                logger.warning(f"Не удалось настроить базовый ретривер стандартным методом: {str(e)}")
                logger.info("Пробуем настроить базовый ретривер вручную")
                try:
                    # Используем FAISSRetriever
                    self.base_retriever = self.vectorstore.FAISSRetriever(
                        search_kwargs=search_kwargs
                    )
                    logger.info("Базовый ретривер успешно настроен вручную")
                except Exception as e:
                    logger.error(f"Ошибка при настройке базового ретривера вручную: {str(e)}")
                    raise
            # Настраиваем фильтр по эмбеддингам
            try:
                embeddings_filter = EmbeddingsFilter(
                    embeddings=self.embedding_model,
                    similarity_threshold=0.75
                )
                logger.info("Фильтр по эмбеддингам успешно настроен")
            except Exception as e:
                logger.warning(f"Не удалось настроить фильтр по эмбеддингам: {str(e)}")
                logger.info("Продолжаем работу без фильтра по эмбеддингам")
                embeddings_filter = None
            # Создаем компресионный ретривер
            try:
                if embeddings_filter:
                    self.retriever = ContextualCompressionRetriever(
                        base_compressor=embeddings_filter,
                        base_retriever=self.base_retriever
                    )
                    logger.info("Компресионный ретривер успешно настроен")
                else:
                    self.retriever = self.base_retriever
                    logger.info("Используется базовый ретривер без фильтрации")
            except Exception as e:
                logger.warning(f"Не удалось создать компресионный ретривер: {str(e)}")
                logger.info("Используем базовый ретривер")
                self.retriever = self.base_retriever
        except Exception as e:
            logger.error(f"Критическая ошибка при настройке ретриверов: {str(e)}")
            raise

