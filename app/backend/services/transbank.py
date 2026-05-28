from __future__ import annotations

from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

from app.backend.core.config import settings


def tbk_options() -> WebpayOptions:
    env = str(getattr(settings, "tbk_env", "integration")).lower().strip()

    if env == "production":
        return WebpayOptions(
            commerce_code=settings.tbk_commerce_code,
            api_key=settings.tbk_api_key,
            integration_type=IntegrationType.LIVE,
        )

    return WebpayOptions(
        commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS,
        api_key=IntegrationApiKeys.WEBPAY,
        integration_type=IntegrationType.TEST,
    )


def create_webpay_transaction(
    buy_order: str,
    session_id: str,
    amount: int,
    return_url: str,
) -> dict:
    response = Transaction(tbk_options()).create(
        buy_order,
        session_id,
        amount,
        return_url,
    )

    print("WEBPAY CREATE RESPONSE:", response)

    return {
        "token": response["token"],
        "url": response["url"],
    }


def commit_transaction(token: str) -> dict:
    response = Transaction(tbk_options()).commit(token)
    print("WEBPAY COMMIT RESPONSE:", response)
    return response