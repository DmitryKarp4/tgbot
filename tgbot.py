import telebot
from config import TG_TOKEN
from checkpassword import check_password
from checkip import is_valid_ip
from techinfo import techinfo
from shodandork import shodan_dork_search

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
        "/techinfo <IP-адрес> - Техническая информация по IP-адресу через Shodan и Censys\n"
        "/shodandork <Dork-запрос> - Составление Shodan Dork поиска\n"
        "Доступные аргументы для Dork-запроса:\n\n"
        "ip=<IP-адрес>,\n port=<порт>,\n service=<сервис>,\n product=<продукт>,\n country=<страна>,\n asn=<ASN>,\n org=<организация>,\n title=<заголовок>,\n hostname=<имя хоста>\n\n"
        "Пример использования Dork-запроса: /shodandork port=80, country=US"
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

# Обработчик команды /techinfo -> техническая информация по IP-адресу
@bot.message_handler(commands=['techinfo'])
def tech_info_handler(message):
    parted_message = message.text.split(maxsplit=1)
    if len(parted_message) != 2:
        bot.reply_to(message, "Пожалуйста, используйте команду в формате: /techinfo <IP-адрес>")
        return
    is_valid, feedback = is_valid_ip(parted_message[1], message.from_user.id)
    if is_valid:
        ip = parted_message[1]
        bot.reply_to(message, f"Получение технической информации для IP-адреса {ip}...")
    else:
        bot.reply_to(message, "Пожалуйста, введите действительный IP-адрес.")
        return
    tech_info_result = techinfo(ip, message.from_user.id)
    bot.reply_to(message, tech_info_result)

# Обработчик команды /shodandork -> составление Shodan Dork поиска
@bot.message_handler(commands=['shodandork'])
def shodan_dork_handler(message):
    parted_message = message.text.split(maxsplit=1)
    if len(parted_message) != 2:
        bot.reply_to(
            message,
            "Формат:\n"
            "/shodandork ip=1.1.1.1 port=443 product=nginx\n\n"
            "Аргументы см. /help"
        )
        return

    dork = parted_message[1]
    user_id = message.from_user.id

    result = shodan_dork_search(dork, user_id)
    bot.reply_to(message, result)

bot.infinity_polling()


# TODO: Domain name info (whois, dns, etc.)
# TODO: Domain name tech info (Shodan)