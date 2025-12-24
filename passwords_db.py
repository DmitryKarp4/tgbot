import sqlite3
import hashlib
import secrets
from crypto_utils import encrypt_password
from log_event import log_event
from pathlib import Path

DB_PATH = Path("people.db")

def _conn():
    return sqlite3.connect(DB_PATH)

def init_passwords_table():
    """Создаём таблицу для хранения паролей менеджера"""
    with _conn() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS user_passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            password TEXT NOT NULL,
            master_password_hash TEXT NOT NULL,
            master_password_salt TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_user_passwords_user_id ON user_passwords(user_id);")
    log_event("Инициализирована таблица для менеджера паролей")

def hash_master_password(master_password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + master_password).encode()).hexdigest()
    hashed_master_password = f"{salt}${pwd_hash}"
    return hashed_master_password, salt

def add_password(user_id: int, master_password: str, service: str, service_password: str):
    enc_password = encrypt_password(service_password, master_password, user_id)
    hashed_master_password, salt = hash_master_password(master_password)
    with _conn() as con:
        con.execute(
            "INSERT INTO user_passwords (user_id, service, password, master_password_hash, master_password_salt) VALUES (?, ?, ?, ?, ?)",
            (user_id, service, enc_password, hashed_master_password, salt)
        )
    log_event(f"Добавлен пароль для сервиса '{service}' пользователя {user_id}")

def get_services(user_id: int):
    with _conn() as con:
        cur = con.execute("SELECT service FROM user_passwords WHERE user_id=?", (user_id,))
        return [row[0] for row in cur.fetchall()]

def check_master_password(user_id: int, master_password: str) -> bool:
    with _conn() as con:
        cur = con.execute(
            "SELECT master_password_hash, master_password_salt FROM user_passwords WHERE user_id=? LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return False
        stored_hash, salt = row
        pwd_hash = stored_hash.split('$')[1]
        user_password_hash = hashlib.sha256((salt + master_password).encode()).hexdigest()
        is_valid = user_password_hash == pwd_hash
        log_event(f"Проверка мастер-пароля для пользователя {user_id}: {'успешна' if is_valid else 'неуспешна'}.")
        return is_valid
    
def get_encrypted_password(user_id: int, service: str) -> str | None:
    with _conn() as con:
        cur = con.execute(
            "SELECT password FROM user_passwords WHERE user_id=? AND service=? LIMIT 1",
            (user_id, service)
        )
        row = cur.fetchone()
        if row:
            return row[0]
        return None