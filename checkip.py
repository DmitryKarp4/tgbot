import ipaddress
from log_event import log_event
def is_valid_ip(ip_str, user_id) -> tuple[bool, str]:
    try:
            ipaddress.ip_address(ip_str)
            log_event(f"Проверка IP-адреса {ip_str} от пользователя {user_id} завершена: действительный IP-адрес.")
            return True, "Это действительный IP-адрес."
    except ValueError:
            log_event(f"Проверка IP-адреса {ip_str} от пользователя {user_id} завершена: недействительный IP-адрес.")
            return False, "Это недействительный IP-адрес."