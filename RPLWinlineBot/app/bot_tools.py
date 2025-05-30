import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

RESET = '\033[0m'
BLUE = '\033[34;1m'
CYAN = '\033[36;1m'
GREEN = '\033[32;1m'
MAGENTA = '\033[35;1m'
RED = '\033[31;1m'
YELLOW = '\033[33;1m'


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

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='отмена',
    )

    logging.info(
        f'{MAGENTA}sent message to {YELLOW}{update.effective_user.id}:\n{GREEN}{sent_message}'
    )

    return ConversationHandler.END
