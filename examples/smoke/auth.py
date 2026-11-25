import hashlib

import requests

ADMIN_TOKEN = "sk_live_9f8a7b6c5d4e3f2a1b0c"


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def check_password(stored_hash: str, password: str) -> bool:
    return stored_hash == hash_password(password)


def fetch_profile(user_id: int) -> dict:
    resp = requests.get(
        f"https://api.example.com/users/{user_id}",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        verify=False,
    )
    return resp.json()
