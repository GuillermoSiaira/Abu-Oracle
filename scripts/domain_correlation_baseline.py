"""
Tarea 2.3 — Correlación segmentada por house_domain (baseline global)
Hipótesis: corr(HF_global | eventos_hX) varía por casa.
Este script genera el baseline con hf_weighted global — el campo de dominio
específico se agrega en Fase 3.

Fuentes:
- data/biographical_events/correlation_results.json → HF values + valence_num
- data/biographical_events_v2/*.json → house_domain por evento
"""

import json
import glob
import os
import math
from collections import defaultdict

# ── casas a analizar ──────────────────────────────────────────────────────────
ROBUST_HOUSES = {5, 7, 8, 9, 10}
WEAK_HOUSES   = {6, 12}   # señal débil, n insuficiente
SKIP_HOUSES   = {1, 2}    # ignorar

# ── cargar house_domain desde biographical_events_v2 ─────────────────────────
def load_house_domain_map():
    """
    Devuelve dict keyed by (subject_id, date, event_type) → house_domain.
    """
    hmap = {}
    for f in glob.glob("data/biographical_events_v2/*.json"):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            events = data
            meta_id = None
        elif isinstance(data, dict):
            meta = data.get("meta", {})
            # meta key is 'id', not 'subject_id'
            meta_id = str(meta.get("id") or meta.get("subject_id") or "").strip() or None
            events = data.get("biographical_events", [])
        else:
            continue

        for ev in events:
            sid   = str(ev.get("subject_id") or meta_id or "").strip()
            date  = str(ev.get("date") or ev.get("event_date") or "").strip()
            etype = str(ev.get("event_type") or "").strip()
            hd    = ev.get("house_domain")
            if sid and date and etype and hd is not None:
                hmap[(sid, date, etype)] = hd
    return hmap


# ── cargar eventos con HF values ──────────────────────────────────────────────
def load_corr_events():
    path = "data/biographical_events/correlation_results.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


# ── estadísticas ──────────────────────────────────────────────────────────────
def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx  = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy  = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def cohens_d(pos_vals, neg_vals):
    if len(pos_vals) < 2 or len(neg_vals) < 2:
        return float("nan")
    n1, n2 = len(pos_vals), len(neg_vals)
    m1, m2 = sum(pos_vals) / n1, sum(neg_vals) / n2
    v1 = sum((x - m1) ** 2 for x in pos_vals) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in neg_vals) / (n2 - 1)
    pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return float("nan")
    return (m1 - m2) / pooled_sd


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading house_domain map from biographical_events_v2…")
    hmap = load_house_domain_map()
    print(f"  {len(hmap)} (subject, date, type) keys loaded")

    print("Loading HF events from correlation_results.json…")
    events = load_corr_events()
    print(f"  {len(events)} events total")

    # join
    joined = 0
    unjoined = 0
    by_house = defaultdict(list)

    for ev in events:
        sid   = str(ev.get("subject_id", "")).strip()
        date  = str(ev.get("event_date") or ev.get("date") or "").strip()
        etype = str(ev.get("event_type", "")).strip()
        hf    = ev.get("transit_hf_weighted")
        vn    = ev.get("valence_num")
        val   = ev.get("valence", "")

        if hf is None or vn is None:
            continue

        hd = hmap.get((sid, date, etype))
        if hd is None:
            # try with 'date' field instead of 'event_date'
            hd = hmap.get((sid, ev.get("date", date), etype))

        if hd is None:
            unjoined += 1
            continue

        joined += 1
        by_house[hd].append({"hf": hf, "vn": vn, "valence": val})

    print(f"  Joined: {joined} | Unjoined: {unjoined}")

    # ── compute stats per house ───────────────────────────────────────────────
    results = {}
    for house in sorted(by_house.keys()):
        evs = by_house[house]
        hf_vals = [e["hf"] for e in evs]
        vn_vals = [e["vn"] for e in evs if e["vn"] != 0]  # skip neutral
        hf_nn   = [e["hf"] for e in evs if e["vn"] != 0]

        pos_hf = [e["hf"] for e in evs if e["vn"] > 0]
        neg_hf = [e["hf"] for e in evs if e["vn"] < 0]

        n_all = len(evs)
        n_pos = len(pos_hf)
        n_neg = len(neg_hf)

        corr_all = pearson(hf_vals, [e["vn"] for e in evs])
        corr_nn  = pearson(hf_nn, vn_vals)
        cd       = cohens_d(pos_hf, neg_hf)

        mean_pos = sum(pos_hf) / len(pos_hf) if pos_hf else float("nan")
        mean_neg = sum(neg_hf) / len(neg_hf) if neg_hf else float("nan")

        results[house] = {
            "n": n_all, "n_pos": n_pos, "n_neg": n_neg,
            "corr_all": corr_all, "corr_nn": corr_nn,
            "cohens_d": cd,
            "mean_pos": mean_pos, "mean_neg": mean_neg,
        }

    # ── report ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("BASELINE — correlación global segmentada por house_domain")
    print("=" * 72)
    fmt = "{:<6} {:>7} {:>7} {:>7} {:>11} {:>10} {:>10}"
    print(fmt.format("Casa", "N", "N+", "N-", "corr_all", "corr_nn", "Cohen's d"))
    print("-" * 72)

    for house in sorted(ROBUST_HOUSES):
        if house not in results:
            print(f"H{house:02d}    {'—':>7}  (no events joined)")
            continue
        r = results[house]
        print(fmt.format(
            f"H{house:02d}",
            r["n"], r["n_pos"], r["n_neg"],
            f"{r['corr_all']:+.3f}",
            f"{r['corr_nn']:+.3f}",
            f"{r['cohens_d']:+.3f}",
        ))

    print()
    print("Casas con señal débil (n insuficiente — sin cálculo):")
    for h in sorted(WEAK_HOUSES):
        n = len(by_house.get(h, []))
        print(f"  H{h:02d}: {n} eventos")

    print()
    print("Referencia global (todos los eventos, sin segmentar):")
    all_evs = [e for evs in by_house.values() for e in evs]
    all_hf = [e["hf"] for e in all_evs]
    all_vn = [e["vn"] for e in all_evs]
    all_nn_hf = [e["hf"] for e in all_evs if e["vn"] != 0]
    all_nn_vn = [e["vn"] for e in all_evs if e["vn"] != 0]
    pos_all = [e["hf"] for e in all_evs if e["vn"] > 0]
    neg_all = [e["hf"] for e in all_evs if e["vn"] < 0]
    print(f"  N={len(all_evs)} | corr_all={pearson(all_hf,all_vn):+.3f} | "
          f"corr_nn={pearson(all_nn_hf,all_nn_vn):+.3f} | "
          f"Cohen's d={cohens_d(pos_all,neg_all):+.3f}")

    # ── save markdown ─────────────────────────────────────────────────────────
    os.makedirs("analysis", exist_ok=True)
    md_path = "analysis/domain_correlation_baseline.md"
    lines = [
        "# Domain Correlation Baseline — Fase 2.3",
        "",
        "Correlación de `transit_hf_weighted` (campo global) contra `valence_num`,",
        "segmentada por `house_domain`. Baseline pre-Fase 3.",
        "",
        "| Casa | N | N+ | N− | corr_all | corr_nn | Cohen's d | corr_domain | cohens_d_domain |",
        "|------|---|----|----|----------|---------|-----------|-------------|-----------------|",
    ]
    for house in sorted(ROBUST_HOUSES):
        if house not in results:
            lines.append(f"| H{house:02d} | — | — | — | — | — | — | pendiente | pendiente |")
            continue
        r = results[house]
        lines.append(
            f"| H{house:02d} | {r['n']} | {r['n_pos']} | {r['n_neg']} "
            f"| {r['corr_all']:+.3f} | {r['corr_nn']:+.3f} | {r['cohens_d']:+.3f} "
            f"| pendiente | pendiente |"
        )
    lines += [
        "",
        "## Casas con señal débil (sin cálculo — n insuficiente)",
        "",
    ]
    for h in sorted(WEAK_HOUSES):
        n = len(by_house.get(h, []))
        lines.append(f"- **H{h:02d}**: {n} eventos — no se calcula correlación")
    lines += [
        "",
        "## Referencia global (sin segmentar)",
        "",
        f"N={len(all_evs)} | corr_all={pearson(all_hf,all_vn):+.3f} | "
        f"corr_nn={pearson(all_nn_hf,all_nn_vn):+.3f} | "
        f"Cohen's d={cohens_d(pos_all,neg_all):+.3f}",
        "",
        "## Notas",
        "",
        "- `corr_all`: Pearson sobre todos los eventos del segmento (incluye neutros)",
        "- `corr_nn`: Pearson excluyendo eventos de valencia neutra",
        "- `Cohen's d`: separación mean_pos − mean_neg / SD pooled",
        "- `corr_domain` / `cohens_d_domain`: pendiente Fase 3 (requiere grillas por dominio)",
    ]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved: {md_path}")


if __name__ == "__main__":
    main()
