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
    - Верификация качества ответов
    
    Компоненты системы:
    1. LLM (Language Model) - основная модель для генерации ответов
    2. Sentence Transformer - модель для создания эмбеддингов
    3. Cross-Encoder - модель для реранжирования документов
    4. Vector Store - хранилище векторных представлений документов
    5. Retriever - компонент для поиска релевантных документов
    6. Prompts - управление промптами для LLM
    7. Format Context - форматирование контекста для LLM
    """
    def __init__(self,
                 model_name: str = None,
                 api_key: Optional[str] = None,
                 base_url: str = None,
                 temperature: float = 0.3):
        """
        Инициализация RAG системы.

        Args:
            model_name (str): Название модели LLM (например, 'gpt-3.5-turbo')
            api_key (Optional[str]): API ключ для доступа к LLM
            base_url (str): Базовый URL для API (для локальных моделей)
            temperature (float): Температура генерации (0.0 - 1.0)
                               Меньшие значения дают более детерминированные ответы

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
            # Инициализация LLM - основной модели для генерации ответов
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            logger.info(f"LLM модель {model_name} успешно инициализирована")
            
            # После инициализации self.llm объект класса AdvancedRAG получает доступ к методам LLM:
            # - invoke: метод для отправки запросов к LLM с использованием промптов
            # - generate: метод для генерации ответов с дополнительными параметрами
            # - stream: метод для потоковой генерации ответов
            # - batch: метод для пакетной обработки запросов
            # Эти методы используются в методе query() класса AdvancedRAG для генерации ответов
            # на вопросы пользователя и в методе verification_query() для проверки качества ответов
            
            # Инициализация модели эмбеддингов - для векторного представления текста
            try:
                # Используем sentence-transformers для создания эмбеддингов
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"Используем устройство: {device}")
                # Инициализируем модель для русского языка
                self.sentence_transformer = SentenceTransformer(
                    "sergeyzh/LaBSE-ru-turbo",
                    device=device
                )
            except Exception as e:
                logger.error(f"Ошибка при инициализации модели эмбеддингов: {str(e)}")
                raise
                
            # После инициализации self.sentence_transformer объект класса AdvancedRAG получает доступ к методам:
            # - encode: метод для создания векторных представлений текста
            # - normalize_embeddings: параметр для нормализации векторов
            # Эта модель используется в классе CustomEmbeddings для создания эмбеддингов документов и запросов,
            # которые затем используются в VectorStore для индексации и поиска документов
                
            # Инициализируем cross-encoder для реранжирования документов
            # Эта модель помогает определить наиболее релевантные документы
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-encoder успешно инициализирован")
            
            # После инициализации self.cross_encoder объект класса AdvancedRAG получает доступ к методам:
            # - predict: метод для оценки релевантности пар вопрос-документ
            # Эта модель используется в классе Promts в методе rerank_documents() для реранжирования
            # документов по их релевантности вопросу пользователя, что улучшает качество поиска
            
            # Инициализация компонентов системы
            self.vectorstore = VectorStore(self)  # Хранилище векторных представлений
            # После инициализации self.vectorstore объект класса AdvancedRAG получает доступ к методам:
            # - create_vector_store: метод для создания векторного хранилища из документов
            # - text_splitter: объект для разбиения документов на чанки
            # - embedding_model: объект для создания эмбеддингов
            # Этот компонент используется в методе setting_up_LLM() в файле start_rag.py для создания
            # векторного хранилища из обработанных документов, что позволяет быстро находить релевантные
            # документы при запросах пользователя
            
            self.retriever = Retriever(self)      # Поиск релевантных документов
            # После инициализации self.retriever объект класса AdvancedRAG получает доступ к методам:
            # - setup_retrievers: метод для настройки системы ретриверов
            # - get_relevant_documents: метод для поиска релевантных документов
            # Этот компонент используется в методе setting_up_LLM() в файле start_rag.py для настройки
            # системы ретриверов, которая используется в методе query() для поиска релевантных документов
            # по запросу пользователя
            
            self.promts = Promts(self)            # Управление промптами
            # После вызова метода setup_prompts() класса Promts объекту класса AdvancedRAG 
            # будут присвоены следующие свойства:
            # - main_prompt: основной промпт для используемой LLM, который определяет
            #   структуру и формат ответа, включая анализ контекста и генерацию ответа
            # - verification_prompt: промпт для проверки качества ответа модели,
            #   который оценивает соответствие ответа контексту и исходному вопросу
            
            self.format_context = FormatContext(self)  # Форматирование контекста
            # После инициализации self.format_context объект класса AdvancedRAG получает доступ к методам:
            # - format_context: метод для форматирования контекста из документов для LLM
            # - max_context_length: максимальная длина контекста в символах
            # Этот компонент используется в методе query() для форматирования контекста из найденных
            # документов, который затем передается в LLM для генерации ответа
            
        except Exception as e:
            logger.error(f"Ошибка инициализации компонентов: {str(e)}")
            raise

    def extract_answer(self, response: str) -> str:
        """
        Извлекает точный ответ из полного ответа модели.
        
        Процесс извлечения:
        1. Проверяет наличие тегов <perfect_answer> и </perfect_answer>
        2. Если теги найдены, извлекает текст между ними
        3. Если теги не найдены, проверяет наличие тегов <answer> и </answer>
        4. Если теги найдены, извлекает текст между ними
        5. Если ничего не найдено, возвращает строку "Ответ не найден"
        
        Args:
            response (str): Полный ответ модели
            
        Returns:
            str: Извлеченный точный ответ
        """
        try:
            # Проверяем наличие тегов <perfect_answer> и </perfect_answer>
            start_tag = "<perfect_answer>"
            end_tag = "</perfect_answer>"
            start_index = response.find(start_tag)
            end_index = response.find(end_tag)
            if start_index != -1 and end_index != -1:
                logger.info("Найден улучшенный ответ")
                return response[start_index + len(start_tag):end_index]

            # Проверяем наличие тегов <answer> и </answer>
            start_tag = "<answer>"
            end_tag = "</answer>"
            start_index = response.find(start_tag)
            end_index = response.find(end_tag)
            if start_index != -1 and end_index != -1:
                logger.info("Найден ответ")
                return response[start_index + len(start_tag):end_index]
            
            logger.info("Ответ не найден")
            return "Ответ не найден"
        
        except Exception as e:
            logger.error(f"Ошибка при извлечении точного ответа: {str(e)}")
            return "Ответ не найден"

    def verification_query(self, question: str, response: str, context: str) -> tuple[bool, str]:
        """
        Проверяет качество сгенерированного ответа.

        Процесс верификации:
        1. Проверяет наличие промпта верификации
        2. Отправляет запрос к LLM с контекстом, вопросом и ответом
        3. Возвращает ответ верификатора


        Args:
            question (str): Исходный вопрос пользователя
            response (str): Сгенерированный ответ
            context (str): Контекст, использованный для генерации

        Returns:
            str: Ответ модели
        """
        try:
            if not hasattr(self, 'verification_prompt'):
                logger.warning("Промпт верификации не инициализирован")
                return response

            verification_response = self.llm.invoke(
                self.verification_prompt.format(
                    context=context,
                    question=question,
                    response=response
                )
            )

            if not verification_response or not verification_response.content:
                logger.warning("Верификатор вернул пустой ответ")
                return response

            return verification_response.content

        except Exception as e:
            logger.error(f"Ошибка при верификации ответа: {str(e)}")
            return response

    def query(self, question: str) -> str:
        """
        Обрабатывает запрос пользователя.

        Процесс обработки запроса:
        1. Поиск релевантных документов
        2. Переранжирование документов
        3. Форматирование контекста
        4. Генерация ответа с помощью LLM
        5. Верификация качества ответа
        6. При необходимости корректировка ответа

        Args:
            question (str): Вопрос пользователя

        Returns:
            str: Ответ модели
        """
        try:
            if not question.strip():
                raise ValueError("Вопрос не может быть пустым")

            if not self.retriever:
                logger.error("Retriever не инициализирован")
                return "Ошибка: система не готова к работе"

            # Поиск релевантных документов
            docs = self.retriever.get_relevant_documents(question)
            if not docs:
                logger.warning("Не найдено релевантных документов")
                return "Извините, я не нашел информации по вашему вопросу"

            # Переранжирование документов
            reranked_docs = self.promts.rerank_documents(question, docs)
            if not reranked_docs:
                logger.warning("Не удалось переранжировать документы")
                return "Извините, произошла ошибка при обработке документов"

            # Форматирование контекста
            context = self.format_context.format_context(reranked_docs)
            if not context:
                logger.warning("Не удалось отформатировать контекст")
                return "Извините, произошла ошибка при подготовке контекста"

            # Генерация ответа
            response = self.llm.invoke(
                self.main_prompt.format(
                    context=context,
                    question=question
                )
            )

            if not response or not response.content:
                logger.warning("LLM вернул пустой ответ")
                return "Извините, произошла ошибка при генерации ответа"

            logger.info(f"Изначальный ответ: {response.content}")
            improved_response = self.verification_query(
                question=question,
                response=response.content,
                context=context
            )
            logger.info(f"Улучшенный ответ: {improved_response}")
            exact_answer = self.extract_answer(improved_response)
            logger.info(f"Точный ответ: {exact_answer}")
            return exact_answer

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {str(e)}")
            return f"Произошла ошибка: {str(e)}"