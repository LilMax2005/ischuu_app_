from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")

from app.backend.services.checkout import (  # noqa: E402
    CheckoutConflictError,
    PaymentValidationError,
    create_order_after_authorization,
    validate_authorized_transaction,
)


def result(*, matched: int = 1, modified: int = 1, inserted_id=None):
    return SimpleNamespace(
        matched_count=matched,
        modified_count=modified,
        deleted_count=matched,
        inserted_id=inserted_id or ObjectId(),
    )


def payment_fixture(product_id: ObjectId, user_id: ObjectId) -> dict:
    return {
        "_id": ObjectId(),
        "token": "token-webpay",
        "buy_order": "ISCHUU-ABC",
        "user_id": str(user_id),
        "items": [
            {
                "product_id": str(product_id),
                "name": "Blind Box",
                "category": "Anime",
                "quantity": 1,
                "price": 10_000,
                "subtotal": 10_000,
            }
        ],
        "subtotal": 10_000,
        "shipping": 3_000,
        "discount": 0,
        "total": 13_000,
        "product_amount_paid": 10_000,
        "points_to_spend": 0,
        "shipping_address": {
            "recipient": "Cliente",
            "phone": "56912345678",
            "region": "Metropolitana",
            "comuna": "Santiago",
            "street": "Alameda",
            "number": "123",
            "details": "",
        },
        "shipping_address_text": "Alameda 123, Santiago, Metropolitana",
        "order_created": False,
    }


class CheckoutTests(unittest.IsolatedAsyncioTestCase):
    def test_rejected_payment_cannot_create_order(self):
        payment = {"total": 10_000, "buy_order": "A"}
        with self.assertRaises(PaymentValidationError):
            validate_authorized_transaction(payment, {"status": "FAILED", "amount": 10_000})

    def test_amount_mismatch_cannot_create_order(self):
        payment = {"total": 10_000, "buy_order": "A"}
        with self.assertRaises(PaymentValidationError):
            validate_authorized_transaction(
                payment,
                {"status": "AUTHORIZED", "amount": 9_000, "buy_order": "A"},
            )

    async def test_existing_order_makes_callback_idempotent(self):
        existing = {"_id": ObjectId(), "webpay_token": "token-webpay"}
        database = SimpleNamespace(
            orders=SimpleNamespace(find_one=AsyncMock(return_value=existing)),
            payments=SimpleNamespace(update_one=AsyncMock()),
        )
        payment = {"token": "token-webpay", "total": 10_000, "buy_order": "A"}
        transaction = {"status": "AUTHORIZED", "amount": 10_000, "buy_order": "A"}
        created = await create_order_after_authorization(database, payment, transaction)
        self.assertIs(created, existing)
        database.payments.update_one.assert_not_awaited()

    async def test_authorized_payment_creates_paid_order_and_decrements_once(self):
        product_id = ObjectId()
        user_id = ObjectId()
        payment = payment_fixture(product_id, user_id)
        transaction = {
            "status": "AUTHORIZED",
            "amount": 13_000,
            "buy_order": "ISCHUU-ABC",
            "authorization_code": "123456",
        }
        order_id = ObjectId()
        database = SimpleNamespace(
            orders=SimpleNamespace(
                find_one=AsyncMock(return_value=None),
                insert_one=AsyncMock(return_value=result(inserted_id=order_id)),
                delete_one=AsyncMock(return_value=result()),
            ),
            payments=SimpleNamespace(update_one=AsyncMock(side_effect=[result(), result()])),
            products=SimpleNamespace(update_one=AsyncMock(return_value=result())),
            users=SimpleNamespace(
                find_one=AsyncMock(
                    return_value={"_id": user_id, "email": "user@example.com", "name": "User", "points": 0}
                ),
                update_one=AsyncMock(return_value=result()),
            ),
        )
        with patch(
            "app.backend.services.checkout.send_order_status_push",
            new=AsyncMock(return_value={"sent": True}),
        ):
            order = await create_order_after_authorization(database, payment, transaction)

        self.assertEqual(order["_id"], order_id)
        self.assertEqual(order["status"], "Pagado")
        self.assertEqual(order["payment_status"], "paid")
        self.assertEqual(database.products.update_one.await_count, 1)
        self.assertEqual(database.orders.insert_one.await_count, 1)

    async def test_concurrent_callback_does_not_create_second_order(self):
        product_id = ObjectId()
        user_id = ObjectId()
        payment = payment_fixture(product_id, user_id)
        transaction = {"status": "AUTHORIZED", "amount": 13_000, "buy_order": "ISCHUU-ABC"}
        database = SimpleNamespace(
            orders=SimpleNamespace(find_one=AsyncMock(side_effect=[None, None])),
            payments=SimpleNamespace(update_one=AsyncMock(return_value=result(matched=1, modified=0))),
        )
        with self.assertRaises(CheckoutConflictError):
            await create_order_after_authorization(database, payment, transaction)


if __name__ == "__main__":
    unittest.main()
