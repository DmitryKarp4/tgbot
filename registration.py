import sqlite3
import hashlib
import secrets
from pathlib import Path
from log_event import log_event

DB_PATH = Path("people.db")


# ---------- DB ----------
def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            login TEXT UNIQUE,
            password_hash TEXT,
            is_registered INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);")


def _ensure_user_row(user_id: int):
    with _conn() as con:
        con.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))


def _get_user(user_id: int):
    with _conn() as con:
        cur = con.execute(
            "SELECT id, user_id, login, is_registered FROM users WHERE user_id=?",
            (user_id,)
        )
        return cur.fetchone()


def _login_exists(login: str) -> bool:
    with _conn() as con:
        cur = con.execute("SELECT 1 FROM users WHERE login=? LIMIT 1", (login,))
        return cur.fetchone() is not None


def _set_login(user_id: int, login: str):
    with _conn() as con:
        con.execute("UPDATE users SET login=? WHERE user_id=?", (login, user_id))


def _finish_registration(user_id: int, password_hash: str):
    with _conn() as con:
        con.execute(
            "UPDATE users SET password_hash=?, is_registered=1 WHERE user_id=?",
            (password_hash, user_id)
        )


# ---------- PASSWORD HASH ----------
def _hash_password(password: str) -> str:
    # безопаснее чем sha256, и без сторонних библиотек
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000
    )
    log_event(f"Пароль от пользователя был захеширован с солью.")
    return f"pbkdf2_sha256${salt}${dk.hex()}"


# ---------- PUBLIC: register handlers ----------
def setup_registration(bot):
    """
    Подключает команды:
      /register - регистрация
      /me       - статус
    И инициализирует БД.
    """
    init_db()

    @bot.message_handler(commands=['me'])
    def _me_handler(message):
        user_id = message.from_user.id
        row = _get_user(user_id)
        if not row:
            bot.reply_to(message, "Тебя ещё нет в базе. Напиши /register")
            return

        _, _, login, is_reg = row
        if is_reg:
            bot.reply_to(message, f"Ты зарегистрирован.\nЛогин: {login}")
            log_event(f"Запрос статуса регистрации через /me от пользователя {user_id}.")
        else:
            bot.reply_to(message, "Регистрация не завершена. Напиши /register")

    @bot.message_handler(commands=['register'])
    def _register_handler(message):
        user_id = message.from_user.id
        _ensure_user_row(user_id)

        row = _get_user(user_id)
        if row and row[3] == 1:
            bot.reply_to(message, "Ты уже зарегистрирован.")
            return

        msg = bot.reply_to(message, "Введи логин (без пробелов, минимум 3 символа):")
        bot.register_next_step_handler(msg, _step_login)

    def _step_login(message):
        user_id = message.from_user.id
        login = (message.text or "").strip()

        if " " in login or len(login) < 3:
            msg = bot.reply_to(message, "Логин должен быть без пробелов и минимум 3 символа. Введи логин ещё раз:")
            bot.register_next_step_handler(msg, _step_login)
            return

        if _login_exists(login):
            msg = bot.reply_to(message, "Этот логин уже занят. Введи другой логин:")
            bot.register_next_step_handler(msg, _step_login)
            return

        _set_login(user_id, login)

        msg = bot.reply_to(message, "Теперь введи пароль (минимум 6 символов):")
        bot.register_next_step_handler(msg, _step_password)

    def _step_password(message):
        user_id = message.from_user.id
        password = (message.text or "").strip()

        if len(password) < 6:
            msg = bot.reply_to(message, "Пароль слишком короткий. Введи пароль ещё раз (минимум 6 символов):")
            bot.register_next_step_handler(msg, _step_password)
            return

        pwd_hash = _hash_password(password)
        _finish_registration(user_id, pwd_hash)

        row = _get_user(user_id)
        login = row[2] if row else "?"
        bot.reply_to(message, f"✅ Готово! Ты зарегистрирован.\nЛогин: {login}")
        log_event(f"Пользователь {user_id} завершил регистрацию с логином {login}.")


# ---------- OPTIONAL: use this in main.py to protect commands ----------
def is_registered(user_id: int) -> bool:
    row = _get_user(user_id)
    return bool(row and row[3] == 1)
