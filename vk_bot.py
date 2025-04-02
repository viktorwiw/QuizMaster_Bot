import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import redis
from environs import Env
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from questions_utils import get_questions, get_filename_images, get_random_question


logger = logging.getLogger('vk_logger')


def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def start(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message='Приветствую!\n\nЯ бот для викторин! Чтобы начать, нажмите кнопку "Новый вопрос"',
        keyboard=get_main_keyboard()
    )


def handle_new_question_request(event, vk_api, questions, redis_db):
    question = get_random_question(questions)
    answer = questions[question].split('.\n', 1)[0].strip(' .!?')

    vk_user_id = f'vk-{event.user_id}'

    redis_db.hset(
        vk_user_id,
        mapping={
            'current_question': question,
            'current_answer': answer,
        },
    )

    logger.info(f'Current question: {redis_db.hgetall(vk_user_id)}')

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=question,
        keyboard=get_main_keyboard()
    )


def handle_solution_attempt(event, vk_api, redis_db):
    vk_user_id = f'vk-{event.user_id}'
    user_answer = event.text.lower().strip(' .!?')
    true_answer = redis_db.hget(vk_user_id, 'current_answer')

    if user_answer in true_answer.lower():
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message='Правильно! Поздравляю! Для следующего вопроса нажмите "Новый вопрос"',
            keyboard=get_main_keyboard()
        )

    elif event.text == 'Сдаться':
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message=f'Правильный ответ: {true_answer}\n\nДля получения нового вопроса нажмите "Новый вопрос"',
            keyboard=get_main_keyboard()
        )

    else:
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            message='Неправильно. Попробуй ещё раз.',
            keyboard=get_main_keyboard()
        )


def main():
    formatter = logging.Formatter(
        "%(name)s | %(levelname)s | %(asctime)s\n"
        "%(message)s | %(filename)s:%(lineno)d",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(Path(__file__).parent / 'vk_bot.log', maxBytes=10000, backupCount=2)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    env = Env()
    env.read_env()

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

    questions = get_questions(get_filename_images())

    vk_token = env.str('VK_TOKEN')

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    logger.info("Bot started")

    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
            continue

        if event.text == 'Начать':
            start(event, vk_api)
            continue

        if event.text == 'Новый вопрос':
            handle_new_question_request(event, vk_api, questions, redis_db)
            continue

        handle_solution_attempt(event, vk_api, redis_db)


if __name__ == '__main__':
    main()
