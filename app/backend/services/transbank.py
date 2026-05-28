from __future__ import annotations

from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction


def tbk_opts() -> WebpayOptions:
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
    response = Transaction(tbk_opts()).create(
        buy_order,
        session_id,
        amount,
        return_url,
    )
    return {
        "token": response["token"],
        "url": response["url"],
        "redirect_url": f"{response['url']}?token_ws={response['token']}",
    }


def commit_transaction(token: str) -> dict:
    return Transaction(tbk_opts()).commit(token)
