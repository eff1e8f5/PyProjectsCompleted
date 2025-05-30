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

(
    START_REG,
    FIRST_NAME,
    LAST_NAME,
    PHONE_NUMBER,
    EMAIL,
    DZO,
    PLAY_FAN,
    TOURNAMENTS_BIG_GAMES,
    TOURNAMENTS,
    BIG_GAMES,
    FOOTBALL,
    VOLLEYBALL,
    TENNIS,
    REG_TEAM,
    SELECT_TEAM,
    SEARCH_TEAM,
) = range(16)

confirm_keyboard = [
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

dzo_list = {
    'chd': 'ЦХД',
    'tci': 'ТЦИ',
    'basis': 'Базис',
    'mmtc': 'ММТС-9',
    'cct': 'ССТ/Ngenix',
    'msk': 'MСК-IX',
}

# context.user_data['reg'] = True
# print(update)
# print(update.message.text)
# print(update.effective_chat.type)
# print(context.user_data)
# print(update.effective_user.id)
# print(update.effective_user.first_name)
# print(update.effective_user.last_name)
# print(update.effective_user.username)
# user_data.clear()
# return ConversationHandler.END

# https://t.me/<bot username>? start=<test>

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    # if update.effective_chat.type == 'private':
    # dir_main = Path(__file__).parent
    # dir_data = dir_data = 'data'
    # file_name = 'Политика_обработки_персональных_данных.docx'

    # file = Path(
    #     dir_main,
    #     dir_data,
    # )
    # await context.bot.send_document(
    #     chat_id=update.effective_chat.id,
    #     document=Path(dir_main, dir_data, file_name), parse_mode='HTML', caption=text
    # )

    keyboard = [
        [
            InlineKeyboardButton(
                'Хочу на СпортФест',
                callback_data='reg',
            ),
            InlineKeyboardButton(
                'Не согласен',
                callback_data='disagree',
            ),
        ]
    ]

    doc_link = 'https://drive.google.com/file/d/1tbrTTze9gVD3wIO0XT1T1c7BlJl76ocZ/view?usp=sharing'

    text = (
        'Привет!\n\n'
        'Этот чат-бот поможет тебе получить 100% драйва от СпортФеста Ростелеком-ЦОД!\n'
        'Регистрация обязательна. Поэтому жми кнопку <b>«Хочу на СпортФест»</b> для участия в любых активностях фестиваля.\n\n'
        f'Нажимая на кнопку <b>«Хочу на СпортФест»</b>, вы даете согласие на обработку персональных данных и соглашаетесь с <a href=\'{doc_link}\'>политикой конфидециальности</a>'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return START_REG


async def disagree(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    text = (
        'Увы! =(\n'
        'Так мы не можем тебя зарегистрировать.\n'
        'Необходимо дать согласие на обработку персональных данных, ведь только так мы сможем записать тебя на участия в соревнованиях или наградить за успехи в активностях.\n\n'
        'Если передумаешь, отправь мне команду /start'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ConversationHandler.END


async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    SELECT * FROM
                        participants
                    WHERE
                        telegram_id = {update.effective_user.id};
                '''
        logging.info(f'{CYAN}db query:\n{query}')
        cursor.execute(query)
        response = cursor.fetchall()
        logging.info(f'{CYAN}db response:\n{response}')
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

    if not response:
        try:
            query = f'''
                        INSERT INTO 
                            participants (telegram_id, username) 
                        VALUES
                            ({update.effective_user.id}, '{update.effective_user.username}')
                        ON CONFLICT DO NOTHING;
                    '''
            logging.info(f'{CYAN}db query: {query}')
            cursor.execute(query)
            conn.commit()
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

    text = (
        'Добро пожаловать на СпортФест!\n\n'
        'Круто, что ты станешь частью спортивной команды Ростелеком-ЦОД. Думаю, это будет самый активный день нашего лета!\n\n'
        'Чтобы начать регистрацию, введи в поле ниже своё имя'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return FIRST_NAME


async def first_name_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['first_name'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Это точно твоё имя?\n{update.message.text}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отлично, теперь впиши фамилию',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return LAST_NAME


async def last_name_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['last_name'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Проверь, всё верно, это твоя фамилия?\n{update.message.text}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Осталось совсем немного: введи актуальный номер мобильного в формате +79001234567',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return PHONE_NUMBER


async def phone_number_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['phone_number'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Проверяй телефон, всё правильно?\n{update.message.text}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Ура, мы на финишной прямой – укажи свой рабочий e-mail',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return EMAIL


async def email_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['email'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Это верный e-mail, нет опечаток?\n{update.message.text}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = []
    for i in dzo_list.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    i[1],
                    callback_data=f'dzo&{i[0]}',
                ),
            ]
        )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='И финальный шаг – выбери свой ДЗО',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return DZO


async def dzo_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    dzo_code = update.callback_query.data.split('&')[1]
    context.user_data['dzo'] = dzo_list[dzo_code]

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Проверяй, верное ли ДЗО?\n{dzo_list[dzo_code]}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None

async def dzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [
            InlineKeyboardButton(
                'Хочу в спорт',
                callback_data='play',
            ),
            InlineKeyboardButton(
                'Хочу общаться',
                callback_data='fan',
            ),
        ]
    ]

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = 'fan'
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
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

    try:
        query = f'''
                    SELECT * FROM
                        participants
                    WHERE
                        telegram_id = {update.effective_user.id};
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        response = cursor.fetchall()
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

    if not response:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить регистрацию позже',
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

        return

    participant_id = response[0][2]
    context.user_data['participant_id'] = participant_id

    text = (
        f'Поздравляю с регистрацией!\n\n'
        f'Лови твой персональный ID {participant_id}\n'
        'Вместе мы точно зажжём покруче, чем на Олимпийских Играх.'
    )
    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        # reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END

# async def dzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     logging.info(
#         f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
#     )

#     try:
#         await update.callback_query.answer()
#     except Exception as e:
#         logging.error(f'{RED}error:', exc_info=True)
#     try:
#         await update.callback_query.edit_message_reply_markup()
#     except Exception as e:
#         logging.error(f'{RED}error:', exc_info=True)

#     keyboard = [
#         [
#             InlineKeyboardButton(
#                 'Хочу в спорт',
#                 callback_data='play',
#             ),
#             InlineKeyboardButton(
#                 'Хочу общаться',
#                 callback_data='fan',
#             ),
#         ]
#     ]

#     try:
#         query = f'''
#                     UPDATE
#                         participants
#                     SET
#                         first_name = '{context.user_data['first_name']}',
#                         last_name = '{context.user_data['last_name']}',
#                         phone_number = '{context.user_data['phone_number']}',
#                         email = '{context.user_data['email']}',
#                         dzo = '{context.user_data['dzo']}'
#                     WHERE
#                         telegram_id = {update.effective_user.id}
#                 '''
#         logging.info(f'{CYAN}db query: {query}')
#         cursor.execute(query)
#         conn.commit()
#     except Exception as e:
#         logging.error(f'{RED}db error:', exc_info=True)

#         conn.rollback()

#         sent_message = await context.bot.send_message(
#             chat_id=update.effective_user.id,
#             text='Что-то пошло не так. Попробуй повторить позже',
#         )

#         logging.info(
#             f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
#         )

#         return

#     try:
#         query = f'''
#                     SELECT * FROM
#                         participants
#                     WHERE
#                         telegram_id = {update.effective_user.id};
#                 '''
#         logging.info(f'{CYAN}db query: {query}')
#         cursor.execute(query)
#         response = cursor.fetchall()
#         logging.info(f'{CYAN}db response: {response}')
#     except Exception as e:
#         logging.error(f'{RED}db error:', exc_info=True)

#         sent_message = await context.bot.send_message(
#             chat_id=update.effective_user.id,
#             text='Что-то пошло не так. Попробуй повторить позже',
#         )

#         logging.info(
#             f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
#         )
#         return

#     if not response:
#         sent_message = await context.bot.send_message(
#             chat_id=update.effective_user.id,
#             text='Что-то пошло не так. Попробуй повторить регистрацию позже',
#         )

#         logging.info(
#             f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
#         )

#         return

#     participant_id = response[0][2]
#     context.user_data['participant_id'] = participant_id

#     text = (
#         f'Поздравляю с регистрацией!\n\n'
#         f'Лови твой персональный ID {participant_id}\n'
#         'Вместе мы точно зажжём покруче, чем на Олимпийских Играх. Теперь самое время определиться с форматом участия: спортсмены или болельщики?'
#     )
#     sent_message = await context.bot.send_message(
#         chat_id=update.effective_chat.id,
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )

#     logging.info(
#         f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
#     )

#     return PLAY_FAN


async def fan_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['subject'] = 'fan'

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Будешь болельщиком?',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def fan(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = '{context.user_data['subject']}',
                        team_id = null,
                        is_captain = false,
                        search_team = false
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{GREEN}sent message to {update.effective_user.id}\n{sent_message}'
        )
        return

    text = (
        'Быть болельщиком – очень ответственная роль: именно от тебя зависит, почувствуют ли наши спортсмены всенародную любовь и поддержку.\n'
        'Так что не подведи: уже можно готовить подбадривающие кричалки и даже рисовать баннеры поддержки.\n\n'
        'Встретимся 26 июля в 14:00 на площадке “Останкино Фест”: обязательно загляни в фан-шоп за атрибутикой – и подари нашим спортсменам всё море своей любви!'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [
            InlineKeyboardButton(
                'Командные турниры',
                callback_data='tournaments',
            ),
            InlineKeyboardButton(
                'Большие игры',
                callback_data='big_games',
            ),
        ]
    ]

    text = (
        'Спортсменам – физкультпривет!\n\n'
        'Для тебя на выбор:\n'
        ' - командные турниры по трём видам спорта (футбол, настольный теннис, волейбол)\n'
        ' - Большие Игры – это несколько необычных спортивных активностей, в которых команды будут последовательно пробовать свои силы.\n\n'
        'В чём хочешь участвовать?'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return TOURNAMENTS_BIG_GAMES


async def tournaments(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [
            InlineKeyboardButton(
                'Мини-футбол',
                callback_data='football',
            ),
        ],
        [
            InlineKeyboardButton(
                'Волейбол',
                callback_data='volleyball',
            ),
        ],
        [
            InlineKeyboardButton(
                'Настольный теннис',
                callback_data='tennis',
            ),
        ],
        [
            InlineKeyboardButton(
                'Я передумал',
                callback_data='back',
            ),
        ],
    ]

    text = (
        'Командные турниры проведём в трёх дисциплинах: мини-футбол, волейбол и настольный теннис.\n\n'
        'В волейболе и мини-футболе участие командное, настольный теннис – одиночные соревнования.\n\n'
        'Выбирай, в чём будешь претендовать на звание чемпиона?'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return TOURNAMENTS


async def tennis_confirmation(
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

    context.user_data['subject'] = 'tennis'

    keyboard = [
        [
            InlineKeyboardButton(
                'Хочу в игру',
                callback_data='yes',
            ),
            InlineKeyboardButton(
                'Я передумал',
                callback_data='back',
            ),
        ],
    ]

    text = (
        'Ракетки наголо!\n\n'
        'Разбивать соперников будем по классике – один на один, женская и мужская группы играют отдельно, каждая игра кончается при 11 победных очках любого из соперников.'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return TENNIS


async def tennis(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = '{context.user_data['subject']}',
                        team_id = null,
                        is_captain = false,
                        search_team = false
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(f'{RED}db error:', exc_info=True)
        conn.rollback()
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Что-то пошло не так. Попробуй повторить позже',
        )
        logging.info(
            f'{GREEN}sent message to {update.effective_user.id}\n{sent_message}'
        )
        return

    text = (
        'Добро пожаловать в турнирную таблицу!\n\n'
        'Можно начинать тренировки и настраиваться на решительную победу.\n\n'
        'До встречи за теннисным столом 26 июля в 14:00 на площадке “Останкино Фест” – проверим, кто станет первой ракеткой Ростелеком-ЦОД!\n\n'
        'P.S. После 12 июля я маякну тебе и начнем подготовку с моими спортивными помощниками!'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def big_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['subject'] = 'big_games'

    keyboard = [
        [
            InlineKeyboardButton(
                'Заявить свою команду',
                callback_data='reg_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Выбрать команду',
                callback_data='select_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Хочу в команду',
                callback_data='search_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Я передумал',
                callback_data='back',
            ),
        ],
    ]

    text = (
        'Большие игры – это соревнования одновременно между несколькими командами в самых необычных командных спортивных активностях со всего мира.\n\n'
        'В каждой команде может быть от 8 до 10 человек, всех их ждёт 6 состязаний и финальная полоса препятствий – нужно будет продемонстрировать и стратегическое мышление, и командную работу, и, конечно, настоящий спортивный дух.\n'
        'Готов попробовать свои силы?'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return BIG_GAMES


async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['subject'] = 'football'

    keyboard = [
        [
            InlineKeyboardButton(
                'Заявить свою команду',
                callback_data='reg_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Выбрать команду',
                callback_data='select_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Хочу в команду',
                callback_data='search_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'я передумал',
                callback_data='back',
            ),
        ],
    ]

    text = (
        'Мини-футбол – нестареющая классика!\n\n'
        'В каждой команде – от 5 до 10 человек (5 – основной состав, и 5 – в запасе). Играем по два тайма, длительность будет зависеть от количества набранных команд.\n'
        'Ты можешь заявить свою команду, присоединиться к одной из имеющихся, если знаешь её название, или просто подать заявку на участие – тогда мы подберём тебе команду автоматически.'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return FOOTBALL


async def volleyball(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['subject'] = 'volleyball'

    keyboard = [
        [
            InlineKeyboardButton(
                'Заявить свою команду',
                callback_data='reg_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Выбрать команду',
                callback_data='select_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Хочу в команду',
                callback_data='search_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Я передумал',
                callback_data='back',
            ),
        ],
    ]

    text = (
        'В волейбол играл каждый – а значит, победа уже в кармане!\n\n'
        'В каждой команде – от 6 до 10 человек (6 – основной состав, и 4 – в запасе). Играем до 25 победных очков у любого соперника в сете.\n'
        'Ты можешь заявить свою команду, присоединиться к одной из имеющихся, если знаешь её название, или просто подать заявку на участие – тогда мы подберём тебе команду автоматически.'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return VOLLEYBALL


async def reg_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    text = (
        'Поздравляем, капитан!\n\n'
        'Твоя заявка принята, теперь нужно придумать название твоей команды'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return REG_TEAM


async def reg_team_confirmation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    context.user_data['team_name'] = update.message.text

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Название как ты хотел, всё верно?\n{update.message.text}',
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def reg_team_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    INSERT INTO 
                        teams (team_name, team_captain_id, team_subject, players_team) 
                    VALUES
                        ('{context.user_data['team_name']}', '{context.user_data['participant_id']}', '{context.user_data['subject']}', 1)
                    ON CONFLICT DO NOTHING;
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
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

    try:
        query = f'''
                    SELECT * FROM
                        teams
                    WHERE
                        team_name = '{context.user_data['team_name']}' and team_captain_id = '{context.user_data['participant_id']}';
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        response = cursor.fetchall()
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

    context.user_data['team_id'] = response[0][0]

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = '{context.user_data['subject']}',
                        team_id = {context.user_data['team_id']},
                        is_captain = true,
                        search_team = false
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
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
    text = (
        'Добро пожаловать в турнирную таблицу!\n\n'
        'Желаем побеждать противников всухую!\n'
        'Чтобы приблизить победу, приглашай коллег присоединиться к твоей команде. Если участников будет не хватать, мы пригласим в ваш состав кого-то, кто заявится без команды.\n\n'
        'До встречи на поле 26 июля в 14:00 на площадке “Останкино Фест”!\n\n'
        'P.S. После 12 июля я маякну тебе и начнем подготовку с моими спортивными помощниками!'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def select_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    def teams_list():
        try:
            query = f'''
                        SELECT * FROM
                            teams
                        WHERE
                            team_subject = '{context.user_data['subject']}' and players_team < 10;
                    '''
            logging.info(f'{CYAN}db query: {query}')
            cursor.execute(query)
            response = cursor.fetchall()
            logging.info(f'{CYAN}db response: {response}')
        except Exception as e:
            # logging.error(f'{RED}db error:', exc_info=True)
            raise e

        teams = []
        for i in response:
            teams.append([i[0], i[1]])

        return teams

    match update.callback_query.data:
        case 'next':
            context.user_data['team_page'] += 1
        case 'previous':
            context.user_data['team_page'] -= 1
        case _:
            context.user_data['team_page'] = 0
            context.user_data['teams'] = []

            try:
                teams = teams_list()
            except Exception as e:
                logging.error(f'{RED}teams_list error:', exc_info=True)
                sent_message = await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text='Что-то пошло не так. Попробуй повторить позже',
                )

                logging.info(
                    f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
                )
                return

            while True:
                if len(teams) > 10:
                    context.user_data['teams'].append(teams[:10])
                    teams = teams[10:]
                else:
                    context.user_data['teams'].append(teams)
                    break

    keyboard = []

    for team in context.user_data['teams'][context.user_data['team_page']]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    team[1],
                    callback_data=f'team&{team[0]}',
                ),
            ]
        )

    if context.user_data['team_page'] == 0:
        if len(context.user_data['teams']) == 1:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        'Нет моей команды',
                        callback_data='no_team',
                    ),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        'Вперёд',
                        callback_data='next',
                    ),
                ]
            )
    elif context.user_data['team_page'] + 1 == len(context.user_data['teams']):
        keyboard.append(
            [
                InlineKeyboardButton(
                    'Назад',
                    callback_data='previous',
                ),
                InlineKeyboardButton(
                    'Нет моей команды',
                    callback_data='no_team',
                ),
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    'Назад',
                    callback_data='previous',
                ),
                InlineKeyboardButton(
                    'Вперёд',
                    callback_data='next',
                ),
            ]
        )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выбирай команду',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return SELECT_TEAM


async def no_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [
            InlineKeyboardButton(
                'Заявить свою команду',
                callback_data='reg_team',
            ),
        ],
        [
            InlineKeyboardButton(
                'Хочу в команду',
                callback_data='search_team',
            ),
        ],
    ]

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Очень жаль. Ты можешь зарегистрировать свою команду или оставь заявку, и мы подберём для тебя команду.',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def select_team_confirmation(
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

    team_id = update.callback_query.data.split('&')[1]
    context.user_data['team_id'] = int(team_id)

    try:
        query = f'''
                    SELECT * FROM
                        teams
                    WHERE
                        team_id = {team_id};
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        response = cursor.fetchall()
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

    team_name = response[0][1]
    context.user_data['team_name'] = team_name

    text = f'Будешь побеждать в составе команды {team_name}?'

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return None


async def select_team_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = '{context.user_data['subject']}',
                        team_id = {context.user_data['team_id']},
                        is_captain = false,
                        search_team = false
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        query = f'''
                    UPDATE
                        teams
                    SET
                        players_team = players_team + 1
                    WHERE
                        team_id = {context.user_data['team_id']}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
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
    text = (
        'Добро пожаловать в команду!\n\n'
        'Отличной игры, и пусть победит сильнейший.\n\n'
        'До встречи на поле 26 июля в 14:00 на площадке “Останкино Фест”!\n\n'
        'P.S. После 12 июля я маякну тебе и начнем подготовку с моими спортивными помощниками!'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def search_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    try:
        query = f'''
                    UPDATE
                        participants
                    SET
                        first_name = '{context.user_data['first_name']}',
                        last_name = '{context.user_data['last_name']}',
                        phone_number = '{context.user_data['phone_number']}',
                        email = '{context.user_data['email']}',
                        dzo = '{context.user_data['dzo']}',
                        subject = '{context.user_data['subject']}',
                        is_captain = false,
                        search_team = true
                    WHERE
                        telegram_id = {update.effective_user.id}
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        conn.commit()
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

    text = (
        'Заявка зарегистрирована!\n\n'
        'Как только подберём для тебя самую лучшую команду – обязательно напишем, будь на связи и начинай тренировки перед матчами.\n\n'
        'Встречаемся 26 июля в 14:00 на площадке “Останкино Фест”!\n\n'
        'P.S. После 12 июля я маякну тебе и начнем подготовку с моими спортивными помощниками!'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def end_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='конец',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Хорошо, возвращайся, когда будешь готов зарегестрироваться',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def start_err(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Не надо так часто отправлять /start\nЯ запутался. Давай начнём сначала',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return ConversationHandler.END


async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Для начала регистрации отправь команду /start',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
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
        await update.callback_query.edit_message_reply_markup()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Что-то пошло не так. Для начала регистрации отправь команду /start',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )
    try:
        query = f'''
                    SELECT * FROM
                        participants
                    WHERE
                        telegram_id = {update.effective_user.id};
                '''
        logging.info(f'{CYAN}db query: {query}')
        cursor.execute(query)
        response = cursor.fetchall()
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

    if not response:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Сначала пройди регистрацию',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    if response[0][3] is None:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Сначала пройди регистрацию',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return

    context.user_data['id'] = response[0][2]
    context.user_data['first_name'] = response[0][3]
    context.user_data['subject'] = response[0][8]
    context.user_data['team_id'] = response[0][9]
    context.user_data['is_captain'] = response[0][10]
    context.user_data['search_team'] = response[0][11]

    text = (
        f'Привет, {context.user_data["first_name"]}!\n\n'
        f'твой ID: {context.user_data["id"]}'
    )

    if context.user_data['subject'] == 'tennis':
        text += '\nтвоя дисциплина: настольный теннис'
    elif context.user_data['subject'] == 'football':
        text += '\nтвоя дисциплина: мини-футбол'
        if context.user_data['search_team']:
            text += '\n\nМы подберём тебе самую лучшую команду'
        else:
            try:
                query = f'''
                    SELECT * FROM
                        teams
                    WHERE
                        team_id = {context.user_data["team_id"]};
                '''
                logging.info(f'{CYAN}db query: {query}')
                cursor.execute(query)
                response = cursor.fetchall()
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

            if context.user_data['is_captain']:
                text += f'\n\nты капитан команды \"{response[0][1]}\"'
            else:
                text += f'\n\nтвоя команда \"{response[0][1]}\"'
    elif context.user_data['subject'] == 'volleyball':
        text += '\nтвоя дисциплина: волейбол'
        if context.user_data['search_team']:
            text += '\n\nМы подберём тебе самую лучшую команду'
        else:
            try:
                query = f'''
                    SELECT * FROM
                        teams
                    WHERE
                        team_id = {context.user_data["team_id"]};
                '''
                logging.info(f'{CYAN}db query: {query}')
                cursor.execute(query)
                response = cursor.fetchall()
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

            if context.user_data['is_captain']:
                text += f'\n\nты капитан команды \"{response[0][1]}\"'
            else:
                text += f'\n\nтвоя команда \"{response[0][1]}\"'
    elif context.user_data['subject'] == 'big_games':
        text += '\nтвоя дисциплина: большие игры'
        if context.user_data['search_team']:
            text += '\n\nМы подберём тебе самую лучшую команду'
        else:
            try:
                query = f'''
                    SELECT * FROM
                        teams
                    WHERE
                        team_id = {context.user_data["team_id"]};
                '''
                logging.info(f'{CYAN}db query: {query}')
                cursor.execute(query)
                response = cursor.fetchall()
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

            if context.user_data['is_captain']:
                text += f'\n\nты капитан команды \"{response[0][1]}\"'
            else:
                text += f'\n\nтвоя команда \"{response[0][1]}\"'
    else:
        ...

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


def main():
    # reg_handler = ConversationHandler(
    #     entry_points=[
    #         CommandHandler('start', start, filters=filters.ChatType.PRIVATE)
    #     ],
    #     states={
    #         START_REG: [
    #             CallbackQueryHandler(start_reg, pattern='^reg$'),
    #             CallbackQueryHandler(disagree, pattern='^disagree$'),
    #         ],
    #         FIRST_NAME: [
    #             MessageHandler(
    #                 filters.TEXT & ~filters.COMMAND,
    #                 first_name_confirmation,
    #             ),
    #             CallbackQueryHandler(first_name, pattern='^yes$'),
    #             CallbackQueryHandler(start_reg, pattern='^no$'),
    #         ],
    #         LAST_NAME: [
    #             MessageHandler(
    #                 filters.TEXT & ~filters.COMMAND,
    #                 last_name_confirmation,
    #             ),
    #             CallbackQueryHandler(last_name, pattern='^yes$'),
    #             CallbackQueryHandler(first_name, pattern='^no$'),
    #         ],
    #         PHONE_NUMBER: [
    #             MessageHandler(
    #                 filters.TEXT & ~filters.COMMAND,
    #                 phone_number_confirmation,
    #             ),
    #             CallbackQueryHandler(phone_number, pattern='^yes$'),
    #             CallbackQueryHandler(last_name, pattern='^no$'),
    #         ],
    #         EMAIL: [
    #             MessageHandler(
    #                 filters.TEXT & ~filters.COMMAND,
    #                 email_confirmation,
    #             ),
    #             CallbackQueryHandler(email, pattern='^yes$'),
    #             CallbackQueryHandler(phone_number, pattern='^no$'),
    #         ],
    #         DZO: [
    #             CallbackQueryHandler(dzo_confirmation, pattern='^dzo'),
    #             CallbackQueryHandler(dzo, pattern='^yes$'),
    #             CallbackQueryHandler(email, pattern='^no$'),
    #         ],
    #         PLAY_FAN: [
    #             CallbackQueryHandler(fan_confirmation, pattern='^fan$'),
    #             CallbackQueryHandler(fan, pattern='^yes$'),
    #             CallbackQueryHandler(dzo, pattern='^no$'),
    #             CallbackQueryHandler(play, pattern='^play$'),
    #         ],
    #         TOURNAMENTS_BIG_GAMES: [
    #             CallbackQueryHandler(tournaments, pattern='^tournaments$'),
    #             CallbackQueryHandler(big_games, pattern='^big_games$'),
    #         ],
    #         TOURNAMENTS: [
    #             CallbackQueryHandler(football, pattern='^football$'),
    #             CallbackQueryHandler(volleyball, pattern='^volleyball$'),
    #             CallbackQueryHandler(tennis_confirmation, pattern='^tennis$'),
    #             CallbackQueryHandler(dzo, pattern='^back$'),
    #         ],
    #         BIG_GAMES: [
    #             CallbackQueryHandler(reg_team, pattern='^reg_team$'),
    #             CallbackQueryHandler(select_team, pattern='^select_team$'),
    #             CallbackQueryHandler(search_team, pattern='^search_team$'),
    #             CallbackQueryHandler(dzo, pattern='^back$'),
    #         ],
    #         FOOTBALL: [
    #             CallbackQueryHandler(reg_team, pattern='^reg_team$'),
    #             CallbackQueryHandler(select_team, pattern='^select_team$'),
    #             CallbackQueryHandler(search_team, pattern='^search_team$'),
    #             CallbackQueryHandler(dzo, pattern='^back$'),
    #         ],
    #         VOLLEYBALL: [
    #             CallbackQueryHandler(reg_team, pattern='^reg_team$'),
    #             CallbackQueryHandler(select_team, pattern='^select_team$'),
    #             CallbackQueryHandler(search_team, pattern='^search_team$'),
    #             CallbackQueryHandler(dzo, pattern='^back$'),
    #         ],
    #         TENNIS: [
    #             CallbackQueryHandler(tennis, pattern='^yes$'),
    #             CallbackQueryHandler(dzo, pattern='^back$'),
    #         ],
    #         REG_TEAM: [
    #             MessageHandler(
    #                 filters.TEXT & ~filters.COMMAND,
    #                 reg_team_confirmation,
    #             ),
    #             CallbackQueryHandler(reg_team_end, pattern='^yes$'),
    #             CallbackQueryHandler(reg_team, pattern='^no'),
    #         ],
    #         SELECT_TEAM: [
    #             CallbackQueryHandler(select_team, pattern='^next$'),
    #             CallbackQueryHandler(select_team, pattern='^previous$'),
    #             CallbackQueryHandler(select_team_confirmation, pattern='^team'),
    #             CallbackQueryHandler(select_team, pattern='^no$'),
    #             CallbackQueryHandler(select_team_end, pattern='^yes$'),
    #             CallbackQueryHandler(no_team, pattern='^no_team$'),
    #             CallbackQueryHandler(reg_team, pattern='^reg_team$'),
    #             CallbackQueryHandler(search_team, pattern='^search_team$'),
    #         ],
    #         # PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler('skip', skip_photo)],
    #         # LOCATION: [
    #         #     MessageHandler(filters.LOCATION, location),
    #         #     CommandHandler('skip', skip_location),
    #         # ],
    #         # BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
    #     },
    #     fallbacks=[
    #         CommandHandler('cancel', cancel),
    #         CommandHandler('start', start_err),
    #     ],
    # )

    # app.add_handler(reg_handler)
    app.add_handler(CommandHandler('info', info))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
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
        os.getenv('BOT_NAME') if os.getenv('BOT_NAME') else 'RTF2024 TEST BOT'
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

    # try:
    conn = psycopg.connect(
        dbname=db_name,
        user='postgres',
        password='1I1DG5reb8Cf9BeP',
        host=db_host,
        port=5432,
    )

    cursor = conn.cursor()
    # except Exception as e:
    #     logging.error(f'{RED}db error:', exc_info=True)

    main()
