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
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Modèles Gemini de secours en cas de saturation ou spike temporaire
GEMINI_FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]

def _format_ai_error(e: httpx.HTTPStatusError) -> str:
    """Traduit les erreurs HTTP de l'API IA en messages clairs et professionnels."""
    code = e.response.status_code
    if code == 503:
        return "Le modèle d'intelligence artificielle subit une forte affluence temporaire. Veuillez patienter quelques secondes et réessayer."
    if code == 429:
        return "Le quota de requêtes vers le service IA est temporairement dépassé. Veuillez patienter un instant."
    if code in (401, 403):
        return "La clé API du service IA est invalide ou expirée. Veuillez vérifier le fichier .env."
    if code == 404:
        return "Le modèle d'intelligence artificielle configuré est temporairement indisponible."

    try:
        data = e.response.json()
        if "error" in data and isinstance(data["error"], dict) and "message" in data["error"]:
            msg = data["error"]["message"]
            if "high demand" in msg.lower() or "overloaded" in msg.lower() or "unavailable" in msg.lower():
                return "Le modèle d'intelligence artificielle subit une forte affluence temporaire. Veuillez patienter quelques secondes et réessayer."
            return f"Erreur IA : {msg}"
    except Exception:
        pass

    return f"Erreur du fournisseur IA (code {code}). Veuillez réessayer."


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

# ── Prompt systeme (format simple — existant) ──────────────────────────
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

# ── Prompt systeme (format structuré — paragraphes + tableaux) ─────────
SYSTEM_PROMPT_STRUCTURED = """Tu es un assistant juridique spécialisé en droit du travail et en rédaction de clauses contractuelles RH.

Tu aides les responsables RH à rédiger des clauses contractuelles professionnelles, claires et directement utilisables dans un contrat de travail.

RÈGLES STRICTES :
1. Le texte que tu produis est une PROPOSITION à valider par un professionnel.
2. Adapte le contenu à la demande spécifique du RH.
3. N'invente PAS de références légales précises si tu n'es pas certain de leur exactitude.
4. Ne présente JAMAIS le résultat comme une garantie juridique.
5. Rédige en français professionnel, clair et structuré.
6. Utilise un langage juridique clair et accessible.
7. Conserve EXACTEMENT les données fournies par le RH (montants, pourcentages, dates, conditions).
8. N'invente PAS de montants, pourcentages, dates ou conditions qui ne sont pas fournis.

FORMAT DE RÉPONSE :
Tu dois déterminer le meilleur format selon la demande :
- "paragraph" : clause narrative classique sous forme de texte.
- "table" : contenu principalement composé d'un tableau structuré.
- "mixed" : introduction/conclusion sous forme de paragraphes + tableau au milieu.

Tu dois TOUJOURS répondre au format JSON suivant, sans texte avant ni après :
{
  "type": "paragraph" | "table" | "mixed",
  "title": "Titre court et descriptif de la clause",
  "category": "Catégorie suggérée (ex: Télétravail, Confidentialité, Non-concurrence, Rémunération, Congés, etc.)",
  "blocks": [
    {
      "type": "paragraph",
      "content": "Texte du paragraphe..."
    },
    {
      "type": "table",
      "headers": ["Colonne 1", "Colonne 2", "Colonne 3"],
      "rows": [
        ["Valeur 1", "Valeur 2", "Valeur 3"],
        ["Valeur 4", "Valeur 5", "Valeur 6"]
      ]
    }
  ]
}

RÈGLES POUR LE FORMAT :
- Utilise "paragraph" quand le contenu est purement narratif (confidentialité, non-concurrence, etc.).
- Utilise "table" ou "mixed" quand les informations se prêtent naturellement à un tableau (grilles de salaires, primes, horaires, barèmes, etc.).
- Pour "mixed", place les paragraphes d'introduction AVANT le tableau et les paragraphes de conclusion APRÈS.
- Chaque bloc "table" DOIT avoir "headers" (liste de chaînes) et "rows" (liste de listes de chaînes).
- Le nombre de colonnes dans chaque ligne de "rows" DOIT correspondre au nombre de "headers".
- Tu peux avoir plusieurs blocs dans "blocks" (plusieurs paragraphes, plusieurs tableaux si nécessaire)."""


def is_configured() -> bool:
    """Verifie que le service IA est correctement configure."""
    cfg = get_config()
    return bool(cfg["api_key"])


# ── Appels aux fournisseurs (format simple — existant) ─────────────────

def _call_gemini(user_prompt: str, cfg: Dict[str, Any]) -> dict:
    """Appel a l'API Google Gemini avec retries et modèle de secours en cas de 503/429."""
    configured_model = cfg.get("model") or "gemini-3.7-flash"
    models_to_try = [configured_model] + [m for m in GEMINI_FALLBACK_MODELS if m != configured_model]

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

    last_exc = None
    with httpx.Client(timeout=cfg["timeout"]) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={cfg['api_key']}"
            for attempt in range(2):
                try:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
                except httpx.HTTPStatusError as e:
                    last_exc = e
                    if e.response.status_code in (503, 429):
                        logger.warning(
                            "[AI-Gemini] Modèle %s saturé (HTTP %s), essai %d/2...",
                            model, e.response.status_code, attempt + 1
                        )
                        time.sleep(1.0)
                        continue
                    raise
                except httpx.TimeoutException as e:
                    last_exc = e
                    logger.warning("[AI-Gemini] Timeout sur %s, modèle suivant...", model)
                    break
                except Exception as e:
                    last_exc = e
                    break

    if last_exc:
        raise last_exc
    raise RuntimeError("Impossible de joindre le fournisseur IA.")



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
        raise RuntimeError(_format_ai_error(e))
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


# ═══════════════════════════════════════════════════════════════════════
# GÉNÉRATION STRUCTURÉE (Paragraphes + Tableaux)
# ═══════════════════════════════════════════════════════════════════════

def _call_gemini_structured(user_prompt: str, cfg: Dict[str, Any]) -> dict:
    """Appel a l'API Google Gemini avec le prompt structuré, retries et modèles de secours."""
    configured_model = cfg.get("model") or "gemini-3.7-flash"
    models_to_try = [configured_model] + [m for m in GEMINI_FALLBACK_MODELS if m != configured_model]

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT_STRUCTURED}\n\nDemande du RH :\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        }
    }

    last_exc = None
    with httpx.Client(timeout=cfg["timeout"]) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={cfg['api_key']}"
            for attempt in range(2):
                try:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
                except httpx.HTTPStatusError as e:
                    last_exc = e
                    if e.response.status_code in (503, 429):
                        logger.warning(
                            "[AI-Gemini-Structured] Modèle %s saturé (HTTP %s), essai %d/2...",
                            model, e.response.status_code, attempt + 1
                        )
                        time.sleep(1.0)
                        continue
                    raise
                except httpx.TimeoutException as e:
                    last_exc = e
                    logger.warning("[AI-Gemini-Structured] Timeout sur %s, modèle suivant...", model)
                    break
                except Exception as e:
                    last_exc = e
                    break

    if last_exc:
        raise last_exc
    raise RuntimeError("Impossible de joindre le fournisseur IA.")


def _call_openai_compatible_structured(user_prompt: str, cfg: Dict[str, Any], base_url: str) -> dict:
    """Appel a une API compatible OpenAI avec le prompt structuré."""
    url = f"{base_url.rstrip('/')}/chat/completions"

    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_STRUCTURED},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
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


# Registre des fournisseurs (format structuré)
_PROVIDERS_STRUCTURED = {
    "gemini": _call_gemini_structured,
    "openai": lambda prompt, cfg: _call_openai_compatible_structured(prompt, cfg, "https://api.openai.com/v1"),
    "grok": lambda prompt, cfg: _call_openai_compatible_structured(prompt, cfg, cfg.get("base_url") or "https://api.x.ai/v1"),
}


def _validate_block(block: dict) -> bool:
    """Valide un bloc individuel (paragraph ou table)."""
    if not isinstance(block, dict):
        return False
    block_type = block.get("type")
    if block_type == "paragraph":
        return isinstance(block.get("content"), str) and len(block["content"].strip()) > 0
    elif block_type == "table":
        headers = block.get("headers")
        rows = block.get("rows")
        if not isinstance(headers, list) or len(headers) == 0:
            return False
        if not isinstance(rows, list) or len(rows) == 0:
            return False
        col_count = len(headers)
        for row in rows:
            if not isinstance(row, list) or len(row) != col_count:
                return False
        return True
    return False


def _validate_structured_result(result: dict) -> bool:
    """Valide la structure complète d'un résultat IA structuré."""
    if not isinstance(result, dict):
        return False
    if result.get("type") not in ("paragraph", "table", "mixed"):
        return False
    if not isinstance(result.get("title"), str) or not result["title"].strip():
        return False
    blocks = result.get("blocks")
    if not isinstance(blocks, list) or len(blocks) == 0:
        return False
    return all(_validate_block(b) for b in blocks)


def _fallback_to_structured(result: dict) -> dict:
    """
    Convertit un résultat au format simple (title/content/category)
    vers le format structuré (paragraph) pour assurer la rétrocompatibilité.
    """
    return {
        "type": "paragraph",
        "title": result.get("title", "").strip(),
        "category": result.get("category", "Général").strip(),
        "blocks": [
            {
                "type": "paragraph",
                "content": result.get("content", "").strip(),
            }
        ],
    }


def generate_structured_clause(prompt: str) -> dict:
    """
    Génère une clause contractuelle structurée (paragraphes + tableaux).
    Retourne un dict avec type, title, category et blocks.
    Fallback automatique vers le format simple si l'IA ne retourne pas
    un JSON structuré valide.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Le prompt ne peut pas être vide.")

    cfg = get_config()
    if not cfg["api_key"]:
        raise RuntimeError(
            "Le service IA n'est pas configuré. "
            "Veuillez renseigner AI_API_KEY dans le fichier .env."
        )

    provider_fn = _PROVIDERS_STRUCTURED.get(cfg["provider"])
    if not provider_fn:
        raise RuntimeError(
            f"Fournisseur IA '{cfg['provider']}' non supporté. "
            f"Fournisseurs disponibles : {', '.join(_PROVIDERS_STRUCTURED.keys())}"
        )

    try:
        result = provider_fn(prompt.strip(), cfg)
    except httpx.TimeoutException:
        logger.error("[AI-Structured] Timeout lors de l'appel au fournisseur %s", cfg["provider"])
        raise RuntimeError("Le fournisseur IA n'a pas répondu dans le délai imparti. Veuillez réessayer.")
    except httpx.HTTPStatusError as e:
        logger.error("[AI-Structured] Erreur HTTP %s : %s", e.response.status_code, e.response.text[:300])
        raise RuntimeError(_format_ai_error(e))
    except json.JSONDecodeError:
        logger.error("[AI-Structured] Réponse IA non parseable en JSON")
        raise RuntimeError("La réponse de l'IA n'est pas au format attendu. Veuillez reformuler votre demande.")
    except Exception as e:
        logger.error("[AI-Structured] Erreur inattendue : %s", str(e))
        raise RuntimeError(f"Erreur inattendue du service IA : {str(e)}")

    if not isinstance(result, dict):
        raise RuntimeError("La réponse de l'IA n'est pas au format attendu.")

    # Si l'IA retourne l'ancien format (title/content), on fait un fallback
    if "blocks" not in result and "content" in result and "title" in result:
        logger.info("[AI-Structured] Fallback depuis le format simple vers structuré")
        return _fallback_to_structured(result)

    # Valider la structure
    if not _validate_structured_result(result):
        logger.warning("[AI-Structured] Structure invalide, tentative de fallback")
        # Tentative de récupération partielle
        if "title" in result and "blocks" in result:
            # Filtrer les blocs valides
            valid_blocks = [b for b in result.get("blocks", []) if _validate_block(b)]
            if valid_blocks:
                return {
                    "type": result.get("type", "paragraph"),
                    "title": result.get("title", "").strip(),
                    "category": result.get("category", "Général").strip(),
                    "blocks": valid_blocks,
                }
        raise RuntimeError("La réponse de l'IA n'est pas au format structuré attendu. Veuillez reformuler votre demande.")

    return {
        "type": result["type"],
        "title": result["title"].strip(),
        "category": result.get("category", "Général").strip(),
        "blocks": result["blocks"],
    }


def structured_to_plaintext(structured: dict) -> str:
    """
    Convertit un résultat structuré en texte brut lisible.
    Utilisé pour le stockage dans contenu_par_defaut (compatibilité)
    et pour l'aperçu dans la liste des articles.
    """
    parts = []
    for block in structured.get("blocks", []):
        if block["type"] == "paragraph":
            parts.append(block["content"])
        elif block["type"] == "table":
            headers = block.get("headers", [])
            rows = block.get("rows", [])
            # Format Markdown table
            parts.append("| " + " | ".join(headers) + " |")
            parts.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in rows:
                parts.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n\n".join(parts)


def parse_structured_content(content_text: Optional[str]) -> Optional[dict]:
    """
    Tente de parser le contenu d'un article comme JSON structuré.
    Retourne le dict structuré si valide, None sinon (texte brut classique).
    """
    if not content_text or not content_text.strip():
        return None
    text = content_text.strip()
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("blocks"), list) and len(data["blocks"]) > 0:
            if all(_validate_block(b) for b in data["blocks"]):
                return data
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return None

