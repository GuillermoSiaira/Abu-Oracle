"""
CLI principal del MILP Framework.

Uso:
  python run_milp.py --instance abu_oracle
  python run_milp.py --instance paperclip --heartbeat 1.0 --b-interno 500
  python run_milp.py --instance both --b-total 3000
  python run_milp.py --instance abu_oracle --output json
  python run_milp.py --instance abu_oracle --output-config
  python run_milp.py --instance paperclip --output-config
  python run_milp.py --instance both --output-config
"""
from __future__ import annotations
import argparse, json, sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from adapters.abu_oracle_adapter import get_recommendations, get_config_json as abu_config_json
from adapters.paperclip_adapter import get_agent_config, get_config_json as paperclip_config_json


# ---------------------------------------------------------------------------
# Formateadores de output legible
# ---------------------------------------------------------------------------

def _print_abu_oracle(rec: dict) -> None:
    s1 = rec['scenario_sonnet_everywhere']
    s2 = rec['scenario_milp_optimized']
    cmp = rec['pricing_comparison']

    print("\n" + "═" * 60)
    print("  MILP Abu Oracle — Instancia A")
    print(f"  Datos: {rec['data_source'].upper()}")
    print("═" * 60)

    print("\n── Escenario 1: Sonnet Everywhere ─────────────────────────")
    print(f"  Status: {s1['status']}")
    print(f"  Costo mensual estimado: ${s1['total_cost_monthly']:,.2f}")
    print("  Rutas:")
    for u, r in s1['routes'].items():
        tag = "  ▶ crítica " if r['is_critical'] else "  ○ secundaria"
        print(f"  {tag}  {u:<14} → {r['model']:<7} max_tokens={r['max_tokens']}")
    print("  Precios mínimos sostenibles (costo + margin floor):")
    for k, p in s1['pricing'].items():
        if k == 'genesis': continue
        print(f"    {k:<10} actual=${p['current']:.2f}  mínimo sostenible=${p['min_sustainable']:.2f}  gap=${p['gap']:.2f}")

    print("\n── Escenario 2: MILP Optimizado (secundarias libres) ────────")
    print(f"  Status: {s2['status']}")
    print(f"  Costo mensual estimado: ${s2['total_cost_monthly']:,.2f}")
    print("  Rutas:")
    for u, r in s2['routes'].items():
        tag = "  ▶ crítica " if r['is_critical'] else "  ○ secundaria"
        decision = " ← MILP decide" if not r['is_critical'] else ""
        print(f"  {tag}  {u:<14} → {r['model']:<7} max_tokens={r['max_tokens']}{decision}")
    print("  Precios mínimos sostenibles:")
    for k, p in s2['pricing'].items():
        if k == 'genesis': continue
        print(f"    {k:<10} actual=${p['current']:.2f}  mínimo sostenible=${p['min_sustainable']:.2f}  gap=${p['gap']:.2f}")

    if s2['shadow_prices']:
        print("  Shadow prices (constraints binding):")
        for name, val in s2['shadow_prices'].items():
            print(f"    {name}: {val}")

    print("\n── Comparación de precios ───────────────────────────────────")
    print(f"  {'Plan':<12} {'Actual':>8} {'Sonnet-all':>12} {'MILP opt.':>12} {'Ahorro/usr':>12}")
    print("  " + "-" * 58)
    for k, v in cmp.items():
        if k == 'genesis': continue
        print(f"  {k:<12} ${v['current']:>6.2f}  ${v['sonnet_everywhere_min']:>9.2f}  ${v['milp_optimized_min']:>9.2f}  ${v['saving_per_user']:>9.2f}")


def _print_paperclip(cfg: dict) -> None:
    print("\n" + "═" * 60)
    print("  MILP Paperclip — Instancia B")
    print(f"  Datos: {cfg['data_source'].upper()}")
    print("═" * 60)
    print(f"\n  Status:           {cfg['status']}")
    print(f"  Costo mensual:    ${cfg['b_interno_monthly']:,.2f}  /  presupuesto ${cfg['b_interno_budget']:,.2f}")
    print(f"  Utilización:      {cfg['utilization_pct']}%")
    print(f"  Heartbeat recom.: {cfg['heartbeat_recommended_hours']:.1f}h")
    print(f"  Señal congestión: {'SÍ ⚠' if cfg['congestion_signal'] else 'NO ✓'}")
    print("\n  Agentes:")
    for agent, a in cfg['agents'].items():
        print(f"    {agent:<15} → {a['model']:<7}  max_tokens={a['max_tokens']}")
    if cfg['shadow_prices']:
        print("  Shadow prices:")
        for name, val in cfg['shadow_prices'].items():
            print(f"    {name}: {val}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description='MILP Framework — Abu Oracle & Paperclip')
    parser.add_argument('--instance', choices=['abu_oracle', 'paperclip', 'both'], default='both')
    parser.add_argument('--b-total',      type=float, default=3000.0)
    parser.add_argument('--b-produccion', type=float, default=None)
    parser.add_argument('--b-interno',    type=float, default=500.0)
    parser.add_argument('--heartbeat',    type=float, default=1.0, help='Heartbeat en horas')
    parser.add_argument('--output', choices=['text', 'json'], default='text')
    parser.add_argument('--output-config', action='store_true',
                        help='Escribe JSON ejecutable en output/ (consumible por dashboard y Paperclip)')
    args = parser.parse_args()

    out_dir = Path(__file__).parent / 'output'

    # ---- Modo --output-config: genera archivos JSON directamente consumibles ----
    if args.output_config:
        out_dir.mkdir(exist_ok=True)
        if args.instance in ('abu_oracle', 'both'):
            data = abu_config_json(b_total=args.b_total, b_produccion=args.b_produccion)
            path = out_dir / 'abu_oracle_config.json'
            path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
            print(f'Escrito: {path}')
        if args.instance in ('paperclip', 'both'):
            data = paperclip_config_json(b_interno=args.b_interno, heartbeat_hours=args.heartbeat, b_total=args.b_total)
            path = out_dir / 'paperclip_config.json'
            path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
            print(f'Escrito: {path}')
        return

    # ---- Modos text / json ----
    results = {}

    if args.instance in ('abu_oracle', 'both'):
        rec = get_recommendations(
            b_total=args.b_total,
            b_produccion=args.b_produccion,
        )
        results['abu_oracle'] = rec
        if args.output == 'text':
            _print_abu_oracle(rec)

    if args.instance in ('paperclip', 'both'):
        cfg = get_agent_config(
            b_interno=args.b_interno,
            heartbeat_hours=args.heartbeat,
            b_total=args.b_total,
        )
        results['paperclip'] = cfg
        if args.output == 'text':
            _print_paperclip(cfg)

    if args.output == 'json':
        print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
