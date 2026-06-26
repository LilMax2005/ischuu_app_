from __future__ import annotations

import unittest

from app.backend.services.preferences import build_preference_profile


class PreferenceProfileTests(unittest.TestCase):
    def test_repeated_category_becomes_favorite(self):
        orders = [
            {
                "created_at": "2026-06-01T12:00:00+00:00",
                "payment_status": "paid",
                "items": [
                    {"category": "Anime", "quantity": 2, "subtotal": 20_000},
                    {"category": "Disney", "quantity": 1, "subtotal": 10_000},
                ],
            },
            {
                "created_at": "2026-06-10T12:00:00+00:00",
                "payment_status": "paid",
                "items": [
                    {"category": "Anime", "quantity": 1, "subtotal": 12_000},
                ],
            },
        ]

        profile = build_preference_profile(orders)

        self.assertEqual(profile["preferences"]["Anime"], 3)
        self.assertIn("Anime", profile["favorite_categories"])
        self.assertEqual(profile["preference_stats"]["Anime"]["orders"], 2)

    def test_single_item_does_not_force_favorite(self):
        profile = build_preference_profile(
            [
                {
                    "created_at": "2026-06-01T12:00:00+00:00",
                    "items": [{"category": "Anime", "quantity": 1, "subtotal": 10_000}],
                }
            ]
        )

        self.assertEqual(profile["preferences"], {"Anime": 1})
        self.assertEqual(profile["favorite_categories"], [])


if __name__ == "__main__":
    unittest.main()
