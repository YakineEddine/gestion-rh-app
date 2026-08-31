"""
Service de vérification Google reCAPTCHA v2.
"""
import logging
import os
from typing import Tuple
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("recaptcha_service")

RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "").strip()

# Clé de test officielle Google reCAPTCHA v2 (toujours valide pour les tests automatisés)
GOOGLE_TEST_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
GOOGLE_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def get_secret_key() -> str:
    return RECAPTCHA_SECRET_KEY or GOOGLE_TEST_SECRET_KEY


def verify_recaptcha_token(token: str, remote_ip: str = None) -> Tuple[bool, str]:
    """
    Vérifie le token reCAPTCHA auprès de l'API Google.
    Retourne (success: bool, error_reason: str).
    error_reason: "" | "missing" | "invalid" | "timeout-or-duplicate"
    """
    if not token or not token.strip():
        return False, "missing"

    secret_key = get_secret_key()

    try:
        data = {
            "secret": secret_key,
            "response": token.strip(),
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(GOOGLE_VERIFY_URL, data=data)
            if resp.status_code != 200:
                logger.warning(f"reCAPTCHA API HTTP status {resp.status_code}")
                return False, "invalid"

            res_json = resp.json()
            is_success = res_json.get("success", False)
            if is_success:
                return True, ""

            error_codes = res_json.get("error-codes", [])
            logger.info(f"reCAPTCHA verification failed: {error_codes}")

            if "timeout-or-duplicate" in error_codes:
                return False, "timeout-or-duplicate"
            return False, "invalid"

    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API reCAPTCHA : {e}")
        return False, "invalid"
