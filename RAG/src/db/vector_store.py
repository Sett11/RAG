from langchain_core.documents import Document
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
import numpy as np

from src.rag import AdvancedRAG
from utils.mylogger import Logger
from src.work_models.custom_embeddings import CustomEmbeddings

logger = Logger('VectorStore', 'logs/rag.log')

class VectorStore:
    def __init__(self, llm: AdvancedRAG) -> None:
        self.llm = llm
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.embedding_model = CustomEmbeddings(Embeddings)

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
                self.llm.vectorstore = FAISS.from_documents(
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
                    index = FAISS.IndexFlatL2(dimension)
                    index.add(np.array(embeddings).astype('float32'))
                    # Создаем векторное хранилище
                    self.llm.vectorstore = FAISS(
                        self.embedding_model.embed_query,
                        index,
                        texts,
                        metadatas
                    )
                    logger.info("Векторное хранилище успешно создано вручную")
                except Exception as e:
                    logger.error(f"Ошибка при создании векторного хранилища вручную: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Критическая ошибка при создании векторного хранилища: {str(e)}")
            raise