from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

from app.backend.routers.notifications import test_notification


class NotificationEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_error_is_reported(self):
        user = {"_id": ObjectId()}
        with patch(
            "app.backend.routers.notifications.send_order_status_push",
            new=AsyncMock(return_value={"sent": False, "reason": "provider_error"}),
        ):
            with self.assertRaises(HTTPException) as context:
                await test_notification(user)
        self.assertEqual(context.exception.status_code, 503)

    async def test_unlinked_phone_is_reported(self):
        user = {"_id": ObjectId()}
        with patch(
            "app.backend.routers.notifications.send_order_status_push",
            new=AsyncMock(return_value={"sent": True, "recipients": 0}),
        ):
            with self.assertRaises(HTTPException) as context:
                await test_notification(user)
        self.assertEqual(context.exception.status_code, 409)

    async def test_linked_phone_receives_test(self):
        user = {"_id": ObjectId()}
        with patch(
            "app.backend.routers.notifications.send_order_status_push",
            new=AsyncMock(return_value={"sent": True, "recipients": 1, "notification_id": "n1"}),
        ):
            result = await test_notification(user)
        self.assertEqual(result["recipients"], 1)
        self.assertEqual(result["message"], "Notificación de prueba enviada")


if __name__ == "__main__":
    unittest.main()
