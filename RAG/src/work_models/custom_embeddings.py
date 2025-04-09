from langchain.embeddings.base import Embeddings
from utils.mylogger import Logger

logger = Logger('CustomEmbeddings', 'logs/rag.log')

class CustomEmbeddings(Embeddings):
    """
    Пользовательский класс для создания эмбеддингов текста.
    
    Этот класс является оберткой для моделей sentence-transformers, 
    обеспечивающей совместимость с интерфейсом LangChain Embeddings.
    
    Attributes:
        model: Модель sentence-transformers для генерации эмбеддингов
        
    Methods:
        embed_documents: Создает эмбеддинги для списка документов
        embed_query: Создает эмбеддинг для одного запроса
    """
    def __init__(self, model):
        """
        Инициализация класса CustomEmbeddings.
        
        Args:
            model: Модель sentence-transformers для генерации эмбеддингов
        """
        self.model = model
        logger.info(f"Инициализация класса CustomEmbeddings. Модель: {model}")
        
    def embed_documents(self, texts):
        """
        Создает эмбеддинги для списка текстовых документов.
        
        Args:
            texts (List[str]): Список текстовых документов
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов для каждого документа
        """
        # Нормализуем эмбеддинги для улучшения качества сравнения
        return self.model.encode(texts, normalize_embeddings=True).tolist()
        
    def embed_query(self, text):
        """
        Создает эмбеддинг для одного текстового запроса.
        
        Args:
            text (str): Текстовый запрос
            
        Returns:
            List[float]: Вектор эмбеддинга для запроса
        """
        # Нормализуем эмбеддинг для согласованности с embed_documents
        return self.model.encode(text, normalize_embeddings=True).tolist() 