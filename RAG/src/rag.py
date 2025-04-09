# общие библиотеки
from typing import List, Optional
import numpy as np
from functools import lru_cache
import os
# библиотеки для работы с LLM
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_openai import ChatOpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer
import torch
# локальные библиотеки
from utils.mylogger import Logger
from src.work_models.retriever import Retriever
from src.db.vector_store import VectorStore
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
            self.retriever.setup_retrievers()
            self.setup_prompts()
        except Exception as e:
            logger.error(f"Ошибка инициализации компонентов: {str(e)}")
            raise

    def setup_prompts(self) -> None:
        """
        Настройка промптов для LLM.
        
        Создает два основных промпта:
        1. main_prompt - для генерации ответов
        2. verification_prompt - для проверки качества ответов
        """
        try:
            self.main_prompt = ChatPromptTemplate.from_messages([
                ("system", """Ты - экспертный русскоязычный AI-ассистент. Анализируй вопрос и контекст, следуя шагам:
1. Определи ключевые аспекты вопроса
2. Выдели релевантные части контекста
3. Сформулируй точный ответ
4. Если нужно, укажи источник информации

Контекст:
{context}

Вопрос: {question}"""),
                ("human", "{question}")
            ])
            
            self.verification_prompt = ChatPromptTemplate.from_messages([
                ("system", """Проверь соответствие ответа контексту. Ответ должен:
1. Быть основан только на контексте
2. Не содержать вымышленных фактов
3. Быть точным и конкретным

Контекст: {context}
Ответ для проверки: {response}"""),
                ("human", "Требуется ли корректировка ответа? Если да, предложи улучшенную версию.")
            ])
            logger.info("Промпты успешно настроены")
        except Exception as e:
            logger.error(f"Ошибка настройки промптов: {str(e)}")
            raise

    def rerank_documents(self, question: str, documents: List[Document]) -> List[Document]:
        """
        Реранжирование документов с использованием cross-encoder.

        Args:
            question (str): Вопрос пользователя
            documents (List[Document]): Список документов для реранжирования

        Returns:
            List[Document]: Отсортированный список документов

        Raises:
            ValueError: Если список документов пуст
            Exception: При ошибках реранжирования
        """
        if not documents:
            raise ValueError("Список документов не может быть пустым")
        try:
            # Подготавливаем пары вопрос-документ
            try:
                pairs = [(question, doc.page_content) for doc in documents]
                logger.info(f"Подготовлено {len(pairs)} пар для реранжирования")
            except Exception as e:
                logger.error(f"Ошибка при подготовке пар для реранжирования: {str(e)}")
                raise
            # Получаем оценки релевантности
            try:
                scores = self.cross_encoder.predict(pairs)
                logger.info("Оценки релевантности успешно получены")
            except Exception as e:
                logger.error(f"Ошибка при получении оценок релевантности: {str(e)}")
                raise
            # Сортируем документы по оценкам
            try:
                # Создаем список пар (документ, оценка)
                doc_score_pairs = list(zip(documents, scores))
                # Сортируем по убыванию оценки
                doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
                # Извлекаем только документы
                reranked_docs = [doc for doc, _ in doc_score_pairs]
                logger.info("Документы успешно реранжированы")
                return reranked_docs
            except Exception as e:
                logger.error(f"Ошибка при сортировке документов: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Критическая ошибка при реранжировании документов: {str(e)}")
            raise

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
                    context_parts.append(context_part)
                # Объединяем все части
                context = "\n".join(context_parts)
                logger.info("Контекст успешно отформатирован")
                return context
            except Exception as e:
                logger.error(f"Ошибка при форматировании контекста: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Критическая ошибка при форматировании контекста: {str(e)}")
            raise

    @lru_cache(maxsize=1000)
    def get_embedding(self, text: str) -> List[float]:
        """
        Получение эмбеддинга для текста с кэшированием.

        Args:
            text (str): Текст для получения эмбеддинга

        Returns:
            List[float]: Вектор эмбеддинга

        Raises:
            ValueError: Если текст пустой
        """
        if not text.strip():
            raise ValueError("Текст не может быть пустым")
        try:
            return self.embedding_model.embed_query(text)
        except Exception as e:
            logger.error(f"Ошибка получения эмбеддинга: {str(e)}")
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
            if not self.retriever:
                error_msg = "Ретривер не инициализирован"
                logger.error(error_msg)
                return "Извините, система не готова к обработке запросов. Пожалуйста, проверьте логи."
            # Получаем релевантные документы
            try:
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
                reranked_docs = self.rerank_documents(question, relevant_docs)
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
                context = self.format_context(reranked_docs)
                if not context:
                    logger.warning("Не удалось сформатировать контекст")
                    return "Извините, не удалось обработать найденную информацию."
                logger.info("Контекст успешно сформатирован")
            except Exception as e:
                logger.error(f"Ошибка при форматировании контекста: {str(e)}")
                return "Извините, произошла ошибка при обработке информации. Пожалуйста, попробуйте позже."
            # Генерируем ответ
            try:
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