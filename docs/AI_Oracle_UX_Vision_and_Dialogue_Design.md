# AI Oracle — UX Vision and Dialogue Design

Actualizado: 2025-11-03

## 🜂 Purpose
AI_Oracle debe ofrecer una experiencia astrológica viva y significativa. El usuario interactúa con entidades arquetípicas —Abu (razón) y Lilly (intuición)— que dialogan entre sí para convertir cálculos celestes en sabiduría comprensible. La UX privilegia claridad, belleza funcional y transparencia simbólica (mostrar cómo se llega a lo dicho).

---

## 🌞 Conceptual Pillars

| Pilar | Descripción |
| --- | --- |
| Dualidad viva | Abu → precisión astronómica (Sol, estructura, razón). Lilly → interpretación simbólica (Luna, emoción, significado). Diálogo como forma. |
| De datos a sentido | Cálculos (posiciones, aspectos, casas) se transforman en narrativa comprensible y emocional. |
| Ritual interactivo | Cada consulta es un micro-ritual: el usuario pregunta → Abu calcula → Lilly interpreta → cierre con intención. |
| Transparencia simbólica | Se muestra carta, tránsitos, axiomas activos y razonamiento de Lilly (por qué dice lo que dice). |
| Belleza funcional | Animaciones suaves, tonos astrales, lenguaje elegante. Ritmo visual claro, sin sobrecarga. |

---

## 🪐 UX Flow Overview

### 🜁 Entry Point
Portal del Oráculo con presentación de Abu y Lilly y tres rutas principales:
- Lectura Diaria
- Revolución Solar
- Lectura Personalizada (por periodo o tema)

Micro-animaciones introductorias (sutiles, no intrusivas).

### 🜃 Calculation Stage (Abu)
Abu calcula posiciones, aspectos y planetas por casas y devuelve JSON estructurado:

```json
{
  "houses": [{"number": 1, "sign": "Aquarius"}],
  "planets": [{"name": "Saturn", "sign": "Pisces", "degree": 12.4, "house": 2}],
  "aspects": [{"a": "Sun", "b": "Saturn", "type": "square", "orb": 1.2}]
}
```

### 🜄 Interpretation Stage (Lilly)
Lilly recibe el output de Abu y produce:
- abu_line → frase racional de contexto (voz de Abu)
- lilly_line → respuesta intuitiva (voz de Lilly)
- headline, narrative, actions
- reasoning → explicación breve de por qué

```json
{
  "abu_line": "Saturn is forming a square with your natal Sun in the 10th House.",
  "lilly_line": "This signals a period of maturity and rebuilding in your vocation.",
  "headline": "Cosechar lo que sembraste",
  "narrative": "...",
  "actions": ["..."],
  "reasoning": "Based on the square aspect between Sun and Saturn..."
}
```

### 🎨 Visual Stage (Frontend)
- Carta circular animada con signos, casas y planetas.
- Colores por elemento (fuego, tierra, aire, agua).
- Aspectos con líneas dinámicas (rojo: cuadratura, azul: trígono, verde: sextil).
- Abu y Lilly visibles al costado del gráfico; líneas de diálogo aparecen gradualmente.

### 🕯 Ritual Closure
Despedida breve y opciones:
- Guardar lectura
- Nueva consulta
- Ver línea de tiempo astral

---

## ⚙️ Implementation Steps

| Fase | Descripción | Resultado |
| --- | --- | --- |
| 1. Abu Engine | Calcular planetas por casas y devolver en JSON. | Datos completos para interpretación. |
| 2. Lilly Engine | Incluir `abu_line` y `lilly_line` en JSON. | Diálogo dual Abu–Lilly. |
| 3. Frontend | Carta animada + burbujas de diálogo. | Interfaz viva y significativa. |
| 4. UX Polish | Transiciones y ritual de cierre. | Experiencia fluida y con alma. |

---

## 🧭 Guiding Principle
“El Oráculo no predice, revela patrones de conciencia.”
Objetivo: abrir espacio de reflexión y alineación con el propio ritmo interior.

---

## 🔧 Design Details and Contracts

- Backend contracts a preservar:
  - Lilly responde JSON válido con claves existentes: `headline`, `narrative`, `actions[]`, `astro_metadata{ source }`. Se permiten campos adicionales (`abu_line`, `lilly_line`, `reasoning`). Español por defecto.
  - Abu expone `/api/astro/chart` y debe incluir planeta→casa cuando esté disponible.
- Axiomas y razonamiento:
  - `reasoning` es opcional (controlado por `LILLY_INCLUDE_REASONING=true|false`).
  - Si falta corpus, se muestra reasoning sin citas clásicas, pero con axiomas.

---

## 🎯 Prioridades de entrega (propuesta)

1) Backend: `abu_line` y `lilly_line` en Lilly (bajo impacto, alto valor).  
2) Frontend: `DialogueBubble` y render en `/interpret`.  
3) Home ritual: portada con presentación de Abu y Lilly.  
4) Carta circular básica (SVG + Framer Motion).  
5) Planet-as-house en Abu (si no estuviera disponible).  
6) Polish de transiciones y cierre ritual.  

---

## 🧪 Validation
- Verificar presencia de `abu_line`, `lilly_line` y `reasoning` en JSON.
- Render correcto en `/interpret` con fallback si faltan campos.
- Logs de Lilly muestran axiomas y reasoning inyectados.

---

## 📎 Notas técnicas sugeridas
- Frontend: React + SVG para carta; Framer Motion para transiciones; Tailwind para estilos.
- Accesibilidad: contraste adecuado, animaciones con preferencia de “reduced motion”.
- Internacionalización: ES por defecto; textos de UI listos para i18n.
