import os
from cryptography.fernet import Fernet

# Load the encryption key from the environment variables
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("No ENCRYPTION_KEY set for Flask application")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt(data: str) -> bytes:
    """Encrypts a string and returns bytes."""
    return cipher_suite.encrypt(data.encode())

def decrypt(token: bytes) -> str:
    """Decrypts a token and returns a string."""
    return cipher_suite.decrypt(token).decode()
