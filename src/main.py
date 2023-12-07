import telebot
import os
import sqlite3
from menu import get_main_menu_markup, first_confirm_deletion, second_confirm_deletion, first_confirm_registration, \
    second_confirm_registration

bot_key = os.environ.get('TELEBOT_KEY')
bot = telebot.TeleBot(bot_key)
group_id = os.environ.get('CHAT_ID')
admin = os.environ.get('ADMIN')
tg_user_id = os.environ.get('TG_USER_ID')

dir_path = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(dir_path, '../db/ostrov_database.db')
# db_path = os.environ.get('DB_PATH')

USER_STATE = {}  # dictionary for tracking user state
user_registration_data = {}
user_deletion_data = {}
apartment = 0


def get_user_state(message):
    print(f"Получение статуса пользователя - {USER_STATE.get(message.from_user.id)}")
    return USER_STATE.get(message.from_user.id)


def set_user_state(user_id, state):
    USER_STATE[user_id] = state
    print(f"Установка статуса пользователя - {USER_STATE[user_id]}")


def create_db(directory_path):
    # create database and tables if not exists
    if os.path.exists(db_path):
        return

    # Создаю базу данных и подключение к ней
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    # Создаю таблицы
    create_table_users = '''CREATE TABLE IF NOT EXISTS USERS (
                        name TEXT,
                        username TEXT,
                        additional_info TEXT,
                        apartment INTEGER,
                        user_id INTEGER
                        );'''

    create_table_users_check = '''CREATE TABLE IF NOT EXISTS Users_check (
                        user_id INTEGER PRIMARY KEY,
                        count_check INTEGER DEFAULT 0
                        );'''

    try:
        cursor.execute(create_table_users)
        cursor.execute(create_table_users_check)
        connection.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        # Закрываю подключение к базе данных
        connection.close()


# Function to check if the user is a member
def is_user_member(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False


# Registration process
def registration_check(message):
    print('Выбрана опция регистрации')
    user_id = message.from_user.id
    first_confirm_registration(user_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("first_confirm_registration"))
def callback_first_confirm_registration(call):
    print('Сработал обработчик callback_first_confirm_registration')
    # User decided to register
    if call.data == "first_confirm_registration_yes":
        print("Отправляю запрос на номер квартиры")
        bot.send_message(call.from_user.id, "Какой у вас номер квартиры? Только номер, без текста и пробелов:")
        set_user_state(call.from_user.id, "awaiting_apartment")
    # User decided not to register
    elif call.data == "first_confirm_registration_no":
        print('Пользователь решил не регистрироваться')
        user_id = call.from_user.id
        second_mess = "Действие отменено."
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
    # Deletion of buttons
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text,
                          reply_markup=None)


@bot.message_handler(func=lambda message: get_user_state(message) == 'awaiting_apartment')
def handle_apartment(message):
    print("Сработал обработчик: handle_apartment")
    try:
        print('Запущена функция на сохранение квартиры')
        user_id = message.from_user.id
        apartment_number = int(message.text)
        if apartment_number not in range(1, 536):
            bot.send_message(message.from_user.id, 'Пожалуйста, введите корректный номер квартиры (от 1 до 535)',
                             reply_markup=get_main_menu_markup())
        else:
            last_name = message.from_user.last_name if message.from_user.last_name is not None else ""
            name = f"{message.from_user.first_name} {last_name}"
            username = f"@{message.from_user.username}" if message.from_user.username is not None else f"[нажмите для связи](tg://user?id={user_id})"
            user_registration_data[user_id] = {'name': name, 'username': username, 'apartment': apartment_number}
            second_confirm_registration(user_id, apartment_number)
    except ValueError as e:
        print('Номер квартиры был введен в некорректном формате', e)
        second_mess = 'Пожалуйста, укажите только номер (число):'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith("second_confirm_registration"))
def callback_second_confirm_registration(call):
    print("Сработал обработчик: callback_second_confirm_registration")
    user_id = call.from_user.id
    if call.data == "second_confirm_registration_yes":
        print('Пользователь решил подтердить регистрацию')
        data = user_registration_data[user_id]
        reg_user(user_id, data['name'], data['username'], data['apartment'])
    elif call.data == "second_confirm_registration_no":
        print('Пользователь решил не подтверждать регистрацию')
        second_mess = "Действие отменено."
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
    set_user_state(user_id, None)
    # Deletion of buttons
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text,
                          reply_markup=None)


def reg_user(user_id, name, username, apartment_number):
    print("Сработал обработчик: reg user")
    connection = None
    # connect to the database
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        print('База данных подключена к SQLite')

        # check if the user is already registered in this apartment
        print('Проверяю, что пользователь еще не зарегистрирован')
        cursor.execute("SELECT apartment FROM Users WHERE user_id = ?", (user_id,))
        user_check_apt = cursor.fetchall()
        print(f'Номер квартиры в базе {user_check_apt}, номер введенной квартиры {apartment_number}')

        if user_check_apt is not None:
            for apt in user_check_apt:
                print(apartment)
                if apartment_number == apt[0]:
                    second_mess = "Вы уже зарегистрированы в этой квартире"
                    bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
                    return
            # add new user to the database
        sqlite_insert_query = """INSERT INTO Users
                              (user_id, name, username, apartment)
                              VALUES
                              (?, ?, ?, ?);"""
        values_to_insert = (user_id, name, username, apartment_number)
        cursor.execute(sqlite_insert_query, values_to_insert)
        connection.commit()
        print('Пользователь успешно зарегистрирован')
        second_mess = 'Пользователь успешно зарегистрирован'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    # except sqlite3.IntegrityError as error:
    #     print("Такой пользователь уже зарегистрирован", error)
    #     second_mess = 'Вы уже зарегистрированы.'
    #     bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка при регистрации'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    finally:
        if connection:
            connection.close()
            print("Соединение с SQLite закрыто")


# Find user by their apartment
def check_user(message):
    connection = None
    user_id = message.from_user.id
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        print('База данных подключена к SQLite')
        cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            print('Запрос отклонен, так как пользователь не зарегистрирован')
            message = 'Только зарегистрированные пользователи могут получать данные о соседях'
            bot.send_message(user_id, message, reply_markup=get_main_menu_markup())
        else:
            print("Отправляю запрос на номер квартиры")
            bot.send_message(message.from_user.id,
                             "Укажите номер квартиры соседа. Только номер, без текста и пробелов:")
            set_user_state(message.from_user.id, "checking_apartment")
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
    finally:
        if connection:
            connection.close()
            print("Соединение с SQLite закрыто")


@bot.message_handler(func=lambda message: get_user_state(message) == 'checking_apartment')
def check_apartment(message):
    print("Сработал обработчик: check_apartment")
    connection = None
    user_id = message.from_user.id
    try:
        print('Запущена функция выдачу данных о квартире')
        apartment_number = int(message.text)
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        print('База данных подключена к SQLite')

        # get information about the user
        print(f"Номер квартиры - {apartment_number}")
        cursor.execute("SELECT name, username FROM Users WHERE apartment = ?", (apartment_number,))
        user_data = cursor.fetchall()
        print(f"Полученные данные из базы - {user_data}")

        # Tracking count of checks made by the user for security purposes
        cursor.execute("SELECT user_id FROM Users_check WHERE user_id = ?", (user_id,))
        users_check_id = cursor.fetchone()
        if not users_check_id:
            cursor.execute("INSERT INTO Users_check (user_id) VALUES (?)", (user_id,))

        cursor.execute("UPDATE Users_check SET count_check = count_check + 1 WHERE user_id = ?", (user_id,))
        connection.commit()
        cursor.execute("SELECT count_check FROM Users_check WHERE user_id = ?", (user_id,))
        count_check = cursor.fetchone()
        print(count_check[0])
        mess = f"Пользователь tg://user?id={user_id} отправил {count_check[0]} запросов на проверку"
        if count_check[0] > 99:
            bot.send_message(tg_user_id, mess)
            second_mess = f'Извините, но вы превысили лимит на проверку. Чтобы вас разблокировали, отправьте сообщение {admin}'
            bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
            return
        if not user_data:
            second_mess = 'Извините, такой пользователь не зарегистрирован.'
            bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
        else:

            for person in user_data:
                mess = f"{person[0]} - {person[1]}"
                bot.send_message(user_id, mess, parse_mode='Markdown', reply_markup=get_main_menu_markup())

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    except ValueError as e:
        print('Номер квартиры был введен в некорректном формате', e)
        second_mess = 'Пожалуйста, укажите только номер (число):'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())

    finally:
        if connection:
            connection.close()
            print("Соединение с SQLite закрыто")
        set_user_state(user_id, None)  # Сброс состояния пользователя


# Delete registration
def delete_registration_check(message):
    # connect to the database
    connection = None
    user_id = message.from_user.id
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        print('База данных подключена к SQLite')
        # check if user is registered
        cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            second_mess = 'Вы еще не зарегистрированы.'
            bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())
        else:
            # confirm deletion
            first_confirm_deletion(user_id)

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка при удалении записи'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())

    finally:
        if connection:
            connection.close()
            print("Соединение с SQLite закрыто")


@bot.callback_query_handler(func=lambda call: call.data.startswith("first_confirm_deletion"))
def callback_confirm_deletion(call):
    print('Сработал обработчик callback_confirm_deletion')
    # User decided to delete registration
    if call.data == "first_confirm_deletion_yes":
        print("Отправляю запрос на номер квартиры")
        bot.send_message(call.from_user.id, "Укажите номер квартиры для удаления. Только номер, без текста:")
        set_user_state(call.from_user.id, "delete_registration")
    # User decided not to delete registration
    elif call.data == "first_confirm_deletion_no":
        print('Пользователь решил не удалять регистрацию')
        user_id = call.from_user.id
        second_mess = "Действие отменено."
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    # Deletion of buttons
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text,
                          reply_markup=None)


@bot.message_handler(func=lambda message: get_user_state(message) == "delete_registration")
def delete_registration(message):
    print('Сработал обработчик delete_registration')
    # connect to the database
    connection = None
    user_id = message.from_user.id
    try:
        apartment_number = int(message.text)
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        print('База данных подключена к SQLite')
        # check and delete registration
        cursor.execute("SELECT * FROM Users WHERE user_id = ? and apartment = ?", (user_id, apartment_number,))
        if cursor.fetchone() is None:
            message = 'Извините, вы не зарегистрированы в этой квартире'
            bot.send_message(user_id, message, reply_markup=get_main_menu_markup())
        else:
            user_deletion_data[user_id] = {'apartment': apartment_number}
            second_confirm_deletion(user_id, apartment_number)
        set_user_state(user_id, None)  # Сброс состояния пользователя
    except ValueError as e:
        print('Номер квартиры был введен в некорректном формате', e)
        second_mess = 'Пожалуйста, укажите только номер (число):'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        error_mess = 'Произошла ошибка при удалении записи'
        bot.send_message(user_id, error_mess, reply_markup=get_main_menu_markup())

    finally:
        if connection:
            connection.close()
            print("Соединение с SQLite закрыто")


@bot.callback_query_handler(func=lambda call: call.data.startswith("second_confirm_deletion"))
def callback_second_confirm_deletion(call):
    print("Сработал обработчик: second_confirm_deletion")
    user_id = call.from_user.id
    connection = None
    if call.data == "second_confirm_deletion_yes":
        print('Пользователь решил подтвердить удаление')
        data = user_deletion_data[user_id]
        apartment_number = data['apartment']
        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            print('База данных подключена к SQLite')
            sql_update_query = """DELETE from Users
                                  where user_id = ? and apartment = ?"""
            cursor.execute(sql_update_query, (user_id, apartment_number,))
            connection.commit()
            second_mess = 'Запись успешно удалена'
            bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)
            second_mess = 'Произошла ошибка при удалении записи'
            bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

        finally:
            if connection:
                connection.close()
                print("Соединение с SQLite закрыто")

    elif call.data == "second_confirm_deletion_no":
        print('Пользователь решил не продолжать удаление')
        message = "Действие отменено."
        bot.send_message(user_id, message, reply_markup=get_main_menu_markup())
    set_user_state(user_id, None)
    # Deletion of buttons
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=call.message.text,
                          reply_markup=None)


# Handle all messages with content_type 'text' and check if the user is in the group
@bot.message_handler(func=lambda message: True)
def check_membership(message):
    print("Сработал обработчик: check_membership")
    user_id = message.from_user.id
    if not is_user_member(group_id, user_id):
        bot.reply_to(message, "Извините, вы не являетесь участником группы и не можете использовать этот бот")
    else:
        # Process the user's command or message
        process_user_message(message)


def process_user_message(message):
    print("Тип чата:", message.chat.type)
    print("Полученное сообщение:", message.text)
    if message.chat.type != 'private':
        return

    if message.text == '/start':
        print("Выбрана команда старт")
        first_mess = (f"<b>{message.from_user.first_name}</b>, привет!\nЧто вы "
                      f"хотите сделать?")
        bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=get_main_menu_markup())

    if message.text == '🔍 Найти соседа':
        print("Выбрана команда найти соседа")
        check_user(message)
    if message.text == '✍️ Регистрация':
        print("Выбрана команда регистрации")
        registration_check(message)
    if message.text == '🗑️ Удалить регистрацию':
        print("Выбрана команда удалить регистрацию")
        delete_registration_check(message)


if __name__ == '__main__':
    create_db(dir_path)
    bot.polling(none_stop=True, interval=0)
