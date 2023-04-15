import csv
import logging
import os
import random
from collections import defaultdict

import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from configs.message_config import START_MESSAGE, HELP_MESSAGE, CHILL_EVENT_MESSAGE, DOUBLE_EVENT_MESSAGE, EXERCISE_INSTRUCTIONS_LINK

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
    
    update.message.reply_text(START_MESSAGE, reply_markup=reply_markup)


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


def select_from_users(cursor, column_name: str, chat_id: int) -> int:
    """Select a column from table 'users' where chat_id equals given chat_id"""
    cursor.execute(f"SELECT {column_name} FROM users WHERE chat_id = '{chat_id}'")
    return cursor.fetchone()


def insert_into_user_roll(cursor, chat_id: int, username: str, roll_result: str, 
                          is_double_event: bool, is_chill_event: bool
                          ) -> None:
    """Insert values into table 'user_roll'"""
    cursor.execute(f"INSERT INTO user_roll (chat_id, username, roll_result, is_double_event, is_chill_event)"
                   f" VALUES ('{chat_id}', '{username}', '{roll_result}', {is_double_event}, {is_chill_event})")
    return


def update_event_counter(cursor, event_realization: int, event_counter_column_name: str, chat_id: int) -> None:
    """Update event counter column in table 'users' based on event realization condition"""
    if event_realization == 1:
        cursor.execute(f"UPDATE users SET {event_counter_column_name} = 0 WHERE chat_id = '{chat_id}';")
    else:
        cursor.execute(f"UPDATE users SET {event_counter_column_name} = {event_counter_column_name} + 1 "
                        f"WHERE chat_id = '{chat_id}';")
    return


def send_workout_text(cursor, 
                      update: Update, context: CallbackContext,
                      chat_id: int, username: str, 
                      double_event_realization: int, chill_event_realization: int,
                      random_exercise_text: str
                      ) -> None:
    """Send message with workout text based on event realization conditions"""
    if double_event_realization == 1 and chill_event_realization == 1:
        update.message.reply_text(CHILL_EVENT_MESSAGE)
        insert_into_user_roll(cursor, chat_id, username, CHILL_EVENT_MESSAGE, True, True)
    elif double_event_realization == 1 and chill_event_realization == 0:
        update.message.reply_text(DOUBLE_EVENT_MESSAGE + random_exercise_text, disable_web_page_preview=True)
        insert_into_user_roll(cursor, chat_id, username, DOUBLE_EVENT_MESSAGE + random_exercise_text, True, False)
    elif double_event_realization == 0 and chill_event_realization == 1:
        update.message.reply_text(CHILL_EVENT_MESSAGE)
        insert_into_user_roll(cursor, chat_id, username, CHILL_EVENT_MESSAGE, False, True)
    else:
        update.message.reply_text(random_exercise_text, disable_web_page_preview=True)
        insert_into_user_roll(cursor, chat_id, username, random_exercise_text, False, False)
    return


def prepare_and_send_workout(update: Update, context: CallbackContext) -> None:
    """Prepare (decide if events have occurred) workout, update info in database and send workout to user"""
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

    if select_from_users(cursor, 'chat_id', chat_id) is None:
        cursor.execute(f"INSERT INTO users (chat_id, username, double_event_counter, chill_event_counter, rolls_counter)"
                       f" VALUES ('{chat_id}', '{username}', 0, 0, 0)")
        double_event_realization = [0]
        chill_event_realization = [0]
        conn.commit()
    else:
        double_event_cnt = select_from_users(cursor, 'double_event_counter', chat_id)
        double_event_counter = double_event_cnt[0] + 1
        double_event_prob = DOUBLE_EVENT_C * double_event_counter

        chill_event_cnt = select_from_users(cursor, 'chill_event_counter', chat_id)
        chill_event_counter = chill_event_cnt[0] + 1
        chill_event_prob = CHILL_EVENT_C * chill_event_counter

        distribution_double = [1 - double_event_prob, double_event_prob]
        distribution_chill = [1 - chill_event_prob, chill_event_prob]

        procs = (0, 1)

        double_event_realization = random.choices(procs, distribution_double)[0]
        chill_event_realization = random.choices(procs, distribution_chill)[0]

        update_event_counter(cursor, double_event_realization, 'double_event_counter', chat_id)
        conn.commit()
        update_event_counter(cursor, chill_event_realization, 'chill_event_counter', chat_id)
        conn.commit()


    cursor.execute(f"UPDATE users SET rolls_counter = rolls_counter + 1 WHERE chat_id = '{chat_id}';")

    random_exercise_list = []

    exercises_dict = get_exercises(os.path.join('configs', 'exercises.csv'))

    for key in exercises_dict:
        random_exercise_list.append(get_random_exercises(exercises_dict)[key])

    random_exercise_text = '\n'.join(random_exercise_list) + '\n\n' + EXERCISE_INSTRUCTIONS_LINK

    send_workout_text(cursor, 
                      update, context,
                      chat_id, username, 
                      double_event_realization, chill_event_realization,
                      random_exercise_text)

    conn.commit()
    cursor.close()
    conn.close()


def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a message when the command /help is issued"""
    update.message.reply_text(HELP_MESSAGE, disable_web_page_preview=True)
