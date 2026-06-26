from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import HTTPException

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"

from app.backend.dependencies import get_current_active_user, get_current_admin  # noqa: E402
from app.backend.routers.auth import login, refresh_session, register  # noqa: E402
from app.backend.schemas import RefreshTokenPayload, UserCreate  # noqa: E402


class SecurityDependencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_inactive_user_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            await get_current_active_user({"is_active": False})
        self.assertEqual(context.exception.status_code, 403)

    async def test_normal_user_cannot_become_admin_by_email(self):
        user = {"email": "admin@ischuu.cl", "is_active": True, "is_admin": False}
        with self.assertRaises(HTTPException) as context:
            await get_current_admin(user)
        self.assertEqual(context.exception.status_code, 403)

    async def test_admin_flag_is_required_and_accepted(self):
        user = {"email": "owner@example.com", "is_active": True, "is_admin": True}
        self.assertIs(await get_current_admin(user), user)

    async def test_bearer_token_is_decoded(self):
        expected = {"is_active": True, "is_admin": False}
        with patch("app.backend.dependencies.decode_token", new=AsyncMock(return_value=expected)) as decoder:
            from app.backend.dependencies import get_current_user

            result = await get_current_user("Bearer abc")
        self.assertIs(result, expected)
        decoder.assert_awaited_once_with("abc")

    async def test_inactive_user_cannot_log_in(self):
        form = SimpleNamespace(username="inactive@example.com", password="secret")
        user = {"email": form.username, "is_active": False}
        with patch("app.backend.routers.auth.authenticate_user", new=AsyncMock(return_value=user)):
            with self.assertRaises(HTTPException) as context:
                await login(form)
        self.assertEqual(context.exception.status_code, 403)

    async def test_registration_creates_normal_active_user(self):
        inserted_id = ObjectId()
        insert_one = AsyncMock(return_value=SimpleNamespace(inserted_id=inserted_id))
        payload = UserCreate(name="Cliente", email="client@example.com", password="secret1")
        with (
            patch("app.backend.routers.auth.get_user_by_email", new=AsyncMock(return_value=None)),
            patch("app.backend.routers.auth.get_password_hash", return_value="hashed"),
            patch(
                "app.backend.routers.auth.db",
                new=SimpleNamespace(users=SimpleNamespace(insert_one=insert_one)),
            ),
        ):
            created = await register(payload)
        document = insert_one.await_args.args[0]
        self.assertEqual(created["id"], str(inserted_id))
        self.assertTrue(document["is_active"])
        self.assertFalse(document["is_admin"])
        self.assertEqual(document["points"], 0)

    async def test_refresh_token_renews_mobile_session(self):
        user = {
            "_id": ObjectId(),
            "email": "client@example.com",
            "name": "Cliente",
            "is_active": True,
        }
        payload = RefreshTokenPayload(refresh_token="x" * 20)
        with patch(
            "app.backend.routers.auth.decode_refresh_token",
            new=AsyncMock(return_value=user),
        ):
            result = await refresh_session(payload)
        self.assertTrue(result["access_token"])
        self.assertTrue(result["refresh_token"])
        self.assertEqual(result["user"]["email"], user["email"])

    async def test_inactive_user_cannot_refresh_session(self):
        user = {
            "_id": ObjectId(),
            "email": "inactive@example.com",
            "is_active": False,
        }
        payload = RefreshTokenPayload(refresh_token="x" * 20)
        with patch(
            "app.backend.routers.auth.decode_refresh_token",
            new=AsyncMock(return_value=user),
        ):
            with self.assertRaises(HTTPException) as context:
                await refresh_session(payload)
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
