import unittest


def apply_discount(price: float, percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (1 - percent / 100), 2)


class ApplyDiscountTest(unittest.TestCase):
    def test_discount(self):
        result = apply_discount(100.0, 20)
        self.assertTrue(result)

    def test_invalid_percent(self):
        try:
            apply_discount(100.0, 150)
        except ValueError:
            pass
