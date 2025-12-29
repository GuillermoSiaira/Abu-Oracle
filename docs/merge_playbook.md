# Merge Playbook: AI_Oracle ↔ v0

Operational guide for integrating the AI_Oracle repository with the forthcoming v0 repository using one of two strategies: direct merge or subtree.

## Goals
- Preserve full commit history of AI_Oracle.
- Minimize merge conflicts.
- Allow reversible decision (subtree vs full merge) without blocking work.

## Strategies

### 1. Direct Merge (Unrelated Histories)
Best when v0 will fully absorb AI_Oracle at root level.

Steps (run inside v0 repo):
```bash
# Add AI_Oracle as remote
git remote add ai_oracle https://github.com/<org>/ai-oracle.git

# Fetch all
git fetch --all

# Create integration branch starting from v0 main
git checkout -b integrate-ai-oracle origin/main

# Merge unrelated histories
git merge --allow-unrelated-histories ai_oracle/main -m "Merge AI_Oracle into v0"

# Resolve conflicts and stage
# ... (manual resolution)

# Push branch
git push -u origin integrate-ai-oracle
```
Pros:
- Single unified root structure.
- Easier for contributors who want one entry point.
Cons:
- Higher chance of path collision if v0 adds similar folders.
- Harder to extract later.

### 2. Git Subtree (Recommended for Monorepo)
Best when v0 will host multiple apps/services and AI_Oracle is one module.

Installation (inside v0 repo):
```bash
# Add AI_Oracle as subtree under apps/ai_oracle
git subtree add --prefix apps/ai_oracle https://github.com/<org>/ai-oracle.git main --squash
```
Updating later:
```bash
git subtree pull --prefix apps/ai_oracle https://github.com/<org>/ai-oracle.git main --squash
```
Pros:
- Clearly scoped path (`apps/ai_oracle`).
- Low conflict risk.
- Can selectively export later.
Cons:
- Squashed history if using --squash (you can omit to keep full history, but log will be larger).
- Slightly less known pattern for some devs.

### Decision Matrix
| Scenario | Recommended |
|----------|-------------|
| v0 = future monorepo | Subtree |
| v0 replaces AI_Oracle | Merge |
| Need clean extraction later | Subtree |
| Want all commits inline | Merge (or Subtree w/o squash) |

## Pre-Merge Checklist
- [ ] v0 scaffold avoids AI_Oracle folder names (`next_app/`, `abu_engine/`, `lilly_engine/`, `docs/`).
- [ ] .gitattributes configured for safe merge behaviors.
- [ ] CI/pipeline in v0 doesn't assume service paths that collide.
- [ ] Decide on strategy (record in ADR or README).

## Conflict Resolution Tips (Direct Merge)
Common hotspots:
- `README.md`: Keep both; rename one to `README_AI_ORACLE.md` if needed.
- `docker-compose.yml`: Retain AI_Oracle version; add v0 overrides in `compose/`.
- `package.json` (root): If both exist, unify dependencies manually; prefer version ranges already tested.
- `.gitignore`: Concatenate; remove duplicates.

Resolution flow:
```bash
git status
# Open each conflict file, resolve, then:

git add <file>

# After all resolved:
git commit
```

## Post-Merge/Subtree Validation
```bash
git log --graph --oneline --decorate | head -n 30

git ls-files | grep abu_engine | wc -l

git ls-files | grep lilly_engine | wc -l

git ls-files | grep next_app | wc -l
```
Checks:
- AI_Oracle folders present and intact.
- v0 scaffold directories still present.

## Rollback Plan
- Direct merge: `git reset --hard <commit_before_merge>` (if branch not pushed) or delete branch.
- Subtree add: `git rm -r apps/ai_oracle && git commit -m "Remove subtree"`.

## Future Migration Path (If Rehoming Entire Project to v0)
1. Freeze AI_Oracle main (tag `pre-migration`).
2. Subtree add into v0.
3. Move active development to v0 branches.
4. Archive AI_Oracle repo (set to read-only or update README with notice).

## FAQs
Q: Why not git submodules?  
A: Higher friction (extra clone steps, version drifting) and poorer DX vs subtree.

Q: Can we unsquash later?  
A: No; if you need full history, omit `--squash` initially.

Q: How to sync AI_Oracle changes into v0 regularly?  
A: Automate `git subtree pull --prefix apps/ai_oracle <repo> main` in a cron/CI job.

## References
- `docs/v0_repo_scaffold.md` (scaffold structure)
- Git docs: Subtree merges

Record the chosen strategy in an ADR once decided.
