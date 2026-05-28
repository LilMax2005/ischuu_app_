from __future__ import annotations

import httpx


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def set_token(self, token: str | None) -> None:
        self.token = token or None

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def login(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": email, "password": password},
            )
            response.raise_for_status()
            return response.json()

    async def register(self, name: str, email: str, password: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/register",
                json={"name": name, "email": email, "password": password},
            )
            response.raise_for_status()
            return response.json()

    async def get_me(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_products(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/products")
            response.raise_for_status()
            return response.json()

    async def get_orders(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/orders",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def quote_cart_payment(
        self,
        items: list[dict],
        use_points: bool = False,
        requested_points: int | None = None,
    ) -> dict:
        payload = {"items": items, "use_points": use_points}
        if requested_points is not None:
            payload["requested_points"] = requested_points

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/payments/webpay/quote",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def create_cart_payment(
        self,
        items: list[dict],
        use_points: bool = False,
        requested_points: int | None = None,
    ) -> dict:
        payload = {"items": items, "use_points": use_points}
        if requested_points is not None:
            payload["requested_points"] = requested_points

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/payments/webpay/cart",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_payment_status(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/payments/webpay/status/{token}",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_get_users(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/users",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_get_products(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/products",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_get_orders(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/orders",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_stock(
            self,
            product_id: str,
            operation: str,
            quantity: int | None = None,
            stock: int | None = None,
    ) -> dict:
        payload = {"operation": operation}

        if quantity is not None:
            payload["quantity"] = quantity

        if stock is not None:
            payload["stock"] = stock

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/products/{product_id}/stock",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_order_status(
            self,
            order_id: str,
            status: str,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/orders/{order_id}/status",
                json={"status": status},
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_user(
            self,
            user_id: str,
            is_active: bool,
            is_admin: bool,
            points: int,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/users/{user_id}",
                json={
                    "is_active": is_active,
                    "is_admin": is_admin,
                    "points": points,
                },
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()