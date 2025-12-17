from os import getenv

TG_TOKEN = getenv("TG_TOKEN") # Для новых токенов структура такая же, просто меняется имя переменной окружения
if not TG_TOKEN:
    raise ValueError("Не задана переменная окружения TG_TOKEN")
