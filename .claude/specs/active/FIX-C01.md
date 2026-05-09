# FIX-C01 — provisionUser: upgrade usuarios existentes + UX post-pago Paddle

## Contexto

Cuando un usuario **free** (que ya se registró en Firebase) paga via Paddle Checkout:
1. Paddle manda webhook → `provisionUser(email, plan)` en `lib/provision-user.ts`
2. `getUserByEmail(email)` lo encuentra → **retorna early sin actualizar Firestore**
3. El `plan` del usuario sigue siendo `free` → el usuario paga y no recibe acceso

Además, después de que Paddle cierra el checkout overlay, el usuario vuelve a la app
sin ningún feedback. No sabe si el pago procesó, no sabe que debe refrescar.

## Archivos a modificar

```
next_app/lib/provision-user.ts        MODIFY — upgrade existing users
next_app/app/layout.tsx               MODIFY — Paddle eventCallback post-pago
next_app/components/OracleChat.tsx    MODIFY — escuchar evento + cerrar modal + mostrar éxito
```

## Spec

### 1. `lib/provision-user.ts` — upgrade de usuarios existentes

Reemplazar el bloque "Idempotency: skip if user already exists" por lógica que
distingue entre "usuario nuevo" (crear) y "usuario existente" (actualizar plan):

```typescript
// Idempotency: if user already exists, upgrade plan and return
try {
  const existing = await getAdminAuth().getUserByEmail(email);
  console.log(`[provision-user] Upgrading existing user: uid=${existing.uid} email=${email} plan=${plan}`);

  await getAdminDb()
    .collection('users')
    .doc(existing.uid)
    .set(
      {
        plan,
        payment_verified: true,
        quota_limit: QUOTA_LIMITS[plan],
        genesis_member: plan === 'genesis',
        updated_at: new Date().toISOString(),
        ...meta,
      },
      { merge: true }  // merge: true — preserva campos existentes (email, uid, etc.)
    );

  await sendUpgradeEmail(email, plan);

  return { uid: existing.uid, email, created: false };
} catch (e: any) {
  // auth/user-not-found → fall through to create new user
  if (e?.errorInfo?.code !== 'auth/user-not-found' && e?.code !== 'auth/user-not-found') {
    throw e;
  }
}
```

Agregar la función `sendUpgradeEmail` **después** de `sendWelcomeEmail`:

```typescript
async function sendUpgradeEmail(email: string, plan: Plan) {
  const resendKey = process.env.RESEND_API_KEY;
  if (!resendKey) return;
  try {
    const { Resend } = await import('resend');
    const resend = new Resend(resendKey);
    const planLabel = PLAN_LABELS[plan];
    await resend.emails.send({
      from: 'Abu Oracle <noreply@abu-oracle.com>',
      to: email,
      subject: `Abu Oracle — Plan ${planLabel} activado ♃`,
      html: `<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#09090b;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090b;padding:48px 16px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111113;border:1px solid #292524;border-radius:12px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#1c1108 0%,#0f0a04 100%);padding:40px;text-align:center;border-bottom:1px solid #292524;">
            <div style="font-size:28px;letter-spacing:0.25em;color:#fbbf24;">ABU ORACLE</div>
            <div style="font-size:12px;letter-spacing:0.3em;color:#78716c;text-transform:uppercase;margin-top:8px;">Astrological Intelligence Engine</div>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <p style="margin:0 0 16px;font-size:17px;color:#e7e5e4;line-height:1.6;">
              Tu plan <strong style="color:#fbbf24;">${planLabel}</strong> está activo.
            </p>
            <p style="margin:0 0 32px;font-size:14px;color:#a8a29e;line-height:1.6;">
              Accedé con tu cuenta de siempre — el acceso ampliado ya está disponible.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr><td align="center">
                <a href="https://app.abu-oracle.com"
                   style="display:inline-block;background:#d97706;color:#fff;text-decoration:none;font-size:14px;font-weight:600;padding:14px 36px;border-radius:6px;">
                  Acceder a Abu Oracle →
                </a>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px;border-top:1px solid #1c1917;text-align:center;">
            <p style="margin:0;font-size:11px;color:#44403c;font-family:sans-serif;">
              Abu Oracle · <a href="https://abu-oracle.com" style="color:#78716c;text-decoration:none;">abu-oracle.com</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`,
    });
  } catch (err) {
    console.error('[provision-user] sendUpgradeEmail error:', err);
  }
}
```

### 2. `app/layout.tsx` — Paddle eventCallback

En el script inline de inicialización de Paddle, agregar `eventCallback` que:
- Detecta `checkout.completed`
- Despacha `CustomEvent('paddle:checkout:completed')` en `window`

El bloque `__html` existente:
```typescript
__html: `
  (function initPaddle() {
    if (window.Paddle) {
      window.Paddle.Initialize({ token: ${JSON.stringify(paddleToken)} });
      return;
    }
    window.setTimeout(initPaddle, 100);
  })();
`,
```

Reemplazar por:
```typescript
__html: `
  (function initPaddle() {
    if (window.Paddle) {
      window.Paddle.Initialize({
        token: ${JSON.stringify(paddleToken)},
        eventCallback: function(event) {
          if (event.name === 'checkout.completed') {
            window.dispatchEvent(new CustomEvent('paddle:checkout:completed'));
          }
        }
      });
      return;
    }
    window.setTimeout(initPaddle, 100);
  })();
`,
```

### 3. `components/OracleChat.tsx` — success state post-pago

Agregar estado `paymentSuccess: boolean` junto a `showUpgrade`:
```tsx
const [paymentSuccess, setPaymentSuccess] = useState(false);
```

Agregar `useEffect` que escucha el evento Paddle (montado una sola vez):
```tsx
useEffect(() => {
  function handlePaddleSuccess() {
    setShowUpgrade(false);
    setPaymentSuccess(true);
    // Reload automático después de 6 segundos para que el webhook procese
    setTimeout(() => window.location.reload(), 6000);
  }
  window.addEventListener('paddle:checkout:completed', handlePaddleSuccess);
  return () => window.removeEventListener('paddle:checkout:completed', handlePaddleSuccess);
}, []);
```

Agregar banner de éxito en el JSX (antes del `<UpgradeModal>`):
```tsx
{paymentSuccess && (
  <div className="fixed inset-x-0 top-0 z-[60] bg-emerald-900/90 backdrop-blur-sm border-b border-emerald-700/50 px-4 py-3 text-center">
    <p className="text-sm text-emerald-200">
      ✓ Pago procesado — activando tu acceso. La página se recargará automáticamente…
    </p>
  </div>
)}
```

## Criterios de aceptación

- [ ] Usuario existente paga via Paddle → Firestore actualiza `plan`, `payment_verified: true`, `quota_limit`
- [ ] Usuario existente recibe email de confirmación de upgrade (no contiene contraseña)
- [ ] Usuario nuevo paga via Paddle → flujo original inalterado (crea cuenta, email con contraseña)
- [ ] Después de checkout.completed → banner verde aparece + reload automático a los 6s
- [ ] `UpgradeModal` se cierra cuando llega el evento de éxito
- [ ] `npx tsc --noEmit` pasa sin errores
