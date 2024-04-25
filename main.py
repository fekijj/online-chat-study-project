import asyncio

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js
import datetime
import sqlite3

# Подключение к базе данных (если файл не существует, он будет создан)
conn = sqlite3.connect('db.db')

# Создание курсора для выполнения SQL-запросов
cur = conn.cursor()

# Создание таблицы 'users' для хранения информации о пользователях
cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                Nickname TEXT,
                Password TEXT,
                Online INTEGER
            )''')



chat_msgs = []
online_users = set()

MAX_MESSAGES_COUNT = 100

show_buttons = True  # Флаг, определяющий, нужно ли показывать кнопки регистрации и авторизации

async def reg():
    reg_login = await input("Введите логин", required=True, placeholder="Логин" )
    reg_password = await input("Введите пароль", required=True, placeholder="Пароль")
    reg_password_conf = await input("Подтвердите пароль", required=True, placeholder="Пароль")

    if reg_password == reg_password_conf:
        put_text("Регистрация успешна.")
        global show_buttons
        show_buttons = False
        await main()
    else:
        put_text("Пароли не совпадают.")

async def auth():
    global show_buttons
    if show_buttons:
        put_buttons(['Зарегистрироваться'], onclick=lambda btn: run_async(reg()))
        put_buttons(["Войти"], onclick=lambda btn: put_text("Авторизация"))
    else:
        put_text("Регистрация успешна. Кнопки скрыты.")


async def main():
    global chat_msgs

<<<<<<< HEAD
=======
   
>>>>>>> e9be7db782d78995bc1f3180358cd69d09c80d11
    put_markdown("## Project M")
    toast(" Прототип чата для защиты индивидуального проекта")

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)

    nickname = await input("Войти в чат", required=True, placeholder="Ваше имя",
                           validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' else None)
    online_users.add(nickname)

    chat_msgs.append(('📢', f'`{nickname}` присоединился к чату!'))
    msg_box.append(put_markdown(f'📢 `{nickname}` присоединился к чату'))
    
    refresh_task = run_async(refresh_msg(nickname, msg_box))

    while True:
        data = await input_group("💭 Новое сообщение", [
            input(placeholder="Текст сообщения ...", name="msg"),
            actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate=lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m['msg'] else None)

        if data is None:
            break
        current_time = datetime.datetime.now().strftime("%H:%M")

        msg_with_time = f"{current_time} {nickname}: {data['msg']}"
        msg_box.append(put_markdown(msg_with_time))

        chat_msgs.append((nickname, data['msg']))
        


    refresh_task.close()

    online_users.remove(nickname)
    toast("Вы вышли из чата!")
    msg_box.append(put_markdown(f'📢 Пользователь `{nickname}` покинул чат!'))
    chat_msgs.append(('📢', f'Пользователь `{nickname}` покинул чат!'))

    put_buttons(['Перезайти'], onclick=lambda btn: run_js('window.location.reload()'))
    


async def refresh_msg(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)

        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:  # if not a message from current user
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))

        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


if __name__ == "__main__":
    start_server(auth, debug=True, port=8080, cdn=False)