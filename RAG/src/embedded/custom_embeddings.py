from langchain.embeddings.base import Embeddings
from utils.mylogger import Logger

# Инициализация логгера для отслеживания работы с эмбеддингами
logger = Logger('CustomEmbeddings', 'logs/rag.log')

class CustomEmbeddings(Embeddings):
    """
    Пользовательский класс для создания эмбеддингов текста.
    
    Этот класс является оберткой для моделей sentence-transformers, 
    обеспечивающей совместимость с интерфейсом LangChain Embeddings.
    
    Особенности:
    - Использует предобученные модели sentence-transformers
    - Поддерживает нормализацию эмбеддингов
    - Оптимизирован для работы с русскоязычными текстами
    - Обеспечивает единый интерфейс для батч-обработки и одиночных запросов
    
    Attributes:
        model: Модель sentence-transformers для генерации эмбеддингов
            Должна поддерживать методы encode() и normalize_embeddings
        
    Methods:
        embed_documents: Создает эмбеддинги для списка документов
        embed_query: Создает эмбеддинг для одного запроса
    """
    def __init__(self, model):
        """
        Инициализация класса CustomEmbeddings.
        
        Args:
            model: Модель sentence-transformers для генерации эмбеддингов
                Должна быть экземпляром класса SentenceTransformer
                и поддерживать русскоязычные тексты
        """
        self.model = model
        logger.info(f"Инициализация класса CustomEmbeddings. Модель: {model}")
        
    def embed_documents(self, texts):
        """
        Создает эмбеддинги для списка текстовых документов.
        
        Процесс:
        1. Принимает список текстовых документов
        2. Преобразует их в векторные представления
        3. Нормализует векторы для улучшения качества сравнения
        
        Args:
            texts (List[str]): Список текстовых документов
                Каждый документ должен быть строкой
                Поддерживаются документы на русском языке
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов для каждого документа
                Каждый вектор - список чисел с плавающей точкой
                Все векторы нормализованы (длина = 1)
        """
        # Нормализуем эмбеддинги для улучшения качества сравнения
        return self.model.encode(texts, normalize_embeddings=True).tolist()
        
    def embed_query(self, text):
        """
        Создает эмбеддинг для одного текстового запроса.
        
        Процесс:
        1. Принимает один текстовый запрос
        2. Преобразует его в векторное представление
        3. Нормализует вектор для согласованности с embed_documents
        
        Args:
            text (str): Текстовый запрос
                Должен быть строкой
                Поддерживаются запросы на русском языке
            
        Returns:
            List[float]: Вектор эмбеддинга для запроса
                Список чисел с плавающей точкой
                Вектор нормализован (длина = 1)
        """
        # Нормализуем эмбеддинг для согласованности с embed_documents
        return self.model.encode(text, normalize_embeddings=True).tolist() 