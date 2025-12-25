import telebot
from telebot import types
from config import TG_TOKEN
from checkpassword import check_password
from checkip import is_valid_ip
from passwords_db import add_password, get_services
from techinfo import techinfo
from shodandork import shodan_dork_search
from registration import setup_registration, is_registered 
from passwords_db import init_passwords_table, check_master_password, get_encrypted_password
from search import search_people
from log_event import log_event
from report_file import send_report_file
from crypto_utils import decrypt_password
from checkvt import check_url, check_file_bytes, set_waiting_file, is_waiting_file
from password_generator import generate_secure_password
import time

bot = telebot.TeleBot(TG_TOKEN)
setup_registration(bot)
init_passwords_table()
user_reports = {} # Временное хранилище отчётов
user_password_steps = {}  # хранит временно ввод пользователя (user_id -> dict)
active_master_sessions: dict[int, dict]
active_master_sessions = {}
master_session_ttl = 120  # секунд

# Функции для управления сессиями мастер-паролей
def set_master_session(user_id: int, master_password: str):
    active_master_sessions[user_id] = {
        "master": master_password,
        "expires_at": time.time() + master_session_ttl
    }

def get_master_session(user_id: int):
    session = active_master_sessions.get(user_id)
    if not session:
        return None

    if time.time() > session["expires_at"]:
        active_master_sessions.pop(user_id, None)
        return None

    return session["master"]

# Обработчик команды /start -> приветственное сообщение
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Я бот, созданный для различных целей. Используйте команды /help чтобы узнать больше.")

# Обработчик команды /help -> список доступных команд
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🤖 *Доступные команды бота*\n\n"

        "📌 *Основные команды*\n"
        "/start — Запуск бота\n"
        "/help — Показать это сообщение\n\n"

        "👤 *Регистрация и профиль*\n"
        "/register — Регистрация пользователя\n"
        "/me — Проверка статуса регистрации\n\n"

        "🔍 *Поиск и аналитика* _(доступно после регистрации)_\n"
        "/find <текст> — Поиск по ФИО / email / телефону\n"
        "/ip <IP или домен> — Проверка IP-адреса или доменного имени\n"
        "/techinfo <IP или домен> — Техническая информация (Shodan, Censys)\n\n"

        "🛡 *Безопасность*\n"
        "/checkpassword <пароль> — Проверка надёжности пароля\n\n"
        "/check <ссылка> — Проверка ссылки через VirusTotal. Для проверки требуется написать /check с пустым аргументом, а файл отправить следующим сообщением.\n\n"
        "/genpass <длина> — Создание рандомного надежного пароля. Если не указать длину - пароль будет иметь 12 символов\n\n"

        "🔎 *Shodan Dork генератор*\n"
        "/shodandork <параметры> — Создание Shodan Dork запроса\n"
        "Доступные параметры:\n"
        "• ip=, port=, service=, product=\n"
        "• country=, asn=, org=, title=, hostname=\n\n"
        "Пример:\n"
        "`/shodandork port=443 product=nginx country=US`\n\n"

        "🔐 *Менеджер паролей*\n"
        "/password — Управление сохранёнными паролями\n"
        "/set_master_password — Установка мастер-пароля\n\n"
        "• Добавление и просмотр паролей сервисов\n"
        "• Все пароли зашифрованы\n"
        "• Доступ через мастер-пароль с TTL-сессией\n\n"

        "⚠️ *Безопасность данных*\n"
        "• Мастер-пароль нигде не хранится в открытом виде\n"
        "• Сессия доступа ограничена по времени\n"
        "• Все действия логируются\n"
    )

    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode="Markdown"
    )

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
        log_event("Попытка использования /find без регистрации")
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

#Обработчик команды genpass. Генерация надежного пароля
@bot.message_handler(commands=['genpass'])
def genpass_handler(message):
    parts = message.text.split(maxsplit=1)

    # /genpass 20
    if len(parts) == 2 and parts[1].isdigit():
        length = int(parts[1])
    else:
        length = 12  # по умолчанию

    try:
        password = generate_secure_password(length)
    except ValueError as e:
        bot.reply_to(message, f"❌ {e}")
        return

    bot.reply_to(
        message,
        f"🔐 Сгенерированный пароль ({length} символов):\n\n`{password}`",
    )


#Обработчик команды check. Проверка файлов и ссылок на VirusTotal.
@bot.message_handler(commands=['check'])
def check_handler(message):
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)

    # /check <url>
    if len(parts) == 2:
        url = parts[1].strip()
        bot.reply_to(message, "⏳ Проверяю ссылку через VirusTotal...")
        result = check_url(url)
        bot.reply_to(message, result)
        return

    # /check (без аргумента) -> ждём файл
    set_waiting_file(user_id, True)
    bot.reply_to(message, "📎 Отправь файл следующим сообщением, и я проверю его через VirusTotal.")

#Обработчик документов
@bot.message_handler(content_types=['document'])
def document_handler(message):
    user_id = message.from_user.id

    # проверяем только если пользователь до этого написал /check
    if not is_waiting_file(user_id):
        return

    set_waiting_file(user_id, False)

    bot.reply_to(message, "⏳ Скачиваю файл и отправляю на проверку...")

    file_info = bot.get_file(message.document.file_id)
    file_bytes = bot.download_file(file_info.file_path)
    filename = message.document.file_name or "file.bin"

    result = check_file_bytes(filename, file_bytes)
    bot.reply_to(message, result)

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

@bot.message_handler(commands=['set_master_password'])
def set_master_password_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        log_event(f"Попытка использования /set_master_password пользователем {message.from_user.id} без регистрации")
        bot.reply_to(message, "❌ Команда /set_master_password доступна только после регистрации. Напиши /register")
        return

    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите новый мастер-пароль:")
    bot.register_next_step_handler(msg, process_set_master_password_step, message.from_user.id)

def process_set_master_password_step(message, user_id):
    set_master_session(user_id, message.text.strip())
    bot.send_message(message.chat.id, "Мастер-пароль установлен!")

@bot.message_handler(commands=['password'])
def passwords_manager_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        log_event(f"Попытка использования /password пользователем {message.from_user.id} без регистрации")
        bot.reply_to(message, "❌ Команда /password доступна только после регистрации. Напиши /register")
        return
    chat_id = message.chat.id 

    # Создаём кнопку
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="Добавить пароль",
            callback_data="add_password"
        ),
        types.InlineKeyboardButton(
            text="Показать пароли",
            callback_data="show_passwords"
        )
    )

    # Отправляем сообщение с кнопкой
    bot.send_message(
        message.chat.id,
        f"Выберите действие ниже:",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data == "add_password")
def callback_add_password(call): # В итоге получаю переменные master_password, service, service_password
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    master_password = active_master_sessions.get(user_id)
    if master_password: # Есть ли уже мастер пароль в сессии
        msg = bot.send_message(chat_id, "Введите название сервиса (например, Gmail, Facebook):")
        bot.register_next_step_handler(msg, process_service_addpass_step, user_id)
    else:
        msg = bot.send_message(chat_id, "Мастер-Пароль еще не был установлен. Введите свой мастер-пароль:")
        bot.register_next_step_handler(msg, process_master_password_step, user_id)
    

def process_master_password_step(message, user_id): # Получение мастер-пароля
    set_master_session(user_id, message.text.strip())
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите название сервиса (например, Gmail, Facebook):")
    bot.register_next_step_handler(msg, process_service_addpass_step, user_id)

def process_service_addpass_step(message, user_id): # Получение названия сервиса
    service = message.text.strip()
    master_password = get_master_session(user_id)
    if not master_password:
        bot.send_message(message.chat.id, "❌ Мастер-сессия истекла. Введите /password заново.")
        return
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите пароль для сервиса:")
    bot.register_next_step_handler(msg, process_addpassword_step, user_id, service)

def process_addpassword_step(message, user_id, service): # Получение пароля сервиса
    service_password = message.text.strip()
    master_password = get_master_session(user_id)
    if not master_password:
        bot.send_message(message.chat.id, "❌ Мастер-сессия истекла. Введите /password заново.")
        return
    chat_id = message.chat.id
    add_password(user_id, master_password, service, service_password) # Добавляем пароль в БД
    bot.send_message(chat_id, f"Пароль для {service} сохранён!")
        


@bot.callback_query_handler(func=lambda call: call.data == "show_passwords")
def callback_add_password(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    services = get_services(user_id)
    msg = bot.send_message(chat_id, "Сохранённые сервисы:\n" + "\n".join(services) if services else "Нет сохранённых паролей.")
    bot.register_next_step_handler(msg, process_service_step, user_id, chat_id)
    
def process_service_step(service, user_id, chat_id): # Получение названия сервиса для получения пароля
    selected_service = service.text.strip()
    master = get_master_session(user_id)
    is_valid = check_master_password(user_id, master)
    if is_valid:
        enc_pass = get_encrypted_password(user_id, selected_service)
        decrypted_password = decrypt_password(enc_pass, master, user_id)
        bot.send_message(chat_id, f"Мастер-пароль найден и верен. Пароль для сервиса **{selected_service}**:\n\n**{decrypted_password}**", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "Неверный мастер-пароль.")

        
@bot.message_handler(commands=['set_master_password'])
def set_master_password_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        log_event(f"Попытка использования /set_master_password пользователем {message.from_user.id} без регистрации")
        bot.reply_to(message, "❌ Команда /set_master_password доступна только после регистрации. Напиши /register")
        return

    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите новый мастер-пароль:")
    bot.register_next_step_handler(msg, process_set_master_password_step, message.from_user.id)

def process_set_master_password_step(message, user_id):
    set_master_session(user_id, message.text.strip())
    bot.send_message(message.chat.id, "Мастер-пароль установлен!")

@bot.message_handler(commands=['password'])
def passwords_manager_handler(message):
    # запрет без регистрации
    if not is_registered(message.from_user.id):
        log_event(f"Попытка использования /password пользователем {message.from_user.id} без регистрации")
        bot.reply_to(message, "❌ Команда /password доступна только после регистрации. Напиши /register")
        return
    chat_id = message.chat.id 

    # Создаём кнопку
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="Добавить пароль",
            callback_data="add_password"
        ),
        types.InlineKeyboardButton(
            text="Показать пароли",
            callback_data="show_passwords"
        )
    )

    # Отправляем сообщение с кнопкой
    bot.send_message(
        chat_id,
        f"Выберите действие ниже:",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data == "add_password")
def callback_add_password(call): # В итоге получаю переменные master_password, service, service_password
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    master_password = active_master_sessions.get(user_id)
    if master_password: # Есть ли уже мастер пароль в сессии
        msg = bot.send_message(chat_id, "Введите название сервиса (например, Gmail, Facebook):")
        bot.register_next_step_handler(msg, process_service_addpass_step, user_id)
    else:
        msg = bot.send_message(chat_id, "Мастер-Пароль еще не был установлен. Введите свой мастер-пароль:")
        bot.register_next_step_handler(msg, process_master_password_step, user_id)
    

def process_master_password_step(message, user_id): # Получение мастер-пароля
    set_master_session(user_id, message.text.strip())
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите название сервиса (например, Gmail, Facebook):")
    bot.register_next_step_handler(msg, process_service_addpass_step, user_id)

def process_service_addpass_step(message, user_id): # Получение названия сервиса
    service = message.text.strip()
    master_password = get_master_session(user_id)
    if not master_password:
        bot.send_message(message.chat.id, "❌ Мастер-сессия истекла. Введите /password заново.")
        return
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите пароль для сервиса:")
    bot.register_next_step_handler(msg, process_addpassword_step, user_id, service)

def process_addpassword_step(message, user_id, service): # Получение пароля сервиса
    service_password = message.text.strip()
    master_password = get_master_session(user_id)
    if not master_password:
        bot.send_message(message.chat.id, "❌ Мастер-сессия истекла. Введите /password заново.")
        return
    chat_id = message.chat.id
    add_password(user_id, master_password, service, service_password) # Добавляем пароль в БД
    bot.send_message(chat_id, f"Пароль для {service} сохранён!")
        


@bot.callback_query_handler(func=lambda call: call.data == "show_passwords")
def callback_add_password(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    services = get_services(user_id)
    msg = bot.send_message(chat_id, "Сохранённые сервисы:\n" + "\n".join(services) if services else "Нет сохранённых паролей.")
    bot.register_next_step_handler(msg, process_service_step, user_id, chat_id)
    
def process_service_step(service, user_id, chat_id): # Получение названия сервиса для получения пароля
    selected_service = service.text.strip()
    master = get_master_session(user_id)
    is_valid = check_master_password(user_id, master)
    if is_valid:
        enc_pass = get_encrypted_password(user_id, selected_service)
        decrypted_password = decrypt_password(enc_pass, master, user_id)
        bot.send_message(chat_id, f"Мастер-пароль найден и верен. Пароль для сервиса **{selected_service}**:\n\n**{decrypted_password}**", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "Неверный мастер-пароль.")

bot.infinity_polling()

# TODO: Domain name info (whois, dns, etc.)
