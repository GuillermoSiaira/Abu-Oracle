---
name: BABEL_literature
description: Mapa de literatura — estado del arte en comunicación animal + IA, gaps identificados
tipo: literature_review
estado: completo
tags: [babel, literatura, bioacustica, NatureLM, CETI, cross-species]
fecha: 2026-05-01
---

# BABEL — Mapa de Literatura

> Sesión de investigación: 2026-05-01. Fuentes verificadas con búsquedas web.

---

## El estado del arte — quién está haciendo qué

### Earth Species Project (ESP)
- **NatureLM-audio** (ICLR 2025, arXiv:2411.07186): primer modelo fundacional audio-lenguaje para bioacústica
- Arquitectura: BEATs encoder + Llama 3.1 8B. Zero-shot sobre especies no vistas.
- Pesos libres en HuggingFace: `EarthSpeciesProject/NatureLM-audio`
- Eje: **intra-especie**. Decodifica una especie a la vez.
- También: modelo de separación de fuentes que resuelve el "cocktail party problem" bioacústico

### Project CETI (Cetacean Translation Initiative)
- Bio-loggers adheridos a cachalotes, datos tailored para ML
- Hallazgo 2025 (UC Berkeley + CETI): cachalotes tienen **estructura fonética análoga a vocales humanas** — patrón ɑ-vowel, i-vowel, diptongos
- Producción intencional y controlada (no ruido aleatorio)
- Derivó en debate sobre **derechos legales de animales**

### Universidad de Copenhague (2025)
- Modelo ML distingue emociones positivas/negativas en **7 especies de ungulados**
- Accuracy: **89.49%** cross-species
- Hallazgo: expresiones vocales de emoción son **evolutivamente conservadas**
- **El único trabajo genuinamente inter-especie hasta ahora** — pero clasifica emoción, no mapea semántica funcional

### NeurIPS 2025 Workshop — AI for Non-Human Animal Communication
- Campo ya tiene presencia formal en ML top-tier
- Papers: WhaleLM, Dolph2Vec, PrimateFace, representaciones autosupervisadas para cetáceos
- Keynotes: Laela Sayigh (WHOI), Oisin Mac Aodha (Edimburgo), Julie Elie (UC Berkeley)
- Desafíos abiertos: escasez de datos etiquetados, generalización inter-especie, interpretabilidad

### Küçükuncular (2025) — AI & Ethics
- *Ethical implications of AI-mediated interspecies communication*. AI and Ethics 5:6379–6391
- Baidu tiene patente en proceso para intérprete de emociones animales
- Riesgo de commodificación: corporaciones controlando quién "escucha" a qué especie
- Principios propuestos: no-maleficencia, beneficencia, autonomía animal, privacidad, honestidad, justicia

### Animals, Zombanimals and the Total Turing Test (Springer, 1998)
- Propone el "Total Turing Test": AGI verdadera debe poder comunicarse con **cualquier** entidad cognitiva
- Crítica al Turing Test estándar: es "chauvinista" — solo mide imitación de comunicación humana
- Este claim de 1998 **sigue sin implementación técnica concreta en 2026** ← el gap de BABEL

---

## El gap central

Todo el trabajo existente comparte esta arquitectura implícita:

```
[señales acústicas especie X] → [modelo] → [etiqueta humana]
```

BABEL propone:

```
[señales especie A] ↘
                    → [nodo función comunicativa] ← [señales especie B]
[señales especie C] ↗
```

**Nadie ha construido el grafo de equivalencias funcionales inter-especie.**

El paper de Copenhague intuye esto al mostrar que los predictores de valencia emocional son "evolutivamente conservados", pero no lo formaliza. El Total Turing Test lo pide desde 1998. BABEL es la propuesta técnica concreta.

---

## Datasets clave

| Dataset | Especies | Labels semánticos | Acceso |
|---|---|---|---|
| Vervet alarm calls (Cheney & Seyfarth 1990) | *C. pygerythrus* | eagle / leopard / snake | Request autores |
| Prairie dog vocabulary (Slobodikoff 2009) | *C. ludovicianus* | intruder shape/speed/color | Request lab |
| Xeno-canto (deprecado API v2, v3 sin acceso público) | Aves múltiples | call type | Web |
| Watkins Marine Mammal DB | Cetáceos, 60+ sp | species-level | Libre manual |
| ESP/NatureLM training set | Multi-especie | species + task | HuggingFace (no comercial) |
| Animal Sound Archive Berlin | 120k+ grabaciones | variado | Libre |
| Macaulay Library (Cornell) | 2M+ registros | variado | Libre con cuenta |

---

## Referencias principales

1. Küçükuncular (2025). *Ethical implications of AI-mediated interspecies communication*. AI & Ethics 5:6379–6391.
2. NatureLM-audio (2024/2025). arXiv:2411.07186. Earth Species Project / ICLR 2025.
3. Rutz et al. (2023). *Using machine learning to decode animal communication*. Science 381:152–155.
4. Cheney & Seyfarth (1990). *How monkeys see the world*. University of Chicago Press.
5. Slobodikoff et al. (2009). *Prairie dog alarm calls*. Animal Behaviour 78(4):964–974.
6. Briefer et al. (2025). *AI unlocks the emotional language of animals*. Copenhagen / ScienceDaily.
7. Harnad, S. (1991). *Other bodies, other minds*. Minds and Machines 1:43–54.
8. Saygin et al. (2000). *Turing Test: 50 years later*. Minds and Machines 10:463–518.
