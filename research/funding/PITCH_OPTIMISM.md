# Pitch — Optimism RetroPGF + Arbitrum DAO

> Dos canales distintos con el mismo activo central: infraestructura de agentes
> autónomos on-chain con base empírica verificable.
> Preparar post en governance forums de cada DAO.

---

## El activo central: Abu Oracle como agente autónomo on-chain

Abu Oracle no es solo una app de astrología con IA. Es la implementación
más completa que existe actualmente de un agente autónomo con:

- **Identidad económica propia** — recibe pago, provisiona acceso, opera sin
  intervención humana
- **Motor de decisión de costos** — MILP que decide en tiempo real qué modelo
  usar por request según el margen disponible
- **Validación empírica** — 5,359 cartas natales, 527 eventos biográficos,
  Cohen's d=0.44. El agente no opera sobre supuestos — opera sobre datos.

Lo que falta para completar el ciclo autónomo: el módulo MILP en producción
(Fase B) y el estándar ERC-8004 para identidad on-chain verificable.

---

## Infraestructura on-chain actual

| Componente | Estado | Contrato/dirección |
|-----------|--------|-------------------|
| Safe multisig (tesorería) | ✅ Producción | `0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82` |
| USDC ERC-20 (Arbitrum One) | ✅ Producción | `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| Alchemy webhook (detección de pago) | ✅ Producción | — |
| Provisioning automático | ✅ Producción | Firebase Auth + Firestore |
| Email automático (Resend) | ✅ Producción | — |
| selectModel() optimizer | ✅ Producción | `next_app/lib/selectModel.ts` |
| MILP exacto (Fase B) | ⏳ Pendiente | — |
| ERC-8004 identity | ⏳ Pendiente decisión | — |

El flujo ya es autónomo: usuario paga USDC → Alchemy detecta → sistema
provisiona → usuario recibe acceso. Sin intervención humana.

---

## Canal 1: Optimism RetroPGF

### Por qué aplica

RetroPGF financia impacto **ya generado** — no propuestas. Abu Oracle califica
porque:

1. **Sistema en producción con impacto real** — usuarios pagos, sistema funcional
2. **Conocimiento público generado** — simulador de carga open source (si se libera),
   paper preliminar, metodología documentada
3. **Infraestructura para el ecosistema** — el MILP es agnóstico al dominio.
   Cualquier SaaS multi-plan sobre LLMs puede usar este código.

### Cómo presentarse

- Ronda: RetroPGF Round 5 o siguiente (monitorear governance.optimism.io)
- Categoría: "OP Stack Tooling" o "Public Goods in the Superchain"
- Framing: "Construimos y publicamos el primer optimizador de costos LLM con
  restricciones de margen por plan, con código open source y paper."
- Requisito: liberar el simulador como open source antes de aplicar

### Ask

$10,000-20,000 USDC (rango típico para proyectos de infraestructura con
preliminary work demostrable)

---

## Canal 2: Arbitrum DAO Grants

### Por qué aplica

Abu Oracle ya opera en Arbitrum One. El Arbitrum DAO financia proyectos que
construyen infraestructura para el ecosistema. El ángulo más fuerte:

**"Estamos construyendo el primer agente autónomo on-chain con motor de
optimización económica verificable, desplegado en Arbitrum."**

Eso encaja en la línea de financiamiento de Arbitrum para:
- Infraestructura de agentes (sector en explosivo crecimiento)
- DeFi tooling (el MILP es gestión de recursos económicos autónoma)
- Proyectos con presencia real en Arbitrum (ya tenemos safe + USDC + webhook)

### Entregables propuestos

1. Liberar el simulador de carga como open source (repo público)
2. Deploy ERC-8004 — identidad on-chain verificable para Abu Oracle
3. Smart contract de tesorería con lógica de reinversión automática
   (margen generado → infraestructura → más capacidad → más margen)
4. Paper publicado como arXiv preprint con Arbitrum en acknowledgments

### Ask

$15,000-30,000 USDC (justificado por: deploy ERC-8004, desarrollo del contrato
de tesorería autónoma, paper, operación 12 meses)

### Proceso

1. Post en governance.arbitrum.io (Arbitrum Grants Program)
2. Forum discussion period (2 semanas)
3. Snapshot vote por ARB holders

---

## Canal 3: LabDAO

### Por qué aplica

LabDAO financia investigadores independientes sin afiliación institucional
que producen conocimiento científico público. Abu Oracle califica exactamente:
investigador independiente, sistema real, resultados empíricos, sin universidad.

### Ask

$2,000-5,000 en compute credits (GCP o AWS) o equivalente en ETH.

### Framing

"Investigador independiente construyendo el primer corpus empírico de validación
astrológica a escala (5,359 cartas, 527 eventos) y el primer optimizador MILP
de costos LLM en producción. Necesito compute para Fase A-2 ($6 API) y
para operar el banco de prueba 6 meses."

---

## Prerrequisito común: open source del simulador

Todos los canales crypto se fortalecen significativamente si el simulador
de carga se libera como open source antes de aplicar.

**Decisión requerida:**
- ¿Liberar `scripts/finops/load_simulator.py` en repo público?
- ¿Separar en repo propio (`abu-oracle-finops`) o en el repo principal?

El código no contiene lógica propietaria del negocio — es un simulador
genérico parametrizado. Liberarlo crea goodwill y fortalece el caso de
"bien público" en RetroPGF y Gitcoin.

---

## El argumento más fuerte para el ecosistema crypto

El shadow price del TPM no es solo un resultado académico. Es la métrica
que le dice al agente autónomo cuándo reinvertir su margen en más capacidad.

Un agente ERC-8004 que:
1. Genera margen operativo (MILP optimizer)
2. Mide el shadow price en tiempo real
3. Decide cuándo subir de tier sin intervención humana
4. Ejecuta la transacción on-chain desde su propia tesorería

...es el primer agente autónomo con racionalidad económica verificable on-chain.
Eso es infraestructura de agentes, no una app de astrología.

---

*Guillermo Siaira · guillermosiaira@gmail.com*
*Safe: 0x95CEaBdf0fE31610b8A0B09DDC0708A7Ed625c82 (Arbitrum One)*
