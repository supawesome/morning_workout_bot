import csv
import logging
import os
import random
from collections import defaultdict

import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext


DATABASE_URL = str(os.environ.get('DATABASE_URL'))
DATABASE_PASSWORD = str(os.environ.get('DATABASE_PASSWORD'))
CHILL_EVENT_C = 0.003802  # 5% please refer to https://github.com/supawesome/PRD
DOUBLE_EVENT_C = 0.014746  # 10% also, refer to https://github.com/supawesome/PRD

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


def start(update: Update, context: CallbackContext) -> None:
    """Sends a 'Hello' message when the command /start is issued."""
    keyboard = [
        '🎲',
    ]

    logging.info(f'Got start message from {update.effective_chat.username}')

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        'Welcome to the workout bot! \n'
        'This bot generates random exercise for each major muscle group (upper, middle or lower body). \n'
        'Moreover, sometimes bot may trigger special events: \n'
        ' - 5% probability of a "Chill" event – means you may skip your workout today \n'
        ' - 10% probability of a "Double" event – means you should do twice more reps for each exercise this time \n \n'
        "Let's roll the dice to get a nice pseudo-random morning workou!t \n \n"
        "To learn more, type /help command.",
        reply_markup=reply_markup
    )


def get_exercises(filename: str) -> dict:
    """Gets data from csv file and places them in a dict."""
    exercises_dict = defaultdict(list)
    exercises_list = []

    with open(filename, mode='r') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        for row in reader:
            exercises_list.append(row)

    for line in exercises_list:
        exercises_dict[line[0]].append(line[1])

    return exercises_dict


def get_random_exercises(exercise_dict: dict) -> dict:
    """Returns 1 random exercise for each category.

    Args:
        exercise_dict: A dict of lists
    """
    random_exercises = {}

    for key, value in exercise_dict.items():
        exercise_count = len(value)
        n = random.randint(0, exercise_count - 1)
        random_exercises[key] = value[n]

    return random_exercises


def get_workout(update: Update, context: CallbackContext) -> None:
    """Sends a workout once the user rolled the dice.

    Actually, this function is needed to:
    1) decide if events have occurred
    2) update proc of events
    """
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    conn = psycopg2.connect(
        host=DATABASE_URL,
        dbname='postgres',
        port=5432,
        user='postgres',
        password=DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT chat_id FROM users WHERE chat_id = '{chat_id}'")
    query_result = cursor.fetchone()

    if query_result is None:
        cursor.execute(f"INSERT INTO users (chat_id, username, double_event_counter, chill_event_counter, rolls_counter)"
                       f" VALUES ('{chat_id}', '{username}', 0, 0, 0)")
        double_event_realization = []
        double_event_realization.append(0)
        chill_event_realization = []
        chill_event_realization.append(0)
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

    cursor.execute(f"UPDATE users SET rolls_counter = rolls_counter + 1 WHERE chat_id = '{chat_id}';")
    conn.commit()
    cursor.close()
    conn.close()

    random_exercise_list = []

    exercises_dict = get_exercises(os.path.join('config', 'exercises.csv'))

    for key in exercises_dict:
        random_exercise_list.append(get_random_exercises(exercises_dict)[key])

    random_exercise_text = '\n'.join(random_exercise_list) + '\nhttps://telegra.ph/Exercises-instructions-04-11'
    if double_event_realization[0] == 1 and chill_event_realization[0] == 1:
        update.message.reply_text(
            "WOW! You've rolled rare Chill event! "
            'No need to do these exercises for today!')
    elif double_event_realization[0] == 1 and chill_event_realization[0] == 0:
        update.message.reply_text("BOOM! You've rolled the rare Double event! "
                                  "Do TWICE as many reps as usual for each exercise! \n \n" +
                                  random_exercise_text, disable_web_page_preview=True)
    elif double_event_realization[0] == 0 and chill_event_realization[0] == 1:
        update.message.reply_text(
            "WOW! You've rolled rare Chill event! "
            'No need to do exercises for today!')
    else:
        update.message.reply_text(random_exercise_text, disable_web_page_preview=True)


def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a message when the command /help is issued"""
    update.message.reply_text(
        'Just tap on the dice and get a set of random exercises! \n'
        'Each exercise belongs to different major muscle group (upper, middle or lower body) \n \n'
        'Why workout is pseudo random? Procs of special events are sampled '
        'from Pseudo-Random Distribution (like random-based abilities in Dota 2) \n'
        'You can read more about the mechanism here: '
        'https://github.com/supawesome/PRD'
    )
