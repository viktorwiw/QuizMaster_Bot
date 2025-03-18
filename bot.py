def get_question():
    with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as file:
        file_content = file.read()
    print(file_content)


def main():
    get_question()


if __name__ == '__main__':
    main()