from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.backend.services.shipping import normalize_shipping_address


def address(**overrides) -> dict:
    data = {
        "recipient": "Cliente",
        "phone": "56912345678",
        "region": "Metropolitana",
        "city": "Santiago",
        "comuna": "Providencia",
        "street": "Alameda",
        "number": "123",
        "details": "",
    }
    data.update(overrides)
    return data


class ShippingValidationTests(unittest.TestCase):
    def test_phone_accepts_only_digits(self):
        with self.assertRaises(HTTPException) as context:
            normalize_shipping_address(address(phone="+56 9 1234 5678"))
        self.assertIn("teléfono", context.exception.detail.lower())

    def test_street_number_accepts_only_digits(self):
        with self.assertRaises(HTTPException) as context:
            normalize_shipping_address(address(number="123A"))
        self.assertIn("número", context.exception.detail.lower())

    def test_city_is_required(self):
        with self.assertRaises(HTTPException) as context:
            normalize_shipping_address(address(city=""))
        self.assertIn("ciudad", context.exception.detail.lower())

    def test_valid_numeric_address_is_normalized(self):
        result = normalize_shipping_address(address())
        self.assertEqual(result["phone"], "56912345678")
        self.assertEqual(result["number"], "123")
        self.assertEqual(
            result["full_address"],
            "Alameda 123, Providencia, Santiago, Metropolitana",
        )


if __name__ == "__main__":
    unittest.main()
