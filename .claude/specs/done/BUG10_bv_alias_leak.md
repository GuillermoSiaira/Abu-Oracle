# BUG-10 — Blind Validation: subject_real leaks into public vault

## Context

`scripts/blind_validation/run_blind_validation.py` generates two output files per experiment:

- `data/blind_validation/BV_NNN_alias.md` — internal file, gitignored (`data/` is in .gitignore) ✅ safe
- `obsidian_vault/03_experimentos/BV_NNN_alias.md` — committed to git, **publicly visible on GitHub** ❌

The vault file currently includes `subject_real` in two places:
1. YAML frontmatter: `subject_real: Donald Trump`
2. Body text: `**Identidad real:** Donald Trump (conocida por el verificador...)`
3. Tags: `tags: [blind_validation, carta_ciega, trump, ...]` — subject name in tag

This breaks the blind validation protocol: Lilly must read the chart without knowing the identity,
and the vault file is generated *before* the verification step.

**Bug status**: 🔴 Open — blocking all new BV experiments.

---

## Files to modify

### 1. `scripts/blind_validation/run_blind_validation.py`

#### Fix A — Auto-generate opaque alias (lines 67, 391, 393)

Current `--alias` default is `"Mr. X"` which is a known placeholder, not opaque.

Replace the alias generation logic in `main()`:

```python
# BEFORE (line 391-393):
bv_id = _next_bv_id()
slug = _slug(args.alias)
print(f"[BV] Iniciando experimento {bv_id} — alias: {args.alias}", flush=True)

# AFTER:
import hashlib
bv_id = _next_bv_id()
_hash_input = f"{args.date}{args.time}{args.lat}{args.lon}"
_opaque = "NTV-" + hashlib.sha256(_hash_input.encode()).hexdigest()[:4].upper()
alias = args.alias if args.alias != "Mr. X" else _opaque
slug = _slug(alias)
print(f"[BV] Iniciando experimento {bv_id} — alias: {alias}", flush=True)
```

Then pass `alias` (not `args.alias`) to all subsequent calls.

#### Fix B — Remove subject_real from `_render_obsidian_md()` (lines 268-325)

The Obsidian note must NOT contain `subject_real` anywhere.

```python
# REMOVE from YAML frontmatter:
subject_real: {subject_real}          # ← DELETE this line

# REMOVE from body:
**Identidad real:** {subject_real}... # ← DELETE this line

# CHANGE tags — remove any subject-derived tag:
tags: [blind_validation, carta_ciega, lilly]  # ← no subject name in tags
```

The function signature can keep `subject_real` as a parameter (for future use or logging)
but must not render it into the returned string.

#### Fix C — Remove `subject_real` from function signature of `_render_obsidian_md`

Since `subject_real` is no longer used inside `_render_obsidian_md`, remove it from the
parameter list and from the call site in `main()` (line 432-442).

---

### 2. `obsidian_vault/03_experimentos/BV_001_trump.md`

The existing BV_001 experiment file leaks the subject identity in the vault.
Since BV_001 was already completed and verified, the reveal was intentional —
but the YAML frontmatter field `subject_real` should still be removed to be consistent
with the fixed protocol.

Remove only: `subject_real: Donald Trump` from the YAML frontmatter.
Keep the body text as-is (BV_001 is a completed experiment with a documented reveal).

---

## What NOT to change

- `data/blind_validation/` rendering (`_render_bv_md`) — these files are gitignored, `subject_real` there is correct
- `_update_index()` — `subject_real` in `BV_index.json` is fine (file is gitignored)
- The `--subject-real` CLI argument itself — it must be collected, just not written to the vault
- `_build_doctrinal_context()` — uses `alias` only, already correct
- `_call_lilly()` — already correct
- Score/verification workflow — no changes needed

---

## Verification

After the fix, run:

```bash
# Dry-run: generate a fake experiment and inspect output
python scripts/blind_validation/run_blind_validation.py \
    --date 1856-07-10 --time 00:00 \
    --lat 46.07 --lon 14.50 \
    --subject-real "Nikola Tesla" \
    --rodden B \
    --abu-url http://localhost:8000
```

Check that:
1. The generated `obsidian_vault/03_experimentos/BV_NNN_*.md` does NOT contain "Tesla" or "Nikola"
2. The generated `obsidian_vault/03_experimentos/BV_NNN_*.md` does NOT have `subject_real:` in frontmatter
3. The alias in stdout is either the provided `--alias` or `NTV-XXXX` format
4. The `data/blind_validation/BV_NNN_*.md` DOES contain `subject_real: Nikola Tesla` (internal file, gitignored)

If Abu Engine is not running locally, the test will fail at chart fetch — that's expected.
In that case, verify only by code review of the rendered template strings.

---

## Commit message

```
fix(bv): remove subject_real from vault output — BUG-10

- _render_obsidian_md: strip subject_real from YAML frontmatter and body
- main(): auto-generate NTV-XXXX alias when --alias not provided
- BV_001_trump.md: remove subject_real from frontmatter (body kept as-is)
- data/blind_validation/ output unchanged (gitignored, subject_real correct there)
```
