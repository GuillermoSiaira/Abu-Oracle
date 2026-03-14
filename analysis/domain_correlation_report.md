# Domain Correlation Report — HF por Casa

Total events analysed: 527

## Hypothesis
corr(HF_domain, valence_domain) > corr(HF_global, valence_domain)

## Results by House Domain

| Casa | N eventos | N+ | N- | corr_global | corr_domain | d_global | d_domain | Δcorr |
|------|-----------|----|----|-------------|-------------|----------|----------|-------|
|    2 |         2 |  0 |  2 | n/a         | n/a         | n/a      | n/a      | n/a   |
|    4 |        34 |  2 |  3 | -0.001      | +0.305      | +0.025   | +1.311   | +0.306 |
|    5 |        57 | 51 |  1 | +0.198      | +0.353      | n/a      | n/a      | +0.155 |
|    6 |        18 |  0 | 10 | -0.317      | +0.051      | n/a      | n/a      | +0.369 |
|    7 |        93 | 81 |  9 | +0.098      | +0.088      | +0.250   | +0.246   | -0.010 |
|    8 |        34 |  0 | 34 | n/a         | n/a         | n/a      | n/a      | n/a   |
|    9 |        56 | 35 |  1 | +0.014      | -0.123      | n/a      | n/a      | -0.138 |
|   10 |       226 | 208 |  4 | +0.090      | +0.033      | +0.871   | -0.033   | -0.057 |
|   12 |         7 |  0 |  5 | +0.472      | -0.224      | n/a      | n/a      | -0.695 |

## Summary

Hypothesis confirmed in 3/7 domains with valid data.

## Notes
- `corr_domain`: correlation of domain-filtered HF vs valence for same-domain events.
- `corr_global`: correlation of global HF vs valence for same-domain events (baseline).
- `Δcorr`: corr_domain - corr_global (positive = hypothesis confirmed).
- Cohen's d: effect size between positive and negative events.