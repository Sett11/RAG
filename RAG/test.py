from langchain_openai import ChatOpenAI
import os
from config import Config_LLM

config = Config_LLM()

# Отключаем использование transformers
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Инициализация ChatOpenAI
llm = ChatOpenAI(
    model=config.model_name,
    api_key=config.api_key,
    base_url=config.base_url,
    temperature=config.temperature
)

print("ChatOpenAI успешно инициализирован") 