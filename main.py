import asyncio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_js, run_async  # Импортируем run_async
import datetime
import sqlite3
import pywebio_battery as pwb

# Подключение к базе данных
conn = sqlite3.connect('db.db')
cur = conn.cursor()

# Создание таблицы 'users'
cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                Nickname TEXT,
                Password TEXT,
                Online INTEGER
            )''')

chat_msgs = []
online_users = set()
MAX_MESSAGES_COUNT = 100

class AuthPage:
    def __init__(self):
        self.login = None
        self.password = None

    async def cookie_user(self):
        #put text as debug
        put_text("Entering cookie_user method")  # Debug output
        registered = await pwb.get_cookie("registered")
        put_text(f"Registered cookie: {registered}")  # Debug output
        if registered == "true":
            self.login = await pwb.get_cookie("username")
            self.password = await pwb.get_cookie("password")
            put_text(f"Login: {self.login}, Password: {self.password}")  # Debug output
            await self.main()
        else:
            self.show_buttons()

    async def auth(self, btn):
        put_text("Auth button clicked")  # Debug output
        self.login = await input("Введите логин", required=True, placeholder="Логин")
        self.password = await input("Введите пароль", required=True, placeholder="Пароль")

        cur.execute("SELECT * FROM users WHERE Nickname = ? AND Password = ?", (self.login, self.password))
        user = cur.fetchone()

        if user:
            await pwb.set_cookie("registered", "true", days=30)
            await pwb.set_cookie("username", self.login, days=30)
            await pwb.set_cookie("password", self.password, days=30)
            await self.main()
        else:
            put_text("Пользователь с таким логином и паролем не найден.")

    async def register(self, btn):
        put_text("Register button clicked")  # Debug output
        self.login = await input("Введите логин", required=True, placeholder="Логин")
        self.reg_password = await input("Введите пароль", required=True, placeholder="Пароль")
        self.reg_password_conf = await input("Подтвердите пароль", required=True, placeholder="Пароль")

        if self.reg_password == self.reg_password_conf:
            cur.execute("INSERT INTO users (Nickname, Password) VALUES (?, ?)", (self.login, self.reg_password))
            conn.commit()
            await pwb.set_cookie("registered", "true", days=30)
            await pwb.set_cookie("username", self.login, days=30)
            await pwb.set_cookie("password", self.reg_password, days=30)
            put_text("Регистрация успешна.")
            await self.main()
        else:
            put_text("Пароли не совпадают.")

    def show_buttons(self):
        put_text("Showing buttons")  # Debug output
        put_buttons(['Зарегистрироваться'], onclick=self.register)
        put_buttons(["Войти"], onclick=self.auth)
        put_text("Buttons added to the page")  # Debug output

    async def main(self):
        global chat_msgs
        put_markdown("## Project M")
        toast("Прототип чата для защиты индивидуального проекта")

        msg_box = output()
        put_scrollable(msg_box, height=300, keep_bottom=True)

        self.nickname = self.login
        online_users.add(self.nickname)

        chat_msgs.append(('📢', f'`{self.nickname}` присоединился к чату!'))
        msg_box.append(put_markdown(f'📢 `{self.nickname}` присоединился к чату'))
    
        refresh_task = run_async(refresh_msg(self.nickname, msg_box))

        while True:
            data = await input_group("💭 Новое сообщение", [
                input(placeholder="Текст сообщения ...", name="msg"),
                actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
            ], validate=lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m['msg'] else None)

            if data is None:
                break
            current_time = datetime.datetime.now().strftime("%H:%M")
            msg_with_time = f"{current_time} {self.nickname}: {data['msg']}"
            msg_box.append(put_markdown(msg_with_time))

            chat_msgs.append((self.nickname, data['msg']))
        
        refresh_task.close()

        online_users.remove(self.nickname)
        toast("Вы вышли из чата!")
        msg_box.append(put_markdown(f'📢 Пользователь `{self.nickname}` покинул чат!'))
        chat_msgs.append(('📢', f'Пользователь `{self.nickname}` покинул чат!'))

        put_buttons(['Перезайти'], onclick=lambda btn: run_js('window.location.reload()'))

async def auth():
    page = AuthPage()
    await page.cookie_user()

async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:  # if not a message from current user
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}`"))

        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)

if __name__ == "__main__":
    start_server(auth, debug=True, port=8080, cdn=False)
