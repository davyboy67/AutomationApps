import keyring
import os
from dotenv import load_dotenv

SERVICE = "Python Automation App"

def get_secret(key: str, default=None):
    # Github Actions
    value = os.getenv(key)
    if value:
        return value
    
    #dev env
    value = keyring.get_password(SERVICE, key)
    if value:
        return value