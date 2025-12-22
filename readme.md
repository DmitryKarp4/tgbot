# Telegram TechINT Bot

## 📌 Описание

Данный Telegram-бот предназначен для базовых **TechINT / Security** проверок и сбора открытой информации по IP-адресам:

* 🔐 **Проверка надежности паролей**
  * локально (длина, состав символов)
  * по списку скомпрометированных паролей `rockyou.txt`
  * через API **Have I Been Pwned**
* 🌐 **Проверка валидности IP-адресов**
* 🛰️ **TechINT-отчёт по IP**
  * данные из **Shodan** (открытые порты, сервисы, версии, HTTP/SSL-информация)
  * поиск доменов и сертификатов через **crt.sh**
* 🕷️ **Создание Shodan-Dork из исходных параметров** 
* 🗂️ **Логирование всех действий пользователей** с указанием `user_id`

Бот написан на Python с использованием библиотеки **pyTelegramBotAPI**. Архитектура модульная и подготовлена для дальнейшего расширения (другие источники TECHINT, Docker, CI).

---

##  Установка и настройка

### 1️⃣ Регистрация Telegram-бота

1. Напишите боту **@BotFather**
2. Выполните команды:

   ```
   /start
   /newbot
   ```
3. Следуйте инструкциям BotFather
4. В результате вы получите **Telegram Bot Token**
   ⚠️ **Никогда не публикуйте и не коммитьте токен**

---

### 2️⃣ Клонирование репозитория

```bash
git clone <URL_репозитория>
cd <папка_проекта>
```

---

### 3️⃣ Настройка переменных окружения

Бот использует переменные окружения (безопасно для Git и Docker).

Минимальный набор:

* `TG_TOKEN` — Telegram Bot Token
* `SHODAN_TOKEN` — API-ключ Shodan

#### Linux / macOS

```bash
export TG_TOKEN=ВАШ_TELEGRAM_TOKEN
export SHODAN_TOKEN=ВАШ_SHODAN_API_KEY
```

#### Windows (PowerShell)

```powershell
setx TG_TOKEN "ВАШ_TELEGRAM_TOKEN"
setx SHODAN_TOKEN "ВАШ_SHODAN_API_KEY"
```
#### .env (PowerShell / Bash)
```bash
cd <папка проекта>
mkdir .env
echo 'TG_TOKEN = "ВАШ_TELEGRAM_TOKEN"' >> .env
echo 'SHODAN_TOKEN = "ВАШ_SHODAN_API_KEY"' >> .env
```
Если обязательные переменные не заданы — бот не запустится.

---

### 4️⃣ Подготовка rockyou.txt

1. Распакуйте `rockyou.txt.zip`
2. Переименуйте файл в:

   ```
   rockyou.txt
   ```
3. Поместите его в корень проекта

---

### 5️⃣ Установка зависимостей

```bash
pip install pyTelegramBotAPI requests shodan ipaddress
```

---

### 6️⃣ Запуск бота

```bash
python main.py
```

После запуска бот начнет принимать команды в Telegram.

---

## 🤖 Доступные команды

| Команда                     | Описание                        |
| --------------------------- | ------------------------------- |
| `/start`                    | Приветственное сообщение        |
| `/help`                     | Список доступных команд         |
| `/ip <IP>`                  | Проверка валидности IP-адреса   |
| `/checkpassword <пароль>`   | Проверка надежности пароля      |
| `/techinfo <IP>`            | TECHINT-отчёт (Shodan + crt.sh) |
| `/shodandork  <Dork-запрос>`| Shodan-Dork запрос              |

### Примеры

```
/ip 8.8.8.8
/checkpassword P@ssw0rd123
/techinfo 1.1.1.1
/shodandork ip=1.1.1.1, port=53, service=nginx
```

---

## 🧾 Логирование

Все действия пользователей логируются в файл:

```
logs.txt
```

Каждая запись содержит:

* время события
* описание действия
* `user_id`

---

## 🛠 Структура проекта

```
.
├── main.py
├── config.py
├── checkpassword.py
├── checkip.py
├── techinfo.py
├── shodandork.py
├── log_event.py
├── rockyou.txt
├── logs.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📦 Используемые технологии

* Python 3
* pyTelegramBotAPI
* requests
* Shodan API
* Have I Been Pwned API
* crt.sh (Certificate Transparency)

---

## 🚧 Планы по развитию

* 🐳 Dockerfile и docker-compose
* 🔎 Дополнительные TECHINT-источники
* 📊 Форматированный отчёт (Markdown / HTML)
