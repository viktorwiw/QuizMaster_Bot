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

ANSWER = range(1)

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
                    full_answer = "{}\n\n{}".format(answer, line.replace('\n', ' ').strip())
    return questions


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='Привет! Я бот для викторин! Чтобы начать, нажмите кнопку "Новый вопрос"',
        reply_markup=get_main_keyboard()
    )


def get_main_keyboard():
    main_keyboard = [
        ['Новый вопрос'],
        ['Мой счет']
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard)
    return reply_markup


def handle_new_question_request(update, context):
    questions = context.bot_data['questions']
    question = random.choice(list(questions.keys()))

    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    redis_db.set(chat_id, question)

    logger.info(redis_db.get(chat_id), '\n\n', f'Ответ: {questions[redis_db.get(chat_id)]}')

    update.message.reply_text(
        f'{question}\n\nВведите ответ:',
        reply_markup=ReplyKeyboardRemove()
    )
    return ANSWER


def handle_button(update: Update, context: CallbackContext):
    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    question = redis_db.get(chat_id)
    answer = context.bot_data['questions'][question]

    if update.message.text.lower() == answer.split('.\n\n', 1)[0].lower():
        update.message.reply_text(
            f'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            reply_markup=get_main_keyboard()
        )
    elif update.message.text.lower() != answer.split('.\n\n', 1)[0].lower():
        update.message.reply_text(
            f'Неправильно. Попробуешь ещё раз?',
            reply_markup=get_main_keyboard()
        )


def handle_solution_attempt():
    pass


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
        entry_points=[MessageHandler(Filters.regex('^(Новый вопрос)$'), handle_new_question_request)],
        states={},
        fallbacks=[]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_button))

    logger.info('Бот запущен')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
