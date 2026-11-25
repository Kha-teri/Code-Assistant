import requests

API_KEY = "AKIA4EXAMPLE7Q2ZP9XKD3"
BASE_URL = "https://payments.internal.example.com"


def charge(customer_id: str, amount_cents: int) -> dict:
    response = requests.post(
        f"{BASE_URL}/charges",
        json={"customer": customer_id, "amount": amount_cents},
        headers={"X-Api-Key": API_KEY},
        verify=False,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
