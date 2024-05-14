from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js, run_async
import datetime
import sqlite3

from tornado.platform import asyncio

# Подключение к базе данных (если файл не существует, он будет создан)
conn = sqlite3.connect('db.db')
cur = conn.cursor()

# Создание таблицы 'users' для хранения информации о пользователях
cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                Nickname TEXT,
                Password TEXT,
                Online INTEGER
            )''')

# Создание таблицы 'messages' для хранения сообщений чата
cur.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                Nickname TEXT,
                Message TEXT,
                Time TEXT
            )''')

chat_msgs = []
online_users = set()

MAX_MESSAGES_COUNT = 100

class auth_page:
    def __init__(self):
        self.reg_button = None
        self.login_button = None
        self.buttons = []  # Хранение кнопок
        self.reg_login = None  # Хранение логина пользователя

        self.show_buttons()  # Отображение начальных кнопок

    async def login(self, btn):
        self.login = await input("Введите логин", required=True, placeholder="Логин")
        self.password = await input("Введите пароль", required=True, placeholder="Пароль")

        # Проверка существует ли пользователь с таким логином и паролем
        cur.execute("SELECT * FROM users WHERE Nickname = ? AND Password = ?", (self.login, self.password))
        user = cur.fetchone()

        if user:
            self.reg_login = self.login  # Пользователь найден, загружаем его сообщения из базы данных
            await self.load_messages()
            await self.main()
        else:
            put_text("Пользователь с таким логином и паролем не найден.")

    async def register(self, btn):
        self.reg_login = await input("Введите логин", required=True, placeholder="Логин")
        self.reg_password = await input("Введите пароль", required=True, placeholder="Пароль")
        self.reg_password_conf = await input("Подтвердите пароль", required=True, placeholder="Пароль")

        if self.reg_password == self.reg_password_conf:
            cur.execute("INSERT INTO users (Nickname, Password) VALUES (?, ?)", (self.reg_login, self.reg_password))
            conn.commit()
            put_text("Регистрация успешна.")
            self.hide_buttons()  # Скрываем кнопки регистрации и входа
            await self.main()
        else:
            put_text("Пароли не совпадают.")

    async def load_messages(self):
        # Загрузка сообщений пользователя из базы данных
        cur.execute("SELECT * FROM messages WHERE Nickname = ?", (self.reg_login,))
        messages = cur.fetchall()
        for message in messages:
            chat_msgs.append((message[1], message[2]))

    def show_buttons(self):
        self.reg_button = put_buttons(['Зарегистрироваться'], onclick=self.register)
        self.login_button = put_buttons(["Войти"], onclick=self.login)

        # Добавляем кнопки в список buttons
        self.buttons.append(self.reg_button)
        self.buttons.append(self.login_button)

    def hide_buttons(self):
        for button in self.buttons:
            button.visible = False  # Скрываем каждую кнопку

    async def main(self):
        global chat_msgs
        put_markdown("## Project M")
        toast(" Прототип чата для защиты индивидуального проекта")

        msg_box = output()
        put_scrollable(msg_box, height=300, keep_bottom=True)

        nickname = self.reg_login
        online_users.add(nickname)

        chat_msgs.append(('📢', f'`{nickname}` присоединился к чату!'))
        msg_box.append(put_markdown(f'📢 `{nickname}` присоединился к чату'))

        refresh_task = run_async(refresh_msg(nickname, msg_box))

        while True:
            data = await input_group("💭 Новое сообщение", [
                input(placeholder="Текст сообщения ...", name="msg"),
                actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
            ], validate=lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m[
                'msg'] else None)

            if data is None:
                break
            current_time = datetime.datetime.now().strftime("%H:%M")

            msg_with_time = f"{current_time} {nickname}: {data['msg']}"
            msg_box.append(put_markdown(msg_with_time))

            # Сохраняем сообщение в базе данных
            cur.execute("INSERT INTO messages (Nickname, Message, Time) VALUES (?, ?, ?)",
                        (nickname, data['msg'], current_time))
            conn.commit()

            chat_msgs.append((nickname, data['msg']))

        refresh_task.close()

        online_users.remove(nickname)
        toast("Вы вышли из чата!")
        msg_box.append(put_markdown(f'📢 Пользователь `{nickname}` покинул чат!'))
        chat_msgs.append(('📢', f'Пользователь `{nickname}` покинул чат!'))

        put_buttons(['Перезайти'], onclick=lambda btn: run_js('window.location.reload()'))


async def auth():
    page = auth_page()
    page.__init__()


async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))

        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


if __name__ == "__main__":
    start_server(auth, debug=True, port=8080, cdn=False)