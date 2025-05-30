import logging
import os
from datetime import datetime, timedelta, timezone

import colorama
import pandas
import psycopg
from pathlib import Path

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

db_name = (
    os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rtfest_summer_2024_test'
)
# db_name = os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rtfest_summer_2024'
db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

conn = psycopg.connect(
    dbname=db_name,
    user='postgres',
    password='1I1DG5reb8Cf9BeP',
    host=db_host,
    port=5432,
)

cursor = conn.cursor()
events = {
    'playstation': 'PlayStation',
    'kinect': 'Kinect',
    'vr_bow': 'VR лук',
    'wrestling': 'Треслинг',
    'shooting_gallery': 'Тир',
    'chess': 'Шахматы',
    'tilt_bench': 'Скамья для наклонов',
    'press_bench': 'Скамья для пресса',
    'low_crossbar_for_pushups': 'Низкая перекладина для отжимания',
    'pulling_up_from_the_hanging_position': 'Подтягивание из положения виса',
    'horizontal_bar_for_pulling_up': 'Турник для подтягивания',
    'cancel': 'отмена',
}


def checkin_report():
    # select p.participant_id, p.first_name, p.last_name, p.phone_number, p.username
    # from checkin c join participants p on c.telegram_id = p.telegram_id order by p.participant_id asc;

    try:
        query = (
            'SELECT p.participant_id, p.first_name, p.last_name, p.phone_number,'
            ' p.username FROM checkin c JOIN participants p'
            ' ON c.telegram_id = p.telegram_id ORDER BY p.last_name asc;'
        )
        logging.info(f'{CYAN}db query: {query}')
        response = cursor.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)

        # sent_message = await context.bot.send_message(
        #     chat_id=update.effective_user.id,
        #     text='Что-то пошло не так. Попробуй повторить позже',
        # )

    participants = []
    for line in response:
        participants.append(
            [
                line[0],
                line[1],
                line[2],
                line[3],
                '' if line[4] == 'None' else f'@{line[4]}',
            ]
        )

    report = pandas.DataFrame(
        data=participants,
        columns=[
            'id',
            'имя',
            'фамилия',
            'телефон',
            'telegram',
        ],
    )

    file_name = 'checkin_report_{}.xlsx'.format(
        datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M")
    )
    dir_main = Path(__file__).parent
    with pandas.ExcelWriter(path=Path(dir_main, 'data', file_name)) as writer:
        report.to_excel(writer, sheet_name='отчёт', index=False)


def events_report():
    participants = []
    for event in events.keys():
        if event == 'cancel':
            pass
        else:
            try:
                query = (
                    'SELECT e.{0}, p.first_name, p.last_name, p.phone_number,'
                    ' p.participant_id, p.username FROM events e JOIN participants p'
                    ' ON e.telegram_id = p.telegram_id'
                    ' WHERE e.{0} > 0 ORDER BY e.{0} DESC;'
                ).format(event)
                logging.info(f'{CYAN}db query: {query}')
                response = cursor.execute(query=query).fetchall()
                logging.info(f'{CYAN}db response: {response}')
            except Exception as e:
                logging.error(f'{RED}db error:', exc_info=True)

                # sent_message = await context.bot.send_message(
                #     chat_id=update.effective_user.id,
                #     text='Что-то пошло не так. Попробуй повторить позже',
                # )

                # logging.info(
                #     f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
                # )
                return
            participants.append([events[event]])
            for line in response:
                if line[0] == 0:
                    pass
                else:
                    participants.append(
                        [
                            line[0],
                            line[1],
                            line[2],
                            line[3],
                            line[4],
                            '' if line[5] == 'None' else f'@{line[5]}',
                        ]
                    )
            participants.append([])

    report = pandas.DataFrame(
        data=participants,
        columns=[
            'баллы',
            'id',
            'имя',
            'фамилия',
            'телефон',
            'telegram',
        ],
    )

    file_name = 'events_report_{}.xlsx'.format(
        datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M")
    )
    dir_main = Path(__file__).parent
    with pandas.ExcelWriter(path=Path(dir_main, 'data', file_name)) as writer:
        report.to_excel(writer, sheet_name='отчёт', index=False)


def participants_report():
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


if __name__ == '__main__':
    events_report()
