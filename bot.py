import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from environs import Env
import redis
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (CallbackContext, CommandHandler, MessageHandler,
                          Filters, Updater, ConversationHandler)

from questions_utils import get_random_question, get_filename_images, get_questions

logger = logging.getLogger(__name__)

ANSWER = range(1)


def get_keyboard():
    return ReplyKeyboardMarkup([
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет']
    ])


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='Приветствую!\n\nЯ бот для викторин! Чтобы начать, нажмите кнопку "Новый вопрос"\n\n/cansel - для отмены',
        reply_markup=get_keyboard()
    )


def handle_new_question_request(update, context):
    questions = context.bot_data['questions']
    question = get_random_question(questions)
    answer = questions[question].split('.\n', 1)[0].strip(' .!?')

    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    current_score = redis_db.hget(chat_id, 'score') or 0
    redis_db.hset(
        chat_id,
        mapping={
            'current_question': question,
            'current_answer': answer,
            'score': current_score
        },
    )

    logger.info(f'Current question: {redis_db.hgetall(chat_id)}')

    update.message.reply_text(
        question,
        reply_markup=get_keyboard()
    )
    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    answer = update.message.text.lower().strip(' .!?\n')

    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id

    true_answer = redis_db.hget(chat_id, 'current_answer').lower()

    if answer in true_answer:
        redis_db.hincrby(chat_id, 'score', 1)
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажмите "Новый вопрос"',
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

    else:
        update.message.reply_text(
            f'Неправильно. Попробуй ещё раз.',
            reply_markup=get_keyboard()
        )
        return ANSWER


def handle_give_up(update: Update, context: CallbackContext):
    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    true_answer = redis_db.hget(chat_id, 'current_answer')

    update.message.reply_text(
        f'Правильный ответ: {true_answer}\n\nДля нового вопроса нажмите "Новый вопрос"',
        reply_markup=get_keyboard()
    )
    return ConversationHandler.END


def handle_answer_dontknown(update: Update, context: CallbackContext):
    update.message.reply_text("Не понимаю")
    return ConversationHandler.END


def handle_cansel(update: Update, context: CallbackContext):
    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    redis_db.delete(chat_id)

    update.message.reply_text(
        'Команда завершения работы викторины и обнуления счета\n\nДля начала викторины нажмите "Новый вопрос".'
    )
    return ConversationHandler.END


def handle_get_score(update: Update, context: CallbackContext):
    redis_db = context.bot_data['redis_db']
    chat_id = update.message.chat_id
    score = redis_db.hget(chat_id, 'score')
    if not score:
        score = 0
    update.message.reply_text(
        f'Ваш счет - {score} очков.\n\nДля продолжения, ответьте на заданный выше вопрос или нажмите "Новый вопрос".'
    )


def main():
    formatter = logging.Formatter(
        "%(name)s | %(levelname)s | %(asctime)s\n"
        "%(message)s | %(filename)s:%(lineno)d",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(Path(__file__).parent / 'tg_bot.log', maxBytes=10000, backupCount=2)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
            ANSWER: [
                MessageHandler(Filters.regex('^(Сдаться)$'), handle_give_up),
                MessageHandler(
                    Filters.text & (~Filters.command),
                    handle_solution_attempt
                ),
            ],
        },

        fallbacks=[
            CommandHandler('cancel', handle_cansel),
            MessageHandler(
                (Filters.video | Filters.photo | Filters.document | Filters.location),
                handle_answer_dontknown
            )
        ]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(
        Filters.regex('^(Мой счет)$'),
        handle_get_score)
    )
    dp.add_handler(conv_handler)

    logger.info('Бот запущен')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
