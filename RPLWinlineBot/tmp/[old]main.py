import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from warnings import filterwarnings
import asyncio
import colorama
import psycopg
from telegram import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    InvalidCallbackData,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning
import re
import pandas

colorama.init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s:%(funcName)s - %(message)s',
)

logging.getLogger('httpx').setLevel(logging.WARNING)
filterwarnings(
    action='ignore', message=r'.*CallbackQueryHandler', category=PTBUserWarning
)

tz = timezone(timedelta(hours=3))
dir_main = Path(__file__).parent

admin_group = -4245235791

RESET = '\033[0m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
GREEN = '\033[32;1m'
MAGENTA = '\033[35;1m'
RED = '\033[31;1m'
YELLOW = '\033[33;1m'

REGISTRATION = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO users (telegram_id, username, first_name, last_name)'
        ' VALUES ({}, \'{}\', \'{}\', \'{}\')'
        ' ON CONFLICT DO NOTHING;'
    ).format(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
        update.message.text,
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Для регистрации отправь свой корпоративный email',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return REGISTRATION


async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    query = 'UPDATE users SET email = \'{}\' WHERE telegram_id = {};'.format(
        update.message.text,
        update.effective_user.id,
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END
    if '@winline.ru' in update.message.text:
        text = (
            'Привет\n\n'
            'В этом боте ты можешь подать заявку на различные мероприятия: матчи Российской Премьер-Лиги\n\n'
            'Для получения билетов оформи заявку, отправив одну из команд:\n'
            '/rpl - на матчи Российской Премьер-Лиги\n'
            '/other_games - на другие матчи и спортивные события\n'
            '/events - на разные мероприятия\n\n'
            'эти команды доступны так же в меню этого чата\n'
            '👇 вот тут'
        )
    else:
        text = 'Спасибо за регистрацию'
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


async def set_me_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return
    if response:
        if 'winline.ru' in response[0][4]:
            pass
        else:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='Извини, но ты не являешься нашим сотрудником. Или указал неверные данные при регистрации',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Ты не прошёл регистрацию. Для регистрации отправь команду /start',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    query = 'UPDATE users SET is_admin = true WHERE telegram_id = {};'.format(
        update.effective_user.id
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'Теперь у тебя админские права в это боте\n\n'
            'Тебе доступны следующие команды:\n'
            '/add_rpl_games - добавить расписание матчей РПЛ в базу\n'
            '/add_other_game - добавить в базу другое спортивное событие\n'
            '/add_event - добавить в базу мероприятие\n'
            '/report - список подавших заявки на актуальные события\n'
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


INPUT_RPL_GAMES, INPUT_RPL_GAMES_HANDLE = range(2)


async def add_rpl_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {} and is_admin = true;'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        pass
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Недостаточно прав. Обратись к администраторам',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'отправь скопированную таблицу расписания с '
            'https://premierliga.ru/calendar/'
        ),
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return INPUT_RPL_GAMES


async def input_rpl_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    data = update.message.text
    data = data.split('\n\n')

    if re.fullmatch(r'.+ - .+', data[0]):
        query = (
            'INSERT INTO rpl_games (game_teams, game_dt, game_location) VALUES '
        )
        for i in range(0, len(data), 4):
            query += '(\'{}\', \'{}\', \'{}\'), '.format(
                data[i],
                datetime.strptime(data[i + 2], r'%d.%m.%Y %H:%M'),
                data[i + 3],
            )
        query = f'{query[:-2]} ON CONFLICT DO NOTHING;'
        try:
            logging.info(f'{CYAN}db query: {query}')
            cur.execute(query)
        except Exception as e:
            logging.error(f'{RED}db error:', exc_info=True)
            conn.rollback()
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='Что-то пошло не так. Попробуй повторить позже',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return ConversationHandler.END
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='игры добавлены',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='проверь отправленные данные и попробуй ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )


(
    ADD_OTHER_GAME_INPUT_TEAMS,
    ADD_OTHER_GAME_INPUT_DATE,
    ADD_OTHER_GAME_INPUT_LOCATION,
    ADD_OTHER_GAME_INPUT_SPORT,
    ADD_OTHER_GAME_CONFIRMATION,
) = range(5)


async def add_other_game_init(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {} and is_admin = true;'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        pass
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Недостаточно прав. Обратись к администраторам',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'Добавление игры не РПЛ.\n\nОтправь название матча.\n\n'
            'пример: Спартак-Москва - Крылья Советов'
        ),
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_OTHER_GAME_INPUT_TEAMS


async def add_other_game_input_teams(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['game_teams'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'Отправь дату проведения матча в формате ДД.ММ.ГГГГ чч:мм\n\n'
            'пример: 18.08.2024 20:00'
        ),
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_OTHER_GAME_INPUT_DATE


async def add_other_game_input_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        datetime.strptime(update.message.text, r'%d.%m.%Y %H:%M')
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неправильный формат даты.\nПроверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ADD_OTHER_GAME_INPUT_DATE

    context.user_data['game_date'] = datetime.strptime(
        update.message.text, r'%d.%m.%Y %H:%M'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=('Отправь место проведения матча\n\n' 'пример: «ВТБ Арена»'),
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_OTHER_GAME_INPUT_LOCATION


async def add_other_game_input_location(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['game_location'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=('Отправь вид спорта\n\n' 'пример: баскетбол'),
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_OTHER_GAME_INPUT_SPORT


async def add_other_game_input_sport(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['game_sport'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'Проверяем:\n\n'
            'Матч: {}\n'
            'Дата: {}\n'
            'Стадион: {}\n'
            'Вид спорта: {}\n\n'
            'верно?'
        ).format(
            context.user_data['game_teams'],
            context.user_data['game_date'],
            context.user_data['game_location'],
            context.user_data['game_sport'],
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='confirmation',
                    ),
                    InlineKeyboardButton(
                        text='отмена',
                        callback_data='cancel',
                    ),
                ]
            ]
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_OTHER_GAME_CONFIRMATION


async def add_other_game_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO other_games (game_teams, game_dt, game_location, type_sport)'
        ' VALUES (\'{}\', \'{}\', \'{}\', \'{}\') ON CONFLICT DO NOTHING;'
    ).format(
        context.user_data['game_teams'],
        context.user_data['game_date'],
        context.user_data['game_location'],
        context.user_data['game_sport'],
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    context.user_data.clear()

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='матч добавлен',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


(
    ADD_EVENT_INPUT_TITLE,
    ADD_EVENT_INPUT_DATE,
    ADD_EVENT_INPUT_LOCATION,
    ADD_EVENT_INPUT_TYPE,
    ADD_EVENT_INPUT_DESCRIPTION,
    ADD_EVENT_CONFIRMATION,
) = range(6)


async def add_event_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {} and is_admin = true;'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        pass
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Недостаточно прав. Обратись к администраторам',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отправь название мероприятия',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_INPUT_TITLE


async def add_event_input_title(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['event_title'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'Отправь дату проведения мероприятия в формате ДД.ММ.ГГГГ чч:мм\n\n'
            'пример: 18.08.2024 20:00'
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_INPUT_DATE


async def add_event_input_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        datetime.strptime(update.message.text, r'%d.%m.%Y %H:%M')
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неправильный формат даты.\nПроверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ADD_OTHER_GAME_INPUT_DATE

    context.user_data['event_date'] = datetime.strptime(
        update.message.text, r'%d.%m.%Y %H:%M'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отправь место проведения мероприятия\n\n',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_INPUT_LOCATION


async def add_event_input_location(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['event_location'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отправь тип мероприятия\n\nпример: концерт',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_INPUT_TYPE


async def add_event_input_type(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['event_type'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отправь описание мероприятия',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_INPUT_DESCRIPTION


async def add_event_input_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['event_description'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            'Проверяем:\n\n'
            'Название: {}\n'
            'Дата: {}\n'
            'Место проведения: {}\n'
            'Мероприятие: {}\n'
            'Описание: {}\n\n'
            'верно?'
        ).format(
            context.user_data['event_title'],
            context.user_data['event_date'],
            context.user_data['event_location'],
            context.user_data['event_type'],
            context.user_data['event_description'],
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='confirmation',
                    ),
                    InlineKeyboardButton(
                        text='отмена',
                        callback_data='cancel',
                    ),
                ]
            ]
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ADD_EVENT_CONFIRMATION


async def add_event_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO events (event_title, event_dt, event_location, event_type, event_description)'
        ' VALUES (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\') ON CONFLICT DO NOTHING;'
    ).format(
        context.user_data['event_title'],
        context.user_data['event_date'],
        context.user_data['event_location'],
        context.user_data['event_type'],
        context.user_data['event_description'],
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    context.user_data.clear()

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='мероприятие добавлено',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


(
    RPL_GAME_SELECTION,
    RPL_GAME_SELECTION_NUMBER_TICKETS,
    RPL_GAME_SELECTION_PARKING,
    RPL_GAME_SELECTION_FAN_ID,
    RPL_GAME_SELECTION_CONFIRMATION,
) = range(5)


async def rpl_game_selection_init(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END
    if response:
        if 'winline.ru' in response[0][4]:
            pass
        else:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='Извини, но ты не являешься нашим сотрудником. Или указал неверные данные при регистрации',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return ConversationHandler.END
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Ты не прошёл регистрацию. Для регистрации отправь команду /start',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    query = 'SELECT * FROM rpl_games WHERE game_dt > \'{}\' ORDER BY game_dt asc'.format(
        datetime.now()
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        n = 5
        if len(response) / n == len(response) // n:
            total_pages = len(response) // n
        else:
            total_pages = len(response) // n + 1
        page_counter = 1
        context.user_data['keyboard_pages'] = {}
        context.user_data['games'] = {}
        context.user_data['current_page'] = 1
        for i in range(0, len(response), n):
            context.user_data['keyboard_pages'][page_counter] = []
            for item in response[i : i + n]:
                context.user_data['games'][item[0]] = [
                    item[1],
                    item[2],
                    item[3],
                ]
                context.user_data['keyboard_pages'][page_counter].append(
                    [
                        InlineKeyboardButton(
                            text='{} / {} / {}'.format(
                                item[1], item[2], item[3]
                            ),
                            callback_data=f'game_id={item[0]}',
                        ),
                    ]
                )
            if page_counter == 1:
                if total_pages == 1:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            else:
                if page_counter == total_pages:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            page_counter += 1
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='предстоящие матчи\n\nматч / дата / стадион',
            reply_markup=InlineKeyboardMarkup(
                context.user_data['keyboard_pages'][
                    context.user_data['current_page']
                ]
            ),
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return RPL_GAME_SELECTION

    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='в ближайшее время матчей нет',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END


async def rpl_game_selection_switching_pages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    switch_pages = update.callback_query.data.split('=')[1]

    match switch_pages:
        case 'next':
            context.user_data['current_page'] += 1
        case 'previous':
            context.user_data['current_page'] -= 1
        case 'current':
            pass
        case _:
            return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='предстоящие матчи\n\nматч / дата / стадион',
        reply_markup=InlineKeyboardMarkup(
            context.user_data['keyboard_pages'][
                context.user_data['current_page']
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION


async def rpl_game_selection_select_game(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    game_id = int(update.callback_query.data.split('=')[1])
    context.user_data['game_id'] = game_id
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n\n'
            'для оформления тебе необходимо будет указать:\n'
            '- количество билетов (можно взять несколько);\n'
            '- нужна/не нужна парковка;\n'
            '- свой FAN ID (номер карты болельщика, инструкция по оформлению'
            ' <a href=\'https://www.gosuslugi.ru/fancard\'>здесь</a>).\n\n'
            '<b>Все билеты придут на твой FAN ID, но у каждого болельщика при'
            ' входе на стадион проверят ID индивидуально.</b>'
        ).format(
            context.user_data['games'][game_id][0],
            context.user_data['games'][game_id][1],
            context.user_data['games'][game_id][2],
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='назад',
                        callback_data='switch_pages=current',
                    ),
                    InlineKeyboardButton(
                        text='отмена',
                        callback_data='cancel',
                    ),
                    InlineKeyboardButton(
                        text='продолжить',
                        callback_data='start_registration',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION


async def rpl_game_selection_start_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Укажи количество билетов:',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION_NUMBER_TICKETS


async def rpl_game_selection_number_tickets(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        int(update.message.text)
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неверное количество.\nПроверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return RPL_GAME_SELECTION_NUMBER_TICKETS

    context.user_data['number_tickets'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Понадобится парковочное место?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='parking=true',
                    ),
                    InlineKeyboardButton(
                        text='нет',
                        callback_data='parking=false',
                    ),
                ]
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION_PARKING


async def rpl_game_selection_parking(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    if update.callback_query.data.split('=')[1] == 'true':
        context.user_data['parking'] = True
    else:
        context.user_data['parking'] = False

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Укажи свой Fan ID:',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION_FAN_ID


async def rpl_game_selection_fan_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['fan_id'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'Проверим:\n\n'
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>\n'
            'fan ID: <b>{}</b>\n'
        ).format(
            context.user_data['games'][context.user_data['game_id']][0],
            context.user_data['games'][context.user_data['game_id']][1],
            context.user_data['games'][context.user_data['game_id']][2],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
            context.user_data['fan_id'],
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='confirmation',
                    ),
                    InlineKeyboardButton(
                        text='к выбору матча',
                        callback_data='switch_pages=current',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return RPL_GAME_SELECTION_CONFIRMATION


async def rpl_game_selection_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO requests_rpl_games'
        ' (telegram_id, game_id, number_tickets, parking, fan_id)'
        ' VALUES ({}, {}, {}, {}, \'{}\') ON CONFLICT DO NOTHING;'
    ).format(
        update.effective_user.id,
        context.user_data['game_id'],
        context.user_data['number_tickets'],
        context.user_data['parking'],
        context.user_data['fan_id'],
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='твоя заявка принята',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=admin_group,
        text=(
            '<b>Новая заявка на билеты РПЛ</b>\n\n'
            'телеграм: <b>{}</b>\n'
            'email: <b>{}</b>\n'
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>\n'
            'fan ID: <b>{}</b>\n'
        ).format(
            '' if response[0][1] == 'None' else f'@{response[0][1]}',
            response[0][4],
            context.user_data['games'][context.user_data['game_id']][0],
            context.user_data['games'][context.user_data['game_id']][1],
            context.user_data['games'][context.user_data['game_id']][2],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
            context.user_data['fan_id'],
        ),
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


(
    OTHER_GAME_SELECTION,
    OTHER_GAME_SELECTION_NUMBER_TICKETS,
    OTHER_GAME_SELECTION_PARKING,
    OTHER_GAME_SELECTION_FAN_ID,
    OTHER_GAME_SELECTION_CONFIRMATION,
) = range(5)


async def other_game_selection_init(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END
    if response:
        if 'winline.ru' in response[0][4]:
            pass
        else:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='Извини, но ты не являешься нашим сотрудником. Или указал неверные данные при регистрации',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return ConversationHandler.END
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Ты не прошёл регистрацию. Для регистрации отправь команду /start',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    query = 'SELECT * FROM other_games WHERE game_dt > \'{}\' ORDER BY game_dt asc'.format(
        datetime.now()
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        n = 5
        if len(response) / n == len(response) // n:
            total_pages = len(response) // n
        else:
            total_pages = len(response) // n + 1
        page_counter = 1
        context.user_data['keyboard_pages'] = {}
        context.user_data['games'] = {}
        context.user_data['current_page'] = 1
        for i in range(0, len(response), n):
            context.user_data['keyboard_pages'][page_counter] = []
            for item in response[i : i + n]:
                context.user_data['games'][item[0]] = [
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                ]
                context.user_data['keyboard_pages'][page_counter].append(
                    [
                        InlineKeyboardButton(
                            text='{} / {} / {} / {}'.format(
                                item[4], item[1], item[2], item[3]
                            ),
                            callback_data=f'game_id={item[0]}',
                        ),
                    ]
                )
            if page_counter == 1:
                if total_pages == 1:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            else:
                if page_counter == total_pages:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            page_counter += 1
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='предстоящие матчи\n\nдисциплина / матч / дата / стадион',
            reply_markup=InlineKeyboardMarkup(
                context.user_data['keyboard_pages'][
                    context.user_data['current_page']
                ]
            ),
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return OTHER_GAME_SELECTION
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='в ближайшее время матчей нет',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END


async def other_game_selection_switching_pages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    switch_pages = update.callback_query.data.split('=')[1]

    match switch_pages:
        case 'next':
            context.user_data['current_page'] += 1
        case 'previous':
            context.user_data['current_page'] -= 1
        case 'current':
            pass
        case _:
            return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='предстоящие матчи\n\nдисциплина / матч / дата / стадион',
        reply_markup=InlineKeyboardMarkup(
            context.user_data['keyboard_pages'][
                context.user_data['current_page']
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION


async def other_game_selection_select_game(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    game_id = int(update.callback_query.data.split('=')[1])
    context.user_data['game_id'] = game_id
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'дисциплина: <b>{}</b>\n'
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n\n'
            'для оформления тебе необходимо будет указать:\n'
            '- количество билетов (можно взять несколько);\n'
            '- нужна/не нужна парковка;\n'
            '- свой FAN ID (номер карты болельщика, инструкция по оформлению'
            ' <a href=\'https://www.gosuslugi.ru/fancard\'>здесь</a>).\n\n'
            '<b>Все билеты придут на твой FAN ID, но у каждого болельщика при'
            ' входе на стадион проверят ID индивидуально.</b>'
        ).format(
            context.user_data['games'][game_id][3],
            context.user_data['games'][game_id][0],
            context.user_data['games'][game_id][1],
            context.user_data['games'][game_id][2],
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='назад',
                        callback_data='switch_pages=current',
                    ),
                    InlineKeyboardButton(
                        text='отмена',
                        callback_data='cancel',
                    ),
                    InlineKeyboardButton(
                        text='продолжить',
                        callback_data='start_registration',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION


async def other_game_selection_start_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Укажи количество билетов:',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION_NUMBER_TICKETS


async def other_game_selection_number_tickets(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        int(update.message.text)
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неверное количество.\nПроверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return OTHER_GAME_SELECTION_NUMBER_TICKETS

    context.user_data['number_tickets'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Понадобится парковочное место?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='parking=true',
                    ),
                    InlineKeyboardButton(
                        text='нет',
                        callback_data='parking=false',
                    ),
                ]
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION_PARKING


async def other_game_selection_parking(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    if update.callback_query.data.split('=')[1] == 'true':
        context.user_data['parking'] = True
    else:
        context.user_data['parking'] = False

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Укажи свой Fan ID:',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION_FAN_ID


async def other_game_selection_fan_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['fan_id'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'Проверим:\n\n'
            'дисциплина: <b>{}</b>\n'
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>\n'
            'fan ID: <b>{}</b>\n'
        ).format(
            context.user_data['games'][context.user_data['game_id']][3],
            context.user_data['games'][context.user_data['game_id']][0],
            context.user_data['games'][context.user_data['game_id']][1],
            context.user_data['games'][context.user_data['game_id']][2],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
            context.user_data['fan_id'],
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='confirmation',
                    ),
                    InlineKeyboardButton(
                        text='к выбору матча',
                        callback_data='switch_pages=current',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return OTHER_GAME_SELECTION_CONFIRMATION


async def other_game_selection_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO requests_other_games'
        ' (telegram_id, game_id, number_tickets, parking, fan_id)'
        ' VALUES ({}, {}, {}, {}, \'{}\') ON CONFLICT DO NOTHING;'
    ).format(
        update.effective_user.id,
        context.user_data['game_id'],
        context.user_data['number_tickets'],
        context.user_data['parking'],
        context.user_data['fan_id'],
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    # context.user_data.clear()
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='твоя заявка принята',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=admin_group,
        text=(
            '<b>Новая заявка на билеты</b>\n\n'
            'телеграм: <b>{}</b>\n'
            'email: <b>{}</b>\n'
            'дисциплина: <b>{}</b>\n'
            'матч: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'стадион: <b>{}</b>\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>\n'
            'fan ID: <b>{}</b>\n'
        ).format(
            '' if response[0][1] == 'None' else f'@{response[0][1]}',
            response[0][4],
            context.user_data['games'][context.user_data['game_id']][3],
            context.user_data['games'][context.user_data['game_id']][0],
            context.user_data['games'][context.user_data['game_id']][1],
            context.user_data['games'][context.user_data['game_id']][2],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
            context.user_data['fan_id'],
        ),
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


(
    EVENT_SELECTION,
    EVENT_SELECTION_NUMBER_TICKETS,
    EVENT_SELECTION_PARKING,
    EVENT_SELECTION_CONFIRMATION,
) = range(4)


async def event_selection_init(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END
    if response:
        if 'winline.ru' in response[0][4]:
            pass
        else:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='Извини, но ты не являешься нашим сотрудником. Или указал неверные данные при регистрации',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return ConversationHandler.END
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Ты не прошёл регистрацию. Для регистрации отправь команду /start',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    query = 'SELECT * FROM events WHERE event_dt > \'{}\' ORDER BY event_dt asc'.format(
        datetime.now()
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    if response:
        n = 5
        if len(response) / n == len(response) // n:
            total_pages = len(response) // n
        else:
            total_pages = len(response) // n + 1
        page_counter = 1
        context.user_data['keyboard_pages'] = {}
        context.user_data['events'] = {}
        context.user_data['current_page'] = 1
        for i in range(0, len(response), n):
            context.user_data['keyboard_pages'][page_counter] = []
            for item in response[i : i + n]:
                context.user_data['events'][item[0]] = [
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    item[5],
                ]
                context.user_data['keyboard_pages'][page_counter].append(
                    [
                        InlineKeyboardButton(
                            text='{} / {} / {} / {}'.format(
                                item[4], item[1], item[2], item[3]
                            ),
                            callback_data=f'event_id={item[0]}',
                        ),
                    ]
                )
            if page_counter == 1:
                if total_pages == 1:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            else:
                if page_counter == total_pages:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                        ]
                    )
                else:
                    context.user_data['keyboard_pages'][page_counter].append(
                        [
                            InlineKeyboardButton(
                                text='<<<',
                                callback_data='switch_pages=previous',
                            ),
                            InlineKeyboardButton(
                                text='отмена',
                                callback_data='cancel',
                            ),
                            InlineKeyboardButton(
                                text='>>>',
                                callback_data='switch_pages=next',
                            ),
                        ]
                    )
            page_counter += 1
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='предстоящие мероприятия',
            reply_markup=InlineKeyboardMarkup(
                context.user_data['keyboard_pages'][
                    context.user_data['current_page']
                ]
            ),
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return EVENT_SELECTION
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='в ближайшее время матчей нет',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END


async def event_selection_switching_pages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    switch_pages = update.callback_query.data.split('=')[1]

    match switch_pages:
        case 'next':
            context.user_data['current_page'] += 1
        case 'previous':
            context.user_data['current_page'] -= 1
        case 'current':
            pass
        case _:
            return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='предстоящие мероприятия',
        reply_markup=InlineKeyboardMarkup(
            context.user_data['keyboard_pages'][
                context.user_data['current_page']
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return EVENT_SELECTION


async def event_selection_select_game(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    event_id = int(update.callback_query.data.split('=')[1])
    context.user_data['event_id'] = event_id
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'мероприятие: <b>{}</b>\n'
            'название: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'место проведения: <b>{}</b>\n'
            'описание: <b>{}</b>\n\n'
            'для оформления тебе необходимо будет указать:\n'
            '- количество билетов (можно взять несколько);\n'
            '- нужна/не нужна парковка;\n'
            '- билеты и всю необходимую информацию ты получишь на свой корпоративный email.'
        ).format(
            context.user_data['events'][event_id][3],
            context.user_data['events'][event_id][0],
            context.user_data['events'][event_id][1],
            context.user_data['events'][event_id][2],
            context.user_data['events'][event_id][4],
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='назад',
                        callback_data='switch_pages=current',
                    ),
                    InlineKeyboardButton(
                        text='отмена',
                        callback_data='cancel',
                    ),
                    InlineKeyboardButton(
                        text='продолжить',
                        callback_data='start_registration',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return EVENT_SELECTION


async def event_selection_start_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Укажи количество билетов:',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return EVENT_SELECTION_NUMBER_TICKETS


async def event_selection_number_tickets(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        int(update.message.text)
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неверное количество.\nПроверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return EVENT_SELECTION_NUMBER_TICKETS

    context.user_data['number_tickets'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='Понадобится парковочное место?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='parking=true',
                    ),
                    InlineKeyboardButton(
                        text='нет',
                        callback_data='parking=false',
                    ),
                ]
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return EVENT_SELECTION_PARKING


async def event_selection_parking(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    if update.callback_query.data.split('=')[1] == 'true':
        context.user_data['parking'] = True
    else:
        context.user_data['parking'] = False

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'Проверим:\n\n'
            'мероприятие: <b>{}</b>\n'
            'название: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'место проведения: <b>{}</b>\n'
            'описание: <b>{}</b>\n\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>\n'
        ).format(
            context.user_data['events'][context.user_data['event_id']][3],
            context.user_data['events'][context.user_data['event_id']][0],
            context.user_data['events'][context.user_data['event_id']][1],
            context.user_data['events'][context.user_data['event_id']][2],
            context.user_data['events'][context.user_data['event_id']][4],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='да',
                        callback_data='confirmation',
                    ),
                    InlineKeyboardButton(
                        text='к мероприятия',
                        callback_data='switch_pages=current',
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return EVENT_SELECTION_CONFIRMATION


async def event_selection_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    query = (
        'INSERT INTO requests_events'
        ' (telegram_id, event_id, number_tickets, parking)'
        ' VALUES ({}, {}, {}, {}) ON CONFLICT DO NOTHING;'
    ).format(
        update.effective_user.id,
        context.user_data['event_id'],
        context.user_data['number_tickets'],
        context.user_data['parking'],
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        cur.execute(query)
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    # context.user_data.clear()
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='твоя заявка принята',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    query = 'SELECT * FROM users WHERE telegram_id = {};'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=admin_group,
        text=(
            '<b>Новая заявка на билеты</b>\n\n'
            'телеграм: <b>{}</b>\n'
            'email: <b>{}</b>\n'
            'мероприятие: <b>{}</b>\n'
            'название: <b>{}</b>\n'
            'дата: <b>{}</b>\n'
            'место проведения: <b>{}</b>\n'
            'описание: <b>{}</b>\n'
            'количество билетов: <b>{}</b>\n'
            'парковка: <b>{}</b>'
        ).format(
            '' if response[0][1] == 'None' else f'@{response[0][1]}',
            response[0][4],
            context.user_data['events'][context.user_data['event_id']][3],
            context.user_data['events'][context.user_data['event_id']][0],
            context.user_data['events'][context.user_data['event_id']][1],
            context.user_data['events'][context.user_data['event_id']][2],
            context.user_data['events'][context.user_data['event_id']][4],
            context.user_data['number_tickets'],
            'нужна' if context.user_data['parking'] else 'не нужна',
        ),
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    query = 'SELECT * FROM users WHERE telegram_id = {} and is_admin = true;'.format(
        update.effective_user.id
    )
    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    if response:
        pass
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Недостаточно прав. Обратись к администраторам',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    # select u.username, u.email, rg.game_teams, rg.game_dt, rrg.number_tickets, rrg.parking,
    # rrg.fan_id from requests_rpl_games rrg join users u on rrg.telegram_id = u.telegram_id
    # join rpl_games rg on rrg.game_id = rg.game_id where rg.game_dt > now();

    query = (
        'SELECT u.username, u.email, rg.game_teams, rg.game_dt,'
        ' rrg.number_tickets, rrg.parking, rrg.fan_id'
        ' FROM requests_rpl_games rrg JOIN users u ON rrg.telegram_id = u.telegram_id'
        ' JOIN rpl_games rg ON rrg.game_id = rg.game_id WHERE rg.game_dt > now();'
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    data = []
    if response:
        for item in response:
            data.append(
                [
                    '' if item[0] == 'None' else f'@{item[0]}',
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    'нужна' if item[5] else 'не нужна',
                    item[6],
                ]
            )
        report_rpl = pandas.DataFrame(
            data=data,
            columns=[
                'телеграм',
                'email',
                'матч',
                'дата',
                'количество билетов',
                'парковка',
                'fan id',
            ],
        )
    else:
        report_rpl = None

    # select u.username, u.email, og.type_sport, og.game_teams, og.game_dt,
    # rog.number_tickets, rog.parking, rog.fan_id from requests_other_games rog
    # join users u on rog.telegram_id = u.telegram_id join other_games og on rog.game_id = og.game_id where og.game_dt > now()

    query = (
        'SELECT u.username, u.email, og.type_sport, og.game_teams, og.game_dt,'
        ' rog.number_tickets, rog.parking, rog.fan_id'
        ' FROM requests_other_games rog JOIN users u ON rog.telegram_id = u.telegram_id'
        ' JOIN other_games og ON rog.game_id = og.game_id WHERE og.game_dt > now();'
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    data = []
    if response:
        for item in response:
            data.append(
                [
                    '' if item[0] == 'None' else f'@{item[0]}',
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    item[5],
                    item[6],
                    item[7],
                ]
            )
        report_other_games = pandas.DataFrame(
            data=data,
            columns=[
                'телеграм',
                'email',
                'дисциплина',
                'матч',
                'дата',
                'количество билетов',
                'парковка',
                'fan id',
            ],
        )
    else:
        report_other_games = None

    # select u.username, u.email, e.event_type, e.event_title, e.event_dt, re.number_tickets, re.parking
    # from requests_events re join users u on re.telegram_id = u.telegram_id join events e on re.event_id = e.event_id where e.event_dt > now();

    query = (
        'SELECT u.username, u.email, e.event_type, e.event_title, e.event_dt,'
        ' re.number_tickets, re.parking'
        ' FROM requests_events re JOIN users u ON re.telegram_id = u.telegram_id'
        ' JOIN events e ON re.event_id = e.event_id WHERE e.event_dt > now();'
    )

    try:
        logging.info(f'{CYAN}db query: {query}')
        response = cur.execute(query=query).fetchall()
        logging.info(f'{CYAN}db response: {response}')
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    data = []
    if response:
        for item in response:
            data.append(
                [
                    '' if item[0] == 'None' else f'@{item[0]}',
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    item[5],
                    item[6],
                ]
            )
        report_events = pandas.DataFrame(
            data=data,
            columns=[
                'телеграм',
                'email',
                'мероприятие',
                'название',
                'дата',
                'количество билетов',
                'парковка',
            ],
        )
    else:
        report_events = None

    if (
        report_rpl is None
        and report_other_games is None
        and report_events is None
    ):
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='заявок нет',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    file_name = 'report_{}.xlsx'.format(
        datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M")
    )
    with pandas.ExcelWriter(path=Path(dir_main, 'data', file_name)) as writer:
        if report_rpl is None:
            pass
        else:
            report_rpl.to_excel(writer, sheet_name='RPL', index=False)
        if report_other_games is None:
            pass
        else:
            report_other_games.to_excel(
                writer, sheet_name='other games', index=False
            )
        if report_events is None:
            pass
        else:
            report_events.to_excel(writer, sheet_name='events', index=False)

    sent_message = await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=Path(dir_main, 'data', file_name),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='your ID: {}\ngroup ID: {}'.format(
            update.effective_user.id,
            update.effective_chat.id,
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )


async def handle_invalid_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)
    try:
        await update.callback_query.delete_message()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception as e:
            logging.error(f'{RED}error:', exc_info=True)
        try:
            await update.callback_query.delete_message()
        except Exception as e:
            logging.error(f'{RED}error:', exc_info=True)
    else:
        try:
            await update.message.delete()
        except Exception as e:
            logging.error(f'{RED}error:', exc_info=True)

    context.user_data.clear()

    return ConversationHandler.END


def main():
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='start',
                    callback=start,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                REGISTRATION: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=registration,
                    ),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='add_rpl_games',
                    callback=add_rpl_games,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                INPUT_RPL_GAMES: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=input_rpl_games,
                    ),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='add_other_game',
                    callback=add_other_game_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                ADD_OTHER_GAME_INPUT_TEAMS: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_other_game_input_teams,
                    ),
                ],
                ADD_OTHER_GAME_INPUT_DATE: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_other_game_input_date,
                    ),
                ],
                ADD_OTHER_GAME_INPUT_LOCATION: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_other_game_input_location,
                    ),
                ],
                ADD_OTHER_GAME_INPUT_SPORT: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_other_game_input_sport,
                    ),
                ],
                ADD_OTHER_GAME_CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=add_other_game_confirmation,
                        pattern='^confirmation$',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel',
                    cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='add_event',
                    callback=add_event_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                ADD_EVENT_INPUT_TITLE: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_event_input_title,
                    ),
                ],
                ADD_EVENT_INPUT_DATE: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_event_input_date,
                    ),
                ],
                ADD_EVENT_INPUT_LOCATION: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_event_input_location,
                    ),
                ],
                ADD_EVENT_INPUT_TYPE: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_event_input_type,
                    ),
                ],
                ADD_EVENT_INPUT_DESCRIPTION: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=add_event_input_description,
                    ),
                ],
                ADD_EVENT_CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=add_event_confirmation,
                        pattern='^confirmation$',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel',
                    cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='rpl',
                    callback=rpl_game_selection_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                RPL_GAME_SELECTION: [
                    CallbackQueryHandler(
                        callback=rpl_game_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                    CallbackQueryHandler(
                        callback=rpl_game_selection_select_game,
                        pattern='^game_id=',
                    ),
                    CallbackQueryHandler(
                        callback=rpl_game_selection_start_registration,
                        pattern='^start_registration$',
                    ),
                ],
                RPL_GAME_SELECTION_NUMBER_TICKETS: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=rpl_game_selection_number_tickets,
                    ),
                ],
                RPL_GAME_SELECTION_PARKING: [
                    CallbackQueryHandler(
                        callback=rpl_game_selection_parking,
                    ),
                ],
                RPL_GAME_SELECTION_FAN_ID: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=rpl_game_selection_fan_id,
                    ),
                ],
                RPL_GAME_SELECTION_CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=rpl_game_selection_confirmation,
                        pattern='^confirmation$',
                    ),
                    CallbackQueryHandler(
                        callback=rpl_game_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel',
                    cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='other_games',
                    callback=other_game_selection_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                OTHER_GAME_SELECTION: [
                    CallbackQueryHandler(
                        callback=other_game_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                    CallbackQueryHandler(
                        callback=other_game_selection_select_game,
                        pattern='^game_id=',
                    ),
                    CallbackQueryHandler(
                        callback=other_game_selection_start_registration,
                        pattern='^start_registration$',
                    ),
                ],
                OTHER_GAME_SELECTION_NUMBER_TICKETS: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=other_game_selection_number_tickets,
                    ),
                ],
                OTHER_GAME_SELECTION_PARKING: [
                    CallbackQueryHandler(
                        callback=other_game_selection_parking,
                    ),
                ],
                OTHER_GAME_SELECTION_FAN_ID: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=other_game_selection_fan_id,
                    ),
                ],
                OTHER_GAME_SELECTION_CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=other_game_selection_confirmation,
                        pattern='^confirmation$',
                    ),
                    CallbackQueryHandler(
                        callback=other_game_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel',
                    cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='events',
                    callback=event_selection_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                EVENT_SELECTION: [
                    CallbackQueryHandler(
                        callback=event_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                    CallbackQueryHandler(
                        callback=event_selection_select_game,
                        pattern='^event_id=',
                    ),
                    CallbackQueryHandler(
                        callback=event_selection_start_registration,
                        pattern='^start_registration$',
                    ),
                ],
                EVENT_SELECTION_NUMBER_TICKETS: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=event_selection_number_tickets,
                    ),
                ],
                EVENT_SELECTION_PARKING: [
                    CallbackQueryHandler(
                        callback=event_selection_parking,
                    ),
                ],
                EVENT_SELECTION_CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=event_selection_confirmation,
                        pattern='^confirmation$',
                    ),
                    CallbackQueryHandler(
                        callback=event_selection_switching_pages,
                        pattern='^switch_pages=',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    'cancel',
                    cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
            ],
        )
    )
    app.add_handler(
        CommandHandler(
            command='report',
            callback=report,
            filters=filters.ChatType.PRIVATE,
        )
    )
    app.add_handler(
        CommandHandler(
            command='set_me_admin',
            callback=set_me_admin,
            filters=filters.ChatType.PRIVATE,
        )
    )
    app.add_handler(
        CommandHandler(
            command='id',
            callback=get_id,
        )
    )
    app.add_handler(MessageHandler(filters=None, callback=handle_messages))
    app.add_handler(CallbackQueryHandler(callback=handle_invalid_button))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    bot_name = os.getenv('BOT_NAME') if os.getenv('BOT_NAME') else 'TEST BOT'
    token = (
        os.getenv('TOKEN')
        if os.getenv('TOKEN')
        else '7119933091:AAHeuezqI-FjWdX6T3zsogcsKUOGFHx-xy4'
    )
    db_name = os.getenv('DB_NAME') if os.getenv('DB_NAME') else 'rplwinlinetest'
    db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

    logging.info(
        f'{YELLOW}\n    bot name: {bot_name};\n    db name: {db_name};\n    db host: {db_host}'
    )

    app = Application.builder().token(token).build()

    conn = psycopg.connect(
        autocommit=True,
        dbname=db_name,
        user='postgres',
        password='1I1DG5reb8Cf9BeP',
        host=db_host,
        port=5432,
    )

    cur = conn.cursor()

    main()
