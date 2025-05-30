'''
start - регистрация
cancel - отмена текущей операции
rpl - запрос на билеты на матчи РПЛ 
other_games - запрос на билеты на другие спортивные события
events - запрос на билеты на прочие мероприятия
add_rpl_games - добавить расписание матчей РПЛ в базу
add_other_game - добавить в базу другое спортивное событие
add_event - добавить в базу мероприятие
report - список подавших заявки на актуальные события
'''

# from datetime import datetime, timedelta, timezone
# tz = timezone(timedelta(hours=3))
# dt_now = datetime.now(tz=tz)
# weekday = dt_now.weekday()
# time = dt_now.time()

# dt = datetime.strptime('04:00', r'%H:%M')
# print(weekday, time, dt.hour)

# if weekday >= 3 and time.hour > 5:
#     print('ooops')


# a = {}

# if a.setdefault('fff') == 'fff':
#     print(True)

# print(a)


# from pathlib import Path

# import pandas
# import psycopg
# import os

# dir_main = Path(__file__).parent

# file_path = Path(dir_main, 'data', 'test_excel_import.xlsx')

# df = pandas.read_excel(file_path)

# df = df.replace({float('nan'): None})

# events_list = []

# for line in df.values:
#     print(line)
#     event_time = datetime.strptime(str(line[4]), r'%H:%M:%S')
#     event_dt = datetime.strptime(
#         str(line[3]), r'%Y-%m-%d %H:%M:%S'
#     ) + timedelta(hours=event_time.hour, minutes=event_time.minute)
#     event = [
#         line[0],
#         line[1],
#         line[2],
#         event_dt,
#         line[5],
#         line[6],
#         True if line[7] == 'да' else False,
#         True if line[8] == 'да' else False,
#     ]
#     events_list.append(event)

# db_name = os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rplwinlinetest'
# db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

# conn = psycopg.connect(
#     autocommit=True,
#     dbname=db_name,
#     user='postgres',
#     password='1I1DG5reb8Cf9BeP',
#     host=db_host,
#     port=5432,
# )
# cur = conn.cursor()

# for event in events_list:
#     print(event)
#     with conn.transaction():
#         query = (
#             'INSERT INTO events (event_category, event_type, event_title, event_datetime,'
#             ' event_location, event_description, event_parking, event_fan_id)'
#             ' VALUES (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', {}, {})'
#             ' ON CONFLICT DO NOTHING;'
#         ).format(
#             event[0],
#             event[1],
#             event[2],
#             event[3],
#             event[4],
#             event[5],
#             event[6],
#             event[7],
#         )
#         cur.execute(query)
    # try:
    #     logging.info(f'{CYAN}db query: {query}')
    #     cur.execute(query)
    # except Exception as e:
    #     logging.error(f'{RED}db error:', exc_info=True)
    #     conn.rollback()
    #     sent_message = await context.bot.send_message(
    #         chat_id=update.effective_user.id,
    #         text='Что-то пошло не так. Попробуй повторить позже',
    #     )
    #     logging.info(
    #         f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    #     )
    #     return ConversationHandler.END

import re

# if re.fullmatch(r'\d{3} \d{3} \d{3}', '111 111 111'):
#     print(1)

# a = 'as111df asg  asdg 3123asdga $$#!/--asg'

# a = re.sub(r'\D', r'', a)

# print(a)

# int('')

if re.fullmatch(r'\d{1,}', '123'):
    print(True)

#     ['РПЛ ' 'матч' 'Акрон- Пари НН' Timestamp('2024-10-05 00:00:00')
#     datetime.time(14, 0) '"Солидарность Самара Арена"' 'Самара' 'да' 'да']

#     ['РПЛ' 'матч' 'Рубин - Крылья Советов' Timestamp('2024-09-16 00:00:00')
#  datetime.time(11, 0) '«Ак Барс Арена»' None 'да' 'да']