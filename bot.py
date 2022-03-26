#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

import logging
import os
import random
import csv
import psycopg2
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


DATABASE_URL = str(os.environ.get('DATABASE_URL'))
CHILL_PERK_C = 0.003802  # 5% https://gaming.stackexchange.com/questions/161430/calculating-the-constant-c-in-dota-2-pseudo-random-distribution?utm_source=pocket_mylist
DOUBLE_PERK_C = 0.014746  # 10%


def start(update: Update, context: CallbackContext) -> None:
    """Send a 'Hello' message when the command /start is issued."""
    # user = update.effective_user

    keyboard = [
        '🎲'
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Hi, this is a workout bot. \n'
        'This bot returns random exercise for each set of exercises. \n'
        'Moreover, sometimes bot returns special events: \n'
        ' - 5% probability of a "Chill" event – means you may skip your workout today \n'
        ' - 10% probability of a "Double" event – means you should do twice more reps for each exercise this time \n \n'
        "Let's roll the dice to get a nice pseudo-random morning workout \n \n"
        "Also, there is /help command.",
        reply_markup=reply_markup
    )


def get_exercises(filename: str) -> dict:
    """
    Get exercises from csv and place them in a dict
    """

    exercises_dict = {}

    with open(filename, mode='r') as infile:
        reader = csv.reader(infile)
        header = next(reader) # to refactor
        exercises_list = []
        for row in reader:
            exercises_list.append(row)

    for line in exercises_list:
        if line[0] in exercises_dict:
            # append the new number to the existing array at this slot
            exercises_dict[line[0]].append(line[1])
        else:
            # create a new array in this slot
            exercises_dict[line[0]] = [line[1]]

    return exercises_dict


def get_random_exercises(exercise_dict: dict) -> dict:
    """
    Returns 1 random exercise for each category.
    exercise_dict is a dict of lists
    """

    random_exercises = {}

    for key in exercise_dict:
        no_exercises = len(exercise_dict[key])
        n = random.randint(0, no_exercises - 1)
        random_exercises[key] = exercise_dict[key][n]

    return random_exercises


EXERCISES_DICT = get_exercises('exercises.csv')


def get_workout(update: Update, context: CallbackContext) -> None:
    """
    Send a workout once the user rolled the dice

    Actually, this function is needed to:
    1) decide if perks have occured
    2) update proc of a Perks
    """

    if update.message.text == '🎲':
        random_exercise_list = []

        chat_id = update.message.chat_id
        username = update.message.from_user.username

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM users_test WHERE chat_id = '{chat_id}'")
        query_result = cursor.fetchone()

        if query_result is None:
            cursor.execute(f"INSERT INTO users_test (chat_id, username, double_perk, chill_perk)"
                           f" VALUES ('{chat_id}', '{username}', 0, 0)") # или 1,1?
            conn.commit()
        else:
            cursor.execute(f"SELECT double_perk FROM users_test WHERE chat_id = '{chat_id}'")
            # double_perk_counter = cursor.fetchone()
            double_perk_cnt = cursor.fetchone()
            double_perk_counter = double_perk_cnt[0] + 1  # ?
            # double_perk_counter += 1 #?
            double_perk_prob = DOUBLE_PERK_C * double_perk_counter

            # update.message.reply_text('double_perk_prob')
            # update.message.reply_text(double_perk_cnt)
            # update.message.reply_text(double_perk_prob)

            cursor.execute(f"SELECT chill_perk FROM users_test WHERE chat_id = '{chat_id}'")
            # update.message.reply_text('2.1.1')
            # chill_perk_counter = cursor.fetchone()
            # chill_perk_counter += 1 #?
            chill_perk_cnt = cursor.fetchone()
            chill_perk_counter = chill_perk_cnt[0] + 1 #?
            chill_perk_prob = CHILL_PERK_C * chill_perk_counter

            # update.message.reply_text('chill_perk_cnt')
            # update.message.reply_text(chill_perk_cnt)
            # update.message.reply_text(chill_perk_prob)

            proc_list = [0, 1]

            distribution_double = [1 - double_perk_prob, double_perk_prob]
            distribution_chill = [1 - chill_perk_prob, chill_perk_prob]

            double_perk_realization = random.choices(proc_list, distribution_double)
            chill_perk_realization = random.choices(proc_list, distribution_chill)

            # update.message.reply_text('double_perk_realization')
            # update.message.reply_text(double_perk_realization)
            # update.message.reply_text('chill_perk_realization')
            # update.message.reply_text(chill_perk_realization)

            if double_perk_realization[0] == 1:
                # update.message.reply_text('BOOM! You rolled rare Double perk! Do all exercises TWICE as usual!').encode('utf-8')
                cursor.execute(f"UPDATE users_test SET double_perk = 0 WHERE chat_id = '{chat_id}';")
                conn.commit()
            else:
                cursor.execute(f"UPDATE users_test SET double_perk = double_perk + 1 WHERE chat_id = '{chat_id}';")
                conn.commit()

            if chill_perk_realization[0] == 1:
                # update.message.reply_text('WOW! You rolled rare Chill perk! No need to do these exercises for today!').encode(
                #     'utf-8')
                cursor.execute(f"UPDATE users_test SET chill_perk = 0 WHERE chat_id = '{chat_id}';")
                conn.commit()
            else:
                cursor.execute(f"UPDATE users_test SET chill_perk = chill_perk + 1 WHERE chat_id = '{chat_id}';")
                conn.commit()

        cursor.close()
        conn.close()

        for key in EXERCISES_DICT:
            random_exercise_list.append(get_random_exercises(EXERCISES_DICT)[key])

        random_exercise_text = ',\n'.join(random_exercise_list)
        if double_perk_realization[0] == 1 and chill_perk_realization[0] == 1:
            update.message.reply_text(
                'WOW! You rolled rare Chill perk! No need to do these exercises for today!').encode(
                    'utf-8')
        elif double_perk_realization[0] == 1 and chill_perk_realization[0] == 0:
            update.message.reply_text('BOOM! You rolled rare Double perk! Do TWICE more reps as usual for each exercise! \n \n' +
                                      random_exercise_text).encode(
                'utf-8')
            # update.message.reply_text(random_exercise_text).encode('utf-8')
        elif double_perk_realization[0] == 0 and chill_perk_realization[0] == 1:
            update.message.reply_text(
                'WOW! You rolled rare Chill perk! No need to do these exercises for today!').encode(
                'utf-8')
        else:
            update.message.reply_text(random_exercise_text).encode('utf-8')
    else:
        pass


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""

    update.message.reply_text(
        'Just tap on dice and get a set of random exercises \n \n'
        'Why wortkout is pseudo random? Procs of special events are taken '
        'from Pseudo-Random Distribution (like random-based abilities in Dota 2) \n'
        'You may read more about the mechanism here: '
        'https://github.com/supawesome/morning_workout_bot/blob/main/PRD.md)'
    )



# def echo(update: Update, context: CallbackContext) -> None:
#     """Echo the user message."""
#     update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    PORT = int(os.environ.get('PORT', '80'))
    TOKEN = str(os.environ.get('TOKEN'))

    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # commands:
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.regex('🎲') & ~Filters.command, get_workout))

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://morning-workout-bot.herokuapp.com/' + TOKEN)

    updater.idle()


if __name__ == '__main__':
    main()
