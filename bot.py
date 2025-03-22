import os


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


def main():
    get_questions(get_filename_images())


if __name__ == '__main__':
    main()
