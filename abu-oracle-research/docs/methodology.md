# Methodology

## Harmony Field (HF)

The Harmony Field is a geographic scalar field measuring natal chart resonance across ~9,425 grid points worldwide (2.5° resolution, lat ∈ [−70, 70], lon ∈ [−180, 175]).

### Formula



- **HF_aspects**: Gaussian resonance sum between planet pairs (fixed per chart)
- **HF_angles**: Angularity to ASC/MC/DESC/IC (varies with lat/lon)
- **HF_houses**: House occupation (varies with lat/lon)

### HF_weighted (production weights)



## Domain Filtering (HF_v6)

Per Axiom 8 of Axiomatics of Heavens v0.4, the HF is recalculated using only the planetary significators of the relevant life domain (house). The planet subset is derived by .

## Biographical Events

Events were labeled with  using . Only events with  per domain were included in domain-level analysis.

## Statistical Tests

- **Pearson r**: between  (−1/0/+1) and 
- **Cohen's d**:  — requires N+≥2 and N−≥2
- **p-value**: two-tailed Pearson significance test

## Data Quality

The  field is  in all records. The  field is used as a quality proxy:

| source_category | Rodden equiv. | N events |
|-----------------|---------------|----------|
| birth_certificate | AA | 425 |
| biography | A/B | 49 |
| other (GS curated) | manual | 53 |
