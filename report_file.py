# report_file.py
import os
from telebot import TeleBot
from log_event import log_event

def send_report_file(bot: TeleBot, chat_id: int, user_id: int, report_text: str):
    """
    Создаёт временный файл с содержимым отчёта и отправляет его пользователю в Telegram.

    :param bot: экземпляр TeleBot
    :param chat_id: id чата пользователя
    :param report_text: текст отчёта
    """
    filename = f"report_{chat_id}.txt"

    # создаём файл
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    # отправляем файл
    with open(filename, "rb") as f:
        bot.send_document(chat_id, f)
        log_event(f"Отправлен файл с отчётом пользователю {user_id}.")

    # удаляем временный файл
    os.remove(filename)
