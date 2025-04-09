# общие библиотеки
from typing import Optional
# библиотеки для работы с LLM
from langchain_openai import ChatOpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer
import torch
# локальные библиотеки
from utils.mylogger import Logger
from src.retrieval.retriever import Retriever
from src.date.vector_store import VectorStore
from src.promts.promts import Promts
from src.format_context.format_context import FormatContext
# Настройка логирования
logger = Logger('RAG', 'logs/rag.log')

class AdvancedRAG:
    """
    Реализация RAG (Retrieval-Augmented Generation) системы.
    
    Особенности:
    - Поддержка множества форматов документов (PDF, TXT, DOCX)
    - Векторное хранилище на основе FAISS
    - Двухэтапное извлечение с реранжированием
    - Кэширование эмбеддингов
    - Расширенная обработка ошибок
    """
    def __init__(self,
                 model_name: str = None,
                 api_key: Optional[str] = None,
                 base_url: str = None,
                 temperature: float = 0.3):
        """
        Инициализация RAG системы.

        Args:
            model_name (str): Название модели LLM
            api_key (Optional[str]): API ключ для доступа к LLM
            base_url (str): Базовый URL для API
            temperature (float): Температура генерации (0.0 - 1.0)

        Raises:
            ValueError: Если model_name не указан
            Exception: При ошибках инициализации компонентов
        """
        if not model_name:
            raise ValueError("model_name не может быть пустым")
        if not api_key:
            raise ValueError("api_key не может быть пустым")
        if not base_url:
            raise ValueError("base_url не может быть пустым")
        try:
            # Инициализация LLM
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            logger.info(f"LLM модель {model_name} успешно инициализирована")
            # Инициализация модели эмбеддингов
            try:
                # Используем sentence-transformers
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"Используем устройство: {device}")
                # Инициализируем модель
                self.sentence_transformer = SentenceTransformer(
                    "sergeyzh/LaBSE-ru-turbo",
                    device=device
                )
            except Exception as e:
                logger.error(f"Ошибка при инициализации модели эмбеддингов: {str(e)}")
                raise
            # Инициализируем cross-encoder для реранжирования
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-encoder успешно инициализирован")
            self.vectorstore = VectorStore(self)
            self.retriever = Retriever(self)
            self.promts = Promts(self)
            self.format_context = FormatContext(self)
        except Exception as e:
            logger.error(f"Ошибка инициализации компонентов: {str(e)}")
            raise

    def query(self, question: str) -> str:
        """
        Обработка запроса пользователя и генерация ответа.

        Args:
            question (str): Вопрос пользователя

        Returns:
            str: Ответ на вопрос

        Raises:
            ValueError: Если вопрос пустой
            Exception: При ошибках обработки запроса
        """
        if not question or not question.strip():
            raise ValueError("Вопрос не может быть пустым")
        try:
            # Проверяем инициализацию ретривера
            if not hasattr(self, 'retriever') or not self.retriever:
                error_msg = "Ретривер не инициализирован"
                logger.error(error_msg)
                return "Извините, система не готова к обработке запросов. Пожалуйста, проверьте логи."
            # Получаем релевантные документы
            try:
                question = question.lower()
                # Используем базовый ретривер
                relevant_docs = self.retriever.get_relevant_documents(question)
                
                if not relevant_docs:
                    logger.warning("Не найдено релевантных документов")
                    return "Извините, не удалось найти информацию по вашему запросу."
                logger.info(f"Найдено {len(relevant_docs)} релевантных документов")
            except Exception as e:
                logger.error(f"Ошибка при поиске релевантных документов: {str(e)}")
                return "Извините, произошла ошибка при поиске информации. Пожалуйста, попробуйте позже."
            # Реранжируем документы
            try:
                reranked_docs = self.promts.rerank_documents(question, relevant_docs)
                if not reranked_docs:
                    logger.warning("Реранжирование не вернуло документов")
                    reranked_docs = relevant_docs
                logger.info(f"Документы успешно реранжированы")
            except Exception as e:
                logger.warning(f"Ошибка при реранжировании документов: {str(e)}")
                logger.info("Используем исходные документы без реранжирования")
                reranked_docs = relevant_docs
            # Форматируем контекст
            try:
                context = self.format_context.format_context(reranked_docs)
                if not context:
                    logger.warning("Не удалось сформатировать контекст")
                    return "Извините, не удалось обработать найденную информацию."
                logger.info("Контекст успешно сформатирован")
            except Exception as e:
                logger.error(f"Ошибка при форматировании контекста: {str(e)}")
                return "Извините, произошла ошибка при обработке информации. Пожалуйста, попробуйте позже."
            # Генерируем ответ
            try:
                # Проверяем инициализацию промптов
                if not hasattr(self, 'main_prompt') or not self.main_prompt:
                    logger.warning("Промпты не инициализированы, используем стандартный промпт")
                    response = self.llm.invoke(
                        f"Контекст:\n{context}\n\nВопрос: {question}"
                    )
                else:
                    response = self.llm.invoke(
                        self.main_prompt.format(
                            context=context,
                            question=question
                        )
                    )            
                if not response or not response.content:
                    logger.warning("LLM вернул пустой ответ")
                    return "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте переформулировать вопрос."
                logger.info("Ответ успешно сгенерирован")
                return response.content
            except Exception as e:
                logger.error(f"Ошибка при генерации ответа: {str(e)}")
                return "Извините, произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке запроса: {str(e)}")
            return "Извините, произошла критическая ошибка. Пожалуйста, проверьте логи и попробуйте позже."