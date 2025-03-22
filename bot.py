import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from environs import Env
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, Updater


logger = logging.getLogger(__name__)


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
            for line in block.split('\n\n'):
                if question is not None and answer is not None:
                    questions[question] = answer
                    question = None
                    answer = None
                elif line.startswith('Вопрос'):
                    question = line.split(':', 1)[1].replace("\n", " ").strip()
                elif line.startswith('Ответ'):
                    answer = line.split(':', 1)[1].replace("\n", " ").strip()


def start(update: Update, context: CallbackContext):
    update.message.reply_text(text="I'm a bot, please talk to me!")


def echo(update: Update, context: CallbackContext):
    update.message.reply_text(text=update.message.text)


def main():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(name)s | %(levelname)s | %(asctime)s\n"
        "%(message)s | %(filename)s:%(lineno)d",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = RotatingFileHandler(
        Path(__file__).parent / 'bot.log',
        maxBytes=1000,
        backupCount=2
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    env = Env()
    env.read_env()

    telegram_token = env.str('TELEGRAM_TOKEN')

    updater = Updater(token=telegram_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))

    updater.start_polling()
    updater.idle()

    get_questions(get_filename_images())


if __name__ == '__main__':
    main()
