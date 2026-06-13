# Middleware de autenticación JWT + quota enforcement via Firestore
# Fase: Multi-Usuario v1.0

import hmac
import os
import sys
import logging
from functools import lru_cache

from fastapi import Header, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import firebase_admin
from firebase_admin import auth, credentials, firestore

logger = logging.getLogger(__name__)

# ── Feature flags y guardrails de seguridad ─────────────────────────────────
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() == "true"
_is_cloud_run = os.environ.get("K_SERVICE") is not None  # Cloud Run setea K_SERVICE
_is_dev = os.environ.get("ENV", "production") == "development"

# Fail-closed: en Cloud Run jamás permitir AUTH deshabilitada
if _is_cloud_run and not AUTH_ENABLED:
    logger.critical("AUTH_ENABLED=false detectado en Cloud Run — abortando startup por seguridad")
    sys.exit(1)

if not AUTH_ENABLED:
    logger.warning("⚠️  AUTH_ENABLED=false — modo desarrollo local, sin autenticación real")

logger.info(
    f"[Auth] startup — AUTH_ENABLED={AUTH_ENABLED} | "
    f"ENV={os.environ.get('ENV', 'production')} | "
    f"cloud_run={_is_cloud_run}"
)

security = HTTPBearer()


# ── Inicialización Firebase Admin (singleton) ──────────────────────────────

@lru_cache(maxsize=1)
def _get_firebase_app():
    """Inicializa Firebase Admin SDK una sola vez."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "abu-oracle")

    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        logger.info(f"Firebase: usando SA key desde {cred_path}")
    else:
        # En Cloud Run con SA asignada, usa Application Default Credentials
        cred = credentials.ApplicationDefault()
        logger.info("Firebase: usando Application Default Credentials")

    return firebase_admin.initialize_app(cred, {"projectId": project_id})


def _get_firestore_client():
    _get_firebase_app()
    return firestore.client()


# ── Dependency principal ───────────────────────────────────────────────────

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Dependency de FastAPI. Uso:
        @router.get("/endpoint")
        async def endpoint(user: dict = Depends(verify_token)):
            ...

    Valida JWT de Firebase Auth y verifica quota en Firestore.
    Retorna el dict del usuario desde Firestore.
    """
    if not AUTH_ENABLED and _is_dev:
        # Dev local — retorna usuario mock, no valida nada
        return {
            "uid": "dev-local",
            "email": "dev@local",
            "plan": "genesis",
            "quota_used": 0,
            "quota_limit": 99999,
            "payment_verified": True
        }
    elif not AUTH_ENABLED:
        # AUTH_ENABLED=false sin ENV=development — fail-closed
        raise HTTPException(status_code=503, detail="Auth misconfiguration")

    token = credentials.credentials

    # 1. Verificar JWT con Firebase Auth
    try:
        _get_firebase_app()  # Garantiza que el SDK esté inicializado
        decoded = auth.verify_id_token(token)
        uid = decoded["uid"]
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Error verificando token: {e}")
        raise HTTPException(status_code=401, detail="Error de autenticación")

    # 2. Buscar usuario en Firestore
    try:
        db = _get_firestore_client()
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
    except Exception as e:
        logger.error(f"Error consultando Firestore para uid={uid}: {e}")
        raise HTTPException(status_code=503, detail="Error de base de datos")

    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="Usuario no registrado")

    user_data = user_doc.to_dict()

    if not user_data.get("payment_verified", False):
        raise HTTPException(status_code=403, detail="Pago no verificado")

    # 3. Verificar quota
    quota_used = user_data.get("quota_used", 0)
    quota_limit = user_data.get("quota_limit", 100)

    if quota_used >= quota_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Quota excedida ({quota_used}/{quota_limit})"
        )

    # 4. Incrementar quota_used (fire-and-forget, no bloquea el request)
    try:
        user_ref.update({"quota_used": firestore.Increment(1)})
    except Exception as e:
        logger.warning(f"No se pudo incrementar quota para uid={uid}: {e}")

    return user_data


# ── Service key (machine-to-machine: EuYin Agent, runtime diario) ──────────
#
# Credencial de SERVICIO, no de persona. Header: X-Abu-Service-Key.
# - Configuración: env var ABU_SERVICE_KEY (Cloud Run: desde Secret Manager).
# - Fail-closed: si ABU_SERVICE_KEY no está seteada, esta vía NO existe y todo
#   se comporta exactamente como antes (solo JWT Firebase).
# - Alcance: los endpoints de cómputo/lectura astrológica que usan
#   verify_token_or_service_key. Nunca aplicarla a rutas administrativas.
# - Rotación: cambiar el secret + la env var del consumidor (MCP/runtime).

ABU_SERVICE_KEY = os.environ.get("ABU_SERVICE_KEY", "").strip()

if ABU_SERVICE_KEY:
    logger.info("[Auth] Service key habilitada (X-Abu-Service-Key) — principal: euyin-agent")

_optional_bearer = HTTPBearer(auto_error=False)

_SERVICE_PRINCIPAL = {
    "uid": "euyin-agent",
    "email": "service@abu-oracle",
    "plan": "service",
    "quota_used": 0,
    "quota_limit": 10**9,
    "payment_verified": True,
    "service": True,
}


async def verify_token_or_service_key(
    x_abu_service_key: str | None = Header(default=None, alias="X-Abu-Service-Key"),
    x_abu_api_key: str | None = Header(default=None, alias="X-Abu-Api-Key"),
    credentials: HTTPAuthorizationCredentials | None = Security(_optional_bearer),
) -> dict:
    """
    Acepta service key (header X-Abu-Service-Key) O el JWT Firebase de siempre.
    La key se compara en tiempo constante. Sin key configurada → solo JWT.
    """
    if not AUTH_ENABLED and _is_dev:
        # Dev local — retorna usuario mock, no valida nada
        return {
            "uid": "dev-local",
            "email": "dev@local",
            "plan": "genesis",
            "quota_used": 0,
            "quota_limit": 99999,
            "payment_verified": True
        }

    if (
        ABU_SERVICE_KEY
        and x_abu_service_key
        and hmac.compare_digest(x_abu_service_key, ABU_SERVICE_KEY)
    ):
        return dict(_SERVICE_PRINCIPAL)

    if x_abu_api_key:
        db = _get_firestore_client()
        docs = list(db.collection("users").where("api_key", "==", x_abu_api_key).limit(1).stream())
        if not docs:
            raise HTTPException(status_code=401, detail="API key inválida")
        user_data = docs[0].to_dict()
        if not user_data.get("payment_verified", False):
            raise HTTPException(status_code=403, detail="Pago no verificado")
        quota_used = user_data.get("quota_used", 0)
        quota_limit = user_data.get("quota_limit", 100)
        if quota_used >= quota_limit:
            raise HTTPException(status_code=429, detail=f"Quota excedida ({quota_used}/{quota_limit})")
        try:
            docs[0].reference.update({"quota_used": firestore.Increment(1)})
        except Exception as e:
            logger.warning(f"No se pudo incrementar quota api_key: {e}")
        return user_data

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing credentials")
    return await verify_token(credentials)


# ── Dependency opcional (para rutas demo/públicas) ─────────────────────────

async def verify_token_optional(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer(auto_error=False))
) -> dict | None:
    """
    Versión opcional — no falla si no hay token.
    Útil para rutas que funcionan autenticadas o como demo.
    """
    if not AUTH_ENABLED and _is_dev:
        return {
            "uid": "dev-local",
            "email": "dev@local",
            "plan": "genesis",
            "quota_used": 0,
            "quota_limit": 99999,
            "payment_verified": True
        }

    if credentials is None:
        return None
    try:
        return await verify_token(credentials)
    except HTTPException:
        return None
