import gspread
from oauth2client.service_account import ServiceAccountCredentials

from pathlib import Path
from datetime import datetime, timedelta
import pandas

dir_main = Path(__file__).parent
credentials_file = Path(dir_main, 'data', 'auth.json')
# Определение области доступа
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Авторизация через credentials.json (сервисный аккаунт)
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)

# Авторизация клиента
client = gspread.authorize(creds)

# Открытие таблицы по ее ID
spreadsheet = client.open_by_key('1JgTNN2npcsLT8v0BpNWQSWjq-8DX5gc5CeY9uoseb1c')

# Выбор конкретного листа (можно по имени)
worksheet = spreadsheet.worksheet('Лист1')

# Получить все данные с листа как список списков
data = worksheet.get_all_values()

# Печать всех данных
for row in data:
    print(row)

# Получить данные из конкретной ячейки
cell = worksheet.cell(1, 1).value  # Получение значения ячейки A1
print(cell)
