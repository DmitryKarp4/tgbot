import telebot
from config import TG_TOKEN
from checkpassword import check_password
from checkip import is_valid_ip
from techinfo import techinfo
from shodandork import shodan_dork_search
from registration import setup_registration, is_registered 
from search import search_people

bot = telebot.TeleBot(TG_TOKEN)
setup_registration(bot)



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
        "/register - Регистрация пользователя\n"
        "/me - Проверка статуса регистрации\n"
        "/find <текст> - Поиск в справочнике по ФИО/email/телефону\n(без учета регистра). БЕЗ РЕГИСТРАЦИИ НЕДОСТУПНО\n"
        "/ip <IP-адрес или Доменное Имя> - Проверка валидности IP-адреса или доменного имени\n"
        "/checkpassword <Пароль> - Проверка надежности пароля\n"
        "/techinfo <IP-адрес или Доменное Имя> - Техническая информация по IP-адресу через Shodan и Censys\n"
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
    user_str = parted_message[1]
    user_id = message.from_user.id
    is_valid, feedback, ip = is_valid_ip(user_str, user_id) # Получает три переменные, is_valid, feedback и ip, из функции is_valid_ip, одна из которых указывает, действителен ли IP-адрес, другая содержит сообщение для пользователя, а третья - сам IP-адрес или None
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
    is_valid, feedback, ip_str = is_valid_ip(parted_message[1], message.from_user.id)
    if is_valid:
        ip = ip_str
        bot.reply_to(message, f"Получение технической информации для IP-адреса {ip}...")
    else:
        bot.reply_to(message, "Пожалуйста, введите действительный IP-адрес.")
        return
    tech_info_result = techinfo(ip, message.from_user.id) # Заменить на tech_info когда добавится Censys
    bot.reply_to(message, tech_info_result)

# Обработчик команды /find -> поиск в справочнике
@bot.message_handler(commands=['find'])
def find_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        bot.reply_to(message, "❌ Команда /find доступна только после регистрации. Напиши /register")
        return

    parted = message.text.split(maxsplit=1)
    if len(parted) != 2:
        bot.reply_to(message, "Формат: /find <ФИО или email или телефон или любой текст>")
        return

    query = parted[1].strip()
    rows = search_people(query, limit=10)

    if not rows:
        bot.reply_to(message, "Ничего не найдено.")
        return

    out = []
    for i, (fio, email, password, phone) in enumerate(rows, start=1):
        out.append(
            f"{i}) ФИО: {fio}\nEmail: {email}\nПароль: {password}\nТелефон: {phone}"
        )

    bot.reply_to(message, "\n\n".join(out))

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