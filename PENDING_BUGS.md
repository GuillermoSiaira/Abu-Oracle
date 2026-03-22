# PENDING_BUGS.md

## BUG-01 — Dignidades planetarias: sistema moderno vs tradicional
**Archivo**: abu_engine/core/extended_calc.py
**Severidad**: Alta — afecta todas las lecturas de Lilly
**Descripción**:
extended_calc.py usa rulerships modernos (Urano→Acuario,
Plutón→Escorpio, Neptuno→Piscis). El sistema doctrinal de Abu Oracle
exige rulerships tradicionales (Saturno→Acuario, Marte→Escorpio,
Júpiter→Piscis) per Axiomática de los Cielos.

Impacto concreto verificado:
- Saturno en Leo: backend devuelve "peregrine", doctrina dice "detriment"
- Cualquier planeta en Acuario/Escorpio/Piscis puede tener
  dignidad incorrecta

Precaución antes de corregir:
- extended_calc.py puede tener dependencias con HF (dignity_score)
- Si se corrigen los rulerships, verificar que HF scores no cambian
  de forma que invalide la validación empírica (527 eventos)
- Mapear todas las dependencias antes de tocar el archivo

**Estado**: Pendiente diagnóstico completo antes de fix.
