import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    payload = {
        "email": user.email,
        "username": user.username,
    }
    return _post_mail_service("/auth-mail/welcome", payload)


def send_password_reset_email(user, reset_code, expires_in_minutes=4):
    payload = {
        "email": user.email,
        "username": user.username,
        "resetCode": reset_code,
        "expiresInMinutes": expires_in_minutes,
    }
    return _post_mail_service("/auth-mail/password-reset", payload)


def _post_mail_service(path, payload):
    base_url = getattr(settings, "MAIL_SERVICE_URL", "http://127.0.0.1:4000").rstrip("/")

    try:
        response = requests.post(f"{base_url}{path}", json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Mail service request failed for %s", path)
        return False
