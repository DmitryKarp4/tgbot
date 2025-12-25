import secrets
import string

# Набор символов для надёжного пароля
ALPHABET = (
    string.ascii_lowercase +   # a-z
    string.ascii_uppercase +   # A-Z
    string.digits +            # 0-9
    "!@#$%^&*()-_=+[]{}<>?"
)

def generate_secure_password(length: int = 12) -> str:
    if length < 8:
        raise ValueError("Длина пароля должна быть не меньше 8")

    return "".join(secrets.choice(ALPHABET) for _ in range(length))
