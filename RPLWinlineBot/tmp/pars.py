from datetime import datetime
import re
import psycopg
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s:%(funcName)s - %(message)s',
)

# dt_text = '20.07.2024 15:00'

# dt = datetime.strptime(dt_text, r'%d.%m.%Y %H:%M')
# print(dt)

# if dt > datetime.now():
#     print(True)

data = '''Локомотив - Акрон

-:-

20.07.2024
15:00

«РЖД Арена»

Крылья Советов - Зенит

-:-

20.07.2024
17:30

«Солидарность Самара Арена»

Ростов - ПФК ЦСКА

-:-

20.07.2024
20:00

«Ростов Арена»

Динамо - Факел

-:-

20.07.2024
20:00

«ВТБ Арена»

Оренбург - Спартак-Москва

-:-

21.07.2024
17:30

«Газовик»

Химки - Динамо (Мх)

-:-

21.07.2024
20:00

«Арена Химки»

Ахмат - Краснодар

-:-

21.07.2024
20:00

«Ахмат Арена»

Пари НН - Рубин

-:-

22.07.2024
20:00

«Нижний Новгород»'''

data = data.split('\n\n')

if not re.fullmatch(r'.+ - .+', data[0]):
    print('pupupu')
    exit()

# games = []
query = 'INSERT INTO games_main (teams, dt, stadium) VALUES '
for i in range(0, len(data), 4):
    teams = data[i]
    dt = datetime.strptime(data[i + 2], r'%d.%m.%Y %H:%M')
    stadium = data[i + 3]
    query += '(\'{}\', \'{}\', \'{}\'), '.format(teams, dt, stadium)
query = f'{query[:-2]} ON CONFLICT DO NOTHING;'
print(query)
# query = f' ON CONFLICT DO NOTHING;'
#     games.append(
#         [
#             data[i],
#             datetime.strptime(data[i + 2], r'%d.%m.%Y %H:%M'),
#             data[i + 3],
#         ],
#     )
# print(games)
# print(data.split('\n\n'))
# for i in data.split('\n\n'):
#     if re.fullmatch(r'.+ - .+', i):
#         print(i)
# conn = psycopg.connect(
#     autocommit=True,
#     dbname='rplwinlinetest',
#     user='postgres',
#     password='1I1DG5reb8Cf9BeP',
#     host='192.168.1.250',
#     port=5432,
# )

# cur = conn.cursor()
# try:
#     cur.execute(query)
# except Exception as e:
#     logging.error(f'error:', exc_info=True)
