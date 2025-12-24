from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, hashlib, base64
from log_event import log_event

def encrypt_password(service_password, master_password, user_id): # plain -> шифруемый пароль, master_password -> мастер-пароль пользователя
    salt = user_id.to_bytes(8, "big") + os.urandom(8)
    key = hashlib.pbkdf2_hmac("sha256", master_password.encode(), salt, 200_000, dklen=32)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, service_password.encode(), None)
    log_event(f"Пароль для пользователя {user_id} зашифрован.")
    return base64.b64encode(salt + nonce + ct).decode()

def decrypt_password(enc, master_password, user_id): # enc -> зашифрованный пароль, master_password -> мастер-пароль пользователя
    raw = base64.b64decode(enc)
    salt = raw[:16]
    nonce = raw[16:28]
    ct = raw[28:]
    key = hashlib.pbkdf2_hmac("sha256", master_password.encode(), salt, 200_000, dklen=32)
    aes = AESGCM(key)
    log_event(f"Пароль для пользователя {user_id} расшифрован.")
    return aes.decrypt(nonce, ct, None).decode()
