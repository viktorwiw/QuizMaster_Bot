# QuizMasterBot
Чат-бот викторина для Telegram и [ВКонтакте](https://vk.com/).
Это познавательный бот, который проверит ваши знания по истории! От древних цивилизаций до современных событий – пройдите увлекательную викторину, узнайте новые факты и станьте настоящим историческим экспертом.

![Mar-31-2025 15-48-14](https://github.com/user-attachments/assets/3d7a2549-f141-4119-851d-c94abcd23d52)

![Mar-31-2025 15-44-11](https://github.com/user-attachments/assets/06a8d442-cee1-493c-90ac-fac5752694e4)


Посмотреть боты:

[Телеграм]()

[Вконтакте]()

---

## Как установить

- создайте телеграм-бот с помощью [**телеграм-бота**](https://t.me/BotFather) и получите токен. Токен выглядит наподобие такой строки: 
```6552612291:AAHL80fIRBI4vRypY2L5K3RXr3F2-tVYf9Q```

- Создайте сообщество Вконтакте для вашего бота.

Получите токен группы в настройках сообщества:

![Снимок экрана 31 03 2025 в 12 31 43](https://github.com/user-attachments/assets/cdf7c494-281b-4dc2-a3ce-727ec4b41856)

Разрешите отправку сообщений:

![Снимок экрана 31 03 2025 в 12 38 14](https://github.com/user-attachments/assets/257e04f4-c8c6-4ef6-9d20-1443e7aab993)

Для работы клавиатуры - включите **возможности ботов**

![Снимок экрана 31 03 2025 в 12 38 30](https://github.com/user-attachments/assets/b5281c41-d450-412d-847b-6cda5f06d2a7)


- Для работы бота, требуется база данных [Redis](https://redis.io).
Для минимальной работы подойдет онлайн база - [см.Документацию к Redis](https://redis.io/docs/latest/operate/rc/rc-quickstart/)
Для работы БД нам потребуются:

**Public endpoint** - находится в разделе General - выглядит так : ``redis-12345.c123.europe-west1-2.gce.redns.redis-cloud.com:16232``
Вконце эндпоинта, после двоеточия это порт - ``16232``

**User и Default user password** - в разделе Security

- Создайте в корне проекта, файл `.env` Пропишите в нем:

```
TG_TOKEN=ТОКЕН ВАШЕГО БОТА TELEGRAM
VK_TOKEN=ТОКЕН ВАШЕЙ ГРУППЫ В VK
DB_REDIS_ENDPOINT=Public endpoint 
DB_REDIS_PORT=16232
DB_REDIS_PASSWORD=Default user password
```

Для изоляции проекта рекомендуется развернуть виртуальное окружение:

для Linux и MacOS
```bash
python3.11 -m venv env
source env/bin/activate
```

для Windows
```bash
python3.11 -m venv env
venv\Scripts\activate.bat
```

Python3 должен быть уже установлен. Затем используйте pip (или pip3, есть конфликт с Python2) для установки зависимостей:

```bash
pip install -r requirements.txt
```

## Использование

Для запуска Телеграм бота запустите скрипт

```bash
python tg_bot.python
```

Для запуска VK бота запустите скрипт

```bash
python vk_bot.py
```
