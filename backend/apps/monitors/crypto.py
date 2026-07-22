from cryptography.fernet import Fernet
from django.conf import settings

# Fernet is symmetric encryption (AES128-CBC + HMAC under the hood) - not
# hashing, this has to be reversible since perform_check needs the actual
# credential back to put it on the outgoing request. Rolled this by hand
# instead of reaching for a django-encrypted-fields package - one function
# each way, nothing to learn beyond "here's the key, here's the ciphertext."


def encrypt(plaintext):
    if not plaintext:
        return ''
    fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext):
    if not ciphertext:
        return ''
    fernet = Fernet(settings.FIELD_ENCRYPTION_KEY)
    return fernet.decrypt(ciphertext.encode()).decode()
