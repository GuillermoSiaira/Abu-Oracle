# QA-C01 — Smoke Test Suite: 11 Rutas Lilly

**Fecha:** 2026-05-08  
**Track:** Quality Assurance  
**Prioridad:** Alta — red de seguridad antes de cambiar proveedor (FI-C01) o KG (KG-C03)  
**Independiente de:** FI-C01, KG-C03 — implementar primero

---

## Objetivo

Un script de integración que verifique que las 11 rutas Lilly responden correctamente.
Detecta regresiones antes de un deploy: ruta que devuelve 500, respuesta vacía, rate limit
roto, o log no escrito a Firestore.

**No testea calidad de contenido** — eso es dominio del experimento KG.  
**Testea infraestructura**: HTTP 200, body bien formado, logging, rate limit.

---

## Archivo a crear: `scripts/qa/smoke_lilly_routes.ts`

### Setup y dependencias

```bash
# Desde next_app/ (ya tiene ts-node y @types/node)
cd d:/projects/ai-oracle/next_app
npx ts-node --project tsconfig.json ../scripts/qa/smoke_lilly_routes.ts
```

**Requisitos para correr:**
- Dev server corriendo en `localhost:3001` (o pasar `BASE_URL` por env var)
- Firebase Auth token válido para un usuario Genesis (pasar como `TEST_TOKEN` env var)
- Abu Engine accesible en `localhost:8000`

```typescript
// scripts/qa/smoke_lilly_routes.ts
const BASE_URL  = process.env.BASE_URL  ?? 'http://localhost:3001';
const TEST_TOKEN = process.env.TEST_TOKEN ?? '';  // Firebase JWT
```

---

### Payloads mínimos por ruta

Los payloads deben incluir los campos mínimos que cada ruta necesita para no lanzar 400.
Usar datos de Einstein como sujeto de prueba (birthDate 1879-03-14, lat 48.4, lon 10.0).

Definir un objeto `BASE_PAYLOAD` compartido:

```typescript
const BASE_PAYLOAD = {
  abuData:   { /* JSON mínimo de /analyze — ver estructura abajo */ },
  birthData: { birthDate: '1879-03-14', lat: 48.4, lon: 10.0, userName: 'Test Einstein' },
  timeline:  null,   // rutas que necesiten timeline: pasar un objeto mínimo
  lang:      'es',
  messages:  [],
};
```

**`abuData` mínimo** (estructura que usan las rutas para `assembleContextBlock`):

```typescript
const MIN_ABU_DATA = {
  person: { name: 'Test Einstein' },
  chart: {
    planets: [
      { name: 'Sol',    sign: 'Piscis',  house: 12, degree: 23.1, longitude: 353.1, dignity: 'peregrine' },
      { name: 'Luna',   sign: 'Sagitario', house: 9, degree: 14.2, longitude: 254.2, dignity: 'peregrine' },
      { name: 'Júpiter', sign: 'Acuario', house: 11, degree: 11.2, longitude: 311.2, dignity: 'peregrine' },
    ],
    houses: [{ house: 1, sign: 'Cáncer', degree: 11.5 }],
    ascendant: { sign: 'Cáncer', degree: 11.5 },
    mc:        { sign: 'Aries',  degree: 5.2  },
  },
  derived: {
    sect:       { sect: 'diurnal', sect_light: 'Sol' },
    profections: [{ house: 12, sign: 'Piscis', lord: 'Júpiter', is_active: true, date_end: '2026-07-14' }],
    firdaria:   [{ major_planet: 'Sol', minor_planet: 'Júpiter', is_active: true, date_end: '2028-03-14' }],
    lots:       {},
  },
};
```

---

### Lista de rutas y payloads específicos

| # | Ruta | Payload adicional | Campo de respuesta |
|---|---|---|---|
| 1 | `POST /api/lilly/screen-open` | `abuData, birthData, lang` | `response` |
| 2 | `POST /api/lilly/planet` | `+ planet: { name:'Sol', sign:'Piscis', house:12, degree:23.1, dignity:'peregrine', retrograde:false }` | `response` |
| 3 | `POST /api/lilly/technique` | `+ technique:'sect', data:{ sect:'diurnal' }` | `response` |
| 4 | `POST /api/lilly/transit` | `+ transit:{ transit_planet:'Júpiter', natal_planet:'Sol', aspect:'trine', exact_date:'2026-06-01' }` | `response` |
| 5 | `POST /api/lilly/domain` | `+ domain:'h10', domainLabel:'Carrera'` | `response` |
| 6 | `POST /api/lilly/city` | `+ city:{ name:'Buenos Aires', lat:-34.6, lon:-58.4, hf_score:0.72 }` | `response` |
| 7 | `POST /api/lilly/house` | `+ house_num:1, cusp_sign:'Cáncer', house_lord:'Luna', occupants:['Júpiter']` | `response` |
| 8 | `POST /api/lilly/sky` | `+ fastTransits:[], lunarData:null` | `response` |
| 9 | `POST /api/lilly/solar-return` | `+ srYear:2026, city:{ name:'Viena', lat:48.2, lon:16.4 }` | `response` |
| 10 | `POST /api/lilly/mundana` | `+ config:{ type:'conjunction_JS', significance:'medium' }, lang:'es'` | `response` |
| 11 | `POST /api/chat` | `+ message:'¿Cuál es mi ascendente?', meta:{ date:'1879-03-14', lat:48.4, lon:10.0 }` | `reply` (campo diferente) |

**Nota ruta 11**: `/api/chat` devuelve `{ reply: string }`, no `{ response: string }`.

---

### Función de test

```typescript
interface TestResult {
  route:    string;
  status:   number;
  passed:   boolean;
  error?:   string;
  respLen?: number;
}

async function testRoute(route: string, payload: object): Promise<TestResult> {
  const url = `${BASE_URL}${route}`;
  try {
    const res = await fetch(url, {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(TEST_TOKEN ? { Authorization: `Bearer ${TEST_TOKEN}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    const body = await res.json().catch(() => ({}));
    const responseField = route === '/api/chat' ? body.reply : body.response;
    const passed = res.status === 200
      && typeof responseField === 'string'
      && responseField.trim().length > 10;

    return {
      route,
      status:  res.status,
      passed,
      error:   passed ? undefined : `status=${res.status} responseLen=${responseField?.length ?? 0}`,
      respLen: responseField?.length,
    };
  } catch (err: unknown) {
    return { route, status: 0, passed: false, error: String(err) };
  }
}
```

---

### Runner principal

```typescript
async function main() {
  console.log(`\n🔍 Abu Oracle — Smoke Test Suite`);
  console.log(`   Base URL : ${BASE_URL}`);
  console.log(`   Auth     : ${TEST_TOKEN ? 'present' : 'MISSING — rate-limit tests may fail'}\n`);

  const results: TestResult[] = [];

  // --- 1. screen-open ---
  results.push(await testRoute('/api/lilly/screen-open', {
    ...BASE_PAYLOAD,
    abuData: MIN_ABU_DATA,
  }));

  // --- 2. planet ---
  results.push(await testRoute('/api/lilly/planet', {
    ...BASE_PAYLOAD,
    abuData: MIN_ABU_DATA,
    planet: { name: 'Sol', sign: 'Piscis', house: 12, degree: 23.1, dignity: 'peregrine', retrograde: false },
  }));

  // ... [3–11 siguiendo la tabla anterior] ...

  // --- Print results ---
  let passed = 0;
  for (const r of results) {
    const icon = r.passed ? '✅' : '❌';
    const extra = r.passed ? `(${r.respLen} chars)` : `ERROR: ${r.error}`;
    console.log(`  ${icon} ${r.route.padEnd(35)} ${extra}`);
    if (r.passed) passed++;
  }

  console.log(`\n  ${passed}/${results.length} routes passing\n`);
  process.exit(passed === results.length ? 0 : 1);
}

main();
```

---

## Test de rate limit

Separado del smoke test principal. Solo correr manualmente con usuario de test.

```typescript
async function testRateLimit() {
  // Requiere TEST_TOKEN de un usuario free (sin payment_verified en Firestore)
  // o un usuario Genesis con contador reseteado manualmente
  
  const LIMIT = 15; // FREE_TIER_LIMIT nuevo (FI-C01)
  console.log(`\n🔢 Rate limit test (FREE_TIER_LIMIT=${LIMIT})\n`);

  let lastStatus = 0;
  for (let i = 1; i <= LIMIT + 1; i++) {
    const res = await fetch(`${BASE_URL}/api/lilly/planet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TEST_TOKEN}` },
      body: JSON.stringify({ ...BASE_PAYLOAD, abuData: MIN_ABU_DATA,
        planet: { name: 'Sol', sign: 'Piscis', house: 12, degree: 23.1, dignity: 'peregrine', retrograde: false },
      }),
    });
    lastStatus = res.status;
    process.stdout.write(`  call ${i}: ${res.status}\n`);
  }

  const passed = lastStatus === 429;
  console.log(`\n  ${passed ? '✅' : '❌'} Call ${LIMIT + 1} returned ${lastStatus} (expected 429)\n`);
  return passed;
}
```

---

## Test de logging Firestore

```typescript
async function testFirestoreLogging() {
  // Hace una llamada y después verifica que apareció un documento en kg_baseline_logs
  // Requiere Firebase Admin SDK accesible (solo en server-side / script Node)
  
  // 1. Timestamp antes
  const before = new Date().toISOString();

  // 2. Llamada a /api/lilly/planet
  await fetch(`${BASE_URL}/api/lilly/planet`, { /* ... */ });

  // 3. Esperar 2s (fire-and-forget puede tardar)
  await new Promise(r => setTimeout(r, 2000));

  // 4. Verificar en Firestore
  // (requiere importar firebase-admin — solo funciona si el script tiene acceso a SA key)
  // Si no hay SA key disponible en el entorno de test: skip this check y marcar como 'skipped'
  console.log('  ⚠️  Firestore logging test requires Firebase Admin — run manually from server context');
}
```

---

## Criterios de aceptación

- [ ] `npx ts-node scripts/qa/smoke_lilly_routes.ts` sale con código 0
- [ ] Las 11 rutas devuelven HTTP 200
- [ ] Cada ruta devuelve `response` (o `reply` para `/api/chat`) con longitud > 10 caracteres
- [ ] El script imprime un resumen claro con ✅/❌ por ruta
- [ ] El script sale con código 1 si alguna ruta falla (para uso en CI)

---

## Cómo correr

```bash
# Desde raíz del repo — con dev server corriendo
cd d:/projects/ai-oracle

# Obtener token (una vez):
# Abrir app en localhost:3001, abrir DevTools → Application → Firebase Auth
# Copiar currentUser.accessToken

# Correr:
TEST_TOKEN="eyJ..." npx ts-node next_app/node_modules/.bin/ts-node \
  --project next_app/tsconfig.json \
  scripts/qa/smoke_lilly_routes.ts
```

---

## Lo que NO hace este spec

- **NO** testea calidad de las interpretaciones (eso es KG-C03)
- **NO** testea el Abu Engine directamente (eso es responsabilidad de pytest)
- **NO** requiere Docker — usa dev server Next.js estándar
- **NO** resetea contadores Firestore automáticamente (rate limit test es manual)

---

## Commit sugerido

```
feat(qa): smoke test suite — 11 Lilly routes (QA-C01)

- scripts/qa/smoke_lilly_routes.ts: integration tests for all Lilly routes
- Verifies: HTTP 200, non-empty response, exit code 1 on failure
- Includes manual rate-limit test function
- Uses Einstein minimal payload for deterministic test setup
```
