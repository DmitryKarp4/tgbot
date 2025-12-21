import ipaddress
import socket
from log_event import log_event
def is_valid_ip(ip_str, user_id) -> tuple[bool, str, str|None]:
    try:
            ipaddress.ip_address(ip_str)
            log_event(f"Проверка IP-адреса {ip_str} от пользователя {user_id} завершена: действительный IP-адрес.")
            return True, "Это действительный IP-адрес."
    except ValueError:
            log_event(f"Проверка IP-адреса {ip_str} от пользователя {user_id} завершена: недействительный IP-адрес.")
            try:
                log_event(f"Попытка разрешения доменного имени {ip_str} от пользователя {user_id}.")
                ip = socket.gethostbyname(ip_str)
                log_event(f"Разрешение доменного имени {ip_str} от пользователя {user_id} успешно: действительный IP-адрес.")
                return True, f"Это действительное доменное имя с IP-адресом: {ip}", ip
            except:
                log_event(f"Разрешение доменного имени {ip_str} от пользователя {user_id} не удалось: недействительный IP-адрес.")
                return False, "Это недействительный IP-адрес и недействительное доменное имя.", None