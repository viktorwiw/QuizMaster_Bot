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

    user_id = event.user_id
    current_score = redis_db.hget(user_id, 'score') or 0
    redis_db.hset(
        user_id,
        mapping={
            'current_question': question,
            'current_answer': answer,
            'score': current_score,
            'waiting_for_answer': '1'
        },
    )

    logger.info(f'Current question: {redis_db.hgetall(user_id)}')

    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=question,
        keyboard=get_main_keyboard()
    )


def handle_solution_attempt(event, vk_api, redis_db):
    user_id = event.user_id
    user_answer = event.text.lower().strip(' .!?')
    true_answer = redis_db.hget(user_id, 'current_answer')

    if user_answer in true_answer.lower():
        redis_db.hincrby(user_id, 'score', 1)
        redis_db.hset(user_id, 'waiting_for_answer', '0')
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message='Правильно! Поздравляю! Для следующего вопроса нажмите "Новый вопрос"',
            keyboard=get_main_keyboard()
        )

    elif event.text == 'Сдаться':
        redis_db.hset(user_id, 'waiting_for_answer', '0')
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=f'Правильный ответ: {true_answer}\n\nДля получения нового вопроса нажмите "Новый вопрос"',
            keyboard=get_main_keyboard()
        )

    elif event.text== 'Новый вопрос':
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message='Сначала ответьте на заданный выше вопрос',
            keyboard=get_main_keyboard()
        )

    else:
        vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message='Неправильно. Попробуй ещё раз.',
            keyboard=get_main_keyboard()
        )


def handle_get_score(event, vk_api, redis_db):
    user_id = event.user_id
    score = redis_db.hget(user_id, 'score')

    if not score:
        score = 0

    vk_api.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=f'Ваш счет - {score} очков.\n\nДля продолжения, ответьте на заданный выше вопрос или нажмите "Новый вопрос".',
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
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            waiting_for_answer = redis_db.hget(user_id, 'waiting_for_answer') == '1'
            if event.text == 'Начать':
                start(event, vk_api)

            elif event.text == 'Мой счёт':
                handle_get_score(event, vk_api, redis_db)

            elif waiting_for_answer:
                handle_solution_attempt(event, vk_api, redis_db)

            elif event.text == 'Новый вопрос':
                handle_new_question_request(event, vk_api, questions, redis_db)


if __name__ == '__main__':
    main()
