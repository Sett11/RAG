from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from typing import Dict
import re
import dotenv
import asyncio
import nest_asyncio
import os
from utils.mylogger import Logger

# Инициализация логгера для модуля агрегатора
logger = Logger('aggregator', 'aggregator.log')
logger.info("Запуск модуля агрегатора")

# Загрузка переменных окружения из .env файла
dotenv.load_dotenv()
logger.debug("Переменные окружения загружены")

# Применение nest_asyncio для решения проблем с вложенными циклами событий
nest_asyncio.apply()
logger.debug("nest_asyncio применен")

class ChannelAggregatorBot:
    """
    Класс бота для агрегации обновлений из телеграм каналов и чатов.
    Позволяет подписываться на каналы и получать их обновления в одном месте.
    """
    def __init__(self, token: str):
        """
        Инициализация бота с указанным токеном.
        
        Args:
            token (str): Токен Telegram бота
        """
        logger.info("Инициализация бота агрегатора каналов")
        if not token:
            logger.error("Токен бота не предоставлен")
            raise ValueError("Токен бота не предоставлен")
            
        self.token = token
        self.bot = Bot(token=token)
        # Создаем диспетчер с правильными настройками для aiogram 3.x
        self.dp = Dispatcher()
        # Словарь для хранения информации о подписанных каналах
        # Формат: {channel_id: {name, link, last_message_id}}
        self.subscribed_channels: Dict[str, Dict] = {}
        
        # Регистрация обработчиков команд и сообщений
        logger.debug("Регистрация обработчиков команд и сообщений")
        # Регистрируем обработчики с использованием декораторов
        self.register_handlers()
        logger.info("Обработчики успешно зарегистрированы")
    
    def register_handlers(self):
        """Регистрация всех обработчиков команд и сообщений"""
        # Регистрируем обработчики команд
        self.dp.message.register(self.start, Command(commands=["start"]))
        self.dp.message.register(self.help, Command(commands=["help"]))
        self.dp.message.register(self.list_channels, Command(commands=["list"]))
        
        # Регистрируем обработчики сообщений
        self.dp.message.register(self.handle_message, F.text & ~F.command)
        self.dp.message.register(self.handle_channel_update, F.chat.type.in_({"channel", "group", "supergroup"}))
        
        # Добавляем обработчик для всех сообщений для отладки
        self.dp.message.register(self.debug_handler, F.all)
    
    async def debug_handler(self, message: Message):
        """Обработчик для отладки - логирует все входящие сообщения"""
        logger.debug(f"Получено сообщение: {message.text if message.text else 'Нет текста'}, "
                    f"тип: {message.content_type}, от: {message.from_user.id if message.from_user else 'Неизвестно'}")
    
    async def start(self, message: Message) -> None:
        """
        Обработчик команды /start.
        Отправляет приветственное сообщение пользователю.
        
        Args:
            message (Message): Объект сообщения от пользователя
        """
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n"
            "🤖 Я бот для агрегации обновлений из телеграм каналов и чатов\n"
            "📥 Отправь мне ссылки на каналы, и я буду публиковать их обновления здесь\n"
            "📚 Тебе не придётся держать у себя в телеграмме кучу каналов \n"
            "📰 Но ты всегда будешь в курсе новостей 😊\n"
            "ℹ️ Используй /help для списка команд."
        )
    
    async def help(self, message: Message) -> None:
        """
        Обработчик команды /help.
        Отправляет пользователю список доступных команд.
        
        Args:
            message (Message): Объект сообщения от пользователя
        """
        logger.info(f"Пользователь {message.from_user.id} запросил справку")
        help_text = (
            "📋 Доступные команды:\n"
            "▶️ /start - начать работу с ботом\n"
            "❓ /help - показать эту справку\n"
            "📑 /list - показать список подписанных каналов\n"
            "\n"
            "🔗 Просто отправьте ссылку на канал, чат или группу, чтобы добавить их в список отслеживаемых."
        )
        await message.answer(help_text)
    
    async def list_channels(self, message: Message) -> None:
        """
        Обработчик команды /list.
        Отправляет пользователю список подписанных каналов.
        
        Args:
            message (Message): Объект сообщения от пользователя
        """
        logger.info(f"Пользователь {message.from_user.id} запросил список каналов")
        if not self.subscribed_channels:
            logger.debug("Список подписанных каналов пуст")
            await message.answer("📭 Вы пока не подписаны ни на один канал.")
            return
        
        channels_list = "\n".join(
            f"{i+1}. {info['name']} ({info['link']})"
            for i, (_, info) in enumerate(self.subscribed_channels.items())
        )
        logger.debug(f"Отправка списка из {len(self.subscribed_channels)} каналов")
        await message.answer(f"📋 Подписанные каналы:\n{channels_list}")
    
    async def handle_message(self, message: Message) -> None:
        """
        Обработчик текстовых сообщений (ссылок на каналы).
        Парсит ссылку и добавляет канал в список отслеживаемых.
        
        Args:
            message (Message): Объект сообщения от пользователя
        """
        logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text}")
        text = message.text.strip()
        channel_info = await self.parse_telegram_link(text)
        
        if not channel_info:
            logger.warning(f"Неверный формат ссылки: {text}")
            await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку на телеграм канал, группу или чат.")
            return
        
        self.subscribed_channels[channel_info['id']] = channel_info
        logger.info(f"Добавлен новый канал: {channel_info['name']} (ID: {channel_info['id']})")
        await message.answer(
            f"✅ Канал {channel_info['name']} добавлен в список отслеживаемых!\n"
            f"📢 Теперь я буду публиковать его обновления здесь."
        )
    
    async def parse_telegram_link(self, link: str) -> Dict | None:
        """
        Парсит ссылку на телеграм канал/чат и получает информацию о нем.
        
        Args:
            link (str): Ссылка на телеграм канал/чат
            
        Returns:
            Dict | None: Словарь с информацией о канале или None, если ссылка неверная
        """
        logger.debug(f"Парсинг ссылки: {link}")
        patterns = [
            r'(?:https?://)?t\.me/([a-zA-Z0-9_]{5,32})/?$',
            r'(?:https?://)?telegram\.me/([a-zA-Z0-9_]{5,32})/?$',
            r'(?:https?://)?telegram\.org/([a-zA-Z0-9_]{5,32})/?$'
        ]
        
        username = None
        for pattern in patterns:
            match = re.match(pattern, link)
            if match:
                username = match.group(1)
                break
        
        if not username:
            logger.warning(f"Не удалось извлечь имя пользователя из ссылки: {link}")
            return None
        
        try:
            logger.debug(f"Получение информации о канале @{username}")
            chat = await self.bot.get_chat(f"@{username}")
            return {
                'id': str(chat.id),
                'name': chat.title or chat.username,
                'link': f"https://t.me/{username}",
                'type': chat.type
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале: {e}")
            return None
    
    async def handle_channel_update(self, message: Message) -> None:
        """
        Обработчик новых сообщений в каналах.
        Пересылает сообщения из отслеживаемых каналов.
        
        Args:
            message (Message): Объект сообщения из канала
        """
        if str(message.chat.id) not in self.subscribed_channels:
            logger.debug(f"Сообщение из неотслеживаемого канала: {message.chat.id}")
            return
        
        channel_info = self.subscribed_channels[str(message.chat.id)]
        logger.info(f"Новое сообщение из канала {channel_info['name']} (ID: {message.chat.id})")
        
        text = (
            f"🔔 Новое сообщение из канала {channel_info['name']}:\n\n"
            f"{message.text or message.caption or ''}"
        )
        
        try:
            if message.photo:
                logger.debug(f"Пересылка фото из канала {channel_info['name']}")
                await self.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=message.photo[-1].file_id,
                    caption=text
                )
            elif message.video:
                logger.debug(f"Пересылка видео из канала {channel_info['name']}")
                await self.bot.send_video(
                    chat_id=message.chat.id,
                    video=message.video.file_id,
                    caption=text
                )
            elif message.document:
                logger.debug(f"Пересылка документа из канала {channel_info['name']}")
                await self.bot.send_document(
                    chat_id=message.chat.id,
                    document=message.document.file_id,
                    caption=text
                )
            else:
                logger.debug(f"Пересылка текстового сообщения из канала {channel_info['name']}")
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text=text
                )
        except Exception as e:
            logger.error(f"Ошибка при пересылке сообщения из канала {channel_info['name']}: {e}")
    
    async def run(self):
        """
        Запускает бота и начинает обработку сообщений.
        """
        logger.info("Запуск бота агрегатора каналов")
        try:
            logger.debug("Начало поллинга бота")
            # Запускаем поллинг с правильными параметрами для aiogram 3.x
            await self.dp.start_polling(self.bot, allowed_updates=["message", "callback_query"])
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise

if __name__ == '__main__':
    # Создание и запуск бота с токеном из переменных окружения
    logger.info("Инициализация приложения")
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("Токен бота не найден в переменных окружения")
        raise ValueError("Токен бота не найден в переменных окружения")
        
    logger.info("Создание экземпляра бота")
    bot = ChannelAggregatorBot(token=token)
    
    try:
        logger.info("Запуск бота")
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise