import hashlib
import requests
from log_event import log_event

# Загрузка скомпрометированных паролей из файла rockyou.txt в множество при инициализации
try:
    with open("rockyou.txt", "r", encoding="latin-1") as file:
            compromised_passwords = set(p.strip() for p in file)
except FileNotFoundError:
    raise Exception("Файл rockyou.txt не найден. Убедитесь, что файл находится в той же директории, что и скрипт.")

def check_password(password, user_id) -> tuple[bool, str]:

    log_event(f"Проверка пароля от пользователя {user_id} начата.")
    # Первичная проверка длины пароля
    if len(password) < 6:
        log_event(f"Проверка пароля от пользователя {user_id} завершена: слишком короткий пароль.")
        return False, "Пароль слишком короткий. Он должен содержать не менее 6 символов."
        
    elif len(password) > 20:
        log_event(f"Проверка пароля от пользователя {user_id} завершена: слишком длинный пароль.")
        return False, "Пароль слишком длинный. Он должен содержать не более 20 символов."

    # Первичная проверка на наличие различных типов символов
    elif not any(char.isdigit() for char in password):
        log_event(f"Проверка пароля от пользователя {user_id} завершена: отсутствуют цифры.")
        return False, "Пароль должен содержать хотя бы одну цифру."
    elif not any(char.isalpha() for char in password):
        log_event(f"Проверка пароля от пользователя {user_id} завершена: отсутствуют буквы.")
        return False, "Пароль должен содержать хотя бы одну букву."
    elif not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
        log_event(f"Проверка пароля от пользователя {user_id} завершена: отсутствуют специальные символы.")
        return False, "Пароль должен содержать хотя бы один специальный символ."
        
    # Проверка по списку скомпрометированных паролей rockyou.txt
    else:
        if password in compromised_passwords:
            log_event(f"Проверка пароля от пользователя {user_id} завершена: пароль скомпрометирован.")
            return False, "Этот пароль слишком распространен и скомпрометирован. Пожалуйста, выберите другой."
        else:

            # Проверяем по API Have I Been Pwned
            sha1_password = hashlib.sha1(password.encode()).hexdigest().upper()
            response = requests.get(f"https://api.pwnedpasswords.com/range/{sha1_password[:5]}")
            if response.status_code == 200:
                if sha1_password[5:] in response.text:
                    log_event(f"Проверка пароля от пользователя {user_id} завершена: пароль скомпрометирован через API.")
                    return False, "Этот пароль был скомпрометирован в утечках данных. Пожалуйста, выберите другой."
                else:
                    log_event(f"Проверка пароля от пользователя {user_id} завершена: пароль надежен.")
                    return True, "Пароль надежен."
            else:
                log_event(f"Проверка пароля от пользователя {user_id} завершена: ошибка при проверке через API.")
                return False, "Не удалось проверить пароль через API. Пожалуйста, попробуйте позже."