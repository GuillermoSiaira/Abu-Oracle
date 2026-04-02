
# APÉNDICE B — PARÁMETROS OPERATIVOS DEL ORQUESTADOR

**Fecha:** 2026-01-02  
**Autor:** Abu Oracle Project  
**Versión:** 1.0  
**Nota:** Documento diseñado para ser ingestado y procesado tanto por agentes de IA como por humanos. Estructura y tablas listas para parsing automático y revisión manual.  
*Referencia axiomática: Axiomatics of Heavens v0.3*

---

## B.1 Objetivo del Apéndice
Define los **parámetros operativos mínimos** para:
- Traducir la axiomática en reglas de enrutamiento y filtrado.
- Garantizar robustez ante datos incompletos mediante **Modos Degradados**.
- Especificar los requisitos geométricos que cada escuela impone al motor de cálculo (Abu).

No introduce nuevas interpretaciones, solo condiciones de ejecución.

---

## B.2 Escala Normalizada de la Función de Costo (J)

**Definición:**
\[
J \in [0.0, 1.0]
\]
- **0.0**: geometría ideal, alta estabilidad, señal robusta
- **1.0**: geometría inestable, alta sensibilidad, señal no confiable

**Normalización:**
\[
J = \mathrm{clip}\left(
\frac{\alpha |dH| + \beta |d\zeta| + \gamma \left| \frac{\partial \psi}{\partial Z} \right|}{J_{\text{ref}}}
\right)
\]
con \( J_{\text{ref}} \) definido empíricamente (percentil alto de errores simulados).

### B.2.2 Umbrales Tentativos por Escuela

| Escuela / Agente         | $J_{max}$ (Estricto) | $J_{robust}$ (Degradado) |
|-------------------------|----------------------|-------------------------|
| Renacentista / Lilly    | 0.25                 | ≤ 0.50                  |
| Helenística (Whole Sign)| 0.45                 | ≤ 0.65                  |
| Védica / Jyotish        | 0.30 (nakshatra)     | ≤ 0.55 (rashi)          |

> Valores iniciales, recalibrar con datos reales.

---

## B.3 Matriz de Compatibilidad Geométrica

| Escuela / Agente             | Tipo de Tiempo Dominante         | Sistema de Coordenadas Dominante | Sensibilidad al Observador (Z) | Transformaciones Necesarias (Abu)         | Técnicas Críticas                  | $J_{max}$ | Comentarios Operativos                                              |
|------------------------------|----------------------------------|----------------------------------|-------------------------------|--------------------------------------------|-------------------------------------|----------|---------------------------------------------------------------------|
| Renacentista / Lilly         | Sidéreo + Solar medio            | Eclíptico → Casas + Horizontal   | Alta                          | Eclíptico → Ecuatorial → Horizontal        | Casas, ángulos, dignidades, horaria | 0.25     | Si $J > J_{max}$, bloquear cúspides finas; advertencia horaria.     |
| Helenística (Whole Sign)     | Sidéreo (Asc) + Solar anual      | Eclíptico (signos=casas) + Hor.  | Media–Alta                    | Eclíptico → Horizontal (Asc/MC)            | Asc, ángulos, profecciones          | 0.45     | Puede operar sin cúspides; Asc crítico.                             |
| Védica / Jyotish             | Sidéreo local + ciclos cualit.   | Eclíptico sidéreo + Ecuatorial   | Alta                          | Ecuatorial ↔ Eclíptico sidéreo             | Lagna, Luna, dashas, divisionales   | 0.30     | Si $J$ alto, bloquear dashas/divisionales; exigir ayanamsa.         |

---

## B.4 Lógica de Degradación (Regla Formal)

**Regla General:**
- Si $J \le J_{max}^{(i)}$ → **Modo Estricto**
- Si $J_{max}^{(i)} < J \le J_{robust}^{(i)}$ → **Modo Robusto (Low-Res / Sign-Only)**
- Si $J > J_{robust}^{(i)}$ → **No invocar agente; advertencia de insuficiencia geométrica**

**Definición de Modo Robusto:**
- Desactivar técnicas sensibles (cúspides finas, divisionales, dashas precisas)
- Limitar lenguaje interpretativo a tendencias generales
- Adjuntar flag explícito de baja resolución al output

**Ejemplo de metadato:**
```json
{
  "mode": "robust",
  "resolution": "low",
  "reason": "J > J_max for fine-grained techniques"
}
```

---

## B.5 Requisitos para Abu Engine (Backend)

Abu debe garantizar:
1. Disponibilidad de:
   - tiempo sidéreo local,
   - tiempo solar verdadero y medio,
   - transformaciones entre sistemas de coordenadas.
2. Cálculo explícito de:
   - $H$, $\zeta$, $\psi$,
   - diferenciales $dH$, $d\zeta$,
   - correcciones aparentes (Axioma 4.4).
3. Emisión de:
   - valor $J$ normalizado,
   - componentes parciales de $J$ (para trazabilidad).

---

## B.6 Estado Operativo
- El Orquestador tiene reglas claras de decisión.
- Abu tiene especificación de requisitos.
- Las escuelas quedan formalizadas como funciones interpretativas condicionadas.
- El sistema evita fragilidad por datos imperfectos.

---

**Nota:** El Modo Degradado es una condición de robustez epistemológica, no una concesión.

---

*Fin del Apéndice B*
