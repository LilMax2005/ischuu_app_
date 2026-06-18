from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bson import ObjectId
from fastapi import HTTPException

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")

from app.backend.services.cart import enrich_cart_items, normalize_cart_items  # noqa: E402
from app.backend.services.checkout import CheckoutConflictError, reserve_stock  # noqa: E402


def update_result(*, matched: int = 1, modified: int = 1):
    return SimpleNamespace(matched_count=matched, modified_count=modified)


class CartTests(unittest.IsolatedAsyncioTestCase):
    def test_empty_cart_has_clear_error(self):
        with self.assertRaises(HTTPException) as context:
            normalize_cart_items([])
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "El carrito está vacío")

    def test_duplicate_products_are_consolidated(self):
        product_id = str(ObjectId())
        result = normalize_cart_items(
            [
                {"product_id": product_id, "quantity": 2},
                {"product_id": product_id, "quantity": 3},
            ]
        )
        self.assertEqual(result, [{"product_id": product_id, "quantity": 5}])

    async def test_insufficient_stock_has_product_and_quantities(self):
        product_id = ObjectId()
        database = SimpleNamespace(
            products=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={"_id": product_id, "name": "Blind Box", "stock": 1, "price": 9_990}
                )
            )
        )
        with self.assertRaises(HTTPException) as context:
            await enrich_cart_items(database, [{"product_id": str(product_id), "quantity": 2}])
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("Disponible: 1", context.exception.detail)
        self.assertIn("solicitado: 2", context.exception.detail)

    async def test_stock_is_decremented_with_gte_condition(self):
        product_id = ObjectId()
        update_one = AsyncMock(return_value=update_result())
        database = SimpleNamespace(products=SimpleNamespace(update_one=update_one))
        await reserve_stock(
            database,
            [{"product_id": str(product_id), "name": "Blind Box", "quantity": 2}],
        )
        update_one.assert_awaited_once_with(
            {"_id": product_id, "stock": {"$gte": 2}},
            {"$inc": {"stock": -2}},
        )

    async def test_partial_stock_reservation_is_rolled_back(self):
        first_id = ObjectId()
        second_id = ObjectId()
        update_one = AsyncMock(
            side_effect=[
                update_result(),
                update_result(matched=0, modified=0),
                update_result(),
            ]
        )
        database = SimpleNamespace(products=SimpleNamespace(update_one=update_one))
        with self.assertRaises(CheckoutConflictError):
            await reserve_stock(
                database,
                [
                    {"product_id": str(first_id), "name": "A", "quantity": 1},
                    {"product_id": str(second_id), "name": "B", "quantity": 1},
                ],
            )
        self.assertEqual(update_one.await_count, 3)
        self.assertEqual(
            update_one.await_args_list[-1].args,
            ({"_id": first_id}, {"$inc": {"stock": 1}}),
        )


if __name__ == "__main__":
    unittest.main()
