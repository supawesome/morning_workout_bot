import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from bot import start, help_command, get_workout


def main() -> None:
    PORT = int(os.environ.get('PORT', '80'))
    TOKEN = str(os.environ.get('TOKEN'))

    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(
        (Filters.regex('🎲') | Filters.dice.dice)
        & ~Filters.command,
        get_workout)
    )

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url='https://workout-bot-prod.fly.dev/' + TOKEN
    )

    updater.idle()


if __name__ == '__main__':
    main()
