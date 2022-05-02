import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from bot import start, help_command, get_workout


def main() -> None:
    """Starts the bot."""
    # Create the Updater and pass it your bot's token.
    PORT = int(os.environ.get('PORT', '80'))
    TOKEN = str(os.environ.get('TOKEN'))

    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # commands:
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(
        (Filters.regex('🎲') | Filters.dice.dice)
        & ~Filters.command,
        get_workout)
    )

    # Start the Bot
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url='https://morning-workout-bot.herokuapp.com/' + TOKEN
    )

    updater.idle()


if __name__ == '__main__':
    main()