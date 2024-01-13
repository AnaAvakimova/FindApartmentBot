import os

import telebot
from telebot import types

bot_key = os.environ.get("TELEBOT_KEY")
bot = telebot.TeleBot(bot_key)
group_id = os.environ.get("CHAT_ID")


# Main menu
def get_main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    button_check = types.KeyboardButton(text="🔍 Найти соседа")
    markup.row(button_check)
    button_reg = types.KeyboardButton(text="✍️ Регистрация")
    button_del = types.KeyboardButton(text="🗑️ Удалить регистрацию")
    markup.row(button_reg, button_del)
    return markup


# Menu for confirm deletion of registration
def first_confirm_deletion(user_id):
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(
        text="Да", callback_data="first_confirm_deletion_yes"
    )
    no_button = types.InlineKeyboardButton(
        text="Нет", callback_data="first_confirm_deletion_no"
    )
    markup.add(yes_button, no_button)
    bot.send_message(
        user_id,
        text="Вы уверены, что хотите удалить свою регистрацию?",
        reply_markup=markup,
    )


def second_confirm_deletion(user_id, apartment):
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(
        text="Да", callback_data="second_confirm_deletion_yes"
    )
    no_button = types.InlineKeyboardButton(
        text="Нет", callback_data="second_confirm_deletion_no"
    )
    markup.add(yes_button, no_button)
    bot.send_message(
        user_id,
        text=f"Вы подтверждаете, что хотите удалить свою регистрацию в квартире {apartment}?",
        reply_markup=markup,
    )


# Menu for confirm registration
def first_confirm_registration(user_id):
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(
        text="Да", callback_data="first_confirm_registration_yes"
    )
    no_button = types.InlineKeyboardButton(
        text="Нет", callback_data="first_confirm_registration_no"
    )
    markup.add(yes_button, no_button)
    bot.send_message(
        user_id, text="Вы уверены, что хотите зарегистрироваться?", reply_markup=markup
    )


def second_confirm_registration(user_id, apartment):
    markup = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(
        text="Да", callback_data="second_confirm_registration_yes"
    )
    no_button = types.InlineKeyboardButton(
        text="Нет", callback_data="second_confirm_registration_no"
    )
    markup.add(yes_button, no_button)
    message = f"Вы подтверждаете, что хотите зарегистрироваться в квартире {apartment}?"
    bot.send_message(user_id, text=message, reply_markup=markup)
