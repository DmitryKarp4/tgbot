from os import getenv

TG_TOKEN = getenv("TG_TOKEN") # Для новых токенов структура такая же, просто меняется имя переменной окружения
if not TG_TOKEN:
    raise ValueError("Не задана переменная окружения TG_TOKEN")

SHODAN_TOKEN = getenv("SHODAN_TOKEN")
if not SHODAN_TOKEN:
    raise ValueError("Не задана переменная окружения SHODAN_TOKEN")

VT_TOKEN = getenv("VT_TOKEN")
if not VT_TOKEN:
    raise ValueError("Не задана переменная окружения VT_TOKEN")

