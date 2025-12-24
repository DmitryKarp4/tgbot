import telebot
from telebot import types
from config import TG_TOKEN
from checkpassword import check_password
from checkip import is_valid_ip
from techinfo import techinfo
from shodandork import shodan_dork_search
from registration import setup_registration, is_registered 
from search import search_people
from log_event import log_event
from report_file import send_report_file

bot = telebot.TeleBot(TG_TOKEN)
setup_registration(bot)
user_reports = {} # Временное хранилище отчётов


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

    # Генерация отчёта
    tech_info_result = techinfo(ip, message.from_user.id)

    # Сохраняем результат для кнопки
    chat_id = message.chat.id 
    user_reports[chat_id] = tech_info_result # Временное сохранение отчёта

    # Создаём кнопку
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="📄 Получить файл с отчётом",
            callback_data="send_report"
        )
    )

    # Отправляем сообщение с кнопкой
    bot.send_message(
        chat_id,
        f"{tech_info_result}\n\nНажмите кнопку ниже, чтобы получить файл с полным отчётом.",
        reply_markup=kb
    )

    

# Обработчик команды /find -> поиск в справочнике
@bot.message_handler(commands=['find'])
def find_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        log_event(message.from_user.id, "Попытка использования /find без регистрации")
        bot.reply_to(message, "❌ Команда /find доступна только после регистрации. Напиши /register")
        return

    parted = message.text.split(maxsplit=1)
    if len(parted) != 2:
        bot.reply_to(message, "Формат: /find <ФИО или email или телефон или любой текст>")
        return

    query = parted[1].strip()
    rows = search_people(query, limit=10, user_id=message.from_user.id)

    if not rows:
        bot.reply_to(message, "Ничего не найдено.")
        return

    out = []
    for i, (fio, email, password, phone) in enumerate(rows, start=1):
        out.append(
            f"{i}) ФИО: {fio}\nEmail: {email}\nПароль: {password}\nТелефон: {phone}"
        )
    
    # Сохраняем результат для кнопки
    find_result = "\n\n".join(out)

    chat_id = message.chat.id 
    user_reports[chat_id] = find_result # Временное сохранение отчёта

    # Создаём кнопку
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="📄 Получить файл с отчётом",
            callback_data="send_report"
        )
    )

    # Отправляем сообщение с кнопкой
    bot.send_message(
        chat_id,
        f"{find_result}\n\nНажмите кнопку ниже, чтобы получить файл с полным отчётом.",
        reply_markup=kb
    )
    

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

    dork_result = shodan_dork_search(dork, user_id)
    
    chat_id = message.chat.id 
    user_reports[chat_id] = dork_result # Временное сохранение отчёта

    # Создаём кнопку
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="📄 Получить файл с отчётом",
            callback_data="send_report"
        )
    )

    # Отправляем сообщение с кнопкой
    bot.send_message(
        chat_id,
        f"{dork_result}\n\nНажмите кнопку ниже, чтобы получить файл с полным отчётом.",
        reply_markup=kb
    )

# Обработчик кнопки
@bot.callback_query_handler(func=lambda call: call.data == "send_report")
def callback_send_report(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    log_event(f"Пользователь {user_id} запросил файл с отчётом через кнопку.")
    report_text = user_reports.get(chat_id)

    if not report_text:
        log_event(f"Отчёт для пользователя {user_id} не найден при попытке отправки файла.")
        bot.answer_callback_query(call.id, "Отчёт не найден. Сначала запросите его через /techinfo.")
        return

    send_report_file(bot, chat_id, user_id, report_text)
    log_event(f"Файл с отчётом отправлен пользователю {user_id} через кнопку.")
    bot.answer_callback_query(call.id, "Файл отправлен ✅")

bot.infinity_polling()

# TODO: Менеджер паролей
# TODO: Поменять Readme.md
# TODO: Domain name info (whois, dns, etc.)