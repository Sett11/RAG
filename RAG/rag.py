# общие библиотеки
from typing import List, Optional, Dict, Any
from glob import glob
import faiss
import numpy as np
from functools import lru_cache
import os
from pathlib import Path
import shutil
import logging

# библиотеки для работы с LLM
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.retrievers import MergerRetriever
from langchain_openai import ChatOpenAI
from langchain.retrievers import EnsembleRetriever
from sentence_transformers import CrossEncoder, SentenceTransformer
from langchain_community.vectorstores import FAISS

from utils.mylogger import Logger
from config import Config_LLM, docs_dir

# Настройка логирования
logger = Logger('RAG', 'logs/rag.log')

# Отключаем использование transformers
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

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

    def __init__(self, model_name: str = None,
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
                # Используем только sentence-transformers
                import torch
                
                # Устанавливаем устройство
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"Используем устройство: {device}")
                
                # Инициализируем модель
                self.sentence_transformer = SentenceTransformer(
                    "sergeyzh/LaBSE-ru-turbo",
                    device=device
                )
                
                # Создаем класс-обертку для совместимости с LangChain
                class CustomEmbeddings:
                    def __init__(self, model):
                        self.model = model
                    
                    def embed_documents(self, texts):
                        return self.model.encode(texts, normalize_embeddings=True).tolist()
                    
                    def embed_query(self, text):
                        return self.model.encode(text, normalize_embeddings=True).tolist()
                
                self.embedding_model = CustomEmbeddings(self.sentence_transformer)
                logger.info("Модель эмбеддингов успешно инициализирована через SentenceTransformer")

            except Exception as e:
                logger.error(f"Ошибка при инициализации модели эмбеддингов: {str(e)}")
                raise

            # Инициализация cross-encoder для реранжирования
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-encoder успешно инициализирован")

            # Настройка сплиттера текста
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=128,
                length_function=len,
                is_separator_regex=False,
            )
            
            self.vectorstore = None
            self.retriever = None
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

    def _check_directory_exists(self, directory: str) -> bool:
        """
        Проверка существования директории.

        Args:
            directory (str): Путь к директории

        Returns:
            bool: True, если директория существует, иначе False
        """
        try:
            if not os.path.exists(directory):
                logger.error(f"Директория не существует: {directory}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке директории {directory}: {str(e)}")
            return False

    def _check_directory_access(self, directory: str) -> bool:
        """
        Проверка прав доступа к директории.

        Args:
            directory (str): Путь к директории

        Returns:
            bool: True, если есть права на чтение, иначе False
        """
        try:
            if not os.access(directory, os.R_OK):
                logger.error(f"Нет прав на чтение директории: {directory}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к директории {directory}: {str(e)}")
            return False

    def _check_file_access(self, file_path: str) -> bool:
        """
        Проверка прав доступа к файлу.

        Args:
            file_path (str): Путь к файлу

        Returns:
            bool: True, если есть права на чтение, иначе False
        """
        try:
            if not os.access(file_path, os.R_OK):
                logger.error(f"Нет прав на чтение файла: {file_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке прав доступа к файлу {file_path}: {str(e)}")
            return False

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

    def load_documents(self, file_patterns: List[str]) -> List[Document]:
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
        if not file_patterns:
            raise ValueError("Список паттернов файлов не может быть пустым")

        documents = []
        loaded_files = 0
        skipped_files = 0

        try:
            for pattern in file_patterns:
                # Получаем директорию из паттерна
                directory = os.path.dirname(pattern)
                
                # Проверяем существование и доступ к директории
                if not self._check_directory_exists(directory):
                    logger.warning(f"Пропускаем паттерн {pattern}: директория не существует")
                    continue
                
                if not self._check_directory_access(directory):
                    logger.warning(f"Пропускаем паттерн {pattern}: нет доступа к директории")
                    continue

                # Находим все файлы по паттерну
                files = glob(pattern)
                if not files:
                    logger.warning(f"Не найдено файлов по паттерну: {pattern}")
                    continue

                for file_path in files:
                    try:
                        # Проверяем формат файла
                        if not self._is_supported_format(file_path):
                            logger.warning(f"Пропускаем неподдерживаемый формат файла: {file_path}")
                            skipped_files += 1
                            continue

                        # Проверяем права доступа к файлу
                        if not self._check_file_access(file_path):
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

    def process_documents(self, documents: List[Document]) -> List[Document]:
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
        if not documents:
            raise ValueError("Список документов не может быть пустым")

        try:
            processed_docs = []
            skipped_docs = 0

            for doc in documents:
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

    def create_vector_store(self, documents: List[Document]) -> None:
        """
        Создание векторного хранилища из документов.

        Args:
            documents (List[Document]): Список документов для индексации

        Raises:
            ValueError: Если список документов пуст
            Exception: При ошибках создания векторного хранилища
        """
        if not documents:
            raise ValueError("Список документов не может быть пустым")

        try:
            # Разбиваем документы на чанки
            try:
                chunks = self.text_splitter.split_documents(documents)
                logger.info(f"Документы разбиты на {len(chunks)} чанков")
            except Exception as e:
                logger.error(f"Ошибка при разбиении документов на чанки: {str(e)}")
                raise

            # Создаем векторное хранилище
            try:
                # Пробуем стандартный метод создания
                self.vectorstore = FAISS.from_documents(
                    documents=chunks,
                    embedding=self.embedding_model
                )
                logger.info("Векторное хранилище успешно создано стандартным методом")
            except Exception as e:
                logger.warning(f"Не удалось создать векторное хранилище стандартным методом: {str(e)}")
                logger.info("Пробуем создать векторное хранилище вручную")

                try:
                    # Извлекаем тексты и метаданные
                    texts = [doc.page_content for doc in chunks]
                    metadatas = [doc.metadata for doc in chunks]

                    # Получаем эмбеддинги
                    embeddings = self.embedding_model.embed_documents(texts)

                    # Создаем индекс FAISS
                    dimension = len(embeddings[0])
                    index = faiss.IndexFlatL2(dimension)
                    index.add(np.array(embeddings).astype('float32'))

                    # Создаем векторное хранилище
                    self.vectorstore = FAISS(
                        self.embedding_model.embed_query,
                        index,
                        texts,
                        metadatas
                    )
                    logger.info("Векторное хранилище успешно создано вручную")
                except Exception as e:
                    logger.error(f"Ошибка при создании векторного хранилища вручную: {str(e)}")
                    raise

            # Настраиваем ретриверы
            self._setup_retrievers()
            logger.info("Ретриверы успешно настроены")

        except Exception as e:
            logger.error(f"Критическая ошибка при создании векторного хранилища: {str(e)}")
            raise

    def _setup_retrievers(self) -> None:
        """
        Настройка системы ретриверов для поиска документов.

        Raises:
            ValueError: Если векторное хранилище не инициализировано
            Exception: При ошибках настройки ретриверов
        """
        if not self.vectorstore:
            raise ValueError("Векторное хранилище не инициализировано")

        try:
            # Настраиваем базовый ретривер
            try:
                self.base_retriever = self.vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": 20,
                        "score_threshold": 0.7
                    }
                )
                logger.info("Базовый ретривер успешно настроен")
            except Exception as e:
                logger.warning(f"Не удалось настроить базовый ретривер стандартным методом: {str(e)}")
                logger.info("Пробуем настроить базовый ретривер вручную")

                try:
                    # Используем стандартный метод as_retriever вместо FAISSRetriever
                    self.base_retriever = self.vectorstore.as_retriever(
                        search_kwargs={
                            "k": 20,
                            "score_threshold": 0.7
                        }
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


# Инициализация конфигурации и создание экземпляра
try:
    llm_config = Config_LLM()
    gpt = AdvancedRAG(
        llm_config.model_name,
        llm_config.api_key,
        llm_config.base_url,
        llm_config.temperature
    )
    logger.info("RAG система успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка инициализации RAG системы: {str(e)}")
    print(f"Ошибка инициализации RAG системы: {str(e)}")
    print("Пожалуйста, проверьте конфигурацию и зависимости.")
    raise

# Загрузка документов и создание векторного хранилища
try:
    # Проверка существования директории с документами
    if not os.path.exists(docs_dir):
        error_msg = f"Директория с документами не существует: {docs_dir}"
        logger.error(error_msg)
        print(error_msg)
        print("Пожалуйста, создайте директорию или укажите правильный путь в config.py")
        raise FileNotFoundError(error_msg)
    
    # Загрузка документов
    try:
        documents = gpt.load_documents([
            f"{docs_dir}\\*.pdf",
            f"{docs_dir}\\*.txt",
            f"{docs_dir}\\*.docx"
        ])
        print(f"Успешно загружено {len(documents)} документов")
    except Exception as e:
        error_msg = f"Ошибка загрузки документов: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        print("Пожалуйста, проверьте наличие документов в указанной директории.")
        raise
    
    # Обработка документов
    try:
        processed_documents = gpt.process_documents(documents)
        print(f"Успешно обработано {len(processed_documents)} документов")
    except Exception as e:
        error_msg = f"Ошибка обработки документов: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        print("Пожалуйста, проверьте формат документов.")
        raise
    
    # Создание векторного хранилища
    try:
        gpt.create_vector_store(processed_documents)
        print("Векторное хранилище успешно создано")
    except Exception as e:
        error_msg = f"Ошибка создания векторного хранилища: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        print("Пожалуйста, проверьте настройки векторного хранилища.")
        raise
    
    # Тестовый запрос
    try:
        print("Выполняем тестовый запрос...")
        response = gpt.query("Какие документы есть в хранилище?")
        print(f"Ответ: {response}")
    except Exception as e:
        error_msg = f"Ошибка выполнения тестового запроса: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        print("Система инициализирована, но возникла ошибка при выполнении запроса.")
    
except Exception as e:
    logger.error(f"Критическая ошибка: {str(e)}")
    print(f"Критическая ошибка: {str(e)}")
    print("Пожалуйста, проверьте логи для получения дополнительной информации.")
    raise