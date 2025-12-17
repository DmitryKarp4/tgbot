import telebot
from config import TG_TOKEN
from checkpassword import check_password
from checkip import is_valid_ip

bot = telebot.TeleBot(TG_TOKEN)


# Обработчик команды /start -> приветственное сообщение
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Я бот, созданный для различных целей. Используйте команды /help чтобы узнать больше.")

# Обработчик команды /help -> список доступных команд
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Приветственное сообщение\n"
        "/help - Список доступных команд\n"
        "/ip <IP-адрес> - Проверка валидности IP-адреса\n"
        "/checkpassword <Пароль> - Проверка надежности пароля\n"
    )
    bot.reply_to(message, help_text)

# Обработчик команды /ip -> проверка валидности IP-адреса
@bot.message_handler(commands=['ip'])
def check_ip_handler(message):
    parted_message = message.text.split()
    if len(parted_message) != 2:
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /ip <IP-адрес>")
        return
    ip_str = parted_message[1]
    user_id = message.from_user.id
    is_valid, feedback = is_valid_ip(ip_str, user_id) # Получает две переменные, is_valid и feedback, из функции is_valid_ip, одна из которых указывает, действителен ли IP-адрес, а другая содержит сообщение для пользователя
    bot.reply_to(message, feedback) # Ответ бота с соответствующим сообщением

# Обработчик команды /checkpassword -> проверка надежности пароля
@bot.message_handler(commands=['checkpassword'])
def check_password_handler(message): # Обработчик команды /checkpassword
    parted_message = message.text.split(maxsplit=1)
    if len(parted_message) != 2:
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /checkpassword <Пароль>")
        return
    password = parted_message[1]
    user_id = message.from_user.id

    is_strong, feedback = check_password(password, user_id) # Получает две переменные, is_strong и feedback, из функции check_password, одна из которых указывает, надежен ли пароль, а другая содержит сообщение для пользователя
    bot.reply_to(message, feedback) # Ответ бота с соответствующим сообщением

bot.infinity_polling()