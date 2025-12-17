import time

def log_event(event) -> None:    # Логирует событие в файл logs.txt с отметкой времени.
    with open("logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{time.ctime()} {event}\n")