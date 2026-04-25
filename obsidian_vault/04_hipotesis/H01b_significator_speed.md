---
id: H01b
tipo: hipotesis
estado: "⚠️ parcial — velocidad confirmada, varianza geográfica refutada"
tags: [hipotesis, dominio, velocidad]
---

# H01b — Significator Speed Hypothesis

## Enunciado
La eficacia del filtro por dominio es función de la velocidad orbital
media de los planetas significadores del dominio.
Dominios con significadores rápidos (Luna, Mercurio, Venus) generan
mayor variabilidad geográfica en HF_domain, amplificando la señal.
Dominios con significadores lentos (Júpiter, Saturno, planetas
exteriores) producen campos casi uniformes, colapsando la señal.

## Fundamento
Velocidad orbital → variabilidad de posición eclíptica → variabilidad
del aspecto geométrico a cada punto del horizonte → variabilidad del HF.
Planetas lentos tienen posición casi idéntica en todos los sujetos
del mismo período histórico → HF_domain casi idéntico → sin discriminación.

## Datos disponibles (2026-04-01)

| Dominio | % Rápidos | % Lentos | Velocidad media | std HF_domain |
|---------|-----------|----------|-----------------|---------------|
| H05 Creatividad | 50.0% | 36.7% | 2.67 deg/día | 0.323 |
| H10 Carrera | 41.1% | 46.7% | 0.96 deg/día | 0.362 |

**Ratio velocidad H05/H10 = 2.77x** — H05 significadores son 3x más rápidos.

**Varianza geográfica**: H10 es *ligeramente mayor* que H05 (0.362 vs 0.323).
Esto contradice la predicción de la hipótesis para la varianza geográfica.

## Estado
PARCIALMENTE CONFIRMADA EN VELOCIDAD · REFUTADA EN VARIANZA GEOGRÁFICA

- La diferencia de velocidades existe y es sustancial (2.77x)
- Pero la varianza geográfica del campo filtrado NO es menor en H10
- Conclusión: la velocidad orbital sola no explica la diferencia en resultados

## Posibles explicaciones alternativas
1. El colapso de d_domain en H10 es un artefacto de N−=5, no del campo
2. La varianza del campo filtrado es similar, pero la señal se pierde en el ruido del corpus
3. Los significadores lentos de H10 generan mayor varianza geográfica en algunos sujetos
   (ver distribución bimodal en parquets: algunos sujetos H10 tienen std_h10 > 0.5)

## Implicación arquitectónica
El HF_domain es útil como filtro para H05 (confirmado).
Para H10, la validación requiere más eventos negativos antes de concluir.
La velocidad orbital no es el único factor relevante para la calidad del filtro.

## Estado
[[EXP_004_HF_v6_domain]] — pendiente de nueva validación con corpus balanceado
[[H01_domain_specificity]] — hipótesis madre

## Próximo experimento sugerido
EXP_005: Con N−≥20 en H10 (post-curaduría Wikidata), recalcular d_domain
y comparar con d_global. Si persiste el colapso → refutación definitiva.
Si d_domain mejora → la hipótesis madre H01 se confirma para H10 también.
