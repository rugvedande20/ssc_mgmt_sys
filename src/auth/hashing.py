import base64
import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived_key).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt_b64, key_b64 = password_hash.split("$", maxsplit=1)
    salt = base64.b64decode(salt_b64.encode())
    expected_key = base64.b64decode(key_b64.encode())
    actual_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return hmac.compare_digest(expected_key, actual_key)
