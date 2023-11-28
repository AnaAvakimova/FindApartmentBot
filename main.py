import telebot
from telebot import types
import os
import sqlite3

bot_key = os.environ.get('TELEBOT_KEY')
bot = telebot.TeleBot(bot_key)
group_id = os.environ.get('CHAT_ID')

USER_STATE = {}  # dictionary for tracking user state
apartment = 0


def get_user_state(message):
    print(f"Получение статуса пользователя - {USER_STATE.get(message.from_user.id)}")
    print(USER_STATE)
    return USER_STATE.get(message.from_user.id)


def set_user_state(user_id, state):
    USER_STATE[user_id] = state
    print(f"Установка статуса пользователя - {USER_STATE[user_id]}")
    print(USER_STATE)


# Function to check if the user is a member
def is_user_member(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False


# Function for /start message
def get_main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_check = types.KeyboardButton(text='🔍 Найти соседа')
    button_reg = types.KeyboardButton(text='✍️ Регистрация')
    button_del = types.KeyboardButton(text='🗑️ Удалить регистрацию')
    markup.add(button_check, button_reg, button_del)
    return markup


# Ask user for their apartment during registration
def ask_apartment(message):
    print("Отправляю запрос на номер квартиры")
    bot.send_message(message.from_user.id, "Какой у вас номер квартиры? Только номер, без текста и пробелов:", reply_markup=get_main_menu_markup())
    set_user_state(message.from_user.id, "awaiting_apartment")


@bot.message_handler(func=lambda message: get_user_state(message) == 'awaiting_apartment')
def handle_apartment(message):
    print("Сработал обработчик: handle_apartment")
    try:
        print('Запущена функция на сохранение квартиры')
        user_id = message.from_user.id
        apartment_number = int(message.text)
        if apartment_number not in range(1, 536):
            bot.send_message(message.from_user.id, 'Пожалуйста, введите корректный номер квартиры', reply_markup=get_main_menu_markup())
        else:
            name = message.from_user.first_name + ' ' + message.from_user.last_name
            username = message.from_user.username
            reg_user(user_id, name, username, apartment_number)  # Функция сохранения данных пользователя
            set_user_state(message.from_user.id, None)  # Сброс состояния пользователя
    except ValueError as e:
        print('Номер квартиры был введен в некорректном формате', e)
        second_mess = 'Пожалуйста, укажите только номер (число):'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())


# Find user by their apartment
def check_user(message):
    print("Отправляю запрос на номер квартиры")
    bot.send_message(message.from_user.id, "Укажите номер квартиры соседа. Только номер, без текста и пробелов:", reply_markup=get_main_menu_markup())
    set_user_state(message.from_user.id, "checking_apartment")


@bot.message_handler(func=lambda message: get_user_state(message) == 'checking_apartment')
def check_apartment(message):
    print("Сработал обработчик: check_apartment")
    try:
        print('Запущена функция выдачу данных о квартире')
        apartment_number = int(message.text)
        user_id = message.from_user.id
        # connect to the database
        try:
            connection = sqlite3.connect('ostrov_database.db')
            cursor = connection.cursor()
            print('База данных подключена к SQLite')

            # get information about the user
            print(f"Номер квартиры - {apartment_number}")
            cursor.execute("SELECT name, username FROM Users WHERE apartment = ?", (apartment_number,))
            user_data = cursor.fetchall()
            print(f"Полученные данные из базы - {user_data}")
            if not user_data:
                second_mess = 'Извините, такой пользователь не зарегистрирован.'
                bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
            else:

                for person in user_data:
                    mess = f"{person[0]} - @{person[1]}"
                    bot.send_message(user_id, mess, reply_markup=get_main_menu_markup())

        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)
            second_mess = 'Произошла ошибка'
            bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

        finally:
            if (connection):
                connection.close()
                print("Соединение с SQLite закрыто")
            set_user_state(user_id, None)  # Сброс состояния пользователя



    except ValueError as e:
        print('Номер квартиры был введен в некорректном формате', e)
        second_mess = 'Пожалуйста, укажите только номер (число):'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())


# Delete registration
def delete_registration(message):
    # connect to the database
    try:
        connection = sqlite3.connect('ostrov_database.db')
        cursor = connection.cursor()
        print('База данных подключена к SQLite')

        # get information about the user
        id = message.from_user.id
        # check if user is registered
        cursor.execute("SELECT * FROM Users WHERE id = ?", (id,))
        if cursor.fetchone() is None:
            second_mess = 'Вы еще не зарегистрированы.'
            bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())
        else:
            # delete registration
            sql_update_query = """DELETE from Users
                                  where id = ?"""
            cursor.execute(sql_update_query, (id,))
            connection.commit()
            second_mess = 'Запись успешно удалена'
            bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка при удалении записи'
        bot.send_message(message.from_user.id, second_mess, reply_markup=get_main_menu_markup())

    finally:
        if (connection):
            connection.close()
            print("Соединение с SQLite закрыто")


# Registration
@bot.message_handler(func=lambda message: get_user_state(message) == "filled_apartment")
def reg_user(user_id, name, username, apartment_number):
    print("Сработал обработчик: reg_user")
    # connect to the database
    try:
        connection = sqlite3.connect('ostrov_database.db')
        cursor = connection.cursor()
        print('База данных подключена к SQLite')

        # add new user to the database
        sqlite_insert_query = """INSERT INTO Users
                              (id, name, username, apartment)
                              VALUES
                              (?, ?, ?, ?);"""
        values_to_insert = (user_id, name, username, apartment_number)
        cursor.execute(sqlite_insert_query, values_to_insert)
        connection.commit()
        second_mess = 'Пользователь успешно зарегистрирован'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    except sqlite3.IntegrityError as error:
        print("Такой пользователь уже зарегистрирован", error)
        second_mess = 'Вы уже зарегистрированы.'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
        second_mess = 'Произошла ошибка при регистрации'
        bot.send_message(user_id, second_mess, reply_markup=get_main_menu_markup())

    finally:
        if (connection):
            connection.close()
            print("Соединение с SQLite закрыто")


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
        first_mess = (f"<b>{message.from_user.first_name} {message.from_user.last_name}</b>, привет!\nЧто вы "
                      f"хотите сделать?")
        bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=get_main_menu_markup())

    if message.text == '🔍 Найти соседа':
        print("Выбрана команда найти соседа")
        check_user(message)
    if message.text == '✍️ Регистрация':
        print("Выбрана команда регистрации")
        ask_apartment(message)
    if message.text == '🗑️ Удалить регистрацию':
        print("Выбрана команда удалить регистрацию")
        delete_registration(message)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
