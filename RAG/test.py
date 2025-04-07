from langchain_openai import ChatOpenAI
from config import Config_LLM

# Инициализация конфигурации
llm_config = Config_LLM()

# Создание экземпляра ChatOpenAI без параметра proxies
llm = ChatOpenAI(
    model=llm_config.model_name,
    api_key=llm_config.api_key,
    base_url=llm_config.base_url,
    temperature=llm_config.temperature
)

# Тестовый запрос
response = llm.invoke("Привет, как дела?")
print(response) 