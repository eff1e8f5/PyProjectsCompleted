# a = '2024-10-24 15:00:00'

# print(a[5:-3])


import datetime

a = datetime.datetime(2024, 10, 24, 15, 0).strftime(r'%d.%m %H:%M')
print(a)

# print(f'{a.day}.{a.month} {a.hour}:{a.minute}')

# print(datetime.datetime.strptime(datetime.datetime(2024, 10, 24, 15, 0), r'%Y-%m-%d'))

