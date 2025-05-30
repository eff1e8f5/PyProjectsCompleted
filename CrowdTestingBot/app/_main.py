import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas
import psycopg
from pyrogram import Client, filters, types
from pyrogram.errors import exceptions
from pyrogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats, BotCommandScopeChat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
)

from variables import (
    bot_name,
    db_host,
    db_name,
    db_password,
    db_port,
    db_user,
    dir_data,
    dir_main,
    dir_tmp,
    group_id,
    tg_api_hash,
    tg_api_id,
    tg_bot_token,
)

if not Path(dir_main, dir_tmp).is_dir():
    Path(dir_main, dir_tmp).mkdir()

log_format = '%(levelname)s: %(asctime)s - %(message)s'
formatter = logging.Formatter(log_format)

logging.basicConfig(level=logging.INFO, format=log_format)

tz = timezone(timedelta(hours=3))

app = Client(
    name=bot_name,
    bot_token=tg_bot_token,
    api_hash=tg_api_hash,
    api_id=tg_api_id,
    workdir=Path(dir_main, dir_tmp),
)

try:
    conn = psycopg.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )

    cursor = conn.cursor()
except Exception as e:
    logging.error(e)
    exit()


@app.on_message(filters.command(commands='ban') & filters.group)
async def ban(client, message):
    logging.info(f'<<< private msg:\n{message}')

    chat_id = message.chat.id

    if chat_id != group_id:
        return

    args = message.text.split(' ')

    comment = ''

    if len(args) == 1:
        await app.send_message(
            chat_id=group_id,
            text='Укажите ID пользователя для выдачи ему бана <pre>/ban ID комментарий</pre>',
        )
        return
    elif len(args) > 1:
        try:
            user_id = int(args[1])
        except ValueError:
            await app.send_message(
                chat_id=group_id,
                text='Проверьте, верно ли указан ID <pre>/ban ID комментарий</pre>',
            )
            return

        for i in args[2:]:
            comment += f'{i} '
    else:
        ...

    try:
        query = f'''
            INSERT INTO
                banned (id, comment)
            VALUES 
                ({user_id}, \'{comment}\')
            ON CONFLICT DO NOTHING;
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=group_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.send_message(
        chat_id=group_id,
        text=f'Пользователь с ID {user_id} заблокирован',
    )


@app.on_message(filters.command(commands='unban') & filters.group)
async def unban(client, message):
    logging.info(f'<<< private msg:\n{message}')

    chat_id = message.chat.id

    if chat_id != group_id:
        return

    args = message.text.split(' ')

    if len(args) == 1:
        await app.send_message(
            chat_id=group_id,
            text='Укажите ID пользователя для снятия с него бана <pre>/unban ID</pre>',
        )
        return
    elif len(args) > 1:
        try:
            user_id = int(message.text.split(' ')[1])
        except ValueError:
            await app.send_message(
                chat_id=group_id,
                text='Проверьте, верно ли указан ID <pre>/unban ID</pre>',
            )
            return
    else:
        ...

    try:
        query = f'''
            SELECT * FROM
                banned
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=group_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        try:
            query = f'''
                DELETE FROM
                    banned
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=group_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.send_message(
            chat_id=group_id,
            text=f'Пользователь c ID {user_id} разблокирован',
        )
    else:
        await app.send_message(
            chat_id=group_id,
            text='Пользователь с таки ID не найден в списке заблокированных',
        )


@app.on_message(filters.command(commands='start') & filters.private)
async def start(client, message):
    logging.info(f'<<< private msg:\n{message}')

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    if message.from_user.username:
        username = f'@{message.from_user.username}'
    else:
        if message.from_user.first_name:
            username = message.from_user.first_name
        else:
            username = ''

    if message.from_user.first_name:
        first_name = message.from_user.first_name
    else:
        first_name = ''

    try:
        query = f'''
            SELECT * FROM
                candidates
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()

        if response:
            query = f'''
                INSERT INTO 
                    archive (
                        id, username, country, years_old, first_android_device, 
                        first_device_model, first_device_os, second_android_device, 
                        second_device_model, second_device_os, mir_card, candidate_name,
                        phone_number, referrer, candidate_status, dt_last_activity, 
                        reminder_sent, name_from_telegram, dt_application_submission
                        )
                SELECT * FROM 
                    candidates 
                WHERE 
                    id = {user_id};
            '''
            cursor.execute(query)

            query = f'''
                DELETE FROM 
                    candidates
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)

        query = f'''
            INSERT INTO
                candidates (id, username, candidate_status, name_from_telegram)
            VALUES 
                ({user_id}, \'{username}\', \'начал\', \'{first_name}\')
            ON CONFLICT DO NOTHING;
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            SELECT * FROM
                expected_action
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()

        if response:
            query = f'''
                DELETE FROM 
                    expected_action
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)

        query = f'''
            INSERT INTO
                expected_action (id, primary_action)
            VALUES 
                ({user_id}, \'button_wait\')
            ON CONFLICT DO NOTHING;
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    btn = [
        [
            InlineKeyboardButton(
                text='🎫 Информация о проекте',
                callback_data='about',
            )
        ],
        [
            InlineKeyboardButton(
                text='✍️ Подать заявку на участие',
                callback_data='submit',
            ),
            InlineKeyboardButton(
                text='❔ Обратная связь',
                callback_data='feedback',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
🖖Вас приветствует <b>Телеграм бот</b> по проектам тестирования от компании Crowdtesting!

Мы хотим предложить вам уникальную возможность познакомиться с миром IT. За вход платите не вы, а вам! 💥

Нам предстоит увлекательное событие - масштабное тестирование мобильного приложения национальной платежной системы. Ведущей силой этого события могли бы стать именно вы! 🚀

Если вы хотите узнать подробнее о проекте - нажмите кнопку <Информация о проекте>
Если хотите присоединиться к нашей команде - нажмите кнопку <Подать заявку на участие>
Если вы хотите связаться с нами, задать вопрос - нажмите кнопку <Обратная связь>. Также вы можете выбрать её в Меню в любой момент.

Ну что, начнем? 😉
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_message(filters.command(commands='report') & filters.group)
async def report(client, message):
    logging.info(message)

    chat_id = message.chat.id

    if chat_id != group_id:
        return

    file = Path(
        dir_main,
        dir_tmp,
        f'report_{datetime.strftime(datetime.now(tz=tz), "%Y%m%d%H%M%S")}.xlsx',
    )

    query = f'''
        SELECT * FROM
            candidates;
    '''
    cursor.execute(query)
    response = cursor.fetchall()

    for num_item in range(len(response)):
        response.append(list(response.pop(0)))

    for item in response:
        if item[15]:
            new_value = datetime.strftime(item[15], '%Y-%m-%d %H:%M:%S.%f %z')
            item[15] = new_value
        if item[18]:
            new_value = datetime.strftime(item[18], '%Y-%m-%d %H:%M:%S.%f %z')
            item[18] = new_value

    df_main = pandas.DataFrame(
        response,
        columns=[
            'id',
            'username',
            'country',
            'years_old',
            'first android device',
            'first device model',
            'first device os',
            'second android device',
            'second device model',
            'second device os',
            'mir card',
            'candidate name',
            'phone number',
            'referrer',
            'candidate status',
            'data/time last activity',
            'reminder sent',
            'name from telegram',
            'data/time application submission',
        ],
    )

    query = f'''
        SELECT * FROM
            archive;
    '''
    cursor.execute(query)
    response = cursor.fetchall()

    for num_item in range(len(response)):
        response.append(list(response.pop(0)))

    for item in response:
        if item[16]:
            new_value = datetime.strftime(item[16], '%Y-%m-%d %H:%M:%S.%f %z')
            item[16] = new_value
        if item[19]:
            new_value = datetime.strftime(item[19], '%Y-%m-%d %H:%M:%S.%f %z')
            item[19] = new_value

    df_archive = pandas.DataFrame(
        response,
        columns=[
            '#',
            'id',
            'username',
            'country',
            'years_old',
            'first android device',
            'first device model',
            'first device os',
            'second android device',
            'second device model',
            'second device os',
            'mir card',
            'candidate name',
            'phone number',
            'referrer',
            'candidate status',
            'data/time last activity',
            'reminder sent',
            'name from telegram',
            'data/time application submission',
        ],
    )

    query = f'''
        SELECT * FROM
            banned;
    '''
    cursor.execute(query)
    response = cursor.fetchall()

    df_banned = pandas.DataFrame(
        response,
        columns=[
            'id',
            'comment',
        ],
    )

    with pandas.ExcelWriter(file) as writer:
        df_main.to_excel(writer, sheet_name='main', index=False)
        df_archive.to_excel(writer, sheet_name='archive', index=False)
        df_banned.to_excel(writer, sheet_name='banned', index=False)

    await app.send_document(chat_id=group_id, document=file)

    try:
        file.unlink()
    except Exception as e:
        logging.error(e)


@app.on_message(filters.command(commands='help') & filters.private)
async def help_group(client, message):
    logging.info(message)

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    await app.send_message(
        chat_id=user_id,
        text='Для начала работы отправьте /start\nЧтобы задать вопрос отправьте /feedback',
    )


@app.on_message(filters.command(commands='help') & filters.group)
async def help_group(client, message):
    logging.info(message)

    chat_id = message.chat.id

    if chat_id != group_id:
        return

    await app.send_message(
        chat_id=chat_id, text='для генерации отчёта отправьте /report\nдля блокировки пользователя используйте <code>/ban ID комментарий</code>\nдля разблокировки пользователя используйте <code>/unban ID</code>\nID пользователя можно посмотреть в отчётах'
    )


@app.on_callback_query(filters.regex('solution'))
async def solution(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    message_id = callback_query.message.id

    if callback_query.from_user.username:
        username = f'@{callback_query.from_user.username}'
    else:
        username = callback_query.from_user.first_name

    if 'solution_accepted' in callback_query.data:
        user_id = callback_query.data.split('id=')[1]

        try:
            query = f'''
                UPDATE
                    candidates
                SET
                    candidate_status = \'принят\'
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        btn = [
            [
                InlineKeyboardButton(
                    text='🔃 Отправить повторно',
                    callback_data=f'solution_repeat?id={user_id}',
                )
            ],
        ]

        await app.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=f'{callback_query.message.caption}\n\n<pre>✅ Принят.\nПорешал: {username}\n{datetime.now(tz=tz).replace(microsecond=0)}</pre>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
        )

        try:
            query = f'''
                SELECT * FROM
                    candidates
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            response = cursor.fetchall()

            if response[0][17]:
                candidate_name = response[0][17]
            else:
                candidate_name = response[0][1]
        except Exception as e:
            logging.error(e)
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        btn = [
            [
                InlineKeyboardButton(
                    text='🔗 Перейти в канал',
                    url='https://t.me/+K4D8yyO8FaE5NmUy',
                ),
            ],
            # [
            #     InlineKeyboardButton(
            #         text='❔ Обратная связь',
            #         callback_data=f'feedback',
            #     ),
            # ],
        ]

        await app.send_message(
            chat_id=user_id,
            disable_web_page_preview=True,
            text=f'''
Отлично, {candidate_name}! 

Мы рады приветствовать вас в канале проекта https://t.me/+K4D8yyO8FaE5NmUy. Скорее переходите по ссылке, и добро пожаловать в команду! В канале вы найдете информацию о проекте, а также все дальнейшие инструкции по участию.
''',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
        )
    elif 'solution_rejected' in callback_query.data:
        user_id = callback_query.data.split('id=')[1]

        try:
            query = f'''
                UPDATE
                    candidates
                SET
                    candidate_status = \'отклонён\'
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=f'{callback_query.message.caption}\n\n<pre>⛔️ Не подходит.\nПорешал: {username}\n{datetime.now(tz=tz).replace(microsecond=0)}</pre>',
        )

        btn = [
            [
                InlineKeyboardButton(
                    text='🔗 Перейти в канал',
                    url='https://t.me/crowdtesting_projects',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='📲 Редактировать данные',
                    callback_data='edit_profile',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='❔ Обратная связь',
                    callback_data='feedback',
                ),
            ],
        ]

        await app.send_message(
            chat_id=user_id,
            disable_web_page_preview=True,
            text='''
Мы очень ценим каждого, кто к нам обращается. В данный момент участие вашего устройства в тестировании не предусмотрено, т.к. оно не подходит под требования заказчика. Если у вас есть другое устройство для участия – можете изменить информацию, нажав на кнопку «Редактировать данные».
Также уверены, что в общем канале (https://t.me/crowdtesting_projects) вы сможете найти проект, который вызовет ваш интерес! Если хотите оставить обратную связь – оставьте свои комментарии, наши менеджеры с вами свяжутся.
            ''',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
        )
    elif 'solution_remake' in callback_query.data:
        user_id = callback_query.data.split('id=')[1]

        dt_now = datetime.now(tz=tz)

        try:
            query = f'''
                UPDATE
                    candidates
                SET
                    candidate_status = \'вернули на переделку\',
                    dt_last_activity = \'{dt_now}\',
                    reminder_sent = null
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)

            query = f'''
                UPDATE
                    expected_action
                SET
                    primary_action = \'NDA\'
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=f'{callback_query.message.caption}\n\n<pre>❔ Переделать.\nПорешал: {username}\n{datetime.now(tz=tz).replace(microsecond=0)}</pre>',
        )

        btn = [
            [
                InlineKeyboardButton(
                    text='❔ Обратная связь',
                    callback_data=f'feedback',
                ),
            ],
        ]

        await app.send_message(
            chat_id=user_id,
            disable_web_page_preview=True,
            text=f'''
Просим вас проверить правильность заполнение формы NDA. Обязательные к заполнению поля:
 - Текущая дата
 - ФИО
 - Паспортные данные
 - Место проживания
 - Подпись

После подписания просим вас повторно отправить корректно заполненный NDA в этот чат (заполнять заново более ранние поля заявки не нужно).
            ''',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
        )
    elif 'solution_repeat' in callback_query.data:
        user_id = callback_query.data.split('id=')[1]

        try:
            query = f'''
                UPDATE
                    candidates
                SET
                    candidate_status = \'отправлено повторно\'
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        try:
            query = f'''
                SELECT * FROM
                    candidates
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            response = cursor.fetchall()

            if response[0][17]:
                candidate_name = response[0][17]
            else:
                candidate_name = response[0][1]
        except Exception as e:
            logging.error(e)
            await app.send_message(
                chat_id=chat_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=f'{callback_query.message.caption}\n\n<pre>🔃 Отправлено повторно.\nПорешал: {username}\n{datetime.now(tz=tz).replace(microsecond=0)}</pre>',
        )

        btn = [
            [
                InlineKeyboardButton(
                    text='🔗 Перейти в канал',
                    url='https://t.me/+K4D8yyO8FaE5NmUy',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='❔ Обратная связь',
                    callback_data=f'feedback',
                ),
            ],
        ]

        await app.send_message(
            chat_id=user_id,
            disable_web_page_preview=True,
            text=f'''
Добрый день, {candidate_name}! 

Похоже, наше приглашение затерялось в потоке сообщений. Напомним, что мы ждем вас в канале проекта https://t.me/+K4D8yyO8FaE5NmUy. Переходите по ссылке и добро пожаловать в команду!
''',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
        )


@app.on_callback_query(filters.regex('feedback'))
async def feedback(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                secondary_action = \'feedback\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            disable_web_page_preview=True,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=(
            f'{callback_query.message.text}\n\n' f'<pre>❔ Обратная связь</pre>'
        ),
    )

    await app.send_message(
        chat_id=user_id,
        disable_web_page_preview=True,
        text=f'Отправьте ваш вопрос',
    )


@app.on_message(filters.command(commands='feedback') & filters.private)
async def feedback_cmd(client, message):
    logging.info(message)

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                secondary_action = \'feedback\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.send_message(
        chat_id=user_id,
        disable_web_page_preview=True,
        text=f'Отправьте ваш вопрос',
    )


@app.on_callback_query(filters.regex('edit_profile'))
async def edit_profile(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=(
            f'{callback_query.message.text}\n\n'
            f'<pre>Редактировать анкету</pre>'
        ),
    )

    await check(user_id)


@app.on_callback_query(filters.regex('about'))
async def about(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=(
            f'{callback_query.message.text}\n\n'
            f'<pre>Информация о проекте</pre>'
        ),
    )

    btn = [
        [
            InlineKeyboardButton(
                text='✍️ Подать заявку на участие',
                callback_data='submit',
            ),
            InlineKeyboardButton(
                text='❔ Обратная связь',
                callback_data='feedback',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
📌 Мы погрузимся в мир тестирования платежных мобильных приложений для Android-смартфонов с NFC.

Наша цель - обеспечить бесперебойную работу приложения федеральной платежной системы за счет исследовательского тестирования на максимальном количестве различных моделей смартфонов с ОС Android.

Что такое исследовательское тестирование? 
Это такая проверка работоспособности приложения, которая означает полную свободу действий тестировщика: можно проверять любые функции приложения, в любых условиях, главное - найти ошибку в работе приложения или влиянии приложения на устройство. Достигнуть успехов можно даже без специфических знаний о тестировании.

⚙️ <u>Что вас ждёт?</u>🤔
- Установка тестовой версии приложения;
- Заполнение отчета о том, как прошла установка (не займёт более 10 минут с перерывом на печеньки);
- Поиск багов и их фиксация.

В общих чертах работа будет выглядеть так: вам предлагается заполнение небольшой анкеты по установке, после чего вы можете перейти к поиску ошибок.

Проект предлагает вам свободное исследование и нахождение дефектов - тут все ограничено только вашей фантазией! Найдите как можно больше ошибок и получите за это отдельное вознаграждение ✨
По секрету🤫: в прошлых этапах проекта было зафиксировано более 180 дефектов!

💰 <u>А что по оплате?</u>
За каждый ваш отчет об установке приложения на одном устройстве - оплата 150 рублей. Можно использовать до двух устройств, оплата будет рассчитана за каждое.

За каждый найденный и подтвержденный баг с:
низкой критичностью – 150 рублей;
средней критичностью – 200 рублей;
высокой критичностью – 250 рублей;

Если ошибка возникает в процессе оплаты, то такие ошибки оцениваются в два раза дороже: 300/400/500 рублей в соответствии с приоритетом дефекта. 

Также для участников предусмотрено вручение именного сертификата после выполнения базовой задачи и отчета, но на этом бонусы не заканчиваются. Тем, кто попадет в топ-10/50 тестировщиков предполагается особое вознаграждение до 3000 рублей. Подробнее о системе вознаграждений вы сможете узнать после регистрации в проекте.

По результатам теста мы определим 5 самых интересных дефектов, дополнительная выплата за них составит 2000 рублей.

🤝 <u>Как можно увеличить оплату?</u>
Вы можете пригласить знакомых и друзей - за каждого, кто подаст заявку, а затем примет участие в тестировании от вас - вы получите 200 рублей.
При подаче заявки через бота вашему знакомому всего лишь нужно указать ваши Фамилию и Имя в поле "Как вы узнали о нас?"

📱 <u>На каких девайсах все это происходит?</u>
Главное требование - ваш смартфон должен иметь версию Android 7 или выше, а также модуль NFC.

📆 <u>Когда старт?</u>
В сентябре! Так что с одной стороны нужно поторопиться, а с другой - у вас есть время, чтобы настроиться на процесс. 

‼️ Заинтересовались? Нажмите на кнопку <Подать заявку на участие> и заполните анкету! 

В процессе мы также попросим вас заполнить и подписать Соглашение о неразглашении коммерческой тайны (NDA). Заполнение NDA не только обеспечивает безопасность проекта, но и позволяет вам участвовать в тестировании других продуктов без необходимости проходить процесс согласования каждый раз. Также данные из NDA дают нам возможность оформить вам именной сертификат, подтверждающий ваше участие в тестировании. Такой сертификат позволит дополнить резюме конкурентоспособной позицией.

Будущий проект - отличная возможность погрузиться в мир IT и тестирования.

С нетерпением ждём вашего участия! 😃
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_message(filters.command(commands='about') & filters.private)
async def about_cmd(client, message):
    logging.info(message)

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    btn = [
        [
            InlineKeyboardButton(
                text='✍️ Подать заявку на участие',
                callback_data='submit',
            ),
            InlineKeyboardButton(
                text='❔ Обратная связь',
                callback_data='feedback',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
📌 Мы погрузимся в мир тестирования платежных мобильных приложений для Android-смартфонов с NFC.

Наша цель - обеспечить бесперебойную работу приложения федеральной платежной системы за счет исследовательского тестирования на максимальном количестве различных моделей смартфонов с ОС Android.

Что такое исследовательское тестирование? 
Это такая проверка работоспособности приложения, которая означает полную свободу действий тестировщика: можно проверять любые функции приложения, в любых условиях, главное - найти ошибку в работе приложения или влиянии приложения на устройство. Достигнуть успехов можно даже без специфических знаний о тестировании.

⚙️ <u>Что вас ждёт?</u>🤔
- Установка тестовой версии приложения;
- Заполнение отчета о том, как прошла установка (не займёт более 10 минут с перерывом на печеньки);
- Поиск багов и их фиксация.

В общих чертах работа будет выглядеть так: вам предлагается заполнение небольшой анкеты по установке, после чего вы можете перейти к поиску ошибок.

Проект предлагает вам свободное исследование и нахождение дефектов - тут все ограничено только вашей фантазией! Найдите как можно больше ошибок и получите за это отдельное вознаграждение ✨
По секрету🤫: в прошлых этапах проекта было зафиксировано более 180 дефектов!

💰 <u>А что по оплате?</u>
За каждый ваш отчет об установке приложения на одном устройстве - оплата 150 рублей. Можно использовать до двух устройств, оплата будет рассчитана за каждое.

За каждый найденный и подтвержденный баг с:
низкой критичностью – 150 рублей;
средней критичностью – 200 рублей;
высокой критичностью – 250 рублей;

Если ошибка возникает в процессе оплаты, то такие ошибки оцениваются в два раза дороже: 300/400/500 рублей в соответствии с приоритетом дефекта. 

Также для участников предусмотрено вручение именного сертификата после выполнения базовой задачи и отчета, но на этом бонусы не заканчиваются. Тем, кто попадет в топ-10/50 тестировщиков предполагается особое вознаграждение до 3000 рублей. Подробнее о системе вознаграждений вы сможете узнать после регистрации в проекте.

По результатам теста мы определим 5 самых интересных дефектов, дополнительная выплата за них составит 2000 рублей.

🤝 <u>Как можно увеличить оплату?</u>
Вы можете пригласить знакомых и друзей - за каждого, кто подаст заявку, а затем примет участие в тестировании от вас - вы получите 200 рублей.
При подаче заявки через бота вашему знакомому всего лишь нужно указать ваши Фамилию и Имя в поле "Как вы узнали о нас?"

📱 <u>На каких девайсах все это происходит?</u>
Главное требование - ваш смартфон должен иметь версию Android 7 или выше, а также модуль NFC.

📆 <u>Когда старт?</u>
В сентябре! Так что с одной стороны нужно поторопиться, а с другой - у вас есть время, чтобы настроиться на процесс. 

‼️ Заинтересовались? Нажмите на кнопку <Подать заявку на участие> и заполните анкету! 

В процессе мы также попросим вас заполнить и подписать Соглашение о неразглашении коммерческой тайны (NDA). Заполнение NDA не только обеспечивает безопасность проекта, но и позволяет вам участвовать в тестировании других продуктов без необходимости проходить процесс согласования каждый раз. Также данные из NDA дают нам возможность оформить вам именной сертификат, подтверждающий ваше участие в тестировании. Такой сертификат позволит дополнить резюме конкурентоспособной позицией.

Будущий проект - отличная возможность погрузиться в мир IT и тестирования.

С нетерпением ждём вашего участия! 😃
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('submit'))
async def submit(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                candidate_status = \'выбор страны\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'submit':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>✍️ Подать заявку на участие</pre>'
        )
    elif callback_query.data == 're_submit':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>♻️ Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    btn = [
        [
            InlineKeyboardButton(
                text='🇷🇺 РФ',
                callback_data='years_old',
            ),
            InlineKeyboardButton(
                text='🌐 Другая страна',
                callback_data='another_country',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='<u>Укажите страну вашего пребывания</u>:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('another_country'))
async def another_country(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                country = \'🌐 Другая страна\',
                candidate_status = \'указал страну не РФ\',
                dt_last_activity = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=(f'{callback_query.message.text}\n\n<pre>🌐 Другая страна</pre>'),
    )

    btn = [
        [
            # InlineKeyboardButton(
            #     text='♻️ Вернуться на шаг назад',
            #     callback_data='re_submit',
            # ),
            InlineKeyboardButton(
                text='🔗 Перейти в канал',
                url='https://t.me/crowdtesting_projects',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='Мы очень ценим ваше желание присоединиться! Но, к сожалению, текущий проект тестирования доступен только для тех, кто находится на территории РФ. Тем не менее, наверняка, в общем канале https://t.me/crowdtesting_projects вы сможете найти другой проект от нашей команды!',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('years_old'))
async def years_old(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                country = \'🇷🇺 РФ\',
                candidate_status = \'выбор возраста\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'years_old':
        text = f'{callback_query.message.text}\n\n<pre>🇷🇺 РФ</pre>'
    elif callback_query.data == 're_years_old':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    btn = [
        [
            InlineKeyboardButton(
                text='🌘 Старше 18 лет',
                callback_data='first_android_device',
            ),
            InlineKeyboardButton(
                text='🌖 Младше 18 лет',
                callback_data='under_18',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='<u>Укажите ваш возраст:</u>:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('under_18'))
async def under_18(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                years_old = \'🌖 Младше 18 лет\',
                candidate_status = \'указал возраст младше 18\',
                dt_last_activity = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f'{callback_query.message.text}\n\n<pre>🌖 Младше 18 лет</pre>',
    )

    btn = [
        [
            # InlineKeyboardButton(
            #     text='♻️ Вернуться на шаг назад',
            #     callback_data='re_years_old',
            # ),
            InlineKeyboardButton(
                text='🔗 Перейти в канал',
                url='https://t.me/crowdtesting_projects',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='Ваш энтузиазм вдохновляет нас! Но, к сожалению, на данный проект мы принимаем только совершеннолетних участников. Тем не менее, в нашем общем канале https://t.me/crowdtesting_projects есть множество проектов, которые будут с нетерпением ждать вашего участия!',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('first_android_device'))
async def first_android_device(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                years_old = \'🌘 Старше 18 лет\',
                candidate_status = \'выбор наличия первого устройства\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'first_android_device':
        text = f'{callback_query.message.text}\n\n<pre>🌘 Старше 18 лет</pre>'
    elif callback_query.data == 're_first_android_device':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    btn = [
        [
            InlineKeyboardButton(
                text='⛔️ Нет',
                callback_data='first_device_no',
            ),
            InlineKeyboardButton(
                text='✅ Да',
                callback_data='input_first_device_model',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
Для тестирования требуется устройство на Android с версией 7+ и NFC-модулем. Имеется ли у вас смартфон с подходящей конфигурацией?
Подсказка: вы можете на время тестирования одолжить подходящее устройство у родных/друзей/знакомых, если они не против
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('first_device_no'))
async def first_device_no(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                first_android_device = \'⛔️ Нет\',
                candidate_status = \'указал отсутствие устройства на андройде\',
                dt_last_activity = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f'{callback_query.message.text}\n\n<pre>⛔️ Нет</pre>',
    )

    btn = [
        [
            InlineKeyboardButton(
                text='♻️ Вернуться на шаг назад',
                callback_data='re_first_android_device',
            ),
            InlineKeyboardButton(
                text='🔗 Перейти в канал',
                url='https://t.me/crowdtesting_projects',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
Благодарим вас за проявленный интерес! К сожалению, текущий проект требует наличие устройства Android. Тем не менее, мы уверены, что в общем канале https://t.me/crowdtesting_projects вас ждут проекты, где именно ваше устройство может первым найти уникальные дефекты!

Если вы считаете, что в ходе заполнения заявки вы допустили ошибку при вводе данных, нажмите на кнопку кнопку <Вернуться на шаг назад>
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('input_first_device_model'))
async def input_first_device_model(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                first_android_device = \'✅ Да\',
                candidate_status = \'указывает модель первого устройства\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'first_device_model\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'input_first_device_model':
        text = f'{callback_query.message.text}\n\n<pre>✅ Да</pre>'
    elif callback_query.data == 're_input_first_device_model':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    await app.send_message(
        chat_id=user_id,
        text='''
Отправьте сообщение с указанием модели вашего устройства без ОС (операционной системы)
<pre>Например: Huawei P Smart Z</pre>
        ''',
    )


@app.on_callback_query(filters.regex('input_second_device_model'))
async def input_second_device_model(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                second_android_device = \'✅ Да\',
                candidate_status = \'указывает модель второго устройства\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'second_device_model\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'input_second_device_model':
        text = f'{callback_query.message.text}\n\n<pre>✅ Да</pre>'
    elif callback_query.data == 're_input_second_device_model':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    await app.send_message(
        chat_id=user_id,
        text='''
Отправьте сообщение с указанием модели вашего устройства без ОС (операционной системы)
<pre>Например: Huawei P Smart Z</pre>
        ''',
    )


@app.on_callback_query(filters.regex('mir'))
async def mir(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                second_android_device = \'⛔️ Нет\',
                candidate_status = \'выбор наличия карты МИР\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'mir':
        text = f'{callback_query.message.text}\n\n<pre>⛔️ Нет</pre>'
    elif callback_query.data == 're_mir':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    elif callback_query.data == 're_re_mir':
        try:
            query = f'''
                UPDATE
                    candidates
                SET
                    second_android_device = \'✅ Да\',
                    dt_last_activity = \'{dt_now}\',
                    reminder_sent = null
                WHERE
                    id = {user_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            await app.send_message(
                chat_id=user_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    btn = [
        [
            InlineKeyboardButton(
                text='✅ Да, есть / Готов оформить',
                callback_data='name_input',
            ),
            InlineKeyboardButton(
                text='⛔️ Нет / Не готов оформлять',
                callback_data='no_card1',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
Есть ли у вас в наличии банковские карты платёжной системы МИР?

Мы не будем запрашивать полные данные ваших карт или доступ к ним. Карта может потребоваться для тестирования. Мы будем тестировать официальное приложение крупной компании, поэтому это абсолютно безопасно. Использовать карту будете только вы сами.

Также вы можете оформить виртуальную карту МИР в любом банковском приложении за пару минут - и закрыть её сразу по окончании тестирования.
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('no_card1'))
async def no_card1(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                mir_card = \'⛔️ Нет / Не готов оформлять\',
                candidate_status = \'указал отсутствие карты МИР\',
                dt_last_activity = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f'{callback_query.message.text}\n\n<pre>⛔️ Нет / Не готов оформлять</pre>',
    )

    btn = [
        [
            InlineKeyboardButton(
                text='♻️ Вернуться на шаг назад',
                callback_data='re_mir',
            ),
            InlineKeyboardButton(
                text='🔗 Перейти в канал',
                url='https://t.me/crowdtesting_projects',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
Мы были бы рады сотрудничать с вами, но для участия потребуется карта МИР. Вы можете посмотреть в общем канале https://t.me/crowdtesting_projects список наших проектов, где имеются иные требования к участию. Мы вас ждем, ваш опыт и навыки бесценны для нас.

Если вы считаете, что в ходе заполнения заявки вы допустили ошибку при вводе данных, нажмите на кнопку <Вернуться на шаг назад> 
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('no_card2'))
async def no_card2(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                mir_card = \'⛔️ Нет / Не готов оформлять\',
                candidate_status = \'указал отсутствие карты МИР\',
                dt_last_activity = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f'{callback_query.message.text}\n\n<pre>⛔️ Нет / Не готов оформлять</pre>',
    )

    btn = [
        [
            InlineKeyboardButton(
                text='♻️ Вернуться на шаг назад',
                callback_data='re_re_mir',
            ),
            InlineKeyboardButton(
                text='🔗 Перейти в канал',
                url='https://t.me/crowdtesting_projects',
            ),
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text='''
Мы были бы рады сотрудничать с вами, но для участия потребуется карта МИР. Вы можете посмотреть в общем канале https://t.me/crowdtesting_projects список наших проектов, где имеются иные требования к участию. Мы вас ждем, ваш опыт и навыки бесценны для нас.

Если вы считаете, что в ходе заполнения заявки вы допустили ошибку при вводе данных, нажмите на кнопку <Вернуться на шаг назад> 
        ''',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('name_input'))
async def name_input(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    dt_now = datetime.now(tz=tz)

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                mir_card = \'✅ Да, есть / Готов оформить\',
                candidate_status = \'указывает имя\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'candidate_name\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'name_input':
        text = f'{callback_query.message.text}\n\n<pre>✅ Да, есть / Готов оформить</pre>'
    elif callback_query.data == 're_name_input':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Вернуться на шаг назад</pre>'
        )
    else:
        text = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    await app.send_message(
        chat_id=user_id,
        text='''
Пожалуйста, отправьте сообщение с указанием ваших ФИО
<pre>Просьба указать данные в формате «Иванов Иван Иванович»</pre>
        ''',
    )


@app.on_message(filters.photo & filters.private)
async def resend_photo(client, message):
    logging.info(f'<<< private document:\n{message}')

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            SELECT * FROM
                expected_action
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        if response[0][2]:
            if response[0][2] == 'feedback':
                try:
                    query = f'''
                        UPDATE
                            expected_action
                        SET
                            secondary_action = null
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                btn = [
                    [
                        InlineKeyboardButton(
                            text='✍️ Ответить',
                            callback_data=f'reply?id={user_id}',
                        )
                    ],
                ]

                if message.from_user.username:
                    username = f'@{message.from_user.username}'
                else:
                    username = ''

                if message.from_user.first_name:
                    first_name = message.from_user.first_name
                else:
                    first_name = ''

                if message.caption:
                    caption = message.caption
                else:
                    caption = ''

                if username and first_name:
                    text = f'{first_name} ({username}) спрашивает:\n\n{caption}'
                elif first_name:
                    text = f'{first_name} спрашивает:\n\n{caption}'
                elif username:
                    text = f'{username} спрашивает:\n\n{caption}'
                else:
                    text = f'anonymous (id: {user_id}) спрашивает:\n\n{caption}'

                if message.photo:
                    file_id = message.photo.file_id
                else:
                    file_id = message.document.file_id

                await app.send_cached_media(
                    chat_id=group_id,
                    file_id=file_id,
                    caption=f'{datetime.now(tz=tz).replace(microsecond=0)}\n{text}',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                )

                await app.send_message(
                    chat_id=user_id,
                    disable_web_page_preview=True,
                    text=f'Ваш вопрос направлен менеджерам проекта. В ближайшее время вам ответят.',
                )
        elif response[0][1]:
            if response[0][1] == 'NDA':
                dt_now = datetime.now(tz=tz)

                try:
                    query = f'''
                        UPDATE
                            candidates
                        SET
                            candidate_status = \'отправил NDA\',
                            dt_last_activity = null,
                            dt_application_submission = \'{dt_now}\'
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                try:
                    query = f'''
                        UPDATE
                            expected_action
                        SET
                            primary_action = null
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                await app.send_message(
                    chat_id=user_id,
                    text='Благодарим вас за заполнение заявки на участие! Осталось немного подождать, пока наши специалисты проверят анкету. Мы сообщим вам результаты проверки в ближайшее время.',
                )

                query = f'''
                    SELECT * FROM
                        candidates
                    WHERE
                        id = {user_id};
                '''
                cursor.execute(query)
                response = cursor.fetchall()

                text = (
                    f'дата: {datetime.now(tz=tz).replace(microsecond=0)}\n\n'
                    f'username: {response[0][1]}\n'
                    f'ФИО: {response[0][11]}\n'
                    f'Номер телефона: {response[0][12]}\n'
                    f'Источник: {response[0][13]}\n'
                )

                if response[0][7] == '⛔️ Нет':
                    text += (
                        f'Модель устройства: {response[0][5]}\n'
                        f'ОС устройства: {response[0][6]}\n'
                    )
                else:
                    text += (
                        f'Модель первого устройства: {response[0][5]}\n'
                        f'ОС первого устройства: {response[0][6]}\n'
                        f'Модель второго устройства: {response[0][8]}\n'
                        f'ОС второго устройства: {response[0][9]}\n'
                    )

                btn = [
                    [
                        InlineKeyboardButton(
                            text='✅ Принять',
                            callback_data=f'solution_accepted?id={user_id}',
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text='⛔️ Отклонить',
                            callback_data=f'solution_rejected?id={user_id}',
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text='❔ На доработку',
                            callback_data=f'solution_remake?id={user_id}',
                        )
                    ],
                ]

                if message.photo:
                    file_id = message.photo.file_id
                else:
                    file_id = message.document.file_id

                await app.send_cached_media(
                    chat_id=group_id,
                    file_id=file_id,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                )


@app.on_message(filters.document & filters.private)
async def resend_document(client, message):
    logging.info(f'<<< private document:\n{message}')

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            SELECT * FROM
                expected_action
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        if response[0][2]:
            if response[0][2] == 'feedback':
                try:
                    query = f'''
                        UPDATE
                            expected_action
                        SET
                            secondary_action = null
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                btn = [
                    [
                        InlineKeyboardButton(
                            text='✍️ Ответить',
                            callback_data=f'reply?id={user_id}',
                        )
                    ],
                ]

                if message.from_user.username:
                    username = f'@{message.from_user.username}'
                else:
                    username = ''

                if message.from_user.first_name:
                    first_name = message.from_user.first_name
                else:
                    first_name = ''

                if message.caption:
                    caption = message.caption
                else:
                    caption = ''

                if username and first_name:
                    text = f'{first_name} ({username}) спрашивает:\n\n{caption}'
                elif first_name:
                    text = f'{first_name} спрашивает:\n\n{caption}'
                elif username:
                    text = f'{username} спрашивает:\n\n{caption}'
                else:
                    text = f'anonymous (id: {user_id}) спрашивает:\n\n{caption}'

                if message.photo:
                    file_id = message.photo.file_id
                else:
                    file_id = message.document.file_id

                await app.send_cached_media(
                    chat_id=group_id,
                    file_id=file_id,
                    caption=f'{datetime.now(tz=tz).replace(microsecond=0)}\n{text}',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                )

                await app.send_message(
                    chat_id=user_id,
                    disable_web_page_preview=True,
                    text=f'Ваш вопрос направлен менеджерам проекта. В ближайшее время вам ответят.',
                )
        elif response[0][1]:
            if response[0][1] == 'NDA':
                dt_now = datetime.now(tz=tz)

                try:
                    query = f'''
                        UPDATE
                            candidates
                        SET
                            candidate_status = \'отправил NDA\',
                            dt_last_activity = null,
                            dt_application_submission = \'{dt_now}\'
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                try:
                    query = f'''
                        UPDATE
                            expected_action
                        SET
                            primary_action = null
                        WHERE
                            id = {user_id};
                    '''
                    cursor.execute(query)
                    conn.commit()
                except Exception as e:
                    logging.error(e)
                    conn.rollback()
                    await app.send_message(
                        chat_id=user_id,
                        text='Что-то пошло не так. Попробуйте повторить чуть позже',
                    )
                    return

                await app.send_message(
                    chat_id=user_id,
                    text='Благодарим вас за заполнение заявки на участие! Осталось немного подождать, пока наши специалисты проверят анкету. Мы сообщим вам результаты проверки в ближайшее время.',
                )

                query = f'''
                    SELECT * FROM
                        candidates
                    WHERE
                        id = {user_id};
                '''
                cursor.execute(query)
                response = cursor.fetchall()

                text = (
                    f'дата: {datetime.now(tz=tz).replace(microsecond=0)}\n\n'
                    f'username: {response[0][1]}\n'
                    f'ФИО: {response[0][11]}\n'
                    f'Номер телефона: {response[0][12]}\n'
                    f'Источник: {response[0][13]}\n'
                )

                if response[0][7] == '⛔️ Нет':
                    text += (
                        f'Модель устройства: {response[0][5]}\n'
                        f'ОС устройства: {response[0][6]}\n'
                    )
                else:
                    text += (
                        f'Модель первого устройства: {response[0][5]}\n'
                        f'ОС первого устройства: {response[0][6]}\n'
                        f'Модель второго устройства: {response[0][8]}\n'
                        f'ОС второго устройства: {response[0][9]}\n'
                    )

                btn = [
                    [
                        InlineKeyboardButton(
                            text='✅ Принять',
                            callback_data=f'solution_accepted?id={user_id}',
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text='⛔️ Отклонить',
                            callback_data=f'solution_rejected?id={user_id}',
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text='❔ На доработку',
                            callback_data=f'solution_remake?id={user_id}',
                        )
                    ],
                ]

                if message.photo:
                    file_id = message.photo.file_id
                else:
                    file_id = message.document.file_id

                await app.send_cached_media(
                    chat_id=group_id,
                    file_id=file_id,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                )


@app.on_message(filters.text & filters.private)
async def private_message_handler(client, message):
    logging.info(f'<<< private msg:\n{message}')

    user_id = message.from_user.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    if len(message.text) > 255:
        ...
    else:
        query = f'''
            SELECT * FROM
                expected_action
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()

        if response:
            if response[0][2]:
                if response[0][2] == 'feedback':
                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                secondary_action = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    btn = [
                        [
                            InlineKeyboardButton(
                                text='✍️ Ответить',
                                callback_data=f'reply?id={user_id}',
                            )
                        ],
                    ]

                    if message.from_user.username:
                        username = f'@{message.from_user.username}'
                    else:
                        username = ''

                    if message.from_user.first_name:
                        first_name = message.from_user.first_name
                    else:
                        first_name = ''

                    if username and first_name:
                        text = f'{first_name} ({username}) спрашивает:\n\n{message.text}'
                    elif first_name:
                        text = f'{first_name} спрашивает:\n\n{message.text}'
                    elif username:
                        text = f'{username} спрашивает:\n\n{message.text}'
                    else:
                        text = f'anonymous (id: {user_id}) спрашивает:\n\n{message.text}'

                    await app.send_message(
                        chat_id=group_id,
                        text=f'{datetime.now(tz=tz).replace(microsecond=0)}\n{text}',
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                    )

                    await app.send_message(
                        chat_id=user_id,
                        disable_web_page_preview=True,
                        text=f'Ваш вопрос направлен менеджерам проекта. В ближайшее время вам ответят.',
                    )
            elif response[0][1]:
                dt_now = datetime.now(tz=tz)

                if response[0][1] == 'first_device_model':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                first_device_model = \'{message.text}\',
                                candidate_status = \'указывает ОС первого устройства\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'first_device_os\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    await app.send_message(
                        chat_id=user_id,
                        text=f'Отправьте сообщение с указанием ОС вашего устройства\n<pre>Например: Android 11</pre>',
                    )

                    # btn = [
                    #     [
                    #         InlineKeyboardButton(
                    #             text='⛔️ Исправить',
                    #             callback_data='re_first_device_model',
                    #         ),
                    #         InlineKeyboardButton(
                    #             text='✅ Верно',
                    #             callback_data='first_device_os',
                    #         ),
                    #     ],
                    # ]

                    # await app.send_message(
                    #     chat_id=user_id,
                    #     text=f'Проверьте правильность введённой информации:\n\n{message.text}',
                    #     reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                    # )
                elif response[0][1] == 'first_device_os':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                first_device_os = \'{message.text}\',
                                candidate_status = \'выбор наличия второго устройства\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'button_wait\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    btn = [
                        [
                            InlineKeyboardButton(
                                text='⛔️ Нет',
                                callback_data='mir',
                            ),
                            InlineKeyboardButton(
                                text='✅ Да',
                                callback_data='input_second_device_model',
                            ),
                        ],
                    ]

                    await app.send_message(
                        chat_id=user_id,
                        text='''
Есть ли у вас второе подходящее устройство на Android с версией 7+ и NFC-модулем, на котором вы также готовы пройти тестирование? 

Если у вас имеется такое устройство, вы также можете пройти тестирование и на нём. Вознаграждение будет за каждое устройство соответственно (но не более двух устройств).
                        ''',
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                    )
                elif response[0][1] == 'second_device_model':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                second_device_model = \'{message.text}\',
                                candidate_status = \'указывает модель ОС устройства\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'second_device_os\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    await app.send_message(
                        chat_id=user_id,
                        text=f'Отправьте сообщение с указанием ОС вашего устройства\n<pre>Например: Android 11</pre>',
                    )
                elif response[0][1] == 'second_device_os':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                second_device_os = \'{message.text}\',
                                candidate_status = \'выбор наличия карты МИР\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'button_wait\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    btn = [
                        [
                            InlineKeyboardButton(
                                text='✅ Да, есть / Готов оформить',
                                callback_data='name_input',
                            ),
                            InlineKeyboardButton(
                                text='⛔️ Нет / Не готов оформлять',
                                callback_data='no_card2',
                            ),
                        ],
                    ]

                    await app.send_message(
                        chat_id=user_id,
                        text='''
Есть ли у вас в наличии банковские карты платёжной системы МИР?

Мы не будем запрашивать полные данные ваших карт или доступ к ним. Карта может потребоваться для тестирования. Мы будем тестировать официальное приложение крупной компании, поэтому это абсолютно безопасно. Использовать карту будете только вы сами.

Также вы можете оформить виртуальную карту МИР в любом банковском приложении за пару минут - и закрыть её сразу по окончании тестирования.
                        ''',
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                    )
                elif response[0][1] == 'candidate_name':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                candidate_name = \'{message.text}\',
                                candidate_status = \'указывает номер телефона\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'phone_number\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    await app.send_message(
                        chat_id=user_id,
                        text=f'Пожалуйста, отправьте сообщение с указанием вашего контактного номера телефона\n<pre>Просьба указывать номер в формате 89ххххххххх</pre>',
                    )
                elif response[0][1] == 'phone_number':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                phone_number = \'{message.text}\',
                                candidate_status = \'указывает источник\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = \'referrer\'
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    await app.send_message(
                        chat_id=user_id,
                        text='''
Как вы узнали о нас?

Укажите источник, который сообщил о проекте. 
 - От человека? Укажите его ФИО. 
 - Из публикации в telegram-канале или в интернете? Укажите название канала/ресурса. 
В случае, если вы узнали о проекте самостоятельно, так и напишите.
                        ''',
                    )
                elif response[0][1] == 'referrer':
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                referrer = \'{message.text}\',
                                candidate_status = \'проверяет акнкету\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return
                    await check(user_id)
                elif response[0][1] == 'NDA':
                    await app.send_message(
                        chat_id=user_id,
                        text='Пожалуйста, заполните NDA и отправьте его в этот чат в удобном для вас формате - pdf, фото, скриншот.',
                    )
                elif 'change_' in response[0][1]:
                    target = response[0][1].replace('change_', '')

                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                {target} = \'{message.text}\',
                                candidate_status = \'редактирует анкету\',
                                dt_last_activity = \'{dt_now}\',
                                reminder_sent = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return

                    try:
                        query = f'''
                            UPDATE
                                expected_action
                            SET
                                primary_action = null
                            WHERE
                                id = {user_id};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        await app.send_message(
                            chat_id=user_id,
                            text='Что-то пошло не так. Попробуйте повторить чуть позже',
                        )
                        return
                    await check(user_id)
                elif response[0][1] == 'button_wait':
                    await app.send_message(
                        chat_id=user_id,
                        text='Пожалуйста, выберите один из вариантов ответа по кнопкам выше.\nЕсли у вас возник вопрос, задайте его введя команду /feedback',
                    )
        else:
            ...


@app.on_callback_query(filters.regex('done'))
async def done(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                candidates
            SET
                candidate_status = \'закончил заполнение анкеты\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'NDA\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=f'{callback_query.message.text}\n\n<pre>✅ Всё правильно</pre>',
    )

    await app.send_document(
        chat_id=user_id,
        document=Path(
            dir_main,
            dir_data,
            'NDA_(soglasheniye_o_nerazglashenii).docx',
        ),
        caption='''
<b>Важным элементом процесса тестирования является NDA (Соглашение о неразглашении информации)</b>

Заполнение NDA не только обеспечивает безопасность проекта, но и позволяет вам участвовать в тестировании других продуктов без необходимости проходить процесс согласования каждый раз.

Также данные из NDA дают нам возможность оформить вам <u>именной сертификат</u>, подтверждающий ваше участие в тестировании. Такой сертификат позволит дополнить резюме конкурентоспособной позицией.

Просто заполните поля, подпишите документ выше и отправьте его в этот чат в удобном для вас формате - pdf, фото, скриншот.

Спешим развеять ваши сомнения: наша компания не передает данные третьим лицам и не использует их никак, кроме возможности зарегистрировать вас на текущий проект. 

Инструкция, как подписать документ, без необходимости его распечатывать - https://drive.google.com/file/d/1G8YMJle8pgYLniirf_2fFflcsDaOMpf0
        ''',
    )


@app.on_callback_query(filters.regex('change_'))
async def change_data(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        query = f'''
                SELECT * FROM
                    banned
                WHERE
                    id = {user_id};
            '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'{callback_query.data}\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if callback_query.data == 'change_candidate_name':
        text = f'{callback_query.message.text}\n\n<pre>Изменить ФИО</pre>'
        text_msg = 'Пожалуйста, отправьте сообщение с указанием ваших ФИО\n<pre>Просьба указать данные в формате «Иванов Иван Иванович»</pre>'
    elif callback_query.data == 'change_phone_number':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Изменить номер телефона</pre>'
        )
        text_msg = 'Пожалуйста, отправьте сообщение с указанием вашего контактного номера телефона\n<pre>Просьба указывать номер в формате 89ххххххххх</pre>'
    elif callback_query.data == 'change_referrer':
        text = (
            f'{callback_query.message.text}\n\n' f'<pre>Изменить источник</pre>'
        )
        text_msg = '''Как вы узнали о нас?

Укажите источник, который сообщил о проекте. 
 - От человека? Укажите его ФИО. 
 - Из публикации в telegram-канале или в интернете? Укажите название канала/ресурса. 
В случае, если вы узнали о проекте самостоятельно, так и напишите.
        '''
    elif callback_query.data == 'change_first_device_model':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Изменить модель устройства</pre>'
        )
        text_msg = 'Отправьте сообщение с указанием модели вашего устройства без ОС (операционной системы)\n<pre>Например: Huawei P Smart Z</pre>'
    elif callback_query.data == 'change_first_device_os':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Изменить ОС устройства</pre>'
        )
        text_msg = 'Отправьте сообщение с указанием ОС вашего устройстваа\n<pre>Например: Android 11</pre>'
    elif callback_query.data == 'change_second_device_model':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Изменить модель устройства</pre>'
        )
        text_msg = 'Отправьте сообщение с указанием модели вашего устройства без ОС (операционной системы)\n<pre>Например: Huawei P Smart Z</pre>'
    elif callback_query.data == 'change_second_device_os':
        text = (
            f'{callback_query.message.text}\n\n'
            f'<pre>Изменить ОС устройства</pre>'
        )
        text_msg = 'Отправьте сообщение с указанием ОС вашего устройства\n<pre>Например: Android 11</pre>'
    else:
        text = ''
        text_msg = ''

    await app.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=text,
    )

    await app.send_message(
        chat_id=user_id,
        text=text_msg,
    )


async def check(user_id):
    dt_now = datetime.now(tz=tz)

    try:
        query = f'''
            UPDATE
                candidates
            SET
                candidate_status = \'редактирует анкету\',
                dt_last_activity = \'{dt_now}\',
                reminder_sent = null
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    try:
        query = f'''
            UPDATE
                expected_action
            SET
                primary_action = \'button_wait\'
            WHERE
                id = {user_id};
        '''
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=user_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    query = f'''
        SELECT * FROM
            candidates
        WHERE
            id = {user_id};
    '''
    cursor.execute(query)
    response = cursor.fetchall()

    text = (
        f'Проверьте правильность введённой информации:\n\n'
        f'ФИО: <i>{response[0][11]}</i>\n'
        f'Номер телефона: <i>{response[0][12]}</i>\n'
        f'Источник: <i>{response[0][13]}</i>\n'
    )

    btn = [
        [
            InlineKeyboardButton(
                text='Изменить ФИО',
                callback_data='change_candidate_name',
            )
        ],
        [
            InlineKeyboardButton(
                text='Изменить номер телефона',
                callback_data='change_phone_number',
            ),
        ],
        [
            InlineKeyboardButton(
                text='Изменить источник',
                callback_data='change_referrer',
            ),
        ],
    ]

    if response[0][7] == '⛔️ Нет':
        text += (
            f'Модель устройства: <i>{response[0][5]}</i>\n'
            f'ОС устройства: <i>{response[0][6]}</i>\n'
        )
        btn += [
            [
                InlineKeyboardButton(
                    text='Изменить модель устройства',
                    callback_data='change_first_device_model',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Изменить ОС устройства',
                    callback_data='change_first_device_os',
                ),
            ],
        ]
    else:
        text += (
            f'Модель первого устройства: <i>{response[0][5]}</i>\n'
            f'ОС первого устройства: <i>{response[0][6]}</i>\n'
            f'Модель второго устройства: <i>{response[0][8]}</i>\n'
            f'ОС второго устройства: <i>{response[0][9]}</i>\n'
        )
        btn += [
            [
                InlineKeyboardButton(
                    text='Изменить модель первого устройства',
                    callback_data='change_first_device_model',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Изменить ОС первого устройства',
                    callback_data='change_first_device_os',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Изменить модель второго устройства',
                    callback_data='change_second_device_model',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Изменить ОС второго устройства',
                    callback_data='change_second_device_os',
                ),
            ],
        ]

    btn += [
        [
            InlineKeyboardButton(
                text='✅ Всё правильно',
                callback_data='done',
            )
        ],
    ]

    await app.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
    )


@app.on_callback_query(filters.regex('reply'))
async def answer(client, callback_query):
    logging.info(callback_query)

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    manager_id = callback_query.from_user.id

    candidate_id = callback_query.data.split('id=')[1]

    message_id = callback_query.message.id

    if callback_query.from_user.username:
        username = f'@{callback_query.from_user.username}'
    else:
        username = callback_query.from_user.first_name

    query = f'''
        SELECT * FROM
            managers
        WHERE
            manager_id = {manager_id};
    '''
    cursor.execute(query)
    response = cursor.fetchall()

    if response:
        await app.send_message(
            chat_id=group_id, text=f'{username}, предыдущий вопрос ещё не решён'
        )
    else:
        try:
            query = f'''
                INSERT INTO
                    managers (manager_id, candidate_id)
                VALUES
                    ({manager_id}, {candidate_id})
                ON CONFLICT DO NOTHING;
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=group_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=(
                f'{callback_query.message.text}\n\n'
                f'{datetime.now(tz=tz).replace(microsecond=0)}\n'
                f'Отвечает {username}'
            ),
        )

        await app.send_message(
            chat_id=group_id, text=f'{username}, напиши ответ пользователю:'
        )


@app.on_message(filters.text & filters.group)
async def private_message_handler(client, message):
    logging.info(f'<<< group msg:\n{message}')

    manager_id = message.from_user.id

    chat_id = message.chat.id

    message_id = message.id

    if chat_id != group_id:
        return

    try:
        query = f'''
            SELECT * FROM
                managers
            WHERE
                manager_id = {manager_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=group_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        try:
            query = f'''
                DELETE FROM 
                    managers
                WHERE
                    manager_id = {manager_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=group_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        await app.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text='Ответ отправлен',
        )

        await app.send_message(
            chat_id=response[0][1],
            text=f'Ответ на ваш вопрос:\n\n{message.text}',
        )
    else:
        ...


@app.on_message(filters.document & filters.group)
async def resend_photo(client, message):
    logging.info(f'<<< group document:\n{message}')

    manager_id = message.from_user.id

    chat_id = message.chat.id

    message_id = message.id

    if chat_id != group_id:
        return

    try:
        query = f'''
            SELECT * FROM
                managers
            WHERE
                manager_id = {manager_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=group_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        try:
            query = f'''
                DELETE FROM 
                    managers
                WHERE
                    manager_id = {manager_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=group_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        if message.photo:
            file_id = message.photo.file_id
        else:
            file_id = message.document.file_id

        if message.caption:
            caption = f'Ответ на ваш вопрос:\n\n{message.caption}'
        else:
            caption = f'Ответ на ваш вопрос'

        await app.send_cached_media(
            chat_id=response[0][1],
            file_id=file_id,
            caption=caption,
        )

        await app.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text='Ответ отправлен',
        )
    else:
        ...


@app.on_message(filters.photo & filters.group)
async def resend_photo(client, message):
    logging.info(f'<<< group photo:\n{message}')

    manager_id = message.from_user.id

    chat_id = message.chat.id

    message_id = message.id

    if chat_id != group_id:
        return

    try:
        query = f'''
            SELECT * FROM
                managers
            WHERE
                manager_id = {manager_id};
        '''
        cursor.execute(query)
        response = cursor.fetchall()
    except Exception as e:
        logging.error(e)
        conn.rollback()
        await app.send_message(
            chat_id=group_id,
            text='Что-то пошло не так. Попробуйте повторить чуть позже',
        )
        return

    if response:
        try:
            query = f'''
                DELETE FROM 
                    managers
                WHERE
                    manager_id = {manager_id};
            '''
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            logging.error(e)
            conn.rollback()
            await app.send_message(
                chat_id=group_id,
                text='Что-то пошло не так. Попробуйте повторить чуть позже',
            )
            return

        if message.photo:
            file_id = message.photo.file_id
        else:
            file_id = message.document.file_id

        if message.caption:
            caption = f'Ответ на ваш вопрос:\n\n{message.caption}'
        else:
            caption = f'Ответ на ваш вопрос'

        await app.send_cached_media(
            chat_id=response[0][1],
            file_id=file_id,
            caption=caption,
        )

        await app.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text='Ответ отправлен',
        )
    else:
        ...


@app.on_message(filters.channel)
async def private_message_handler(client, message):
    logging.info(f'<<< channel msg:\n{message}')


@app.on_callback_query()
async def solution(client, callback_query):
    logging.info(f'<<< not registred callback_query:\n{callback_query}')

    callback_query_id = callback_query.id

    try:
        await app.answer_callback_query(callback_query_id=callback_query_id)
    except exceptions.bad_request_400.QueryIdInvalid:
        ...

    chat_id = callback_query.message.chat.id

    user_id = callback_query.from_user.id

    message_id = callback_query.message.id

    try:
        await app.delete_messages(chat_id=chat_id, message_ids=message_id)

        await app.send_message(chat_id=chat_id, text='Oops!')
    except Exception as e:
        logging.error(e)


@app.on_message()
async def start(client, message):
    logging.info(f'<<< other msg:\n{message}')


def add_bot_menu():
    time.sleep(5)
    app.set_bot_commands(
        commands=[
            BotCommand(command='start', description='Подать заявку'),
            BotCommand(command='about', description='Информация о проекте'),
            BotCommand(command='feedback', description='Задать вопрос'),
            BotCommand(command='help', description='Помощь'),
        ],
        scope=BotCommandScopeAllPrivateChats(),
    )
    app.set_bot_commands(
        commands=[
            BotCommand(command='report', description='Отчёт'),
            BotCommand(command='help', description='Помощь'),
        ],
        scope=BotCommandScopeChat(chat_id=group_id),
    )
    logging.info('menu updated')


def reminder():
    time.sleep(5)

    while True:
        dt_now = datetime.now(tz=tz)

        try:
            query = f'''
                SELECT * FROM
                    candidates
                WHERE
                    dt_last_activity is not null
                AND
                    reminder_sent is not true;
            '''
            cursor.execute(query)
            response = cursor.fetchall()
        except Exception as e:
            logging.error(e)
            break

        if response:
            for item in response:
                if item[15] + timedelta(days=1) < dt_now:
                    try:
                        query = f'''
                            UPDATE
                                candidates
                            SET
                                candidate_status = \'остановился\',
                                reminder_sent = true
                            WHERE
                                id = {item[0]};
                        '''
                        cursor.execute(query)
                        conn.commit()
                    except Exception as e:
                        logging.error(e)
                        conn.rollback()
                        app.send_message(
                            chat_id=group_id,
                            text=f'Что-то пошло не так. Не удалось отправить напоминание {item[1]}\n\nОшибка: {e}',
                        )
                        break

                    btn = [
                        [
                            InlineKeyboardButton(
                                text='❔ Обратная связь',
                                callback_data='feedback',
                            ),
                        ],
                    ]

                    try:
                        app.send_message(
                            chat_id=item[0],
                            text=f'''
Добрый день, {item[17]}!
Заметили, что вы не завершили заполнение анкеты для участия в проекте. Будем рады, если найдете минутку, чтобы дополнить информацию. Если возникли вопросы или трудности с заполнением заявки - оставьте нам сообщение, менеджер проекта свяжется с вами для уточнения деталей. Спасибо!
                            ''',
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=btn
                            ),
                        )
                    except Exception as e:
                        logging.error(e)
                        app.send_message(
                            chat_id=group_id,
                            text=f'Что-то пошло не так. Не удалось отправить напоминание {item[1]}\n\nОшибка: {e}',
                        )

        time.sleep(300)


if __name__ == '__main__':
    threading.Thread(target=add_bot_menu, daemon=True).start()
    threading.Thread(target=reminder, daemon=True).start()

    try:
        app.run()
    except Exception as e:
        logging.error(e)
        exit()
