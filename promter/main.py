import os
from typing import Optional, Dict
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hitalic
from openai import AsyncOpenAI
import redis
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import nest_asyncio

from utils.mylogger import Logger

# избегаем ошибки вложенния асинхронных циклов
nest_asyncio.apply()
# Загрузка переменных окружения
load_dotenv()

# Настройка логов
logger = Logger("promter", "bot.log")

# Инициализация бота и Redis
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Подключение к Redis с обработкой ошибок
try:
    logger.info("Подключение к Redis")
    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL"),
        socket_timeout=5,
        socket_connect_timeout=5,
        decode_responses=True
    )
    redis_client.ping()  # Проверка соединения
    logger.info("Успешно подключено к Redis.")
except redis.RedisError as e:
    logger.error(f"Ошибка подключения к Redis: {e}")
    raise

# Настройки OpenAI
openai_client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)
GPT_MODEL = os.getenv("MODEL_NAME") # модель GPT
temperature = float(os.getenv("TEMPERATURE", "0.7")) # температура для GPT
MAX_HISTORY = int(os.getenv("MAX_HISTORY"))  # Максимальное количество сообщений в истории

# Состояние ожидания цели
waiting_for_goal: Dict[int, bool] = {}

# Клавиатуры
def get_main_keyboard():
    logger.info("Клавиатура получена")
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="/set_goal")],
            [types.KeyboardButton(text="/current_goal"), types.KeyboardButton(text="/clear_history")],
            [types.KeyboardButton(text="/help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

# Модели данных
class UserData(BaseModel):
    goal: str = Field(..., description="Цель переговоров")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    additional_info: Optional[str] = Field(None, description="Дополнительная информация")

class DialogSettings(BaseModel):
    max_history: int = Field(default=MAX_HISTORY, description="Максимальная длина истории диалога")
    gpt_temperature: float = Field(default=temperature, description="Температура для GPT")

# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    logger.info("Старт бота")
    welcome_text = (
        f"Привет, {hbold(message.from_user.full_name)}! 👋\n"
        "Я твой ассистент для переговоров.\n\n"
        f"{hitalic('Основные команды:')}\n"
        "/set_goal - установить цель переговоров\n"
        "/current_goal - текущая цель\n"
        "/clear_history - очистить историю диалога\n"
        "/help - помощь и инструкции"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

# Команда /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    logger.info("Помощь по боту")
    help_text = (
        f"{hbold('Помощь по боту:')}\n\n"
        "1. Сначала установите цель переговоров командой /set_goal\n"
        "2. Начните диалог - я буду анализировать ваши сообщения\n"
        "3. Получайте советы по ведению переговоров\n\n"
        f"{hitalic('Пример:')}\n"
        "/set_goal договориться с девушкой о встрече на сеновале\n\n"
        f"Я сохраняю историю последних {MAX_HISTORY} сообщений для контекста.\n"
        "Вы можете очистить историю командой /clear_history"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

# Команда /set_goal - установка цели
@dp.message(Command("set_goal"))
async def set_goal(message: types.Message):
    logger.info("Установка цели")
    args = message.text.split(maxsplit=1)
    user_id = message.from_user.id
    
    if len(args) < 2:
        # Если цель не указана в команде, устанавливаем флаг ожидания цели
        waiting_for_goal[user_id] = True
        await message.answer(
            "Пожалуйста, укажите цель в следующем сообщении.\n"
            f"{hitalic('Пример:')} договориться с кузнецом",
            parse_mode="HTML"
        )
        return

    # Если цель указана в команде, сохраняем её
    goal = args[1]
    await save_goal(message, goal)

# Функция для сохранения цели
async def save_goal(message: types.Message, goal: str):
    user_id = message.from_user.id
    user_data = UserData(goal=goal)
    
    try:
        # Преобразуем все значения в строки, чтобы избежать ошибки с NoneType
        user_data_dict = user_data.dict()
        for key, value in user_data_dict.items():
            if value is None:
                user_data_dict[key] = ""
            else:
                user_data_dict[key] = str(value)
                
        redis_client.hset(
            f"user:{user_id}",
            mapping=user_data_dict
        )
        # Сбрасываем флаг ожидания цели
        waiting_for_goal[user_id] = False
        await message.answer(
            f"🎯 Цель успешно установлена:\n{hbold(goal)}",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения цели: {e}")
        await message.answer("⚠️ Произошла ошибка при сохранении цели. Попробуйте позже.")

# Команда /current_goal - текущая цель
@dp.message(Command("current_goal"))
async def current_goal(message: types.Message):
    logger.info("Текущая цель")
    try:
        user_data = redis_client.hgetall(f"user:{message.from_user.id}")
        if not user_data:
            await message.answer("ℹ️ Цель не установлена. Используйте /set_goal")
            return
            
        goal = user_data.get("goal", "Цель не установлена")
        created_at = user_data.get("created_at", "неизвестно")
        
        response = (
            f"📌 {hbold('Текущая цель:')}\n"
            f"{goal}\n\n"
            f"🕒 Установлена: {created_at}"
        )
        
        await message.answer(response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка получения цели: {e}")
        await message.answer("⚠️ Произошла ошибка при получении цели.")

# Команда /clear_history - очистка истории
@dp.message(Command("clear_history"))
async def clear_history(message: types.Message):
    logger.info("Очистка истории")
    chat_id = message.chat.id
    try:
        redis_client.delete(f"dialog:{chat_id}")
        await message.answer("🗑️ История диалога очищена!", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка очистки истории: {e}")
        await message.answer("⚠️ Произошла ошибка при очистке истории.")

# Обработка обычных сообщений
@dp.message(F.text)
async def handle_message(message: types.Message):
    logger.info("Обработка сообщения")
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем, ожидаем ли мы цель от этого пользователя
    if user_id in waiting_for_goal and waiting_for_goal[user_id]:
        await save_goal(message, message.text)
        return
    
    try:
        # Проверяем, есть ли цель у пользователя
        if not redis_client.hexists(f"user:{user_id}", "goal"):
            await message.answer(
                "ℹ️ Сначала установите цель переговоров с помощью /set_goal",
                reply_markup=get_main_keyboard()
            )
            return

        # Получаем данные пользователя
        user_data = redis_client.hgetall(f"user:{user_id}")
        goal = user_data["goal"]
        
        # Сохраняем сообщение в историю
        message_text = f"user:{user_id}: {message.text}"
        redis_client.rpush(f"dialog:{chat_id}", message_text)
        
        # Получаем историю диалога (с ограничением по количеству)
        dialog_history = redis_client.lrange(f"dialog:{chat_id}", -MAX_HISTORY, -1)
        context = "\n".join(dialog_history)
        logger.info("Формирование промта")
        # Формируем промпт для GPT
        prompt = (
            "Ты — профессиональный ассистент для переговоров. Пользователь хочет достичь следующей цели:\n"
            f"Цель: {goal}\n\n"
            "Контекст текущего диалога:\n"
            f"{context}\n\n"
            "Проанализируй диалог и дай 1-2 конкретных совета, что можно ответить, "
            "чтобы продвинуться к цели. Будь кратким и конкретным. "
            "Если в диалоге есть спорные моменты, укажи на них."
        )
        logger.info("Отправка запроса к OpenAI")
        # Отправляем запрос к OpenAI
        try:
            response = await openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=int(os.getenv("MAX_TOKENS", "500"))
            )
            logger.info("Получение ответа от OpenAI")
            advice = response.choices[0].message.content
            logger.info(f"Ответ от OpenAI: {advice}")
            await message.answer(
                f"💡 {hbold('Совет по переговорам:')}\n{advice}",parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            await message.answer("⚠️ Произошла ошибка при обработке запроса. Попробуйте позже.")
            
    except redis.RedisError as e:
        logger.error(f"Redis Error: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке данных. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        await message.answer("⚠️ Произошла непредвиденная ошибка. Попробуйте позже.")

# Обработка ошибок
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    logger.error(f"Update {update} caused error {exception}")
    # Можно добавить отправку сообщения админу или пользователю
    return True

# Запуск бота
async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())