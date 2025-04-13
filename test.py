
import asyncio
from collections import defaultdict
from typing import Dict, List
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument

from bot import bot

router =Router()


CHANNEL_ID = -1002478734152

media_groups: Dict[str, List[Message]] = defaultdict(list)
timers: Dict[str, asyncio.Task] = {}


async def process_media_group(media_group_id: str):
    await asyncio.sleep(10)  # Даем время на получение всех частей группы
    messages = media_groups.pop(media_group_id, [])

    if not messages:
        return

    # Собираем медиа для альбома
    media = []
    for idx, msg in enumerate(messages):
        if msg.photo:
            file_id = msg.photo[-1].file_id
            item = InputMediaPhoto(media=file_id)
        elif msg.video:
            file_id = msg.video.file_id
            item = InputMediaVideo(media=file_id)
        elif msg.document:
            file_id = msg.document.file_id
            item = InputMediaDocument(media=file_id)
        else:
            continue

        # Добавляем подпись только к первому элементу
        if idx == 0 and msg.caption:
            item.caption = msg.caption
            # Исправление здесь: проверяем наличие parse_mode
            if hasattr(msg, 'parse_mode'):
                item.parse_mode = msg.parse_mode

        media.append(item)

    if media:
        try:
            await bot.send_media_group(chat_id=USER_ID, media=media)
        except Exception as e:
            print(f"Ошибка отправки медиагруппы: {e}")


@router.channel_post()
async def handle_channel_post(message: Message):
    if message.chat.id != CHANNEL_ID:
        return

    # Обработка медиагрупп
    if message.media_group_id:
        media_group_id = message.media_group_id

        # Отменяем предыдущий таймер для этой группы
        if media_group_id in timers:
            timers[media_group_id].cancel()

        media_groups[media_group_id].append(message)

        # Запускаем новый таймер
        timers[media_group_id] = asyncio.create_task(
            process_media_group(media_group_id)
        )
    else:
        # Обычное сообщение (не медиагруппа)
        try:
            await message.forward(chat_id=USER_ID)
        except Exception as e:
            print(f"Ошибка пересылки: {e}")
