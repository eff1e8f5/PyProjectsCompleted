import logging
import os
from datetime import datetime, timedelta, timezone

import colorama
import pandas
import psycopg

colorama.init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s:%(funcName)s - %(message)s',
)

logging.getLogger('httpx').setLevel(logging.WARNING)

# BLUE = colorama.Fore.BLUE
# CYAN = colorama.Fore.CYAN
# GREEN = colorama.Fore.GREEN
# MAGENTA = colorama.Fore.MAGENTA
# RED = colorama.Fore.RED
# YELLOW = colorama.Fore.YELLOW

RESET = '\033[0m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
GREEN = '\033[32;1m'
MAGENTA = '\033[35;1m'
RED = '\033[31;1m'
YELLOW = '\033[33;1m'

tz = timezone(timedelta(hours=3))

db_name = os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rtfest_summer_2024'
db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

conn = psycopg.connect(
    dbname=db_name,
    user='postgres',
    password='1I1DG5reb8Cf9BeP',
    host=db_host,
    port=5432,
)

cursor = conn.cursor()

query = f'''
            SELECT * FROM
                teams
            ORDER BY
                team_id
            ASC;
        '''
cursor.execute(query)
response = cursor.fetchall()
# print(response)

teams = {}

for line in response:
    teams[line[0]] = line[1]

# for team in teams:
#     print(team)

query = f'''
            SELECT * FROM
                participants
            ORDER BY
                participant_id
            ASC;
        '''
cursor.execute(query)
response = cursor.fetchall()

print(len(response))

participants = []

for line in response:
    if line[3]:
        participant = [
            '' if line[1] == 'None' else f'@{line[1]}',
            line[2],
            line[3],
            line[4],
            line[5],
            line[6],
            line[7],
            line[8],
            teams[line[9]] if line[9] else '',
            'капитан' if line[10] else '',
            'хочет в команду' if line[11] else '',
        ]
        match participant[7]:
            case 'fan':
                participant[7] = 'болельщик'
            case 'big_games':
                participant[7] = 'большие игры'
            case 'volleyball':
                participant[7] = 'волейбол'
            case 'football':
                participant[7] = 'футбол'
            case 'tennis':
                participant[7] = 'теннис'
            case _:
                participant[7] = 'болельщик'

        participants.append(participant)
print(len(participants))
# for participant in participants:
#     print(participant)

report = pandas.DataFrame(
    data=participants,
    columns=[
        'telegram',
        'id',
        'имя',
        'фамилия',
        'телефон',
        'email',
        'ДЗО',
        'активность',
        'команда',
        'капитан',
        'хочет в команду',
    ],
)

file_name = (
    f'report_{datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M")}.xlsx'
)

with pandas.ExcelWriter(file_name) as writer:
    report.to_excel(writer, sheet_name='отчёт', index=False)
