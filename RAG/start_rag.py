from typing import List
from src.rag import AdvancedRAG
from src.handle_dir_and_files.load_documents import LoadDocuments
from src.handle_dir_and_files.process_documents import ProcessDocuments
from utils.mylogger import Logger
from config import Config_LLM, docs_dir
import os

# if os.path.exists('logs/rag.log'):
#     os.remove('logs/rag.log')

# Инициализация логгера для отслеживания работы приложения
logger = Logger('Start RAG', 'logs/rag.log')

def create_LLM(llm, config):
    """
    Создает и настраивает экземпляр класса AdvancedRAG.

    Процесс создания:
    1. Получение конфигурации из config
    2. Инициализация AdvancedRAG с параметрами из конфигурации
    3. Возврат готового экземпляра

    Args:
        llm: Класс AdvancedRAG для создания экземпляра
        config: Объект конфигурации с параметрами для LLM
            - model_name: название модели
            - api_key: ключ API
            - base_url: базовый URL
            - temperature: температура генерации

    Returns:
        AdvancedRAG: Настроенный экземпляр класса AdvancedRAG
    """
    conf = config
    LLM = llm(
        conf.model_name,
        conf.api_key,
        conf.base_url,
        conf.temperature
    )
    return LLM

def setting_up_LLM(llm, documents: List[str]):
    """
    Настраивает LLM для работы с документами.

    Процесс настройки:
    1. Загрузка документов из указанных путей
    2. Обработка документов (разбивка на чанки)
    3. Создание векторного хранилища
    4. Настройка ретриверов
    5. Настройка промптов

    Args:
        llm: Экземпляр класса AdvancedRAG
        documents: Список путей к документам для обработки
            Поддерживаемые форматы: PDF, TXT, DOCX

    Returns:
        AdvancedRAG: Настроенный экземпляр с загруженными документами
    """
    # Загрузка документов из файлов
    loaded_documents = LoadDocuments(documents).load_documents()
    # Обработка документов (разбивка на чанки)
    processed_documents = ProcessDocuments(loaded_documents).process_documents()
    # Создание векторного хранилища для быстрого поиска
    llm.vectorstore.create_vector_store(processed_documents)
    # Настройка компонентов для поиска документов
    llm.retriever.setup_retrievers()
    # Настройка промптов для генерации ответов
    llm.promts.setup_prompts()
    return llm

def main():
    """
    Основная функция приложения.
    
    Процесс работы:
    1. Создание экземпляра AdvancedRAG
    2. Проверка наличия директории с документами
    3. Настройка путей к документам
    4. Инициализация LLM с документами
    5. Цикл обработки вопросов пользователя
    6. Извлечение и вывод точных ответов
    """
    try:
        # Создание и настройка LLM
        llm = create_LLM(AdvancedRAG, Config_LLM)
        
        # Настройка LLM для работы с документами
        llm = setting_up_LLM(llm, [docs_dir])
        
        # Получение вопроса от пользователя
        question = input("Введите ваш вопрос: ")

        while question != "exit":
            # Получение ответа от LLM
            response = llm.query(question)
            
            # Выводим ответ
            print("\nОтвет:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
            # Получение нового вопроса
            question = input("Введите ваш вопрос: ")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    logger.info("Запуск приложения")
    main()