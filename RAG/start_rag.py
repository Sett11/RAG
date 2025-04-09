from typing import List
import os
from src.rag import AdvancedRAG
from src.handle_dir_and_files.load_documents import LoadDocuments
from src.handle_dir_and_files.process_documents import ProcessDocuments
from utils.mylogger import Logger
from config import Config_LLM, docs_dir

logger = Logger('Start RAG', 'logs/rag.log')

def create_LLM(llm, config):
    """
    Создает и настраивает экземпляр класса AdvancedRAG.

    Args:
        llm: Экземпляр класса AdvancedRAG.
        config: Конфигурация для LLM.

    Returns:
        AdvancedRAG: Экземпляр класса AdvancedRAG.
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
    Создает и настраивает llm.

    Args:
        llm: Экземпляр класса AdvancedRAG.
        config: Конфигурация для LLM.
        documents: Список документов.
    """
    loaded_documents = LoadDocuments(documents).load_documents()
    processed_documents = ProcessDocuments(loaded_documents).process_documents()
    llm.vectorstore.create_vector_store(processed_documents)
    llm.retriever.setup_retrievers()
    llm.promts.setup_prompts()
    return llm

def extract_exact_answer(response: str) -> str:
    """
    Извлекает точный ответ из полного ответа LLM.
    
    Args:
        response (str): Полный ответ от LLM
        
    Returns:
        str: Точный ответ или исходный ответ, если раздел не найден
    """
    try:
        # Ищем раздел "Точный ответ"
        start_marker = "3. **Точный ответ**:"
        end_marker = "4. **Источник информации**"
        
        start_idx = response.find(start_marker)
        if start_idx == -1:
            return response
            
        start_idx += len(start_marker)
        end_idx = response.find(end_marker, start_idx)
        
        if end_idx == -1:
            return response[start_idx:].strip()
            
        return response[start_idx + len(start_marker):end_idx].strip()
    except Exception as e:
        logger.error(f"Ошибка при извлечении точного ответа: {str(e)}")
        return response

def main():
    LLM = create_LLM(AdvancedRAG, Config_LLM)
    # Проверяем существование директории
    if not os.path.exists(docs_dir):
        logger.error(f"Директория не существует: {docs_dir}")
        print(f"Ошибка: Директория не существует: {docs_dir}")
        return
    
    # Формируем пути к файлам
    file_patterns = [
        os.path.join(docs_dir, "*.pdf"),
        os.path.join(docs_dir, "*.txt"),
        os.path.join(docs_dir, "*.docx")
    ]
    
    setting_up_LLM(LLM, file_patterns)
    user_question = input("Введите ваш вопрос: ")
    while user_question != "exit":
        print(f"Выполняем запрос: {user_question}")
        response = LLM.query(user_question)
        exact_answer = extract_exact_answer(response)
        print(f"\nТочный ответ:\n{exact_answer}\n")
        logger.info(f"Ответ: {response}")
        user_question = input("Введите ваш вопрос: ")

if __name__ == "__main__":
    logger.info("Запуск приложения")
    main()