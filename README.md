# Neighborhood Bot for Telegram

## Description
This Telegram bot is designed to facilitate interaction within a residential community. It allows users to register their apartment numbers, find their neighbors, and manage their registration information. The bot uses SQLite for storing user data, ensuring a lightweight and efficient data management system.

## Features
- User Registration: Users can register their apartment numbers.
- Neighbor Lookup: Users can look up their neighbors using apartment numbers.
- Registration Management: Users can delete their registration details.

# Usage

## Prerequisites
- Python 3.x
- SQLite3
- A Telegram Bot Token (obtainable through BotFather on Telegram)

## Running the image
```sh
docker run \
    -d \
    -e TELEBOT_KEY="your_telegram_bot_key" \
    -e CHAT_ID="telegram_chat_id" \
    -e TG_USER_ID="telegram_user_id" \
    -e ADMIN="telegram_username" \
    -e DB_PATH="database_path" \
    ghcr.io/anaavakimova/findapartmentbot:master
```

## Commands

- /start: Begin interaction with the bot.
- 🔍 Найти соседа: Find a neighbor by apartment number.
- ✍️ Регистрация: Register your apartment number.
- 🗑️ Удалить регистрацию: Delete your registration.

## Environment parameters
Configuration of the bot is done using environment parameters. See the list below:

| Name        | Default      | Description                                                                                                                                                                                                                             |
|-------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TELEBOT_KEY | \<required\> | Your Telegram bot token                                                                                                                                                                                                                 |
| CHAT_ID     | \<required\> | ID of your neighborhood  Telegram group. Bot checks if the user is a member of this group. Users who are not part of this group cannot use the bot's functionality.                                                                     |
| Admin       | \<required\> | Your username in Telegram. The bot has a limit for checking users for security purposes. If the number of views from one ID exceeds 100, then the bot closes access to viewing and asks user to contact the admin using tthis username.` 
| TG_USER_ID  | \<required\> | Your username in Telegram. If the number of views from one ID exceeds 100, the bot sends private message to this ID to notify you.`                                                                                                     
| DB_PATH     | \<required\> | Path for your SQLite database.`                                                                                                                                                                                                              

## License MIT