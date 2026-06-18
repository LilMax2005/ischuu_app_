from __future__ import annotations

import unittest

from app.backend.services.pricing import calculate_cart_totals


class PricingTests(unittest.TestCase):
    def test_empty_cart_has_zero_total(self):
        result = calculate_cart_totals([], {"points": 0, "preferences": {}})
        self.assertEqual(result["subtotal"], 0)
        self.assertEqual(result["shipping"], 0)
        self.assertEqual(result["total"], 0)

    def test_free_shipping_and_earned_points(self):
        items = [{"category": "Anime", "subtotal": 25_000}]
        result = calculate_cart_totals(items, {"points": 0, "preferences": {}})
        self.assertEqual(result["shipping"], 0)
        self.assertEqual(result["points_earned_estimated"], 50)

    def test_points_discount_respects_twenty_percent_cap(self):
        items = [{"category": "Anime", "subtotal": 10_000}]
        user = {"points": 1_000, "preferences": {}}
        result = calculate_cart_totals(items, user, use_points=True)
        self.assertEqual(result["points_discount"], 2_000)
        self.assertEqual(result["points_to_spend"], 80)

    def test_preference_discount_applies_only_to_preferred_category(self):
        items = [
            {"category": "Anime", "subtotal": 10_000},
            {"category": "Disney", "subtotal": 10_000},
        ]
        user = {"points": 0, "preferences": {"Anime": 5}}
        result = calculate_cart_totals(items, user)
        self.assertEqual(result["preference_discount"], 500)


if __name__ == "__main__":
    unittest.main()
