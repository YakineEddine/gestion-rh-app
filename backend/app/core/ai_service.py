"""
Service IA centralise pour la generation de clauses contractuelles.

Fournisseurs supportes :
  - gemini   (Google Gemini / Generative AI)
  - openai   (OpenAI GPT)
  - grok     (xAI Grok — compatible OpenAI)

Le fournisseur est configurable dynamiquement via le fichier .env :
  AI_PROVIDER=grok
  AI_API_KEY=votre_cle_api
  AI_MODEL=grok-4.3
  AI_BASE_URL=https://api.x.ai/v1
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Chemin absolu vers le fichier .env du backend
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

def _reload_env():
    """Recharge le fichier .env pour prendre en compte les modifications en direct."""
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        load_dotenv(override=True)

def get_config() -> Dict[str, str]:
    """Recupere la configuration IA a jour."""
    _reload_env()
    provider = os.getenv("AI_PROVIDER", "grok").strip().lower()
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "grok-2-latest").strip()
    base_url = os.getenv("AI_BASE_URL", "https://api.x.ai/v1").strip()
    timeout = int(os.getenv("AI_TIMEOUT", "35").strip())

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "timeout": timeout,
    }

# ── Prompt systeme ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un assistant juridique spécialisé en droit du travail.
Tu aides les responsables RH à rédiger des clauses contractuelles professionnelles.

Règles STRICTES à respecter :
1. Le texte que tu produis est une PROPOSITION à valider par un professionnel.
2. Adapte le contenu à la demande spécifique du RH.
3. N'invente PAS de références légales précises si tu n'es pas certain de leur exactitude.
4. Ne présente JAMAIS le résultat comme une garantie juridique.
5. Rédige en français professionnel, clair et structuré.
6. Le contenu doit être directement utilisable dans un contrat de travail.

Tu dois TOUJOURS répondre au format JSON suivant, sans texte avant ni après :
{
  "title": "Titre court et descriptif de la clause",
  "content": "Contenu complet de la clause, bien structuré et prêt à être inséré dans un contrat",
  "category": "Catégorie suggérée (ex: Télétravail, Confidentialité, Non-concurrence, Propriété intellectuelle, Durée du travail, Rémunération, Congés, etc.)"
}"""


def is_configured() -> bool:
    """Verifie que le service IA est correctement configure."""
    cfg = get_config()
    return bool(cfg["api_key"])


def _call_gemini(user_prompt: str, cfg: Dict[str, Any]) -> dict:
    """Appel a l'API Google Gemini (Generative AI REST API)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model']}:generateContent?key={cfg['api_key']}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\nDemande du RH :\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        }
    }

    with httpx.Client(timeout=cfg["timeout"]) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def _call_openai_compatible(user_prompt: str, cfg: Dict[str, Any], base_url: str) -> dict:
    """
    Appel a une API compatible OpenAI (OpenAI, xAI/Grok, etc.).
    """
    url = f"{base_url.rstrip('/')}/chat/completions"

    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=cfg["timeout"]) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()

    data = response.json()
    text = data["choices"][0]["message"]["content"]

    # Nettoyer les eventuels blocs markdown ```json ... ```
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    return json.loads(cleaned)


def _call_openai(user_prompt: str, cfg: Dict[str, Any]) -> dict:
    """Appel a l'API OpenAI (GPT)."""
    return _call_openai_compatible(user_prompt, cfg, base_url="https://api.openai.com/v1")


def _call_grok(user_prompt: str, cfg: Dict[str, Any]) -> dict:
    """Appel a l'API xAI / Grok (compatible OpenAI)."""
    base = cfg.get("base_url") or "https://api.x.ai/v1"
    return _call_openai_compatible(user_prompt, cfg, base_url=base)


# Registre des fournisseurs
_PROVIDERS = {
    "gemini": _call_gemini,
    "openai": _call_openai,
    "grok": _call_grok,
}


def generate_clause(prompt: str) -> dict:
    """
    Point d'entree principal : genere une clause contractuelle a partir
    d'un prompt en langage naturel.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Le prompt ne peut pas être vide.")

    cfg = get_config()
    if not cfg["api_key"]:
        raise RuntimeError(
            "Le service IA n'est pas configuré. "
            "Veuillez renseigner AI_API_KEY dans le fichier .env."
        )

    provider_fn = _PROVIDERS.get(cfg["provider"])
    if not provider_fn:
        raise RuntimeError(
            f"Fournisseur IA '{cfg['provider']}' non supporté. "
            f"Fournisseurs disponibles : {', '.join(_PROVIDERS.keys())}"
        )

    try:
        result = provider_fn(prompt.strip(), cfg)
    except httpx.TimeoutException:
        logger.error("[AI] Timeout lors de l'appel au fournisseur %s", cfg["provider"])
        raise RuntimeError("Le fournisseur IA n'a pas répondu dans le délai imparti. Veuillez réessayer.")
    except httpx.HTTPStatusError as e:
        logger.error("[AI] Erreur HTTP %s : %s", e.response.status_code, e.response.text[:300])
        err_msg = e.response.text[:200]
        raise RuntimeError(f"Erreur du fournisseur IA (HTTP {e.response.status_code}) : {err_msg}")
    except json.JSONDecodeError:
        logger.error("[AI] Réponse IA non parseable en JSON")
        raise RuntimeError("La réponse de l'IA n'est pas au format attendu. Veuillez reformuler votre demande.")
    except Exception as e:
        logger.error("[AI] Erreur inattendue : %s", str(e))
        raise RuntimeError(f"Erreur inattendue du service IA : {str(e)}")

    if not isinstance(result, dict):
        raise RuntimeError("La réponse de l'IA n'est pas au format attendu.")
    if "title" not in result or "content" not in result:
        raise RuntimeError("La réponse de l'IA est incomplète (titre ou contenu manquant).")

    return {
        "title": result.get("title", "").strip(),
        "content": result.get("content", "").strip(),
        "category": result.get("category", "Général").strip(),
    }
