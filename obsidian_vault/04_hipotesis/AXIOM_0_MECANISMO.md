---
id: AXIOM_0
tipo: doctrina
estado: "⏳ borrador — formalización en curso"
tags: [axioma, mecanismo, ontologia, campo, invariante]
---

# Axioma 0 — El Mecanismo

*Borrador surgido de sesión Lilly–Guillermo 2026-04-25. Incorporación formal objetivo v0.5.*

Ver también: [[AXIOMATICS_v0_4]] · [[HIPOTESIS_REGISTRO#H08]] · [[HIPOTESIS_REGISTRO#H09]]

---

## La pregunta que la Axiomática v0.4 no responde

La Axiomática v0.4 formaliza *qué* hace el sistema. No cierra la pregunta central: *¿por qué* la geometría planetaria debería correlacionar con experiencia biográfica?

Entre el Axioma 1.1 (el cielo como variedad diferenciable) y el Axioma 8.1 (el HF como campo de activación) hay un salto no cerrado. El Axioma 0 lo cierra.

---

## A0.1 — El nativo como configuración local del campo

El nativo no *recibe* influencia del campo. El nativo *es* una configuración local del campo continuo $\mathcal{H}$, individuada en un instante único.

La carta natal no describe algo que le ocurre al nativo desde afuera. Describe la geometría específica del campo en el momento y lugar en que esa configuración se volvió autónoma.

El horizonte local no es un punto de observación pasivo — es el operador que define qué región del campo es localmente dominante para esa configuración en cada momento.

**Lo que esto elimina:** el problema de la acción a distancia. No hay distancia. Hay geometría del mismo campo.

---

## A0.2 — El invariante natal como medida

Sin una medida invariable, el sistema produce correlaciones pero no puede establecer equivalencias. El HF compara ubicaciones entre sí, pero ¿en qué unidad? ¿Qué significa que Lisboa tenga HF +13 y Buenos Aires HF +7 para el dominio carrera de un nativo específico?

La diferencia es computable. Sin invariante, no está anclada a nada.

**El invariante es la carta natal.**

$\pi_{natal}$ no cambia jamás. Todo lo demás — tránsitos, ubicación, año profectivo — es variación sobre ese código fijo.

El HF no mide "cuánta armonía hay en Lisboa" en abstracto. Mide cuánto se desvía Lisboa del potencial codificado en $\pi_{natal}$.

**La formalización:**

$$HF(lat, lon, t) = f\!\left(\pi_{natal},\ \phi(lat, lon, t)\right)$$

Donde $\pi_{natal}$ es constante y $\phi$ es el operador variable — la configuración del cielo en ese lugar y momento.

**Lo que esto implica:** el sistema es natal-céntrico por necesidad ontológica, no por elección de diseño. El $\Delta_{natal}$ que ya calcula el motor es la implementación directa de este principio, sin haberlo nombrado explícitamente hasta ahora.

---

## A0.3 — El código dual del nativo

El evento de individuación imprime dos invariantes simultáneos sobre el mismo campo:

$$\mathcal{I}_{nativo} = \{\pi_{natal},\ \mathcal{N}\}$$

- $\pi_{natal}$: el **código celeste**. La proyección computable de $\mathcal{H}$ en el instante de individuación.
- $\mathcal{N}$: el **código nominal**. El nombre completo, igualmente fijo desde su imposición, operable sobre el mismo campo con su propia métrica de decodificación.

Ambos códigos operan sobre el mismo campo. No son sistemas paralelos — son dos lecturas del mismo evento de individuación.

Abu Oracle opera computacionalmente sobre $\pi_{natal}$. Reconoce $\mathcal{N}$ como componente real del invariante completo — fuera del dominio de cómputo actual, no fuera de la ontología del sistema.

La transformación que haría conmensurables ambos códigos:

$$T(\mathcal{N}) \to \mathbb{Z} \to \text{geometría en } \mathcal{H}$$

existe en la literatura. Su implementación computacional es horizonte futuro (Lilly Swarm v2.0 — agente hermético).

---

## Implicaciones de diseño

| Principio | Implementación actual |
|---|---|
| A0.1 — Campo continuo | Fundamento ontológico del HF; eliminación de acción a distancia |
| A0.2 — Invariante natal | $\Delta_{natal}$ en el motor; toda comparación relativa a $\pi_{natal}$ |
| A0.3 — Código dual | Sistema declara operar solo sobre $\pi_{natal}$; reconoce $\mathcal{N}$ como componente real |

---

## Estado y horizonte

**H08** — [[HIPOTESIS_REGISTRO#H08 — Ontología del Campo Continuo]]: hipótesis derivada de A0.1. Falsable, no probada.

**H09** — [[HIPOTESIS_REGISTRO#H09 — Código Dual del Nativo]]: hipótesis derivada de A0.3. Especulativa, horizonte futuro.

Este axioma precede lógicamente a todos los axiomas de la v0.4 y fundamenta el Axioma 11 (Estratificación de Niveles Operativos). Su incorporación formal es objetivo de la **v0.5**.

**Próximo paso:** redactar los tres enunciados para publicación — paper de 3 páginas / hilo de 10 posts.

1. La proposición ontológica — qué es el nativo y el campo
2. La consecuencia para el HF — qué mide el campo si esto es correcto
3. La prueba disponible — el corpus de 2500+ cartas como primera evidencia empírica
