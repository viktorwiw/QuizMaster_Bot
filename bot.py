import os
import logging
import random

from environs import Env
import redis
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, Updater, ConversationHandler


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

ANSWER, NEW_QUESTION = range(2)

def get_filename_images():
    with os.scandir('quiz-questions/') as files:
        name_images = [file.name for file in files]
    return name_images


def get_questions(file_names):
    questions = {}
    for name in file_names:
        with open(f'quiz-questions/{name}', 'r', encoding='KOI8-R') as file:
            file_content = file.read()

        for block in file_content.split('\n\n\n'):
            question = None
            answer = None
            full_answer = None

            for line in block.split('\n\n'):
                if question and (answer or full_answer):
                    if full_answer:
                        questions[question] = full_answer
                        answer = None
                        question = None
                        full_answer = None
                    else:
                        questions[question] = answer
                        full_answer = None
                if line.startswith('Вопрос'):
                    question = line.split(':', 1)[1].replace("\n", " ").strip()
                elif line.startswith('Ответ'):
                    answer = line.split(':', 1)[1].replace("\n", " ").strip()
                elif line.startswith('Комментарий'):
                    full_answer = "{}\n\n{}".format(
                        answer,
                        line.replace('\n', ' ').strip()
                    )
    return questions


def get_random_question(questions):
    return random.choice(list(questions.keys()))


def start(update: Update, context: CallbackContext):
    reply_keyboard = [
        ['Новый вопрос'],
        ['Мой счет']
    ]
    update.message.reply_text(
        text='Привет! Я бот для викторин! Чтобы начать, нажмите кнопку "Новый вопрос"',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )


def handle_new_question_request(update, context):
    questions = context.bot_data['questions']
    question = get_random_question(questions)

    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    redis_db.set(chat_id, question)

    print(redis_db.get(chat_id), '\n\n', f'Ответ: {questions[redis_db.get(chat_id)]}')

    update.message.reply_text(
        f'{question}\n\nВведите ответ:',
        reply_markup=ReplyKeyboardRemove()
    )
    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    reply_keyboard = [
        ['Сдаться'],
        ['Мой счет']
    ]
    questions = context.bot_data['questions']
    # new_question = get_random_question(questions)

    answer = update.message.text.lower()

    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    question = redis_db.get(chat_id)
    true_answer = context.bot_data['questions'][question].split('.\n', 1)[0].lower()

    if answer != true_answer:
        update.message.reply_text(
            f'Неправильно. Попробуешь ещё раз?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return ANSWER

    else:
        # context.user_data['answer_count'] += 1
        update.message.reply_text('Правильно! Поздравляю!')
        return ConversationHandler.END


def cansel(update: Update, context: CallbackContext):
    update.message.reply_text('Правильный ответ:  , Для нового вопроса нажмите "Новый вопрос"')
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()

    telegram_token = env.str('TELEGRAM_TOKEN')
    db_host = env.str('DB_REDIS_ENDPOINT')
    db_port = env.int('DB_REDIS_PORT')
    db_password = env.str('DB_REDIS_PASSWORD')

    redis_db = redis.Redis(
        host=db_host,
        port=db_port,
        decode_responses=True,
        username="default",
        password=db_password,
    )

    updater = Updater(token=telegram_token)

    dp = updater.dispatcher

    dp.bot_data['questions'] = get_questions(get_filename_images())
    dp.bot_data['redis_db'] = redis_db

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.regex('^(Новый вопрос)$'),
            handle_new_question_request
        )],

        states={
            ANSWER: [MessageHandler(Filters.text, handle_solution_attempt)],
        },

        fallbacks=[CommandHandler('cancel', cansel)],
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv_handler)

    logger.info('Бот запущен')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
