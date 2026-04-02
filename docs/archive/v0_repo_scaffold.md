# v0 Repo Scaffold (Low-Conflict Merge Ready)

This guide defines the initial structure and guardrails for the new v0 repository so that we can:
- Minimize merge conflicts with AI_Oracle
- Preserve AI_Oracle history when merging (or using subtree)
- Keep clear boundaries between v0 and AI_Oracle assets

Use this document as the source-of-truth and copy the "Prompt to initialize v0" section directly when creating the new repo.

## Principles

- No top-level name collisions with AI_Oracle. Avoid: `next_app/`, `abu_engine/`, `lilly_engine/`, `docs/`.
- Keep v0 assets scoped under distinct folders: `apps/v0_web/`, `docs_v0/`, `infra_v0/`.
- Prefer separate compose files or a `compose/` directory (no root-level `docker-compose.yml` in v0).
- Add `.gitattributes` with safe merge strategies for common conflicts (lockfiles, envs, package manifests).

## Target Structure (v0)

```
.
├─ .gitattributes
├─ .gitignore
├─ LICENSE
├─ README.md
├─ docs_v0/
│  ├─ ADRs/
│  └─ Roadmap.md
├─ apps/
│  └─ v0_web/
│     ├─ README.md
│     ├─ package.json
│     ├─ src/
│     └─ (your framework of choice)
├─ compose/
│  └─ docker-compose.v0.yml
├─ infra_v0/
│  ├─ environments/
│  └─ pipeline/
└─ scripts/
   └─ dev.ps1
```

Notes:
- If v0 needs Docker, use `compose/docker-compose.v0.yml` to avoid clashing with AI_Oracle's `docker-compose.yml`.
- If v0 adds a Next.js app, keep it in `apps/v0_web/` so it won't collide with AI_Oracle's `next_app/`.
- Put v0 docs under `docs_v0/` to avoid conflicts with AI_Oracle `docs/`.

## .gitattributes (recommended)

Use sane defaults to reduce conflict churn:

```
# Prefer ours for environment files (local developer overrides)
*.env merge=ours
*.env.local merge=ours

# Lockfiles: keep theirs on v0 side to reduce churn during merges
package-lock.json merge=theirs
pnpm-lock.yaml merge=theirs
yarn.lock merge=theirs

# JSON manifests: attempt union for simple dependency additions
package.json merge=union

# OS/IDE noise
*.DS_Store merge=ours
.vscode/* merge=ours
```

Add custom drivers if needed:

```
# .git/config example
[merge "union"]
    name = Keep all unique lines from both versions
    driver = union
```

## Prompt to initialize v0

Copy/paste the following when creating v0 to scaffold the repo:

```
Create a new repository with the following structure and files:

- .gitattributes (use the content from this guide)
- .gitignore (Node, Python, Docker, OS/IDE ignores)
- LICENSE (MIT)
- README.md (project overview and how to run)
- docs_v0/
  - README.md
  - ADRs/ (empty placeholder)
  - Roadmap.md (initial milestones)
- apps/
  - v0_web/
    - README.md
    - package.json (empty skeleton, name: v0-web, scripts: dev/build/start)
    - src/ (empty placeholder)
- compose/
  - docker-compose.v0.yml (placeholder with a comment: "v0 services only")
- infra_v0/
  - environments/ (empty placeholder)
  - pipeline/ (empty placeholder)
- scripts/
  - dev.ps1 (echo "Run v0 dev stack")

Conventions:
- Do not add a root-level docker-compose.yml. Use compose/docker-compose.v0.yml instead.
- Do not create folders named next_app, abu_engine, lilly_engine, or docs to avoid collisions with AI_Oracle.
- Keep all v0-specific documentation under docs_v0/.
```

## Merge Strategies (two paths)

1) Merge AI_Oracle into v0 (unrelated histories)
- Create a branch in v0: `git checkout -b integrate-ai-oracle`
- Add AI_Oracle remote: `git remote add ai_oracle https://github.com/<org>/ai-oracle.git`
- Fetch: `git fetch ai_oracle`
- Merge: `git merge --allow-unrelated-histories ai_oracle/main`
- Resolve conflicts (should be minimal due to folder separation)

2) Add AI_Oracle as a subtree (preserves history, clean paths)
- In v0: `git subtree add --prefix apps/ai_oracle https://github.com/<org>/ai-oracle.git main --squash`
- Future updates: `git subtree pull --prefix apps/ai_oracle https://github.com/<org>/ai-oracle.git main --squash`

Recommendation: Start with option (2) if you want a monorepo structure in v0 with AI_Oracle nested. Use option (1) if you plan to fully unify repos at root later.

## Conflict Hotspots to Avoid

- `README.md`: Keep project-specific readmes separate (v0 in root, AI_Oracle inside its folder if subtree).
- `docker-compose.yml`: Use `compose/` in v0. AI_Oracle keeps its root-level compose.
- `docs/`: v0 uses `docs_v0/` to avoid clashing with AI_Oracle `docs/`.
- `next_app/`: v0’s web should live at `apps/v0_web/`.

## Verification Checklist (post-merge or subtree)

- [ ] `AI_Oracle` folders present and untouched: `abu_engine/`, `lilly_engine/`, `next_app/`, `docs/`.
- [ ] v0 folders isolated in `apps/v0_web/`, `docs_v0/`, `compose/`, `infra_v0/`.
- [ ] No root-level file collisions (`docker-compose.yml`, `README.md`, etc.).
- [ ] Git history preserved (check `git log --graph --decorate --oneline`).

## Notes

- If v0 later needs to consume AI_Oracle services, reference via Docker networks or compose overrides from v0.
- If v0 is purely frontend, point to AI_Oracle services via environment variables.
