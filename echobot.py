#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
import random

from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


TEST_EXERCISES_DICT = {
    'upper_body': ['анжуманя', 'турник'],
    'middle_body': ['пресс качат', 'ещё пресс качат', 'и ещё пресс качат'],
    'lower_body': ['приседания', 'приседания 2']
}

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    # user = update.effective_user
    keyboard = [
        '🎲'
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Hi, this is a workout bot. \n'
        "Let's roll the dice to get a nice pseudo-random morning workout",
        reply_markup=reply_markup,
        resize_keyboard=TRUE
    )


# exercise_dict = {'upper': ('one', 'two'), 'middle': 'three'}

def get_random_exercises(exercise_dict: dict) -> dict:
    """
    Returns 1 random exercise for each category
    exercise_dict is a dict of lists
    """

    random_exercises = {}

    for key in exercise_dict:
        no_exercises = len(exercise_dict[key])
        n = random.randint(0, no_exercises - 1)
        random_exercises[key] = exercise_dict[key][n]

    return random_exercises


def get_workout(update: Update, context: CallbackContext) -> None:
    """Send a workout when the user rolled the dice"""

    if update.message.text == '🎲':
        for key in TEST_EXERCISES_DICT:
            update.message.reply_text(
                get_random_exercises(TEST_EXERCISES_DICT)[key]
            ).encode('utf-8')

        # update.message.reply_text(
        #     for key in TEST_EXERCISES_DICT:
        #         print(TEST_EXERCISES_DICT[key])
        # )
    else:
        pass


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!11111')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    PORT = int(os.environ.get('PORT', '80'))
    TOKEN = str(os.environ.get('TOKEN')) # TODO: alive
    # TOKEN = app_token # TODO: kill


    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.regex('🎲') & ~Filters.command, get_workout))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    #updater.start_polling()


    # updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    # updater.bot.set_webhook('https://morning-workout-bot.herokuapp.com/' + TOKEN)

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://morning-workout-bot.herokuapp.com/' + TOKEN)

    updater.idle()


if __name__ == '__main__':
    main()