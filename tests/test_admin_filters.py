from __future__ import annotations

import os
import unittest

from bson import ObjectId

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")

from app.backend.routers.admin import build_order_filters  # noqa: E402


class AdminOrderFilterTests(unittest.TestCase):
    def test_search_accepts_order_object_id(self):
        order_id = ObjectId()
        filters = build_order_filters(search=str(order_id))

        self.assertIn("$or", filters)
        self.assertIn({"_id": order_id}, filters["$or"])

    def test_combines_status_category_and_date_range(self):
        filters = build_order_filters(
            status="Pagado",
            category="Anime",
            start_date="2026-06-01",
            end_date="2026-06-30",
        )

        self.assertIn("$and", filters)
        self.assertIn({"status": "Pagado"}, filters["$and"])
        self.assertTrue(
            any(condition.get("items.category") for condition in filters["$and"])
        )
        self.assertTrue(
            any(condition.get("created_at") for condition in filters["$and"])
        )


if __name__ == "__main__":
    unittest.main()
