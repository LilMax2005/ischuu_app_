from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(
        os.getenv("SMTP_HOST")
        and os.getenv("SMTP_USER")
        and os.getenv("SMTP_PASSWORD")
    )


def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
    if not to:
        return False

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", user)

    if not smtp_configured():
        print("SMTP no configurado. Correo simulado:")
        print("PARA:", to)
        print("ASUNTO:", subject)
        print(body)

        if html_body:
            print("HTML:")
            print(html_body)

        return False

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    # Versión texto plano
    msg.set_content(body)

    # Versión HTML profesional
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)

        print(f"Correo enviado correctamente a {to}")
        return True

    except Exception as exc:
        print(f"Error enviando correo SMTP: {exc}")
        return False