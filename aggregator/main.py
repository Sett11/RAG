# импорты стандартных модулей
import re
import os
from typing import Dict, List, Optional
import asyncio
from enum import Enum, auto

# импорты устоновленных библиотек
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram.enums import ChatType
import dotenv
import nest_asyncio
import redis.asyncio as redis
from pydantic import BaseModel

# локальные модули
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

# Конфигурация
class Config:
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    MAX_SUBSCRIPTIONS_PER_USER = int(os.getenv('MAX_SUBSCRIPTIONS_PER_USER', 50))
    SUPPORTED_CONTENT_TYPES = {
        ContentType.TEXT,
        ContentType.PHOTO,
        ContentType.VIDEO,
        ContentType.DOCUMENT,
        ContentType.AUDIO,
        ContentType.VOICE
    }

# Модели данных
class ChannelInfo(BaseModel):
    id: str
    name: str
    link: str
    type: ChatType

class ContentTypeFilter(Enum):
    ALL = auto()
    TEXT = auto()
    MEDIA = auto()

# Инициализация Redis
async def init_redis() -> redis.Redis:
    return redis.from_url(Config.REDIS_URL)

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
        self.dp = Dispatcher()
        self.redis = None
        
        # Регистрация обработчиков команд и сообщений
        logger.debug("Регистрация обработчиков команд и сообщений")
        self.register_handlers()
        logger.info("Обработчики успешно зарегистрированы")
    
    async def init(self):
        """Асинхронная инициализация (Redis)"""
        self.redis = await init_redis()
    
    def register_handlers(self):
        """Регистрация всех обработчиков команд и сообщений"""
        # Команды
        self.dp.message.register(self.start, Command(commands=["start"]))
        self.dp.message.register(self.help, Command(commands=["help"]))
        self.dp.message.register(self.list_channels, Command(commands=["list"]))
        self.dp.message.register(self.unsubscribe, Command(commands=["unsubscribe"]))
        
        # Обработчики сообщений
        self.dp.message.register(self.handle_message, F.text & ~F.command)
        self.dp.message.register(
            self.handle_channel_update, 
            F.chat.type.in_({ChatType.CHANNEL, ChatType.GROUP, ChatType.SUPERGROUP})
        )
        
        # Обработчик для отладки
        self.dp.message.register(self.debug_handler)
    
    async def debug_handler(self, message: Message):
        """Обработчик для отладки - логирует все входящие сообщения"""
        logger.debug(f"Получено сообщение: {message.text if message.text else 'Нет текста'}, "
                    f"тип: {message.content_type}, от: {message.from_user.id if message.from_user else 'Неизвестно'}")
    
    async def start(self, message: Message) -> None:
        """
        Обработчик команды /start.
        Отправляет приветственное сообщение пользователю.
        """
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n"
            "🤖 Я бот для агрегации обновлений из телеграм каналов и чатов\n"
            "📥 Отправь мне ссылки на каналы, и я буду присылать их обновления\n"
            "📚 Тебе не придётся держать у себя в телеграмме кучу каналов\n"
            "📰 Но ты всегда будешь в курсе новостей 😊\n"
            "ℹ️ Используй /help для списка команд."
        )
    
    async def help(self, message: Message) -> None:
        """
        Обработчик команды /help.
        Отправляет пользователю список доступных команд.
        """
        logger.info(f"Пользователь {message.from_user.id} запросил справку")
        help_text = (
            "📋 Доступные команды:\n"
            "▶️ /start - начать работу с ботом\n"
            "❓ /help - показать эту справку\n"
            "📑 /list - показать список подписанных каналов\n"
            "❌ /unsubscribe - отписаться от канала\n"
            "\n"
            "🔗 Просто отправьте ссылку на канал, чат или группу, чтобы добавить их в список отслеживаемых."
        )
        await message.answer(help_text)
    
    async def list_channels(self, message: Message) -> None:
        """
        Обработчик команды /list.
        Отправляет пользователю список подписанных каналов.
        """
        user_id = str(message.from_user.id)
        logger.info(f"Пользователь {user_id} запросил список каналов")
        
        subscribed_channels = await self.get_user_subscriptions(user_id)
        if not subscribed_channels:
            logger.debug("Список подписанных каналов пуст")
            await message.answer("📭 Вы пока не подписаны ни на один канал.")
            return
        
        channels_info = []
        for channel_id in subscribed_channels:
            channel = await self.get_channel_info(channel_id)
            if channel:
                channels_info.append(f"• {channel.name} ({channel.link})")
        
        if not channels_info:
            await message.answer("📭 Нет активных подписок.")
            return
        
        channels_list = "\n".join(channels_info)
        logger.debug(f"Отправка списка из {len(channels_info)} каналов")
        await message.answer(f"📋 Ваши подписки:\n{channels_list}")
    
    async def unsubscribe(self, message: Message) -> None:
        """
        Обработчик команды /unsubscribe.
        Позволяет отписаться от канала.
        """
        user_id = str(message.from_user.id)
        args = message.text.split()[1:]
        
        if not args:
            await message.answer("ℹ️ Укажите ссылку на канал или его ID после команды /unsubscribe")
            return
        
        channel_identifier = args[0]
        channel_info = await self.parse_telegram_link(channel_identifier) or await self.get_channel_info(channel_identifier)
        
        if not channel_info:
            await message.answer("⚠️ Канал не найден. Укажите корректную ссылку или ID канала.")
            return
        
        if not await self.is_user_subscribed(user_id, channel_info.id):
            await message.answer(f"ℹ️ Вы не подписаны на канал {channel_info.name}.")
            return
        
        await self.remove_user_subscription(user_id, channel_info.id)
        await message.answer(f"✅ Вы отписались от канала {channel_info.name}.")
    
    async def handle_message(self, message: Message) -> None:
        """
        Обработчик текстовых сообщений (ссылок на каналы).
        Парсит ссылку и добавляет канал в список отслеживаемых.
        """
        user_id = str(message.from_user.id)
        logger.info(f"Получено сообщение от пользователя {user_id}: {message.text}")
        
        text = message.text.strip()
        channel_info = await self.parse_telegram_link(text)
        
        if not channel_info:
            logger.warning(f"Неверный формат ссылки: {text}")
            await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку на телеграм канал, группу или чат.")
            return
        
        # Проверка количества подписок
        user_subs = await self.get_user_subscriptions(user_id)
        if len(user_subs) >= Config.MAX_SUBSCRIPTIONS_PER_USER:
            await message.answer(f"⚠️ Вы достигли лимита подписок ({Config.MAX_SUBSCRIPTIONS_PER_USER}).")
            return
        
        # Проверка доступа бота к каналу
        # try:
        #     chat_member = await self.bot.get_chat_member(chat_id=channel_info.id, user_id=self.bot.id)
        #     if chat_member.status not in ['administrator', 'member', 'creator']:
        #         await message.answer("⚠️ Бот не имеет доступа к этому каналу. Добавьте бота в канал как администратора.")
        #         return
        # except Exception as e:
        #     logger.error(f"Ошибка проверки доступа к каналу: {e}")
        #     await message.answer("⚠️ Не удалось проверить доступ к каналу. Убедитесь, что бот добавлен в канал.")
        #     return
        
        # Добавление подписки
        await self.save_channel_info(channel_info)
        await self.add_user_subscription(user_id, channel_info.id)
        
        logger.info(f"Пользователь {user_id} подписан на канал: {channel_info.name} (ID: {channel_info.id})")
        await message.answer(
            f"✅ Канал {channel_info.name} добавлен в ваши подписки!\n"
            f"📢 Теперь вы будете получать его обновления."
        )
    
    async def handle_channel_update(self, message: Message) -> None:
        """
        Обработчик новых сообщений в каналах.
        Пересылает сообщения подписанным пользователям.
        """
        channel_id = str(message.chat.id)
        if not await self.is_channel_tracked(channel_id):
            logger.debug(f"Сообщение из неотслеживаемого канала: {channel_id}")
            return
        
        channel_info = await self.get_channel_info(channel_id)
        if not channel_info:
            return
        
        logger.info(f"Новое сообщение из канала {channel_info.name} (ID: {channel_id})")
        
        # Получаем всех подписчиков канала
        subscribers = await self.get_channel_subscribers(channel_id)
        if not subscribers:
            return
        
        # Формируем текст сообщения
        text = (
            f"🔔 Новое сообщение из канала {channel_info.name}:\n\n"
            f"{message.text or message.caption or ''}"
        )
        
        # Отправляем сообщение всем подписчикам
        for user_id in subscribers:
            try:
                if message.content_type == ContentType.TEXT:
                    await self.bot.send_message(chat_id=user_id, text=text)
                elif message.content_type == ContentType.PHOTO:
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=message.photo[-1].file_id,
                        caption=text
                    )
                elif message.content_type == ContentType.VIDEO:
                    await self.bot.send_video(
                        chat_id=user_id,
                        video=message.video.file_id,
                        caption=text
                    )
                elif message.content_type == ContentType.DOCUMENT:
                    await self.bot.send_document(
                        chat_id=user_id,
                        document=message.document.file_id,
                        caption=text
                    )
                elif message.content_type in (ContentType.AUDIO, ContentType.VOICE):
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Новое аудио из канала {channel_info.name} (бот пока не поддерживает пересылку аудио)"
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
                # Удаляем неактивного пользователя из подписок
                await self.remove_user_subscription(user_id, channel_id)
    
    # Redis методы
    async def save_channel_info(self, channel_info: ChannelInfo) -> None:
        """Сохраняет информацию о канале в Redis"""
        await self.redis.hset(
            f"channel:{channel_info.id}",
            mapping={
                "name": channel_info.name,
                "link": channel_info.link,
                "type": channel_info.type.value
            }
        )
    
    async def get_channel_info(self, channel_id: str) -> Optional[ChannelInfo]:
        """Получает информацию о канале из Redis"""
        data = await self.redis.hgetall(f"channel:{channel_id}")
        if not data:
            return None
        
        return ChannelInfo(
            id=channel_id,
            name=data.get(b'name', b'').decode(),
            link=data.get(b'link', b'').decode(),
            type=ChatType(data.get(b'type', b'').decode())
        )
    
    async def is_channel_tracked(self, channel_id: str) -> bool:
        """Проверяет, отслеживается ли канал кем-либо"""
        subscribers = await self.get_channel_subscribers(channel_id)
        return len(subscribers) > 0
    
    async def add_user_subscription(self, user_id: str, channel_id: str) -> None:
        """Добавляет подписку пользователя на канал"""
        await self.redis.sadd(f"user:{user_id}:subscriptions", channel_id)
        await self.redis.sadd(f"channel:{channel_id}:subscribers", user_id)
    
    async def remove_user_subscription(self, user_id: str, channel_id: str) -> None:
        """Удаляет подписку пользователя на канал"""
        await self.redis.srem(f"user:{user_id}:subscriptions", channel_id)
        await self.redis.srem(f"channel:{channel_id}:subscribers", user_id)
    
    async def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Получает список подписок пользователя"""
        members = await self.redis.smembers(f"user:{user_id}:subscriptions")
        return [channel_id.decode() for channel_id in members]
    
    async def get_channel_subscribers(self, channel_id: str) -> List[str]:
        """Получает список подписчиков канала"""
        return [user_id.decode() async for user_id in await self.redis.smembers(f"channel:{channel_id}:subscribers")]
    
    async def is_user_subscribed(self, user_id: str, channel_id: str) -> bool:
        """Проверяет, подписан ли пользователь на канал"""
        return await self.redis.sismember(f"user:{user_id}:subscriptions", channel_id)
    
    # Вспомогательные методы
    async def parse_telegram_link(self, link: str) -> Optional[ChannelInfo]:
        """
        Парсит ссылку на телеграм канал/чат и получает информацию о нем.
        Возвращает ChannelInfo или None, если ссылка неверная.
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
            return ChannelInfo(
                id=str(chat.id),
                name=chat.title or chat.username,
                link=f"https://t.me/{username}",
                type=chat.type
            )
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале: {e}")
            return None
    
    async def run(self):
        """
        Запускает бота и начинает обработку сообщений.
        """
        logger.info("Запуск бота агрегатора каналов")
        try:
            await self.init()
            logger.debug("Начало поллинга бота")
            await self.dp.start_polling(
                self.bot, 
                allowed_updates=["message", "callback_query"],
                skip_updates=True
            )
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise
        finally:
            if self.redis:
                await self.redis.close()

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