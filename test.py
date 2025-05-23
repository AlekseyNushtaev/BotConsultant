import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import asyncio

TOKEN = "7467186280:AAFrTYhr5SBy-EDyGr3vGUvGglUePUxpNZc"
dp = Dispatcher()

# Создаем inline-клавиатуру с кнопкой
def get_participate_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Принять участие", callback_data="participate")
    return builder.as_markup()

# Обработчик команды /post (только для групповых чатов)
@dp.message(Command("post"), F.chat.type.in_({"group", "supergroup"}))
async def post_message(message: types.Message):
    await message.answer(
        "🎉 Примите участие в нашем мероприятии!",
        reply_markup=get_participate_keyboard()
    )

# Обработчик нажатия на кнопку
@dp.callback_query(F.data == "participate")
async def handle_participation(callback: types.CallbackQuery, bot: Bot):
    user = callback.from_user
    try:
        # Пытаемся отправить сообщение в личку
        await bot.send_message(
            chat_id=user.id,
            text=f"Привет, {user.first_name}! Спасибо за участие! 🎉"
        )
        await callback.answer("✅ Проверьте свои личные сообщения!")
    except Exception as e:
        # Если не удалось отправить сообщение
        error_message = f"❌ {user.first_name}, пожалуйста, напишите мне в личку сначала!"
        await callback.answer(error_message, show_alert=True)
        logging.error(f"Error sending message to {user.id}: {e}")

async def main():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


logging.basicConfig(level=logging.INFO)
asyncio.run(main())