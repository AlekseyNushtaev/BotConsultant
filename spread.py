import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Данные для доступа к Google Таблице
SERVICE_ACCOUNT_FILE = 'creds.json'
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID_QUEST = '1EJpnscQbDO7_zaWeFcj3bKhntON4W0uK3H5cGo9QTYI'
SPREADSHEET_ID_USER = '16iKOI2lehCARQf7OtXE0wIWsuqplQB416chxWybF_QI'

# Функция для авторизации в Google Таблицах
async def get_sheet_questions():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID_QUEST).sheet1
    return sheet


async def get_sheet_users():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID_USER).sheet1
    return sheet


