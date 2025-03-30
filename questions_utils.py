import os
import random

def get_filename_images():
    with os.scandir('quiz-questions/') as files:
        file_names = [file.name for file in files]
    return file_names


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
