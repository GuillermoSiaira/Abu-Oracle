# Abu Oracle — Arquitectura Multi-Usuario en GCP
> Documento de diseño previo a implementación
> Fecha: 2026-03-17
> Estado: Aprobado para implementación

> ⚠️ Última revisión: 2026-03-27. Procesador de pagos: Paddle (no Lemon Squeezy).
> Schema Firestore extendido en Fases 8.12+. Ver DATABASE_STRUCTURE.md para schema completo.

---

## Situación actual

| Servicio | Estado | URL |
|---|---|---|
| `abu-engine` | ✅ Cloud Run con auth JWT + Firestore quota | https://abu-engine-503488473965.us-central1.run.app |
| `lilly-engine` | ✅ Cloud Run | https://lilly-engine-503488473965.us-central1.run.app |
| Cloud SQL | ❌ No habilitado (no necesario en v1) | — |
| Firebase Auth | ✅ API habilitada (Identity Toolkit) | proyecto `abu-oracle` |
| Firestore | ✅ Habilitado + DB Native `us-central1` | colección `users` activa para quota |
| Frontend Next.js | ✅ Docker local / GCP pendiente | localhost:3000 |

**Estado actual:** Abu Engine ya valida Bearer JWT y controla acceso en endpoints protegidos. Falta cerrar el flujo completo en frontend (login/register + guard + token real desde cliente).

---

## Arquitectura objetivo

```
Usuario
  ↓ register/login
Firebase Auth (Google Identity Platform)
  ↓ JWT token
Next.js Frontend
  ↓ requests con Bearer token
Abu Engine (Cloud Run)
  ↓ valida JWT → busca user en DB → verifica quota
Cloud Firestore (users collection)
  ↓ user_id, api_key, plan, quota_used, quota_limit
```

---

## Decisión de base de datos: Firestore vs Cloud SQL

**Elegimos Firestore** porque:
- Ya está disponible en GCP sin configuración adicional
- Abu Engine no tiene schema relacional complejo para usuarios
- Latencia baja para lookups por user_id o api_key
- Sin servidor que administrar (serverless)
- Cloud SQL requiere habilitar API + instancia siempre encendida = costo fijo

---

## Schema de usuarios en Firestore

```
Collection: users
Document ID: firebase_uid

{
  uid: string,              // Firebase UID
  email: string,
  api_key: string,          // UUID generado al registrar — para acceso API directo
  plan: "genesis" | "monthly" | "annual" | "free",
  quota_used: number,       // requests usados este mes
  quota_limit: number,      // genesis = 10000, free = 100
  created_at: timestamp,
  genesis_member: boolean,
  payment_verified: boolean, // true cuando se confirma el pago

  // Campos de suscripción Paddle (monthly/annual)
  paddle_subscription_id?: string,
  paddle_customer_id?: string,
  subscription_status?: "active" | "cancelled" | "past_due",
  subscription_renews_at?: timestamp,
}

// Subcollecciones de memoria Lilly (Fase 8.12)
// users/{uid}/lilly_exchanges/{docId}
// {
//   user_message: string,
//   assistant_response: string,
//   event_type: string,
//   subject_name: string,
//   created_at: string  // ISO
// }
//
// users/{uid}/lilly_summary/current
// {
//   content: string,        // resumen comprimido por Haiku
//   updated_at: string,     // ISO
//   exchange_count: number
// }
```

---

## Flujo de registro Genesis Member

```
1. Usuario paga → Paddle webhook → POST /api/webhook/payment
2. Backend crea usuario en Firebase Auth (email)
3. Backend crea documento en Firestore con plan="genesis", quota_limit=10000
4. Backend genera api_key (UUID)
5. Backend envía email con credenciales via SendGrid/Resend
6. Usuario hace login → ve su carta natal → puede usar el producto
```

---

## Cambios en Abu Engine

Abu Engine necesita un nuevo middleware de autenticación:

```python
# Nuevo: middleware JWT en abu_engine/core/auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials, firestore

security = HTTPBearer()

async def verify_token(token: str = Security(security)):
    try:
        decoded = auth.verify_id_token(token.credentials)
        uid = decoded['uid']
        # Verificar quota en Firestore
        db = firestore.client()
        user = db.collection('users').document(uid).get()
        if not user.exists:
            raise HTTPException(status_code=403, detail="User not found")
        user_data = user.to_dict()
        if user_data['quota_used'] >= user_data['quota_limit']:
            raise HTTPException(status_code=429, detail="Quota exceeded")
        return user_data
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Rutas protegidas** (requieren token):
- `/api/astro/chart/extended`
- `/api/astro/forecast`
- `/api/astro/relocation-field`
- `/api/astro/domain-ranking`
- `/api/lilly/*` (todas las routes de Lilly)

**Rutas públicas** (sin token):
- `/health`
- `/api/demo/*` (para la demo pública)

---

## Cambios en el Frontend Next.js

### Nuevas páginas/componentes:
```
next_app/app/
  auth/
    login/page.tsx       ← Login con Firebase
    register/page.tsx    ← Registro (solo con código de acceso Genesis)
  dashboard/page.tsx     ← Página principal post-login (reemplaza /chart)
```

### Nuevo contexto de auth:
```typescript
// next_app/lib/auth-context.tsx
// Provee: user, loading, login(), logout(), register()
// Usa Firebase Auth SDK
// Si no hay user → redirect a /auth/login
```

### Flujo de sesión:
```
Usuario visita /chart
  → AuthGuard verifica Firebase session
  → Si no autenticado → redirect /auth/login
  → Si autenticado → carga AbuContext del usuario
  → Renderiza carta natal
```

---

## Webhook de pago

```typescript
// next_app/app/api/webhook/payment/route.ts
// Recibe: POST de Paddle cuando se completa un pago
// Verifica: firma HMAC del webhook
// Crea: usuario en Firebase Auth + Firestore
// Envía: email de bienvenida con credenciales
```

---

## Email de bienvenida

Proveedor: **Resend** (resend.com) — más simple que SendGrid, gratis hasta 3000 emails/mes.

Contenido del email:
```
Asunto: Abu Oracle — Acceso Genesis activado ♃ ♄

Bienvenido a Abu Oracle.

Tu acceso Genesis está activo.

Email: {email}
Contraseña temporal: {password}  ← cambiar en primer login

Accedé en: https://abu-oracle.com/chart

Tu API key (para integraciones): {api_key}

Cupo Genesis: acceso de por vida · todas las features futuras incluidas.

— El equipo de Abu Oracle
```

---

## Plan de implementación — orden exacto

### Estado de implementación (actualizado 2026-03-17)

✅ Completado:
1. Habilitar Firebase Auth en proyecto `abu-oracle`
2. Habilitar Firestore en proyecto `abu-oracle`
3. Agregar `firebase-admin` a abu-engine + middleware auth
4. Deploy `abu-engine` con auth en Cloud Run (SA dedicada)
5. Quota enforcement inicial en Abu Engine (Firestore `users`)
6. Smoke tests backend: health público + 401 en rutas protegidas sin/falso token

⏳ Pendiente inmediato:
7. Login/register en Next.js con Firebase SDK
8. AuthGuard en `/chart`
9. Enviar Bearer token real desde frontend a endpoints protegidos

⏳ Pendiente comercial/ops:
10. Webhook de pago (Paddle)
11. Creación automática de usuario post-pago
12. Email de bienvenida con Resend
13. Testing end-to-end (pago → usuario → login → carta)
14. Testing con pago real de $1
15. **LANZAMIENTO**

---

## Variables de entorno a agregar en Cloud Run

```bash
# Abu Engine
FIREBASE_PROJECT_ID=abu-oracle
AUTH_ENABLED=true
ENV=production

# Recomendado en Cloud Run: usar Service Account adjunta (ADC)
# y NO montar GOOGLE_APPLICATION_CREDENTIALS en archivo.

# Next.js
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=abu-oracle.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=abu-oracle
RESEND_API_KEY=...
PADDLE_WEBHOOK_SECRET=...
```

---

## Costo estimado en GCP

| Servicio | Costo | Notas |
|---|---|---|
| Cloud Run (abu-engine) | ~$0/mes | Gratis hasta 2M requests/mes |
| Firestore | ~$0/mes | Gratis hasta 50K reads/day |
| Firebase Auth | $0 | Gratis hasta 10K usuarios |
| Resend | $0 | Gratis hasta 3K emails/mes |
| Total primeros meses | ~$0 | Dentro del free tier |

---

## Lo que NO cambia

- La lógica de Abu Engine (cálculos HF, efemérides, Lilly) — intacta
- El contrato AbuContext (ARCHITECTURE.md) — intacto
- El sistema de casas, planetas, aspectos — intacto
- El frontend actual — solo se agrega auth encima

---

*Abu Oracle — Multi-User Architecture v1.0*
*Implementar en orden estricto. No saltear pasos.*
