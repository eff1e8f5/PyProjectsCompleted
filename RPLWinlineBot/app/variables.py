import os
from datetime import timedelta, timezone
from pathlib import Path

import psycopg

RESET = '\033[0m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
GREEN = '\033[32;1m'
MAGENTA = '\033[35;1m'
RED = '\033[31;1m'
YELLOW = '\033[33;1m'

tz = timezone(timedelta(hours=3))
dir_main = Path(__file__).parent

bot_name = os.getenv('BOT_NAME') if os.getenv('BOT_NAME') else 'TEST BOT'
token = (
    os.getenv('TOKEN')
    if os.getenv('TOKEN')
    else '7119933091:AAHeuezqI-FjWdX6T3zsogcsKUOGFHx-xy4'
)
db_name = 'rplwinlinetest'
# db_name = os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rplwinlinetest'
db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

conn = psycopg.connect(
    autocommit=True,
    dbname=db_name,
    user='postgres',
    password='1I1DG5reb8Cf9BeP',
    host=db_host,
    port=5432,
)

cur = conn.cursor()
