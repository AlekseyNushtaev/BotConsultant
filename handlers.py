import asyncio
import csv
import datetime
import openpyxl
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import bot
from spread import get_sheet

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter, ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, FSInputFile, InlineKeyboardButton, InputMediaPhoto, \
    InputMediaVideo, InputMediaDocument
from collections import defaultdict
from typing import Dict, List
from config import ADMIN_IDS, CHANEL_ID
from db.util import add_user_to_db, update_user_blocked, update_user_unblocked, add_question_to_db, get_all_questions, \
    delete_all_questions, get_all_users
from keyboard import create_kb

router = Router()

media_groups: Dict[str, List[Message]] = defaultdict(list)
timers: Dict[str, asyncio.Task] = {}
builder = InlineKeyboardBuilder()

builder.row(InlineKeyboardButton(text="Записаться на консультацию ✅", callback_data="quest_1"))
builder.row(InlineKeyboardButton(text="Подписаться на телеграм канал", url="https://t.me/andreikuvshinov"))

main_keyboard_markup = builder.as_markup()

class FSMFillForm(StatesGroup):
    get_full_name = State()
    get_question = State()
    get_contact = State()


async def scheduler(time):
    while True:
        await asyncio.sleep(10)
        print(datetime.datetime.now())
        try:
            sheet = await get_sheet()
            sheet.clear()
            quests = get_all_questions()
            users = get_all_users()
            sheet.append_rows(quests)
            sheet.append_rows(users)
            empty_row = ['' for cell in range(sheet.col_count)]
            sheet.insert_row(empty_row, len(quests) + 1)
            print(datetime.datetime.now())
        except Exception as e:
            await bot.send_message(1012882762, str(e))
        await asyncio.sleep(time)


async def process_media_group(media_group_id: str):
    await asyncio.sleep(5)  # Даем время на получение всех частей группы
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
        users = get_all_users()
        cnt = 0
        for user in users[1:]:
            if not user[6]:
                try:
                    await bot.send_media_group(chat_id=int(user[1]), media=media)
                    await asyncio.sleep(0.2)
                    cnt += 1
                except Exception as e:
                    print(f"Ошибка отправки медиагруппы: {e}")
        await bot.send_message(1012882762, f'Переслано {cnt} юзерам')


@router.message(CommandStart(), StateFilter(default_state))
async def process_start_user(message: Message):
    add_user_to_db(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
        datetime.datetime.now()
    )
    await message.answer_video_note('DQACAgIAAxkBAAMkZ7YTobVOP3LcI_-weFilb18kwXkAAiJtAALpnalJe1wSU2ZnRM82BA')
    await asyncio.sleep(0.3)
    await message.answer(
        text="""
Здравствуйте! 👋🏻

Вы попали в официальный бот Андрея Кувшинова – бизнес-юриста.

🔹 Здесь вы можете оставить заявку на бесплатную юридическую консультацию по вопросам корпоративного права, банкротства и защиты бизнеса.

📌 Как оставить заявку?
Просто нажмите на кнопку ниже и заполните короткую форму – мы свяжемся с вами в ближайшее время.

💼 Помогаем бизнесу решать сложные юридические вопросы просто и эффективно!
        """,
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard_markup
    )
    await asyncio.sleep(1)
    await message.answer(text="""
📘 Мы в ЮК «СТАРТ» не просто юристы — мы ваши антикризисные союзники. Подготовили для вас 2 практичных гайда, которые помогут пережить налоговую проверку и не утонуть в кризисе.

📍 Первый гайд — антикризисное руководство для логистики: как договориться с лизингом и банками, что делать с дебиторкой, как не слить имущество и не угодить под субсидиарку.

📍 Второй — про налоговые проверки 2025: что ждать, как действовать, что говорить (а главное — чего не говорить), чтобы не оказаться в плане выездной.

🎁 Эти гайды — не вода, а конкретика и опыт. *Скачивайте, читайте и действуйте*. Пока другие в панике — вы уже на шаг впереди. Ссылки ниже 👇  
    """,
                         reply_markup=create_kb(1,
                                                faq_1='Гайд "Как сохранить логистический бизнес"',
                                                faq_2='Гайд по Налоговым проверкам 2025'))


@router.callback_query(F.data == 'quest_1', StateFilter(default_state))
async def step_1(cb: CallbackQuery, state: FSMContext):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    await cb.message.answer(text="""
Отлично, теперь напишите как к Вам обращаться?      
    """)
    await state.set_state(FSMFillForm.get_full_name)


@router.callback_query(F.data == 'new', StateFilter(default_state))
async def step_1_1(cb: CallbackQuery, state: FSMContext):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    await cb.message.answer(text="""
Отлично, теперь напишите как к Вам обращаться?     
    """)
    await state.set_state(FSMFillForm.get_full_name)


@router.message(F.text, StateFilter(FSMFillForm.get_full_name))
async def step_2(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(text='Отлично, какой у вас вопрос?')
    await state.set_state(FSMFillForm.get_question)


@router.message(F.text, StateFilter(FSMFillForm.get_question))
async def step_3(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer(text='Оставьте свои контактные данные (номер телефона или email)',
                         reply_markup=create_kb(1, telegram="Связаться в телеграм"))
    await state.set_state(FSMFillForm.get_contact)


@router.message(F.text, StateFilter(FSMFillForm.get_contact))
async def step_4_1(message: types.Message, state: FSMContext):
    contact = message.text
    dct = await state.get_data()
    add_question_to_db(message.from_user.id, dct['full_name'], dct['question'], contact, datetime.datetime.now())
    await state.set_state(default_state)
    await state.clear()
    await message.answer(text='''
Спасибо, ваша заявка оформлена, в ближайшее время с Вами свяжутся.
    
💼 Подписывайтесь в соц. сетях, чтобы разбираться в законах без сложных терминов:
🔹 YouTube (https://www.youtube.com/@urstart)
🔹 VK (https://vk.com/club229212039)
🔹 VC (https://vc.ru/u/4590675-andrei-kuvshinov-biznes-yurist)
🔹 Дзен (https://dzen.ru/id/5de8bbf3c7e50cf95e813aaa)
    ''',
                         reply_markup=create_kb(1,
                                                new='Записаться на консультацию ✅',
                                                faq='Хочу гайд')
                         )


@router.callback_query(F.data == 'telegram', StateFilter(FSMFillForm.get_contact))
async def step_4_2(cb: types.CallbackQuery, state: FSMContext):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    dct = await state.get_data()
    add_question_to_db(cb.from_user.id, dct['full_name'], dct['question'], 'Написать в телеграме', datetime.datetime.now())
    await state.set_state(default_state)
    await state.clear()
    await cb.message.answer(text='''
Спасибо, ваша заявка оформлена, в ближайшее время с Вами свяжутся.
    
💼 Подписывайтесь в соц. сетях, чтобы разбираться в законах без сложных терминов:
🔹 YouTube (https://www.youtube.com/@urstart)
🔹 VK (https://vk.com/club229212039)
🔹 VC (https://vc.ru/u/4590675-andrei-kuvshinov-biznes-yurist)
🔹 Дзен (https://dzen.ru/id/5de8bbf3c7e50cf95e813aaa)
    ''',
                            reply_markup=create_kb(1,
                                                   new='Записаться на консультацию ✅',
                                                   faq='Хочу гайд'))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    update_user_blocked(event.from_user.id)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    update_user_unblocked(event.from_user.id)


@router.message(F.video_note, F.from_user.id.in_(ADMIN_IDS))
async def get_note(message: types.Message):
    print(message.video_note.file_id)


@router.message(F.text == 'Excel', F.from_user.id.in_(ADMIN_IDS), StateFilter(default_state))
async def excel(message: types.Message):
    quests = get_all_questions()
    users = get_all_users()
    wb = openpyxl.Workbook()
    sh = wb['Sheet']
    for i in range(1, len(quests) + 1):
        for y in range(1, 12):
            if quests[i-1][y-1]:
                sh.cell(i, y).value = quests[i-1][y-1]
    for i in range(len(quests) + 2, len(quests) + 2 + len(users)):
        for y in range(1, 8):
            if users[i - len(quests) - 2][y-1]:
                sh.cell(i, y).value = users[i - len(quests) - 2][y-1]
    wb.save('questions.xlsx')
    await message.answer_document(FSInputFile('questions.xlsx'))


@router.message(F.text == 'Csv', F.from_user.id.in_(ADMIN_IDS), StateFilter(default_state))
async def csv(message: types.Message):
    quests = get_all_questions()
    with open('questions.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(quests)
    await message.answer_document(FSInputFile('questions.csv'))


@router.message(F.text == 'Delete_all', F.from_user.id.in_([1012882762]), StateFilter(default_state))
async def delete_all(message: Message):
    delete_all_questions()


@router.callback_query(F.data == 'faq_1', StateFilter(default_state))
async def faq(cb: CallbackQuery):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    await cb.message.answer_document(FSInputFile('Гайд Как сохранить логистический бизнес.pdf'),
                                     reply_markup=create_kb(1,
                                                            quest_1="Записаться на консультацию ✅"))

@router.callback_query(F.data == 'faq_2', StateFilter(default_state))
async def faq(cb: CallbackQuery):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    await cb.message.answer_document(
        FSInputFile('Гайд по Налоговым проверкам 2025.pdf'),
        reply_markup=create_kb(1,
                               quest_1="Записаться на консультацию ✅"))


@router.callback_query(F.data == 'faq', StateFilter(default_state))
async def faq(cb: CallbackQuery):
    add_user_to_db(
        cb.from_user.id,
        cb.from_user.username,
        cb.from_user.first_name,
        cb.from_user.last_name,
        datetime.datetime.now()
    )
    await cb.message.answer(text="""
📘 Мы в ЮК «СТАРТ» не просто юристы — мы ваши антикризисные союзники. Подготовили для вас 2 практичных гайда, которые помогут пережить налоговую проверку и не утонуть в кризисе.

📍 Первый гайд — антикризисное руководство для логистики: как договориться с лизингом и банками, что делать с дебиторкой, как не слить имущество и не угодить под субсидиарку.

📍 Второй — про налоговые проверки 2025: что ждать, как действовать, что говорить (а главное — чего не говорить), чтобы не оказаться в плане выездной.

🎁 Эти гайды — не вода, а конкретика и опыт. *Скачивайте, читайте и действуйте*. Пока другие в панике — вы уже на шаг впереди. Ссылки ниже 👇  
    """,
                         reply_markup=create_kb(1,
                                                faq_1='Гайд "Как сохранить логистический бизнес"',
                                                faq_2='Гайд по Налоговым проверкам 2025'))


@router.channel_post()
async def handle_channel_post(message: Message):
    if message.chat.id != CHANEL_ID:
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
        users = get_all_users()
        cnt = 0
        for user in users[1:]:
            if not user[6]:
                try:
                    await message.forward(chat_id=int(user[1]))
                    await asyncio.sleep(0.2)
                    cnt += 1
                except Exception as e:
                    print(f"Ошибка пересылки: {e}")
        await bot.send_message(1012882762, f'Переслано {cnt} юзерам')
