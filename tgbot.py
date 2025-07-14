import telebot
import hashlib
import requests
import time

bot = telebot.TeleBot('YOUR-API')


# Обработчик команды /startt
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Я бот, созданный для проверки паролей. Напиши мне пароль, и я скажу, насколько он надежен.")

# Обработчик всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def check_password(message):
    # Функция для записи в лог, если пароль не прошел проверку
    def failed_check():
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{time.ctime()} Пароль пользователя {message.from_user.username} ({message.from_user.id}) не прошел проверку. \n")
            
    with open("logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.ctime()} Пользователь {message.from_user.username} ({message.from_user.id}) отправил пароль, начинаю проверку. \n")
    password = message.text
    # Первичная проверка длины пароля
    if len(password) < 6:
        bot.reply_to(message, "Пароль слишком короткий. Он должен содержать не менее 6 символов.")
        failed_check()
        
    elif len(password) > 20:
        bot.reply_to(message, "Пароль слишком длинный. Он должен содержать не более 20 символов.")
        failed_check()

    # Первичная проверка на наличие различных типов символов
    elif not any(char.isdigit() for char in password):
        bot.reply_to(message, "Пароль должен содержать хотя бы одну цифру.")
        failed_check()
    elif not any(char.isalpha() for char in password):
        bot.reply_to(message, "Пароль должен содержать хотя бы одну букву.")
        failed_check()
    elif not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
        bot.reply_to(message, "Пароль должен содержать хотя бы один специальный символ.")
        failed_check()
        
    # Проверка по списку скомпрометированных паролей rockyou.txt
    else:
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{time.ctime()} Пароль пользователя {message.from_user.username} ({message.from_user.id}) прошел первичную проверку, начинаю проверку по списку популярных паролей. \n")
        bot.reply_to(message, "Проверка пароля... Пожалуйста, подождите.")
        with open("rockyou.txt", "r", encoding="latin-1") as file:
            compromised_passwords = set(p.strip() for p in file)
        if password in compromised_passwords:
            bot.reply_to(message, "Пароль слишком распространен. Пожалуйста, выберите более сложный пароль.")
            failed_check()
        else:

            # Проверяем по API Have I Been Pwned
            sha1_password = hashlib.sha1(password.encode()).hexdigest().upper()
            response = requests.get(f"https://api.pwnedpasswords.com/range/{sha1_password[:5]}")
            if response.status_code == 200:
                if sha1_password[5:] in response.text:
                    bot.reply_to(message, "Пароль был скомпрометирован. Пожалуйста, выберите более сложный пароль.")
                    failed_check()
                else:
                    bot.reply_to(message, "Пароль надежный!")
                    with open("logs.txt", "a", encoding="utf-8") as log_file:
                        log_file.write(f"{time.ctime()} Пароль пользователя {message.from_user.username} ({message.from_user.id}) прошел все проверки. \n")
            else:
                bot.reply_to(message, "Ошибка проверки пароля.")

bot.infinity_polling()