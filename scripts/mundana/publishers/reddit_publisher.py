"""
reddit_publisher.py — Publica en Reddit via PRAW (Python Reddit API Wrapper).

Variables de entorno requeridas:
  REDDIT_CLIENT_ID     — app client ID (reddit.com/prefs/apps)
  REDDIT_CLIENT_SECRET — app client secret
  REDDIT_USERNAME      — usuario de la cuenta
  REDDIT_PASSWORD      — contraseña de la cuenta
  REDDIT_SUBREDDIT     — subreddit destino (default: astrology)

Tipo de post: texto (self post) con título + cuerpo.
Reddit no tiene límite estricto de chars en el cuerpo (40.000 aprox).

Requiere: pip install praw
"""

from __future__ import annotations

import os


REDDIT_SUBREDDIT_DEFAULT = "astrology"

# Subreddits relevantes para rotación futura:
#   r/astrology       — 1.2M miembros, general
#   r/mundaneastrology — nicho técnico
#   r/AskAstrologers  — preguntas (requiere formato diferente)


def publish_reddit(text: str, title: str | None = None) -> dict:
    """
    Publica un self post en Reddit.

    Retorna: { 'status': 'published' | 'error', 'url': str | None, 'detail': str }
    """
    client_id     = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    username      = os.environ.get("REDDIT_USERNAME")
    password      = os.environ.get("REDDIT_PASSWORD")
    subreddit     = os.environ.get("REDDIT_SUBREDDIT", REDDIT_SUBREDDIT_DEFAULT)

    if not all([client_id, client_secret, username, password]):
        return {
            "status": "error",
            "url": None,
            "detail": "REDDIT_CLIENT_ID / SECRET / USERNAME / PASSWORD no configurados",
        }

    # Título por defecto si no se proporciona
    if not title:
        # Extraer primera oración como título (máx 300 chars para Reddit)
        first_sentence = text.split("—")[0].split(".")[0].strip()
        title = first_sentence[:297] + "..." if len(first_sentence) > 300 else first_sentence

    try:
        import praw  # type: ignore

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=f"AbuOracle/1.0 (by u/{username})",
        )

        sub  = reddit.subreddit(subreddit)
        post = sub.submit(title=title, selftext=text)

        url = f"https://reddit.com{post.permalink}"
        print(f"[reddit] Publicado OK — {url}")
        return {"status": "published", "url": url, "detail": "OK"}

    except ImportError:
        return {
            "status": "error",
            "url": None,
            "detail": "praw no instalado — ejecutar: pip install praw",
        }
    except Exception as e:
        print(f"[reddit] Excepción: {e}")
        return {"status": "error", "url": None, "detail": str(e)}
