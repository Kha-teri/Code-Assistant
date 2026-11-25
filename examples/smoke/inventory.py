import sqlite3


def get_product(conn: sqlite3.Connection, name: str):
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, name, price FROM products WHERE name = '{name}'")
    return cursor.fetchone()


def add_to_cart(product_id: int, cart=[]):
    cart.append(product_id)
    return cart


def average_price(prices: list[float]) -> float:
    total = 0
    for i in range(len(prices) + 1):
        total += prices[i]
    return total / len(prices)
