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

    def verification_query(self, question: str, response: str, context: str) -> tuple[bool, str]:
        """
        Проверяет качество сгенерированного ответа.

        Процесс верификации:
        1. Проверяет наличие промпта верификации
        2. Отправляет запрос к LLM с контекстом, вопросом и ответом
        3. Анализирует ответ верификатора
        4. При необходимости извлекает улучшенную версию ответа

        Args:
            question (str): Исходный вопрос пользователя
            response (str): Сгенерированный ответ
            context (str): Контекст, использованный для генерации

        Returns:
            tuple[bool, str]: (требуется_ли_корректировка, полный_ответ)
        """
        try:
            if not hasattr(self, 'verification_prompt'):
                logger.warning("Промпт верификации не инициализирован")
                return False, response

            verification_response = self.llm.invoke(
                self.verification_prompt.format(
                    context=context,
                    question=question,
                    response=response
                )
            )

            if not verification_response or not verification_response.content:
                logger.warning("Верификатор вернул пустой ответ")
                return False, response

            # Анализируем ответ верификатора
            content = verification_response.content.lower()
            logger.info(f"Ответ верификатора: {content}")
            needs_correction = "да" in content or "требуется" in content
            improved_response = response

            if needs_correction:
                # Проверяем наличие тегов <answer> и </answer>
                start_tag = "<answer>"
                end_tag = "</answer>"
                
                start_idx = content.find(start_tag)
                if start_idx != -1:
                    start_idx += len(start_tag)
                    end_idx = content.find(end_tag, start_idx)
                    
                    if end_idx != -1:
                        logger.info("Найдена улучшенная версия ответа в тегах <answer> и </answer>")
                        improved_text = content[start_idx:end_idx].strip()
                        # Заменяем текст между тегами <answer> и </answer> в исходном ответе
                        if "<answer>" in response and "</answer>" in response:
                            response_start = response.find("<answer>") + len("<answer>")
                            response_end = response.find("</answer>", response_start)
                            improved_response = response[:response_start] + improved_text + response[response_end:]
                        else:
                            # Если в исходном ответе нет тегов, добавляем их
                            improved_response = f"{response}\n\n<answer>{improved_text}</answer>"
                        return needs_correction, improved_response
                    else:
                        logger.warning("Найден открывающий тег <answer>, но не найден закрывающий тег </answer>")
                
                # Если теги не найдены, ищем "улучшенная версия:"
                improved_start = content.find("улучшенная версия:")
                if improved_start != -1:
                    # Извлекаем текст после "улучшенная версия:"
                    improved_text = content[improved_start:].split("\n")[0].replace("улучшенная версия:", "").strip()
                    
                    # Если улучшенный текст слишком короткий, попробуем получить больше текста
                    if len(improved_text) < 50:
                        # Ищем следующий раздел или конец текста
                        next_section = content.find("**", improved_start + len("улучшенная версия:"))
                        if next_section != -1:
                            improved_text = content[improved_start + len("улучшенная версия:"):next_section].strip()
                        else:
                            # Если нет следующего раздела, берем весь текст до конца
                            improved_text = content[improved_start + len("улучшенная версия:"):].strip()
                    
                    # Заменяем текст между тегами <answer> и </answer> в исходном ответе
                    if "<answer>" in response and "</answer>" in response:
                        response_start = response.find("<answer>") + len("<answer>")
                        response_end = response.find("</answer>", response_start)
                        improved_response = response[:response_start] + improved_text + response[response_end:]
                    else:
                        # Если в исходном ответе нет тегов, добавляем их
                        improved_response = f"{response}\n\n<answer>{improved_text}</answer>"
                else:
                    # Если не нашли маркер "улучшенная версия:", попробуем найти сам ответ
                    # Обычно он идет после "вот" или "это"
                    for marker in ["вот", "это"]:
                        marker_pos = content.find(marker)
                        if marker_pos != -1:
                            # Берем текст после маркера до следующего раздела или конца
                            next_section = content.find("**", marker_pos)
                            if next_section != -1:
                                improved_text = content[marker_pos + len(marker):next_section].strip()
                            else:
                                improved_text = content[marker_pos + len(marker):].strip()
                            
                            if improved_text:
                                # Заменяем текст между тегами <answer> и </answer> в исходном ответе
                                if "<answer>" in response and "</answer>" in response:
                                    response_start = response.find("<answer>") + len("<answer>")
                                    response_end = response.find("</answer>", response_start)
                                    improved_response = response[:response_start] + improved_text + response[response_end:]
                                else:
                                    # Если в исходном ответе нет тегов, добавляем их
                                    improved_response = f"{response}\n\n<answer>{improved_text}</answer>"
                                break

            logger.info(f"Верификация ответа: {'требуется корректировка' if needs_correction else 'ответ приемлем'}")
            return needs_correction, improved_response

        except Exception as e:
            logger.error(f"Ошибка при верификации ответа: {str(e)}")
            return False, response

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
            str: Полный ответ модели
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

            # Проверяем наличие тегов <answer> и </answer>
            if "<answer>" in response.content and "</answer>" in response.content:
                logger.info("Ответ содержит теги <answer> и </answer>")
                return response.content

            # Если тегов нет, проверяем качество ответа
            needs_correction, improved_response = self.verification_query(
                question=question,
                response=response.content,
                context=context
            )

            if needs_correction:
                logger.info("Ответ был улучшен в процессе верификации")
                return improved_response

            # Если ответ не требует корректировки, добавляем теги
            if "<answer>" not in response.content and "</answer>" not in response.content:
                # Ищем точный ответ в тексте
                exact_answer = self.extract_exact_answer(response.content)
                if exact_answer:
                    return f"{response.content}\n\n<answer>{exact_answer}</answer>"

            return response.content

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {str(e)}")
            return f"Произошла ошибка: {str(e)}"