import os
from typing import List, Optional
from glob import glob

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.retrievers.merger_redundant_filter import MergerRetriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.retrievers import EnsembleRetriever
from sentence_transformers import CrossEncoder
import numpy as np

class AdvancedRAG:
    def __init__(self, model_name: str = "llama3-8b-8192", groq_api_key: Optional[str] = None):
        # Инициализация модели и компонентов
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=groq_api_key or os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            temperature=0.3
        )
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sergeyzh/LaBSE-ru-turbo",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128,
            length_function=len,
            is_separator_regex=False,
        )
        self.vectorstore = None
        self.retriever = None
        self.setup_prompts()

    def setup_prompts(self):
        # Улучшенные промпты с многошаговым reasoning
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

    def load_documents(self, file_patterns: List[str]) -> List[Document]:
        """Загрузка документов разных форматов с обработкой ошибок"""
        documents = []
        for pattern in file_patterns:
            for file_path in glob(pattern):
                try:
                    if file_path.endswith('.pdf'):
                        loader = PyPDFLoader(file_path)
                    elif file_path.endswith('.txt'):
                        loader = TextLoader(file_path, encoding='utf-8')
                    elif file_path.endswith('.docx'):
                        loader = Docx2txtLoader(file_path)
                    else:
                        print(f"Пропущен неподдерживаемый формат: {file_path}")
                        continue
                    
                    docs = loader.load()
                    documents.extend(docs)
                    print(f"Успешно загружен: {file_path}")
                except Exception as e:
                    print(f"Ошибка загрузки {file_path}: {str(e)}")
        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Расширенная обработка документов перед разбиением"""
        processed = []
        for doc in documents:
            # Базовая очистка текста
            doc.page_content = doc.page_content.replace('\x00', '').strip()
            if len(doc.page_content) > 50:  # Игнорируем слишком короткие документы
                processed.append(doc)
        return processed

    def create_vector_store(self, documents: List[Document]):
        """Создание векторного хранилища с персистентностью"""
        if not documents:
            raise ValueError("Нет документов для индексации")
        
        # Разбиение на чанки с учетом структуры документа
        splits = self.text_splitter.split_documents(documents)
        
        # Создание FAISS индекса с возможностью сохранения на диск
        self.vectorstore = FAISS.from_documents(
            splits,
            self.embedding_model
        )
        self._setup_retrievers()

    def _setup_retrievers(self):
        """Настройка сложной системы извлечения с реранжированием"""
        base_retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 20,
                "score_threshold": 0.7,
                "filter": {"source": None}  # Можно добавить фильтрацию по метаданным
            }
        )
        
        # Компрессия и фильтрация результатов
        embeddings_filter = EmbeddingsFilter(
            embeddings=self.embedding_model,
            similarity_threshold=0.75
        )
        
        # Комбинированный ретривер
        self.retriever = ContextualCompressionRetriever(
            base_compressor=embeddings_filter,
            base_retriever=base_retriever
        )

    def rerank_documents(self, query: str, documents: List[Document]) -> List[Document]:
        """Реранжирование результатов с помощью cross-encoder"""
        if not documents:
            return []
        
        # Подготовка пар (запрос, документ) для cross-encoder
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Получение скоринга релевантности
        scores = self.cross_encoder.predict(pairs)
        
        # Сортировка документов по убыванию релевантности
        sorted_indices = np.argsort(scores)[::-1]
        return [documents[i] for i in sorted_indices[:10]]  # Возвращаем топ-10

    def format_context(self, docs: List[Document]) -> str:
        """Умное форматирование контекста для промпта"""
        if not docs:
            return "Контекст отсутствует"
        
        # Группировка по источникам
        sources = {}
        for doc in docs:
            source = doc.metadata.get('source', 'Неизвестный источник')
            if source not in sources:
                sources[source] = []
            sources[source].append(doc.page_content)
        
        # Форматирование с указанием источников
        formatted = []
        for source, contents in sources.items():
            formatted.append(f"### Источник: {source}")