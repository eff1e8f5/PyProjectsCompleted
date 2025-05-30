import logging
import os
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

ADD_EVENTS = 1


async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        return None

    if response:
        return True
    else:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Недостаточно прав. Обратись к администраторам',
        )
        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )
        return False


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
        if response[0][5]:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    'Теперь у тебя админские права в это боте\n\n'
                    'Тебе доступны следующие команды:\n\n'
                    '/add_events - добавить в базу мероприятия\n'
                    '/report - получить актуальные заявки\n'
                    '/edit_events - редактировать список мероприятий'
                ),
            )
            logging.info(
                f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
            )
            return
        elif 'winline.ru' in response[0][4]:
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
            'Тебе доступны следующие команды:\n\n'
            '/add_events - добавить в базу мероприятие\n'
            '/report - список подавших заявки на актуальные события\n'
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    await context.bot.pin_chat_message(
        chat_id=update.effective_user.id, message_id=sent_message.id
    )


async def add_events_init(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    match await admin_check(update, context):
        case True:
            pass
        case _:
            return ConversationHandler.END

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Отправь файл excel с расписанием мероприятий',
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
    return ADD_EVENTS


async def add_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    file = await context.bot.get_file(file_id=update.message.document.file_id)

    file_name = 'schedule_events_{}.xlsx'.format(
        datetime.strftime(datetime.now(tz=tz), r'%Y%m%d%H%M')
    )

    file_path = Path(dir_main, 'data', file_name)

    await file.download_to_drive(file_path)

    df = pandas.read_excel(file_path).replace({float('nan'): None})
    print(df)
    events_list = []
    event_count = 0
    list_error_line = []
    for line in df.values:
        print(line)
        try:
            event_time = datetime.strptime(str(line[4]), r'%H:%M:%S')
            event_dt = datetime.strptime(
                str(line[3]), r'%Y-%m-%d %H:%M:%S'
            ) + timedelta(hours=event_time.hour, minutes=event_time.minute)
                    
            values_category = line[0].lower()
            if 'не рпл' in values_category:
                event_category = 'not_rpl'
            elif 'другой спорт' in values_category:
                event_category = 'not_rpl'
            elif 'рпл' in values_category:
                event_category = 'rpl'
            elif 'не спорт' in values_category:
                event_category = 'not_sport'
            else:
                event_category = None

            if event_category:
                event = [
                    event_category,
                    line[1],
                    line[2],
                    event_dt,
                    line[5],
                    line[6] if line[6] else '',
                    True if line[7] == 'да' else False,
                    True if line[8] == 'да' else False,
                ]
                events_list.append(event)
                event_count += 1
        except Exception as e:
            list_error_line.append(list(line))
            logging.error(f'{RED}error:', exc_info=True)

    try:
        print(events_list)
        for event in events_list:
            with conn.transaction():
                query = (
                    'INSERT INTO events (event_category, event_type, event_title, event_datetime,'
                    ' event_location, event_description, event_parking, event_fan_id)'
                    ' VALUES (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', {}, {})'
                    ' ON CONFLICT DO NOTHING;'
                ).format(
                    event[0],
                    event[1],
                    event[2],
                    event[3],
                    event[4],
                    event[5],
                    event[6],
                    event[7],
                )
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

    text = f'Добавлено мероприятий: {event_count}\n\n'

    if list_error_line:
        text += 'список недобавленных срок:\n'
        for line in list_error_line:
            text += f'{line}\n'

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )


EDIT_SELECT_CATEGORY, EDIT_SELECT_EVENT = range(2)


async def edit_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if await admin_check(update, context):
        pass
    else:
        return

    keyboard = [
        [
            InlineKeyboardButton(
                'Матчи РПЛ',
                callback_data='events_category=rpl',
            ),
        ],
        [
            InlineKeyboardButton(
                'Другие спортивные события',
                callback_data='events_category=not_rpl',
            ),
        ],
        [
            InlineKeyboardButton(
                'Неспортивные мероприятия',
                callback_data='events_category=not_sport',
            ),
        ],
        [
            InlineKeyboardButton(
                'отмена',
                callback_data='cancel',
            ),
        ],
    ]

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Какие события тебя интересуют?',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return EDIT_SELECT_CATEGORY


async def edit_select_category(
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

    context.user_data['events_category'] = update.callback_query.data.split(
        '='
    )[1]

    query = (
        'SELECT * FROM events WHERE event_category = \'{}\' and event_datetime > \'{}\''
        ' order by event_datetime asc;'
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
                    'в начало',
                    callback_data='category',
                ),
                InlineKeyboardButton(
                    'отмена',
                    callback_data='cancel',
                ),
            ],
        ]

        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='В этой категории нет предстоящих собыий.',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

        return EDIT_SELECT_EVENT

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
                event[9],
            ]
            context.user_data['keyboard_pages'][page_counter].append(
                [
                    InlineKeyboardButton(
                        text='{} {} / {} / {}'.format(
                            '✅' if event[9] else '❌',
                            event[3],
                            event[4],
                            event[5],
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
                    text='в начало',
                    callback_data='category',
                ),
                InlineKeyboardButton(
                    text='отмена',
                    callback_data='cancel',
                ),
            ]
        )
        page_counter += 1

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            '✅ - событие отображается у пользователей\n'
            '❌ - событие не отображается у пользователей'
        ),
        reply_markup=InlineKeyboardMarkup(
            context.user_data['keyboard_pages'][
                context.user_data['current_page']
            ]
        ),
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return EDIT_SELECT_EVENT


async def edit_switching_pages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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

    return EDIT_SELECT_EVENT


async def edit_select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                'матч: <b>{}</b>\n' 'дата: <b>{}</b>\n' 'стадион: <b>{}</b>\n\n'
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

            # text += (
            #     '\nдля оформления тебе необходимо будет указать:\n'
            #     '- количество билетов (можно взять несколько);\n'
            # )

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
                '\nдля оформления тебе необходимо будет указать:\n'
                '- количество билетов (можно взять несколько);\n'
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

    if context.user_data['events'][event_id][7]:
        keyboard = [
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
                    text='убрать событие',
                    callback_data='disable',
                ),
            ]
        ]
    else:
        keyboard = [
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
                    text='вернуть событие',
                    callback_data='enable',
                ),
            ]
        ]

    sent_message = await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return EDIT_SELECT_EVENT


async def edit_event_visibility(
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

    query = 'UPDATE events SET event_visible = {} WHERE event_id = {};'.format(
        True if update.callback_query.data == 'enable' else False,
        context.user_data['event_id'],
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
        text='готово',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text='вернуться к выбору категории',
                        callback_data='category',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='закончить',
                        callback_data='cancel',
                    ),
                ],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return EDIT_SELECT_EVENT


async def get_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(
        f'{MAGENTA}received message from {YELLOW}{update.effective_user.id}:\n{GREEN}{update}'
    )

    try:
        await update.message.delete()
    except Exception as e:
        logging.error(f'{RED}error:', exc_info=True)

    if await admin_check(update, context):
        pass
    else:
        return

    # select u.email, u.username, tr.number_tickets, e.event_category, e.event_type,
    # e.event_title, e.event_datetime, e.event_location, tr.parking, tr.fan_id from
    # ticket_requests tr join users u on tr.telegram_id = u.telegram_id join events e
    # on tr.event_id = e.event_id where e.event_datetime > now() order by e.event_category asc;

    query = (
        'SELECT u.email, u.username, tr.number_tickets, e.event_category,'
        ' e.event_type, e.event_title, e.event_datetime, e.event_location,'
        ' tr.parking, tr.fan_id'
        ' FROM ticket_requests tr JOIN users u ON tr.telegram_id = u.telegram_id'
        ' JOIN events e ON tr.event_id = e.event_id WHERE e.event_datetime > now()'
        ' ORDER BY e.event_category asc;'
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
            text='Нет оформленных заявок',
        )

        logging.info(
            f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
        )

        return

    event_category = {
        'rpl': 'РПЛ',
        'not_rpl': 'другой спорт',
        'not_sport': 'не спорт',
    }

    data = []

    for item in response:
        data.append(
            [
                item[0],
                '' if item[0] == 'None' else f'@{item[1]}',
                item[2],
                event_category[item[3]],
                item[4],
                item[5],
                item[6],
                item[7],
                'нужна' if item[8] else 'не нужна',
                item[9] if item[9] else '',
            ]
        )

    df = pandas.DataFrame(
        data=data,
        columns=[
            'email',
            'тг',
            'количество билетов',
            'категория',
            'тип',
            'название',
            'дата/время',
            'место',
            'парковка',
            'fan id',
        ],
    )

    file_name = 'report_{}.xlsx'.format(
        datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M")
    )

    file_path = Path(dir_main, 'data', file_name)

    with pandas.ExcelWriter(path=file_path) as writer:
        df.to_excel(writer, sheet_name='заявки', index=False)

    sent_message = await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=file_path,
    )
    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )
