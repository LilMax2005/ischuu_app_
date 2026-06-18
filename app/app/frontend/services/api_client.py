from __future__ import annotations

from pathlib import Path

import httpx


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

        self.timeout = httpx.Timeout(
            timeout=45.0,
            connect=20.0,
            read=45.0,
            write=20.0,
            pool=20.0,
        )

    def set_token(self, token: str | None) -> None:
        self.token = token

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    # =========================
    # AUTH
    # =========================

    async def login(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                data={
                    "username": email,
                    "password": password,
                },
            )
            response.raise_for_status()
            return response.json()

    async def register(self, name: str, email: str, password: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "name": name,
                    "email": email,
                    "password": password,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_me(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # RECUPERACIÓN CONTRASEÑA
    # =========================

    async def forgot_password(self, email: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/password/forgot",
                json={
                    "email": email,
                },
            )
            response.raise_for_status()
            return response.json()

    async def reset_password(self, token: str, new_password: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/password/reset",
                json={
                    "token": token,
                    "new_password": new_password,
                },
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # PRODUCTOS
    # =========================

    async def get_products(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/products"
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # PEDIDOS
    # =========================

    async def get_orders(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/orders",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_notification_config(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/notifications/config"
            )
            response.raise_for_status()
            return response.json()

    async def update_notification_preference(self, enabled: bool) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/auth/me/notifications",
                json={"enabled": enabled},
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # WEBPAY
    # =========================

    async def quote_cart_payment(
        self,
        items: list[dict],
        use_points: bool = False,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/payments/webpay/quote",
                json={
                    "items": items,
                    "use_points": use_points,
                },
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def create_cart_payment(
            self,
            items: list[dict],
            use_points: bool = False,
            shipping_address: dict | None = None,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/payments/webpay/cart",
                json={
                    "items": items,
                    "use_points": use_points,
                    "shipping_address": shipping_address or {},
                },
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()


    async def get_payment_status(self, token: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/payments/webpay/status/{token}",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def update_my_shipping_address(self, shipping_address: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/auth/me/shipping-address",
                json=shipping_address,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()
    # =========================
    # ADMIN - ESTADÍSTICAS
    # =========================

    async def admin_get_summary(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/summary",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # ADMIN - USUARIOS
    # =========================

    async def admin_get_users(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/users",
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
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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

    # =========================
    # ADMIN - PRODUCTOS
    # =========================

    async def admin_get_products(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/products",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_create_product(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/admin/products",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_product(
        self,
        product_id: str,
        payload: dict,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/products/{product_id}",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_delete_product(self, product_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/admin/products/{product_id}",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_upload_product_image(self, image_path: str) -> dict:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"No existe la imagen: {image_path}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with path.open("rb") as file:
                response = await client.post(
                    f"{self.base_url}/api/v1/admin/products/upload-image",
                    files={
                        "file": (
                            path.name,
                            file,
                            "application/octet-stream",
                        )
                    },
                    headers={
                        "Authorization": f"Bearer {self.token}"
                    }
                    if self.token
                    else {},
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
        payload = {
            "operation": operation,
        }

        if quantity is not None:
            payload["quantity"] = quantity

        if stock is not None:
            payload["stock"] = stock

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/products/{product_id}/stock",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    # =========================
    # ADMIN - PEDIDOS
    # =========================

    async def admin_get_orders(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/orders",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_order_status(
        self,
        order_id: str,
        status: str,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/orders/{order_id}/status",
                json={
                    "status": status,
                },
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_export_orders(self, output_path: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/orders/export",
                headers=self.headers(),
            )
            response.raise_for_status()

        Path(output_path).write_bytes(response.content)

        return output_path

    # =========================
    # ADMIN - REDES SOCIALES
    # =========================

    async def admin_get_settings(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/settings",
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()

    async def admin_update_settings(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/admin/settings",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            return response.json()
