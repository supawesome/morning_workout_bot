# import logging
import os
import random
import csv

import psycopg2
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# # Enable logging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
# )
#
# logger = logging.getLogger(__name__)


DATABASE_URL = str(os.environ.get('DATABASE_URL'))
CHILL_EVENT_C = 0.003802  # 5% https://gaming.stackexchange.com/questions/161430/calculating-the-constant-c-in-dota-2-pseudo-random-distribution?utm_source=pocket_mylist
DOUBLE_EVENT_C= 0.014746  # 10%


def start(update: Update, context: CallbackContext) -> None:
    """Sends a 'Hello' message when the command /start is issued."""
    # user = update.effective_user

    keyboard = [
        '🎲',
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
    """Gets data from csv file and places them in a dict."""

    exercises_dict = {}
    exercises_list = []

    with open(filename, mode='r') as infile:
        reader = csv.reader(infile)
        header = next(reader) # to refactor
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
    """Returns 1 random exercise for each category.

    Args:
        exercise_dict: A dict of lists
    """
# todo document and explain more in docstring

    random_exercises = {}

    for key in exercise_dict:
        no_exercises = len(exercise_dict[key])
        n = random.randint(0, no_exercises - 1)
        random_exercises[key] = exercise_dict[key][n]

    return random_exercises


EXERCISES_DICT = get_exercises('exercises.csv')


def get_workout(update: Update, context: CallbackContext) -> None:
    """Sends a workout once the user rolled the dice.

    Actually, this function is needed to:
    1) decide if events have occurred
    2) update proc of events
    """

    if update.message.text == '🎲':

        chat_id = update.message.chat_id
        username = update.message.from_user.username

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM users WHERE chat_id = '{chat_id}'")
        query_result = cursor.fetchone()

        if query_result is None:
            cursor.execute(f"INSERT INTO users (chat_id, username, double_event_counter, chill_event_counter)"
                           f" VALUES ('{chat_id}', '{username}', 0, 0)")
            conn.commit()
        else:
            cursor.execute(f"SELECT double_event_counter FROM users WHERE chat_id = '{chat_id}'")
            double_event_cnt = cursor.fetchone()
            double_event_counter = double_event_cnt[0] + 1
            double_event_prob = DOUBLE_EVENT_C * double_event_counter

            cursor.execute(f"SELECT chill_event_counter FROM users WHERE chat_id = '{chat_id}'")
            chill_event_cnt = cursor.fetchone()
            chill_event_counter = chill_event_cnt[0] + 1
            chill_event_prob = CHILL_EVENT_C * chill_event_counter

            distribution_double = [1 - double_event_prob, double_event_prob]
            distribution_chill = [1 - chill_event_prob, chill_event_prob]

            procs = (0, 1)

            double_event_realization = random.choices(procs, distribution_double)
            chill_event_realization = random.choices(procs, distribution_chill)

            if double_event_realization[0] == 1:
                cursor.execute(f"UPDATE users SET double_event_counter = 0 WHERE chat_id = '{chat_id}';")
            else:
                cursor.execute(f"UPDATE users SET double_event_counter = double_event_counter + 1 "
                               f"WHERE chat_id = '{chat_id}';")
            conn.commit()

            if chill_event_realization[0] == 1:
                cursor.execute(f"UPDATE users SET chill_event_counter = 0 WHERE chat_id = '{chat_id}';")
            else:
                cursor.execute(f"UPDATE users SET chill_event_counter = chill_event_counter + 1 "
                               f"WHERE chat_id = '{chat_id}';")
            conn.commit()

        cursor.close()
        conn.close()

        random_exercise_list = []

        for key in EXERCISES_DICT:
            random_exercise_list.append(get_random_exercises(EXERCISES_DICT)[key])

        random_exercise_text = ',\n'.join(random_exercise_list)
        if double_event_realization[0] == 1 and chill_event_realization[0] == 1:
            update.message.reply_text(
                'WOW! You rolled rare Chill event! No need to do these exercises for today!').encode(
                    'utf-8')
        elif double_event_realization[0] == 1 and chill_event_realization[0] == 0:
            update.message.reply_text('BOOM! You rolled rare Double event! '
                                      'Do TWICE more reps as usual for each exercise! \n \n' +
                                      random_exercise_text).encode(
                'utf-8')
        elif double_event_realization[0] == 0 and chill_event_realization[0] == 1:
            update.message.reply_text(
                'WOW! You rolled rare Chill event! '
                'No need to do these exercises for today!').encode(
                'utf-8')
        else:
            update.message.reply_text(random_exercise_text).encode('utf-8')
    # else:
    #     pass


def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a message when the command /help is issued."""

    update.message.reply_text(
        'Just tap on dice and get a set of random exercises \n \n'
        'Why wortkout is pseudo random? Procs of special events are taken '
        'from Pseudo-Random Distribution (like random-based abilities in Dota 2) \n'
        'You can read more about the mechanism here: '
        'https://github.com/supawesome/morning_workout_bot/blob/main/PRD.md)'
    )


# def echo(update: Update, context: CallbackContext) -> None:
#     """Echo the user message."""
#     update.message.reply_text(update.message.text)


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

    dispatcher.add_handler(MessageHandler(Filters.regex('🎲') & ~Filters.command, get_workout))

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url='https://morning-workout-bot.herokuapp.com/' + TOKEN)

    updater.idle()


if __name__ == '__main__':
    main()
