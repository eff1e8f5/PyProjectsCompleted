import logging
from warnings import filterwarnings

import colorama
from bot_admin_func import *
from bot_client_func import *
from bot_tools import *
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning
from variables import *

colorama.init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s:%(funcName)s - %(message)s',
)

logging.getLogger('httpx').setLevel(logging.WARNING)
filterwarnings(
    action='ignore', message=r'.*CallbackQueryHandler', category=PTBUserWarning
)


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
                CommandHandler(
                    command='cancel',
                    callback=cancel,
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='add_events',
                    callback=add_events_init,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                ADD_EVENTS: [
                    MessageHandler(
                        filters=filters.Document.MimeType(
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        ),
                        callback=add_events,
                    )
                ],
            },
            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=cancel,
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='events',
                    callback=events,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                SELECT_CATEGORY: [
                    CallbackQueryHandler(
                        callback=select_category,
                        pattern='^events_category=',
                    ),
                ],
                SELECT_EVENT: [
                    CallbackQueryHandler(
                        callback=events,
                        pattern='^category$',
                    ),
                    CallbackQueryHandler(
                        callback=select_event,
                        pattern='^event_id=',
                    ),
                    CallbackQueryHandler(
                        callback=switching_pages,
                        pattern='^switch_pages=',
                    ),
                    CallbackQueryHandler(
                        callback=continue_registration,
                        pattern='^continue$',
                    ),
                ],
                NUMBER_TICKETS: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=number_tickets,
                    ),
                ],
                PARKING: [
                    CallbackQueryHandler(
                        callback=parking,
                        pattern='^parking=',
                    ),
                ],
                FAN_ID: [
                    MessageHandler(
                        filters=filters.TEXT & ~filters.COMMAND,
                        callback=fan_id,
                    ),
                ],
                CONFIRMATION: [
                    CallbackQueryHandler(
                        callback=confirmation,
                        pattern='^confirmation$',
                    ),
                    CallbackQueryHandler(
                        callback=events,
                        pattern='^category$',
                    ),
                    CallbackQueryHandler(
                        callback=confirmation,
                        pattern='^confirmation$',
                    ),
                ],
                END: [
                    CallbackQueryHandler(
                        callback=events,
                        pattern='^category$',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=cancel,
                ),
                CallbackQueryHandler(
                    callback=cancel,
                    pattern='^cancel$',
                ),
                CallbackQueryHandler(
                    callback=not_interested,
                    pattern='^not_interested$',
                ),
            ],
        )
    )
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler(
                    command='edit_events',
                    callback=edit_events,
                    filters=filters.ChatType.PRIVATE,
                )
            ],
            states={
                EDIT_SELECT_CATEGORY: [
                    CallbackQueryHandler(
                        callback=edit_select_category,
                        pattern='^events_category=',
                    ),
                ],
                EDIT_SELECT_EVENT: [
                    CallbackQueryHandler(
                        callback=edit_events,
                        pattern='^category$',
                    ),
                    CallbackQueryHandler(
                        callback=edit_select_event,
                        pattern='^event_id=',
                    ),
                    CallbackQueryHandler(
                        callback=edit_switching_pages,
                        pattern='^switch_pages=',
                    ),
                    CallbackQueryHandler(
                        callback=edit_event_visibility,
                        pattern='^disable$',
                    ),
                    CallbackQueryHandler(
                        callback=edit_event_visibility,
                        pattern='^enable$',
                    ),
                    CallbackQueryHandler(
                        callback=edit_select_category,
                        pattern='^category$',
                    ),
                ],
            },
            fallbacks=[
                CommandHandler(
                    command='cancel',
                    callback=cancel,
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
            command='id',
            callback=get_id,
        )
    )
    app.add_handler(
        CommandHandler(
            command='set_me_admin',
            callback=set_me_admin,
        )
    )
    app.add_handler(
        CommandHandler(
            command='report',
            callback=get_report,
        )
    )
    app.add_handler(MessageHandler(filters=None, callback=handle_messages))
    app.add_handler(CallbackQueryHandler(callback=handle_invalid_button))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    logging.info(
        f'{YELLOW}\n    bot name: {bot_name};\n    db name: {db_name};\n    db host: {db_host}'
    )

    app = Application.builder().token(token).build()

    main()
