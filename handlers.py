import asyncio
import csv
import datetime
import openpyxl

from bot import bot
from spread import get_sheet

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter, ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, FSInputFile

from config import ADMIN_IDS
from db.util import add_user_to_db, update_user_blocked, update_user_unblocked, add_question_to_db, get_all_questions, \
    delete_all_questions
from keyboard import create_kb


router = Router()


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
            sheet.append_rows(quests)
            print(datetime.datetime.now())
        except Exception as e:
            await bot.send_message(1012882762, str(e))
        await asyncio.sleep(time)


@router.message(CommandStart(), StateFilter(default_state))
async def process_start_user(message: Message):
    add_user_to_db(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
        datetime.datetime.now()
    )
    # await message.answer_video_note('DQACAgIAAxkBAAMkZ7YTobVOP3LcI_-weFilb18kwXkAAiJtAALpnalJe1wSU2ZnRM82BA')
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
        reply_markup=create_kb(1,
                               quest_1="✅Оставить заявку на консультацию"
                               )
    )
    await asyncio.sleep(1)
    await message.answer(text="""
📘 Мы подготовили серию практичных PDF-гайдов от экспертов с опытом 12+ лет — для предпринимателей, которые хотят действовать уверенно в любой ситуации.

🔹 Поддержка бизнеса в условиях неопределённости
🔹 Юридическая защита и грамотное сопровождение
🔹 Снижение рисков и сохранение активов
🔹 Оптимизация процессов и расходов

👇 Все материалы — бесплатно. Выберите нужный гайд по кнопкам ниже:   
    """,
                         reply_markup=create_kb(1,
                                                faq_1='Руководство для логистического бизнеса в кризис',
                                                faq_2='Гайд по Налоговым проверкам 2025'))


@router.callback_query(F.data == 'quest_1', StateFilter(default_state))
async def step_1(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(text="""
Отлично, теперь напишите как к Вам обращаться?      
    """)
    await state.set_state(FSMFillForm.get_full_name)


@router.callback_query(F.data == 'new', StateFilter(default_state))
async def step_1_1(cb: CallbackQuery, state: FSMContext):
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
                                                new='Создать новую заявку',
                                                faq='Хочу гайд')
                         )


@router.callback_query(F.data == 'telegram', StateFilter(FSMFillForm.get_contact))
async def step_4_2(cb: types.CallbackQuery, state: FSMContext):
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
                                                   new='Создать новую заявку',
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
    wb = openpyxl.Workbook()
    sh = wb['Sheet']
    for i in range(1, len(quests) + 1):
        for y in range(1, 11):
            if quests[i-1][y-1]:
                sh.cell(i, y).value = quests[i-1][y-1]
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
    await cb.message.answer_document(FSInputFile('Руководство для логистического бизнеса в кризис.pdf'),
                                     reply_markup=create_kb(1,
                                                            quest_1="✅Оставить заявку на консультацию"))

@router.callback_query(F.data == 'faq_2', StateFilter(default_state))
async def faq(cb: CallbackQuery):
    await cb.message.answer_document(
        FSInputFile('Гайд по Налоговым проверкам 2025.pdf'),
        reply_markup=create_kb(1,
                               quest_1="✅Оставить заявку на консультацию"))


@router.callback_query(F.data == 'faq', StateFilter(default_state))
async def faq(cb: CallbackQuery):
    await cb.message.answer(text="""
📘 Мы подготовили серию практичных PDF-гайдов от экспертов с опытом 12+ лет — для предпринимателей, которые хотят действовать уверенно в любой ситуации.

🔹 Поддержка бизнеса в условиях неопределённости
🔹 Юридическая защита и грамотное сопровождение
🔹 Снижение рисков и сохранение активов
🔹 Оптимизация процессов и расходов

👇 Все материалы — бесплатно. Выберите нужный гайд по кнопкам ниже:   
    """,
                         reply_markup=create_kb(1,
                                                faq_1='Руководство для логистического бизнеса в кризис',
                                                faq_2='Гайд по Налоговым проверкам 2025'))
