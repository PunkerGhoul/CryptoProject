import secrets
import string


def generate_secure_password(length):
    letters = string.ascii_letters
    digits = string.digits
    special_chars = string.punctuation
    alphabet = letters + digits + special_chars

    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if any(char in special_chars for char in pwd) and sum(char in digits for char in pwd) >= 2 and not any(pwd[i].lower() == pwd[i+1].lower() for i in range(len(pwd)-1)):
            return pwd
