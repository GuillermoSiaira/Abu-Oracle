# H01 — Domain Specificity Hypothesis

## Enunciado
```
corr(HF_domain_k, eventos_casa_k) > corr(HF_global, eventos_casa_k)
para todo k con n_eventos >= 10.
```

## Fundamento doctrinal
**Axioma 8 — Especificidad de Dominio** (Axiomatics of Heavens v0.4):

> "El HF global mezcla señales de distintas casas. La correlación significativa
> emerge cuando el campo se calcula exclusivamente con los significadores
> de la casa correspondiente al tipo de evento."

Abu Mashar: "cuando los señores de los tiempos coinciden con los señores
del evento, el efecto es extremo e inconfundible."

## Estado

**PARCIALMENTE CONFIRMADA** — [[EXP_004_HF_v6_domain]]

| Casa | Resultado | Evidencia |
|------|-----------|-----------|
| H05 Creatividad | ✅ CONFIRMADA | Δr = +0.150 (0.200 → 0.350) |
| H07 Relaciones | ⬜ NEUTRO | Señal marginal en ambos modos |
| H09 Expansión | ⬜ DÉBIL | Señal negativa en ambos modos |
| H10 Carrera | ❌ REFUTADA | d colapsa (0.567 → 0.056) |
| H01/H02/H03/H04 | ⬜ N/A | N insuficiente |

## Limitación estructural conocida
El corpus tiene desbalance severo de valence (ratio positivo:negativo ≈ 5.5:1).
Esto impide que Pearson r detecte señal en dominios con casi solo positivos.
Cohen's d es más robusto para este desequilibrio, pero también falla cuando
N- < 2.

## Implicación arquitectónica
El HF debe calcularse con filtro de significadores de casa para producir señal
interpretable. Para H10, se requiere investigación adicional sobre qué
planetas son realmente predictivos vs qué planetas tienen varianza temporal.

## Próximo paso sugerido
- Excluir planetas transpersonales (Urano, Neptuno, Plutón) de los
  significadores de H10 y re-evaluar
- Ampliar corpus con eventos negativos en H10 para balancear valence

## Links
[[EXP_003_HF_v3_global]] — baseline global
[[EXP_004_HF_v6_domain]] — experimento de validación
