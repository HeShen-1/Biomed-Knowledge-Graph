# Biomed Knowledge Graph Platform

Full-stack biomedical knowledge graph integrating UniProt, STRING, ChEMBL, Open Targets, and PubMed data.
44,294 nodes · 71,453 edges across 5 relationship types.

## Architecture

```
backend/                          # Python FastAPI
  app/
    main.py                       # FastAPI app, CORS (:5173/:5174), request_id middleware, global error handler
    config.py                     # Pydantic BaseSettings (BIOMED_ prefix), dev-mode allows default neo4j password
    errors.py                     # AppError subclasses (404/408/400/502/503) + catch-all Exception→500 handler
    db/                           # neo4j.py (basic_auth, keep_alive, max_connection_lifetime=3600)
                                  # postgres.py (asyncpg pool, min=2 max=10)
    models/                       # Pydantic models: graph.py (EdgeModel has source_id/target_id), search.py, ingest.py
    routers/                      # HTTP layer: graph.py, search.py, ingest.py
    repositories/                 # Data access: parameterized Cypher, full-text search, DISTINCT+LIMIT, query timeout
    services/                     # Business logic (no FastAPI imports)
  ingest/                         # Data pipeline
    base.py                       # BaseIngester + UNWIND batched build_queries + _derive_type() prefix mapping
    pipeline.py                   # Orchestrator: fetch→normalize→flush with retry + rate-limit
    models.py                     # NormalizedRecord, NormalizedNode, NormalizedEdge
    serializers.py                # safe_label/safe_relation whitelist + batch_write
    sources/                      # uniprot.py, string.py, chembl.py, opentargets.py, pubmed.py
    resolvers/                    # gene.py, disease.py, compound.py
    stats.py                      # PG ingest_status upsert
    search_sync.py                # PG entities_search sync
  tasks/                          # Celery (include=["tasks.sync"], worker_pool="solo" for Windows)
  migrations/                     # SQL DDL: entities_search, ingest_status, ingest_log
  tests/                          # pytest 18 tests (unit + snapshot, all pass)
frontend/                         # React 18 + TypeScript 5 + Vite 6
  src/
    pages/GraphExplorer/          # Three-panel layout + dark/light theme + anime.js v4 animations
      GraphCanvas/                # CytoscapeRenderer (incremental cy.add, useMemo elements, rAF stagger)
                                  # GraphCanvas (legend, node/edge count, empty state)
                                  # LayoutControls (props-based: layout + onLayoutChange)
      SearchPanel/                # SearchInput (magnifier icon + Cmd+K), FilterBar (chip toggle)
                                  # SuggestionList (stagger entrance, type badges, CSS :hover)
      DetailPanel/                # NodeDetail (KV table with stagger), RelationTable (color-coded by relation)
                                  # ExternalLinks (external link icon + source label)
      ThemeToggle.tsx             # Knob slides left↔right, sun ☀/moon ☾ icons
    api/                          # Axios client, EdgeData has source_id: string + target_id: string (required)
    hooks/                        # TanStack Query hooks + useCytoscapeState (combined Zustand selector)
    store/                        # searchStore, graphStore, uiStore, themeStore (4 independent stores)
    styles/                       # Dark theme (default) + light theme CSS variables + prefers-reduced-motion
    __tests__/                    # Vitest unit + Playwright E2E
```

## Key Conventions

- **Backend layer order**: routers → services → repositories (enforced by import-linter)
- **Models are pure**: no internal imports allowed
- **Ingest sources independent**: no cross-source imports
- **Env vars**: BIOMED_ prefix, loaded from .env via pydantic-settings
- **Frontend state**: Zustand for UI state, TanStack Query for server state
- **Cytoscape.js**: incremental updates (cy.add/remove), 9px labels, text-wrap: ellipsis, 18-char truncation
- **API proxy**: Vite proxies /api → localhost:8000
- **Neo4j**: basic_auth() required for driver 6.x, never use tuple auth or routing_="r"
- **Theme**: data-theme attribute on <html>, localStorage persistence, CSS variables switch

## CodeGraph

This project has a CodeGraph index (`.codegraph/`). Prefer it over grep/Glob for structural queries.

| Question | Tool |
|---|---|
| "Where is X defined?" | `codegraph_search` |
| "What calls Y?" / "What does Y call?" | `codegraph_callers` / `codegraph_callees` |
| "What would break if I changed Z?" | `codegraph_impact` |
| "Show me Y's source/signature" | `codegraph_node` |
| "Context for a task/feature/area" | `codegraph_context` (one call, composes search+callers+callees) |
| "See several related symbols at once" | `codegraph_explore` (one capped call, prefer over many codegraph_node) |
| "What files in directory X?" | `codegraph_files` |

**Rules**: Answer structural questions with 2-3 codegraph calls — `codegraph_context` first, then `codegraph_explore` for source. Don't delegate exploration to subagents. Don't grep first for symbol lookup. Don't chain `codegraph_search` + `codegraph_node` when `codegraph_context` does both. Index lags ~500ms behind writes — don't re-query immediately after editing in same turn.

## Databases

- **Neo4j 5-community** (Docker): bolt://localhost:7687, neo4j/password, 44K nodes, 71K edges
- **PostgreSQL 16-alpine** (Docker): localhost:5434, biomed/biomed123/biomed, 32K search rows
- **Redis 7-alpine** (Docker): localhost:6380, Celery broker + result backend

## Current Data

| Label | Count |
|-------|-------|
| Gene | 20,200 |
| Protein | 23,090 |
| Compound | 941 |
| Disease | 11 |
| Article | 52 |

| Relation | Count |
|----------|-------|
| ENCODES | 19,425 |
| INTERACTS_WITH | 49,919 |
| BINDS_TO | 500 |
| TARGETS | 1,599 |
| MENTIONS | 10 |

## Commands

| What | Command |
|------|---------|
| Backend dev | `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Frontend dev | `cd frontend && npm run dev` |
| Backend tests | `cd backend && python -m pytest tests/ -v` (18 pass) |
| Frontend tests | `cd frontend && npx vitest run` |
| E2E tests | `cd frontend && npx playwright test` |
| Python lint | `cd backend && ruff check .` |
| TS lint | `cd frontend && npm run lint` |
| Type check | `cd frontend && npx tsc -b` |
| Celery worker | `cd backend && python -m celery -A tasks.celery_app worker --loglevel=info --pool=solo` |
| Frontend build | `cd frontend && npx vite build` |
| Start databases | `docker start biomed-postgres biomed-neo4j biomed-redis` |

## Ingest Pipeline

Sources: UniProt (gene→protein), STRING (protein-protein, 35 key genes), ChEMBL (compounds + BINDS_TO), Open Targets (gene→disease, 10 diseases), PubMed (article→gene)
Flow: source → pipeline (fetch → normalize → flush via UNWIND batch) → Neo4j + Postgres
Windows: use `--pool=solo` for Celery worker

## Known Gaps

- STRING protein IDs use gene symbols, UniProt uses accessions — separate nodes, need resolver
- ChEMBL target IDs (`protein:CHEMBL_*`) don't match UniProt accessions
- OpenTargets limited to 1 page/disease (dev setting)
- UniProt ASSOCIATED_WITH edges not populated (source data lacks disease comments)
- No code splitting for anime.js + cytoscape (~700KB combined)
- Neo4j indexes on :NodeType(id) should be verified at startup
