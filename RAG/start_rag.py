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

def extract_exact_answer(response: str) -> str:
    """
    Извлекает точный ответ из полного ответа модели.
    
    Процесс извлечения:
    1. Проверяет наличие тегов <answer> и </answer>
    2. Если теги найдены, извлекает текст между ними
    3. Если теги не найдены, проверяет наличие "улучшенная версия:"
    4. Если ничего не найдено, возвращает исходный ответ
    
    Args:
        response (str): Полный ответ модели
        
    Returns:
        str: Извлеченный точный ответ
    """
    try:
        # Проверяем наличие тегов <answer> и </answer>
        start_tag = "<answer>"
        end_tag = "</answer>"
        
        start_idx = response.find(start_tag)
        if start_idx != -1:
            start_idx += len(start_tag)
            end_idx = response.find(end_tag, start_idx)
            
            if end_idx != -1:
                logger.info("Найден ответ в тегах <answer> и </answer>")
                return response[start_idx:end_idx].strip()
            else:
                logger.warning("Найден открывающий тег <answer>, но не найден закрывающий тег </answer>")
        
        # Если теги не найдены, проверяем наличие "улучшенная версия:"
        if "улучшенная версия:" in response.lower():
            # Извлекаем текст после "улучшенная версия:"
            improved_start = response.lower().find("улучшенная версия:")
            improved_text = response[improved_start:].split("\n")[0].replace("улучшенная версия:", "").strip()
            
            # Если текст слишком короткий, пробуем получить больше
            if len(improved_text) < 50:
                next_section = response.find("**", improved_start + len("улучшенная версия:"))
                if next_section != -1:
                    improved_text = response[improved_start + len("улучшенная версия:"):next_section].strip()
                else:
                    improved_text = response[improved_start + len("улучшенная версия:"):].strip()
            
            logger.info("Найден ответ в разделе 'улучшенная версия:'")
            return improved_text
            
        # Если ответ не скорректирован, используем стандартный метод
        start_marker = "3. **Точный ответ**:"
        end_marker = "4. **Источник информации**"
        
        start_idx = response.find(start_marker)
        if start_idx == -1:
            logger.warning("Маркер начала точного ответа не найден")
            return response
            
        start_idx += len(start_marker)
        end_idx = response.find(end_marker, start_idx)
        
        if end_idx == -1:
            logger.warning("Маркер конца точного ответа не найден")
            return response[start_idx:].strip()
            
        logger.info("Найден ответ в разделе 'Точный ответ'")
        return response[start_idx:end_idx].strip()
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении точного ответа: {str(e)}")
        return response

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
            
            # Извлекаем точный ответ из полного ответа модели
            exact_answer = extract_exact_answer(response)
            
            # Выводим точный ответ
            print("\nТочный ответ:")
            print("-" * 50)
            print(exact_answer)
            print("-" * 50)
            
            # Получение нового вопроса
            question = input("Введите ваш вопрос: ")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    logger.info("Запуск приложения")
    main()