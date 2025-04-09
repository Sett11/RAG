from src.rag import AdvancedRAG
from src.handle_dir_and_files.load_documents import LoadDocuments
from src.handle_dir_and_files.process_documents import ProcessDocuments
from utils.mylogger import Logger
from config import Config_LLM, docs_dir

logger = Logger('Start RAG', 'logs/rag.log')

llm_config = Config_LLM()

LLM = AdvancedRAG(
    llm_config.model_name,
    llm_config.api_key,
    llm_config.base_url,
    llm_config.temperature
)

documents = LoadDocuments([
    f"{docs_dir}\\*.pdf",
    f"{docs_dir}\\*.txt",
    f"{docs_dir}\\*.docx"
]).load_documents()

processed_documents = ProcessDocuments(documents).process_documents()

LLM.create_vector_store(processed_documents)

user_question = input("Введите ваш вопрос: ")
while user_question != "exit":
    print(f"Выполняем запрос: {user_question}")
    response = LLM.query(user_question)
    print(f"Ответ: {response}")
    logger.info(f"Ответ: {response}")
    user_question = input("Введите ваш вопрос: ")