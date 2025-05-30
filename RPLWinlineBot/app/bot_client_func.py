import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas
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
from variables import *


async def email_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = 'SELECT * FROM users WHERE telegram_id = {} AND email LIKE \'%@winline.ru\' OR email LIKE \'%@alkorbar.ru\';'.format(
        update.effective_user.id,
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
        return None

    if response:
        return True
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                'У тебя нет доступа к этому разделу.\n\n'
                'В случае вопросов пиши hr@winline.ru'
            ),
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return False


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
        text='Привет, я WinlineGo, давай знакомиться. Введи свою корпоративную почту.',
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
    if (
        '@winline.ru' in update.message.text
        or '@alkorbar.ru' in update.message.text
    ):
        text = 'Отлично. Отправь команду /events и смотри, что доступно.'
    else:
        text = (
            'Ты неверно указал почту. Я не могу принять заявку.\n\n'
            'Чтобы повторно пройти регистрацию отправь команду /start\n\n'
            'В случае вопросов пиши hr@winline.ru'
        )
    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ConversationHandler.END


(
    SELECT_CATEGORY,
    SELECT_EVENT,
    NUMBER_TICKETS,
    PARKING,
    FAN_ID,
    CONFIRMATION,
    END,
) = range(7)


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    match await email_check(update, context):
        case True:
            pass
        case _:
            return ConversationHandler.END

    context.user_data.clear()

    keyboard = []

    dt_now = datetime.now(tz=tz)

    if dt_now.weekday() > 4:
        pass
    elif dt_now.weekday() == 3 and dt_now.hour > 16:
        pass
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    'Матчи РПЛ',
                    callback_data='events_category=rpl',
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                'Другие спортивные события',
                callback_data='events_category=not_rpl',
            ),
        ],
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                'Неспортивные мероприятия',
                callback_data='events_category=not_sport',
            ),
        ],
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                'нет ничего интересного',
                callback_data='not_interested',
            ),
        ],
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Какие события тебя интересуют?',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return SELECT_CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['events_category'] = update.callback_query.data.split(
        '='
    )[1]

    query = (
        'SELECT * FROM events WHERE event_category = \'{}\' and event_datetime > \'{}\''
        ' and event_visible = true order by event_datetime asc;'
    ).format(
        context.user_data['events_category'],
        datetime.now(tz=tz),
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
        return ConversationHandler.END

    if response:
        pass
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    'к списку мероприятий',
                    callback_data='category',
                ),
            ],
            [
                InlineKeyboardButton(
                    'нет ничего интересного',
                    callback_data='not_interested',
                ),
            ],
        ]

        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='В этой категории нет предстоящих событий.',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

        return SELECT_EVENT

    n = 8
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
        for event in response[i : i + n]:
            context.user_data['events'][event[0]] = [
                event[2],
                event[3],
                event[4],
                event[5],
                event[6],
                event[7],
                event[8],
            ]
            context.user_data['keyboard_pages'][page_counter].append(
                [
                    InlineKeyboardButton(
                        text='{} / {}'.format(
                            event[3],
                            event[4].strftime(r'%d.%m %H:%M'),
                            # event[5],
                        ),
                        callback_data=f'event_id={event[0]}',
                    ),
                ]
            )
        if page_counter == 1:
            if total_pages == 1:
                pass
            else:
                context.user_data['keyboard_pages'][page_counter].append(
                    [
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
                            text='>>>',
                            callback_data='switch_pages=next',
                        ),
                    ]
                )
        context.user_data['keyboard_pages'][page_counter].append(
            [
                InlineKeyboardButton(
                    text='к списку мероприятий',
                    callback_data='category',
                ),
            ],
        )
        context.user_data['keyboard_pages'][page_counter].append(
            [
                InlineKeyboardButton(
                    text='нет ничего интересного',
                    callback_data='not_interested',
                ),
            ],
        )
        page_counter += 1

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text='предстоящие события:',
        reply_markup=InlineKeyboardMarkup(
            context.user_data['keyboard_pages'][
                context.user_data['current_page']
            ]
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return SELECT_EVENT


async def switching_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.callback_query.answer()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    match update.callback_query.data.split('=')[1]:
        case 'next':
            context.user_data['current_page'] += 1
        case 'previous':
            context.user_data['current_page'] -= 1
        case 'current':
            pass
        case _:
            return ConversationHandler.END

    try:
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                context.user_data['keyboard_pages'][
                    context.user_data['current_page']
                ]
            ),
        )
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='предстоящие события:',
            reply_markup=InlineKeyboardMarkup(
                context.user_data['keyboard_pages'][
                    context.user_data['current_page']
                ]
            ),
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

    return SELECT_EVENT


async def select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    match context.user_data['events_category']:
        case 'rpl':
            text = (
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                '\nподумай сколько билетов тебе требуется, подготовь свой'
                ' <a href=\'https://www.gosuslugi.ru/fancard\'>FAN ID</a>'
                ' и нажимай "продолжить оформление"'
            ).format(
                context.user_data['events'][event_id][1],
                context.user_data['events'][event_id][2],
                context.user_data['events'][event_id][3],
            )

            # if context.user_data['events'][event_id][5]:
            #     text += '- нужна/не нужна парковка;\n'
            # if context.user_data['events'][event_id][6]:
            #     text += (
            #         '- свой FAN ID (номер карты болельщика, инструкция по оформлению'
            #         ' <a href=\'https://www.gosuslugi.ru/fancard\'>здесь</a>).\n\n'
            #         '<b>Все билеты придут на твой FAN ID, но у каждого болельщика при'
            #         ' входе на стадион проверят ID индивидуально.</b>'
            #     )
        case 'not_rpl':
            text = (
                '<b>{}</b>\n'
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
            ).format(
                context.user_data['events'][event_id][0],
                context.user_data['events'][event_id][1],
                context.user_data['events'][event_id][2],
                context.user_data['events'][event_id][3],
            )
            if context.user_data['events'][event_id][4]:
                text += 'описание: {}\n'.format(
                    context.user_data['events'][event_id][4],
                )

            text += (
                '\nподумай сколько билетов тебе требуется, подготовь свой'
                ' <a href=\'https://www.gosuslugi.ru/fancard\'>FAN ID</a>'
                ' и нажимай "продолжить оформление"'
            )

            # if context.user_data['events'][event_id][5]:
            #     text += '- нужна/не нужна парковка;\n'
            # if context.user_data['events'][event_id][6]:
            #     text += (
            #         '- свой FAN ID (номер карты болельщика, инструкция по оформлению'
            #         ' <a href=\'https://www.gosuslugi.ru/fancard\'>здесь</a>).\n\n'
            #         '<b>Все билеты придут на твой FAN ID, но у каждого болельщика при'
            #         ' входе на стадион проверят ID индивидуально.</b>'
            #     )
        case 'not_sport':
            text = (
                '<b>{}</b>\n'
                '<b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'место проведения: <b>{}</b>\n'
            ).format(
                context.user_data['events'][event_id][0],
                context.user_data['events'][event_id][1],
                context.user_data['events'][event_id][2],
                context.user_data['events'][event_id][3],
            )
            if context.user_data['events'][event_id][4]:
                text += 'описание: {}\n'.format(
                    context.user_data['events'][event_id][4],
                )

            text += (
                '\nподумай сколько билетов тебе требуется'
                ' и нажимай "продолжить оформление"'
            )

            # if context.user_data['events'][event_id][5]:
            #     text += '- нужна/не нужна парковка;\n'
            # if context.user_data['events'][event_id][6]:
            #     text += (
            #         '- свой FAN ID (номер карты болельщика, инструкция по оформлению'
            #         ' <a href=\'https://www.gosuslugi.ru/fancard\'>здесь</a>).\n\n'
            #         '<b>Все билеты придут на твой FAN ID, но у каждого болельщика при'
            #         ' входе на стадион проверят ID индивидуально.</b>'
            #     )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='продолжить оформление',
                        callback_data='continue',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='я передумал, прервать оформление',
                        callback_data='not_interested',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='вернуться к списку',
                        callback_data='category',
                    ),
                ],
            ]
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return SELECT_EVENT


async def continue_registration(
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
        chat_id=update.effective_user.id,
        text='Укажи количество билетов:',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return NUMBER_TICKETS


async def number_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        return NUMBER_TICKETS

    context.user_data['number_tickets'] = update.message.text

    if context.user_data['events'][context.user_data['event_id']][5]:
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
        return PARKING
    elif context.user_data['events'][context.user_data['event_id']][6]:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Укажи свой FAN ID (обычно 9 цифр)',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return FAN_ID

    text = 'Проверим:\n\n'

    match context.user_data['events_category']:
        case 'rpl':
            text += (
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>'
            ).format(
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_rpl':
            text += (
                '<b>{}</b>\n'
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_sport':
            text += (
                '<b>{}</b>\n'
                '<b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'место проведения: <b>{}</b>\n'
                'количество билетов: <b>{}</b>'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='всё верно',
                        callback_data='confirmation',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='к списку мероприятий',
                        callback_data='category',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='я передумал',
                        callback_data='not_interested',
                    ),
                ],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return CONFIRMATION


async def parking(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['parking'] = (
        True if update.callback_query.data.split('=')[1] == 'true' else False
    )

    if context.user_data['events'][context.user_data['event_id']][6]:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Укажи свой FAN ID (обычно 9 цифр)',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return FAN_ID

    text = 'Проверим:\n\n'

    match context.user_data['events_category']:
        case 'rpl':
            text += (
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_rpl':
            text += (
                '<b>{}</b>\n'
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_sport':
            text += (
                '<b>{}</b>\n'
                '<b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'место проведения: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )

    text += 'парковочное место: <b>{}</b>'.format(
        'нужно' if context.user_data['parking'] else 'не нужно'
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='всё верно',
                        callback_data='confirmation',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='к списку мероприятий',
                        callback_data='category',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='я передумал',
                        callback_data='not_interested',
                    ),
                ],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return CONFIRMATION


async def fan_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    data = re.sub(r'\D', r'', update.message.text)
    if re.fullmatch(r'\d{1,}', data):
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                'Все билеты придут на твой FAN ID, но у каждого болельщика при'
                ' входе на стадион проверят ID индивидуально'
            ),
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Неверно указан FAN ID. Проверь и отправь ещё раз',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return FAN_ID

    context.user_data['fan_id'] = data

    text = 'Проверим:\n\n'

    match context.user_data['events_category']:
        case 'rpl':
            text += (
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_rpl':
            text += (
                '<b>{}</b>\n'
                'матч: <b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'стадион: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )
        case 'not_sport':
            text += (
                '<b>{}</b>\n'
                '<b>{}</b>\n'
                'дата: <b>{}</b>\n'
                'место проведения: <b>{}</b>\n'
                'количество билетов: <b>{}</b>\n'
            ).format(
                context.user_data['events'][context.user_data['event_id']][0],
                context.user_data['events'][context.user_data['event_id']][1],
                context.user_data['events'][context.user_data['event_id']][2],
                context.user_data['events'][context.user_data['event_id']][3],
                context.user_data['number_tickets'],
            )

    if context.user_data.setdefault('parking'):
        text += 'парковочное место: <b>{}</b>\n'.format(
            'нужно' if context.user_data['parking'] else 'не нужно'
        )

    text += 'FAN ID: <b>{}</b>\n'.format(
        context.user_data['fan_id'],
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='всё верно',
                        callback_data='confirmation',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='к списку мероприятий',
                        callback_data='category',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='я передумал',
                        callback_data='not_interested',
                    ),
                ],
            ]
        ),
        parse_mode=ParseMode.HTML,
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

    query = (
        'INSERT INTO ticket_requests (telegram_id, event_id, number_tickets, parking, fan_id)'
        ' VALUES ({}, {}, {}, {}, {})'
    ).format(
        update.effective_user.id,
        context.user_data['event_id'],
        context.user_data['number_tickets'],
        (
            'null'
            if context.user_data.setdefault('parking') is None
            else context.user_data.setdefault('parking')
        ),
        (
            'null'
            if context.user_data.setdefault('fan_id') is None
            else '\'{}\''.format(context.user_data.setdefault('fan_id'))
        ),
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
        text='Спасибо. Твоя заявка принята. Соберем все заявки и вернемся к тебе с ответом на твой запрос. В случае вопросов обращайся в hr@winline.ru',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='к списку мероприятий',
                        callback_data='category',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='спасибо, у меня всё',
                        callback_data='not_interested',
                    ),
                ],
            ]
        ),
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    context.user_data.clear()

    return END


async def not_interested(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data.clear()

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Жду тебя снова. В случае вопросов пиши hr@winline.ru',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ConversationHandler.END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data.clear()

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Жду тебя снова. В случае вопросов пиши hr@winline.ru',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ConversationHandler.END
