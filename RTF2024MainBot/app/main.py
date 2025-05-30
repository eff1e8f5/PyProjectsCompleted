import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from warnings import filterwarnings

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

colorama.init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s:%(funcName)s - %(message)s',
)

logging.getLogger('httpx').setLevel(logging.WARNING)
filterwarnings(
    action='ignore', message=r'.*CallbackQueryHandler', category=PTBUserWarning
)

RESET = '\033[0m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
GREEN = '\033[32;1m'
MAGENTA = '\033[35;1m'
RED = '\033[31;1m'
YELLOW = '\033[33;1m'

# confirm_keyboard = [
#     [
#         InlineKeyboardButton(
#             'да',
#             callback_data='yes',
#         ),
#         InlineKeyboardButton(
#             'нет',
#             callback_data='no',
#         ),
#     ]
# ]

# dzo_list = {
#     'chd': 'ЦХД',
#     'tci': 'ТЦИ',
#     'basis': 'Базис',
#     'mmtc': 'ММТС-9',
#     'cct': 'ССТ/Ngenix',
#     'msk': 'MСК-IX',
# }

# https://t.me/<bot username>?start=<test>
# https://t.me/MrClouds_sport_bot?start=checkin
# https://t.me/MrClouds_sport_bot?start=addreg

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
}

keyboard = [
    [
        InlineKeyboardButton(
            callback_data='playstation',
            text='PlayStation',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='kinect',
            text='Kinect',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='vr_bow',
            text='VR лук',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='wrestling',
            text='Треслинг',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='shooting_gallery',
            text='Тир',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='chess',
            text='Шахматы',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='tilt_bench',
            text='Скамья для наклонов',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='press_bench',
            text='Скамья для пресса',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='low_crossbar_for_pushups',
            text='Низкая перекладина для отжимания',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='pulling_up_from_the_hanging_position',
            text='Подтягивание из положения виса',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='horizontal_bar_for_pulling_up',
            text='Турник для подтягивания',
        )
    ],
    [
        InlineKeyboardButton(
            callback_data='cancel',
            text='отмена',
        )
    ],
]

(
    FIRST_NAME,
    LAST_NAME,
    PHONE_NUMBER,
    CONFIRMATION,
    GET_RATING,
) = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    try:
        param = update.message.text.split(' ')[1]
    except Exception as e:
        logging.error(f'{YELLOW}error:', exc_info=True)
        return ConversationHandler.END

    match param:
        case 'checkin':
            try:
                query = (
                    'INSERT INTO checkin (telegram_id) VALUES ({})'
                    ' ON CONFLICT DO NOTHING;'
                ).format(update.effective_user.id)
                logging.info(f'{CYAN}db query: {query}')
                cursor.execute(query)
            except psycopg.errors.ForeignKeyViolation:
                logging.error(f'{RED}db error:', exc_info=True)
                conn.rollback()
                sent_message = await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=(
                        'Ты точно проходил регистрацию?\n'
                        'Обратись за помощью к администраторам на стойке регистрации'
                    ),
                )
                logging.info(
                    f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
                )
                return ConversationHandler.END
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
                text='Просто покажи это сообщение на входе',
            )
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text='✅',
            )
            return ConversationHandler.END
        case 'addreg':
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    'Добро пожаловать на СпортФест!\n\n'
                    'Чтобы начать регистрацию, введи в поле ниже своё имя'
                ),
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return FIRST_NAME
        case _:
            return ConversationHandler.END


async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['first_name'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отлично, теперь впиши фамилию',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return LAST_NAME


async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['last_name'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Осталось совсем немного: введи актуальный номер мобильного в формате +79001234567',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return PHONE_NUMBER


async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['phone_number'] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton(
                'да',
                callback_data='yes',
            ),
            InlineKeyboardButton(
                'нет',
                callback_data='no',
            ),
        ]
    ]

    text = 'Давай проверим, всё верно?\n\nимя: {}\nфамилия: {}\nтелефон: {}'.format(
        context.user_data['first_name'],
        context.user_data['last_name'],
        context.user_data['phone_number'],
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return CONFIRMATION


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    match update.callback_query.data:
        case 'yes':
            try:
                query = (
                    'INSERT INTO participants'
                    ' (telegram_id, username, first_name, last_name, phone_number)'
                    ' VALUES ({}, \'{}\', \'{}\', \'{}\', \'{}\')'
                    ' ON CONFLICT DO NOTHING;'
                ).format(
                    update.effective_user.id,
                    update.effective_user.username,
                    context.user_data['first_name'],
                    context.user_data['last_name'],
                    context.user_data['phone_number'],
                )
                logging.info(f'{CYAN}db query: {query}')
                cursor.execute(query)
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
                text=(
                    'Добро пожаловать на СпортФест!\n\n'
                    'Чтобы узнать свой ID, отправь мне команду /id'
                ),
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return ConversationHandler.END
        case 'no':
            sent_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Давай попробуем ещё раз. Введи своё имя',
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return FIRST_NAME
        case _:
            return ConversationHandler.END


async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    try:
        query = (
            'INSERT INTO checkin (telegram_id) VALUES ({})'
            ' ON CONFLICT DO NOTHING;'
        ).format(update.effective_user.id)
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
    except psycopg.errors.ForeignKeyViolation:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                'Ты точно проходил регистрацию?\n'
                'Обратись за помощью к администраторам на стойке регистрации'
            ),
        )
        return
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
        text='Просто покажи это сообщение на входе',
    )
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='✅',
    )


async def addreg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            'Добро пожаловать на СпортФест!\n\n'
            'Чтобы начать регистрацию, введи в поле ниже своё имя'
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return FIRST_NAME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отмена',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выбор активности',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return GET_RATING


async def get_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if update.callback_query.data == 'cancel':
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='отмена',
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

        return ConversationHandler.END
    # select participants.first_name, events.playstation from events join
    # participants on events.telegram_id = participants.telegram_id order by playstation desc;
    try:
        query = (
            'SELECT p.first_name, e.{0} FROM events e JOIN'
            ' participants p ON e.telegram_id = p.telegram_id'
            ' WHERE e.{0} > 0 ORDER BY e.{0} DESC;'
        ).format(update.callback_query.data)
        logging.info(f'{CYAN}db query: {query}')
        response = cursor.execute(query=query).fetchall()
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
    text = '{}:\n\n'.format(events[update.callback_query.data])
    if len(response) == 0:
        counter = 0
    elif len(response) < 10:
        counter = len(response)
    else:
        counter = 10

    if counter:
        for i in range(counter):
            text += '{}. {} / {}\n'.format(
                i + 1,
                response[i][0],
                response[i][1],
            )
        try:
            query = (
                'SELECT {0} FROM events WHERE telegram_id = {1} and {0} > 0;'
            ).format(update.callback_query.data, update.effective_user.id)
            logging.info(f'{CYAN}db query: {query}')
            response = cursor.execute(query=query).fetchall()
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
            text += '\nТвой рейтинг: {}'.format(response[0][0])
        else:
            text += '\nТы ещё не участвовал'
    else:
        text += 'Ещё никто не участвовал'

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ConversationHandler.END


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    try:
        query = 'SELECT * FROM participants WHERE telegram_id = {};'.format(
            update.effective_user.id
        )
        logging.info(f'{CYAN}db query: {query}')
        response = cursor.execute(query=query).fetchall()
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

    if response:
        text = f'Твой ID: {response[0][2]}'
    else:
        text = (
            'Ты точно проходил регистрацию?\n'
            'Обратись за помощью к администраторам на стойке регистрации'
        )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)


async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    # sent_message = await context.bot.send_message(
    #     chat_id=update.effective_chat.id,
    #     text='Для начала регистрации отправь команду /start',
    # )

    # logging.info(
    #     f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    # )


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


def main():
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='start',
                    callback=start,
                    filters=filters.ChatType.PRIVATE,
                ),
                CommandHandler(
                    command='addreg',
                    callback=addreg,
                    filters=filters.ChatType.PRIVATE,
                ),
            ],
            states={
                FIRST_NAME: [
                    MessageHandler(
                        filters=filters.TEXT
                        & ~filters.COMMAND
                        & filters.ChatType.PRIVATE,
                        callback=first_name,
                    ),
                ],
                LAST_NAME: [
                    MessageHandler(
                        filters=filters.TEXT
                        & ~filters.COMMAND
                        & filters.ChatType.PRIVATE,
                        callback=last_name,
                    ),
                ],
                PHONE_NUMBER: [
                    MessageHandler(
                        filters=filters.TEXT
                        & ~filters.COMMAND
                        & filters.ChatType.PRIVATE,
                        callback=phone_number,
                    ),
                ],
                CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=confirmation,
                        # pattern='^yes$',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=cancel,
                    filters=filters.ChatType.PRIVATE,
                ),
            ],
        )
    )

    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='rating',
                    callback=rating,
                    filters=filters.ChatType.PRIVATE,
                ),
            ],
            states={
                GET_RATING: [
                    CallbackQueryHandler(
                        callback=get_rating,
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=cancel,
                    filters=filters.ChatType.PRIVATE,
                ),
            ],
        )
    )

    # app.add_handler(
    #     CommandHandler(
    #         command='start',
    #         callback=start,
    #         filters=filters.ChatType.PRIVATE,
    #     )
    # )
    app.add_handler(
        CommandHandler(
            command='id',
            callback=get_id,
            filters=filters.ChatType.PRIVATE,
        )
    )
    app.add_handler(
        CommandHandler(
            command='checkin',
            callback=checkin,
            filters=filters.ChatType.PRIVATE,
        )
    )
    app.add_handler(
        CommandHandler(
            command='help',
            callback=get_help,
            filters=filters.ChatType.PRIVATE,
        )
    )
    app.add_handler(
        MessageHandler(
            filters=filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
            callback=msg,
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            handle_invalid_button,
        )
    )

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    # for key in logging.Logger.manager.loggerDict:
    #     print(key)

    # token = '7119933091:AAHeuezqI-FjWdX6T3zsogcsKUOGFHx-xy4'

    bot_name = (
        os.getenv('BOT_NAME') if os.getenv('BOT_NAME') else 'MrClouds TEST bot'
    )
    token = (
        os.getenv('TOKEN')
        if os.getenv('TOKEN')
        else '7373143982:AAEBGiL7YRrPF7gKVP2-g2Qllvk3c-aUsCM'
    )
    db_name = (
        os.getenv('DB_NAME')
        if os.getenv('DB_NAME')
        else 'rtfest_summer_2024_test'
    )
    db_host = os.getenv('DB_HOST') if os.getenv('DB_HOST') else '192.168.1.250'

    # tz = timezone(timedelta(hours=3))

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

    cursor = conn.cursor()

    main()
