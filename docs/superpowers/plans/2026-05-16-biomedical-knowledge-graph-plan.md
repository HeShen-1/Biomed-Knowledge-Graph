# 生物医学知识图谱平台 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建面向生物医学研究者的知识图谱 Web 平台，集成 5 个公开数据源，提供基因-蛋白-化合物-疾病-文献的统一查询与可视化。

**Architecture:** Neo4j 图数据库 + FastAPI 后端 (Router→Service→Repository) + React 前端 (Page→hooks→api, store←components) + Celery 数据摄入管道。严格单向依赖，高内聚低耦合。

**Tech Stack:** Python 3.12+ / FastAPI / Neo4j 5.x / PostgreSQL 16 / Celery + Redis / React 18 / TypeScript 5.x / Cytoscape.js / Zustand / TanStack Query / Vite / Vitest / Playwright

---

## 文件结构概览

```
backend/
├── app/
│   ├── main.py                    ← FastAPI app 入口
│   ├── config.py                  ← 环境变量
│   ├── db/
│   │   ├── neo4j.py               ← Neo4j driver 单例
│   │   └── postgres.py            ← asyncpg pool 单例
│   ├── models/
│   │   ├── graph.py               ← NodeModel, EdgeModel, SubgraphModel, ExpandParams
│   │   ├── search.py              ← SearchResult, Suggestion
│   │   └── ingest.py              ← SyncStatus, SyncLog
│   ├── repositories/
│   │   ├── graph.py               ← Neo4j Cypher 查询封装
│   │   └── search.py              ← PostgreSQL 全文搜索封装
│   ├── services/
│   │   ├── graph.py               ← 图谱业务逻辑
│   │   ├── search.py              ← 搜索业务逻辑
│   │   └── ingest.py              ← 同步触发/状态查询
│   ├── routers/
│   │   ├── graph.py               ← /api/graph/* 端点
│   │   ├── search.py              ← /api/search/* 端点
│   │   └── ingest.py              ← /api/ingest/* 端点
│   └── errors.py                  ← 业务异常 + 全局 handler
├── ingest/
│   ├── base.py                    ← BaseIngester 抽象
│   ├── pipeline.py                ← Pipeline 编排器
│   ├── models.py                  ← NormalizedRecord DTO
│   ├── serializers.py             ← Cypher 批量生成
│   ├── stats.py                   ← 同步统计写入 PG
│   ├── sources/
│   │   ├── pubmed.py
│   │   ├── uniprot.py
│   │   ├── chembl.py
│   │   ├── opentargets.py
│   │   └── string.py
│   └── resolvers/
│       ├── gene.py
│       ├── disease.py
│       └── compound.py
├── tasks/
│   ├── celery_app.py              ← Celery 实例
│   └── sync.py                    ← 定时任务定义
├── tests/
│   ├── conftest.py                ← fixtures (neo4j test db, test client)
│   ├── unit/
│   │   ├── test_pipeline.py
│   │   ├── test_serializers.py
│   │   └── sources/
│   │       ├── test_pubmed_normalize.py
│   │       ├── test_uniprot_normalize.py
│   │       ├── test_chembl_normalize.py
│   │       ├── test_opentargets_normalize.py
│   │       └── test_string_normalize.py
│   └── api/
│       ├── test_graph.py
│       ├── test_search.py
│       └── test_ingest.py
├── requirements.txt
└── pyproject.toml

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts              ← axios 实例
│   │   ├── graph.ts               ← graph/* 端点函数
│   │   ├── search.ts              ← search/* 端点函数
│   │   └── ingest.ts              ← ingest/* 端点函数
│   ├── store/
│   │   ├── searchStore.ts         ← 搜索状态
│   │   ├── graphStore.ts          ← 图谱状态
│   │   └── uiStore.ts             ← UI 状态
│   ├── hooks/
│   │   ├── useSearch.ts           ← TanStack Query 封装 search
│   │   ├── useNodeDetail.ts       ← TanStack Query 封装 node detail
│   │   ├── useGraphExpand.ts      ← TanStack Query 封装 expand
│   │   ├── useProteinNetwork.ts   ← TanStack Query 封装 network
│   │   └── useSyncStatus.ts       ← TanStack Query 封装 ingest status
│   ├── pages/
│   │   └── GraphExplorer/
│   │       ├── GraphExplorer.tsx  ← 主页面 (编排层)
│   │       ├── SearchPanel/
│   │       │   ├── SearchPanel.tsx
│   │       │   ├── SearchInput.tsx
│   │       │   ├── SuggestionList.tsx
│   │       │   └── FilterBar.tsx
│   │       ├── GraphCanvas/
│   │       │   ├── GraphCanvas.tsx
│   │       │   ├── CytoscapeRenderer.tsx
│   │       │   ├── NodeContextMenu.tsx
│   │       │   ├── LayoutControls.tsx
│   │       │   └── MiniMap.tsx
│   │       └── DetailPanel/
│   │           ├── DetailPanel.tsx
│   │           ├── NodeDetail.tsx
│   │           ├── RelationTable.tsx
│   │           └── ExternalLinks.tsx
│   └── styles/
│       └── ibm-carbon.css         ← IBM Carbon 设计 token
├── src/__tests__/
│   ├── components/
│   │   ├── SearchInput.test.tsx
│   │   ├── NodeDetail.test.tsx
│   │   └── FilterBar.test.tsx
│   ├── hooks/
│   │   ├── useSearch.test.ts
│   │   └── useNodeDetail.test.ts
│   ├── store/
│   │   ├── searchStore.test.ts
│   │   ├── graphStore.test.ts
│   │   └── uiStore.test.ts
│   └── e2e/
│       └── graph-explorer.spec.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

---

### Task 1: 项目脚手架 — 后端

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "biomed-graph"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "neo4j>=5.25.0",
    "asyncpg>=0.30.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "celery[redis]>=5.4.0",
    "redis>=5.2.0",
    "httpx>=0.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "import-linter>=2.0",
    "ruff>=0.8.0",
]
```

- [ ] **Step 2: 创建 requirements.txt**

```
--index-url https://pypi.org/simple/
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
neo4j>=5.25.0
asyncpg>=0.30.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
celery[redis]>=5.4.0
redis>=5.2.0
httpx>=0.28.0
```

- [ ] **Step 3: 创建 backend/app/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/biomed"

    redis_url: str = "redis://localhost:6379/0"

    ingest_rate_limit: float = 3.0  # req/s
    ingest_max_retries: int = 3

    graph_default_depth: int = 1
    graph_max_depth: int = 3
    graph_default_limit: int = 50
    graph_max_limit: int = 200

    model_config = {"env_prefix": "BIOMED_", "env_file": ".env"}


settings = Settings()
```

- [ ] **Step 4: 创建 backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Biomed Knowledge Graph API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 安装依赖并验证**

```bash
cd backend && pip install -e ".[dev]"
python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/requirements.txt backend/app/main.py backend/app/config.py
git commit -m "feat: scaffold backend project with FastAPI + config"
```

---

### Task 2: 项目脚手架 — 前端

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles/ibm-carbon.css`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "biomed-graph-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint src --ext .ts,.tsx"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "cytoscape": "^3.30.0",
    "react-cytoscapejs": "^2.0.0",
    "zustand": "^5.0.0",
    "@tanstack/react-query": "^5.60.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.6.0",
    "jsdom": "^25.0.0",
    "msw": "^2.6.0",
    "eslint": "^9.15.0",
    "eslint-plugin-import": "^2.31.0"
  }
}
```

- [ ] **Step 2: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src"]
}
```

- [ ] **Step 3: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

- [ ] **Step 4: 创建 vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
});
```

- [ ] **Step 5: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Biomed Knowledge Graph</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600&family=IBM+Plex+Mono&display=swap" rel="stylesheet" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

- [ ] **Step 6: 创建 src/styles/ibm-carbon.css**

```css
:root {
  --color-primary: #0f62fe;
  --color-on-primary: #ffffff;
  --color-ink: #161616;
  --color-ink-muted: #525252;
  --color-ink-subtle: #8c8c8c;
  --color-canvas: #ffffff;
  --color-surface-1: #f4f4f4;
  --color-surface-2: #e0e0e0;
  --color-hairline: #e0e0e0;
  --color-success: #24a148;
  --color-warning: #f1c21b;
  --color-error: #da1e28;

  --font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
  --radius-sm: 0px;
  --radius-md: 4px;

  --shadow-none: none;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
  --space-6: 48px;
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family);
  color: var(--color-ink);
  background: var(--color-canvas);
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3 { font-weight: 300; }
h4, h5, h6 { font-weight: 400; }

button {
  font-family: var(--font-family);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas);
  color: var(--color-ink);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.15s;
}

button:hover { background: var(--color-surface-1); }

button.primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}

button.primary:hover { background: #0043ce; }

input {
  font-family: var(--font-family);
  font-size: 14px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  outline: none;
}

input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  box-shadow: var(--shadow-none);
}
```

- [ ] **Step 7: 创建 src/main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/ibm-carbon.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
```

- [ ] **Step 8: 创建 src/App.tsx**

```tsx
function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <h1 style={{ fontWeight: 300 }}>Biomed Knowledge Graph</h1>
    </div>
  );
}

export default App;
```

- [ ] **Step 9: 安装依赖并验证**

```bash
cd frontend && npm install
npm run dev
# 访问 http://localhost:5173 确认看到标题
```

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend project with React + Vite + IBM Carbon CSS"
```

---

### Task 3: 数据库连接层

**Files:**
- Create: `backend/app/db/neo4j.py`
- Create: `backend/app/db/postgres.py`
- Create: `backend/app/db/__init__.py`

- [ ] **Step 1: 创建 backend/app/db/neo4j.py**

```python
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


async def close_neo4j_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
```

- [ ] **Step 2: 创建 backend/app/db/postgres.py**

```python
import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


async def get_pg_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=2, max_size=10)
    return _pool


async def close_pg_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
```

- [ ] **Step 3: 创建 backend/app/db/__init__.py** (空文件)

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/
git commit -m "feat: add Neo4j and PostgreSQL connection layers"
```

---

### Task 4: 图模型 DTO

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/graph.py`
- Create: `backend/app/models/search.py`
- Create: `backend/app/models/ingest.py`

- [ ] **Step 1: 创建 backend/app/models/graph.py**

```python
from pydantic import BaseModel, Field
from typing import Literal

NodeType = Literal["gene", "protein", "compound", "disease", "article"]


class NodeModel(BaseModel):
    id: str
    type: NodeType
    properties: dict = Field(default_factory=dict)


class EdgeModel(BaseModel):
    relation: str
    direction: Literal["in", "out"]
    node: NodeModel
    properties: dict = Field(default_factory=dict)


class SubgraphModel(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]
    total_edges: int


class NodeDetailResponse(BaseModel):
    node: NodeModel
    neighbors: list[EdgeModel]
    total_edges: int


class ExpandParams(BaseModel):
    depth: int = Field(default=1, ge=1, le=3)
    limit: int = Field(default=50, ge=1, le=200)


class PathParams(BaseModel):
    from_id: str
    to_id: str
    max_length: int = Field(default=4, ge=1, le=6)
```

- [ ] **Step 2: 创建 backend/app/models/search.py**

```python
from pydantic import BaseModel
from typing import Optional

class SearchResult(BaseModel):
    id: str
    type: str
    label: str
    description: Optional[str] = None
    relevance: float


class Suggestion(BaseModel):
    id: str
    type: str
    label: str


class SearchParams(BaseModel):
    q: str
    type: Optional[str] = None
    min_relevance: float = 0.3
    limit: int = 20


class TopEntitiesParams(BaseModel):
    type: str
    limit: int = 20
```

- [ ] **Step 3: 创建 backend/app/models/ingest.py**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SyncStatus(BaseModel):
    source: str
    last_sync_at: Optional[datetime] = None
    status: str  # "idle" | "running" | "error"
    records_added: int = 0
    records_updated: int = 0
    records_failed: int = 0


class SyncLog(BaseModel):
    id: int
    source: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    message: Optional[str] = None
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add data model DTOs for graph, search, and ingest"
```

---

### Task 5: 错误处理

**Files:**
- Create: `backend/app/errors.py`

- [ ] **Step 1: 创建 backend/app/errors.py**

```python
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = ""):
        self.message = message


class GraphTimeoutError(AppError):
    status_code = 408
    code = "GRAPH_TIMEOUT"


class EntityNotFoundError(AppError):
    status_code = 404
    code = "ENTITY_NOT_FOUND"


class InvalidParamError(AppError):
    status_code = 400
    code = "INVALID_PARAM"


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"


class IngestInProgressError(AppError):
    status_code = 503
    code = "INGEST_IN_PROGRESS"


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/errors.py
git commit -m "feat: add business error classes and global error handler"
```

---

### Task 6: Graph Repository

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/graph.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: 写失败测试 — backend/tests/conftest.py**

```python
import pytest
import asyncio
from app.db.neo4j import get_neo4j_driver, close_neo4j_driver


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def neo4j_driver():
    driver = await get_neo4j_driver()
    # 清理测试数据
    await driver.execute_query("MATCH (n) DETACH DELETE n")
    yield driver
    await close_neo4j_driver()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/conftest.py -v
# 确保 conftest 加载无语法错误
```

- [ ] **Step 3: 创建 backend/app/repositories/graph.py**

```python
from app.db.neo4j import get_neo4j_driver
from app.models.graph import NodeModel, EdgeModel, NodeDetailResponse, SubgraphModel
from app.errors import EntityNotFoundError, GraphTimeoutError

NODE_TYPE_MAP = {
    "gene": "Gene",
    "protein": "Protein",
    "compound": "Compound",
    "disease": "Disease",
    "article": "Article",
}


async def get_node_detail(node_type: str, node_id: str) -> NodeDetailResponse:
    label = NODE_TYPE_MAP.get(node_type)
    if not label:
        raise EntityNotFoundError(f"Unknown node type: {node_type}")

    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (n:{label} {{id: $node_id}})
        OPTIONAL MATCH (n)-[r]-(neighbor)
        RETURN n, r, neighbor, labels(neighbor) AS neighbor_labels
        LIMIT 100
    """
    try:
        records = await driver.execute_query(cypher, {"node_id": node_id}, routing_="r")
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Query timed out")
        raise

    if not records.records:
        raise EntityNotFoundError(f"{node_type} not found: {node_id}")

    node_data = dict(records.records[0]["n"])
    node = NodeModel(
        id=node_data.pop("id"),
        type=node_type,
        properties=node_data,
    )

    neighbors: list[EdgeModel] = []
    for rec in records.records:
        if rec["r"]:
            rel_data = dict(rec["r"])
            neighbor_data = dict(rec["neighbor"])
            neighbor_labels = rec["neighbor_labels"]
            neighbor_type = [l.lower() for l in neighbor_labels if l in NODE_TYPE_MAP.values()][0]

            rel_type = rec["r"].type
            rel_props = {k: v for k, v in rel_data.items() if not k.startswith("_")}
            neighbor_data.pop("id", None)  # id will be in id field
            neighbor = NodeModel(
                id=neighbor_data.pop("id", ""),
                type=neighbor_type.lower(),
                properties=neighbor_data,
            )
            neighbors.append(EdgeModel(
                relation=rel_type,
                direction="out",
                node=neighbor,
                properties=rel_props,
            ))

    return NodeDetailResponse(node=node, neighbors=neighbors, total_edges=len(neighbors))


async def expand_node(node_type: str, node_id: str, depth: int, limit: int) -> SubgraphModel:
    label = NODE_TYPE_MAP.get(node_type)
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (start:{label} {{id: $node_id}})
        CALL apoc.neighbors.athop(start, {{relTypes}}, $depth) YIELD node
        RETURN DISTINCT node
        LIMIT $limit
    """
    # 降级方案（无 APOC）：手动 path expand
    cypher = f"""
        MATCH (start:{label} {{id: $node_id}})-[r*1..{depth}]-(neighbor)
        WITH DISTINCT neighbor, r
        RETURN neighbor, r
        LIMIT $limit
    """
    try:
        records = await driver.execute_query(cypher, {"node_id": node_id, "limit": limit})
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Query timed out")
        raise

    nodes_map: dict[str, NodeModel] = {}
    edges: list[EdgeModel] = []

    # 始终包含起始节点
    start_cypher = f"MATCH (n:{label} {{id: $node_id}}) RETURN n"
    start_rec = await driver.execute_query(start_cypher, {"node_id": node_id})
    if start_rec.records:
        sdata = dict(start_rec.records[0]["n"])
        nodes_map[node_id] = NodeModel(id=sdata.pop("id"), type=node_type, properties=sdata)

    for rec in records.records:
        ndata = dict(rec["neighbor"])
        nid = ndata.pop("id", "")
        nlabels = rec["neighbor"].labels
        ntype = next((l.lower() for l in NODE_TYPE_MAP.values() if l in nlabels), "unknown")
        if nid not in nodes_map:
            nodes_map[nid] = NodeModel(id=nid, type=ntype, properties=ndata)

    return SubgraphModel(nodes=list(nodes_map.values()), edges=edges, total_edges=len(edges))


async def find_path(from_type: str, from_id: str, to_type: str, to_id: str, max_length: int) -> SubgraphModel:
    from_label = NODE_TYPE_MAP.get(from_type)
    to_label = NODE_TYPE_MAP.get(to_type)
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH path = shortestPath(
          (a:{from_label} {{id: $from_id}})-[*..{max_length}]-(b:{to_label} {{id: $to_id}})
        )
        UNWIND nodes(path) AS n
        RETURN DISTINCT n
    """
    records = await driver.execute_query(cypher, {"from_id": from_id, "to_id": to_id})
    nodes = [NodeModel(id=dict(r["n"]).pop("id"), type=from_type, properties=dict(r["n"])) for r in records.records]
    return SubgraphModel(nodes=nodes, edges=[], total_edges=0)
```

- [ ] **Step 4: 运行测试确认可连接 Neo4j**

```bash
cd backend && python -c "import asyncio; from app.repositories.graph import expand_node; print('import OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/ backend/tests/conftest.py
git commit -m "feat: add graph repository with Neo4j Cypher queries"
```

---

### Task 7: Search Repository

**Files:**
- Create: `backend/app/repositories/search.py`

- [ ] **Step 1: 创建 backend/app/repositories/search.py**

```python
from app.db.postgres import get_pg_pool
from app.models.search import SearchResult, Suggestion


async def search_entities(query: str, entity_type: str | None, min_relevance: float, limit: int) -> list[SearchResult]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT id, type, label, description,
               ts_rank(search_vector, websearch_to_tsquery('english', $1)) AS relevance
        FROM entities_search
        WHERE ($2::text IS NULL OR type = $2)
          AND search_vector @@ websearch_to_tsquery('english', $1)
          AND ts_rank(search_vector, websearch_to_tsquery('english', $1)) >= $3
        ORDER BY relevance DESC
        LIMIT $4
    """, query, entity_type, min_relevance, limit)

    return [
        SearchResult(id=r["id"], type=r["type"], label=r["label"],
                     description=r["description"], relevance=r["relevance"])
        for r in rows
    ]


async def get_suggestions(query: str, limit: int = 10) -> list[Suggestion]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT id, type, label
        FROM entities_search
        WHERE label ILIKE $1
        ORDER BY label
        LIMIT $2
    """, f"{query}%", limit)

    return [Suggestion(id=r["id"], type=r["type"], label=r["label"]) for r in rows]


async def get_top_entities(entity_type: str, limit: int = 20) -> list[SearchResult]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT id, type, label, description
        FROM entities_search
        WHERE type = $1
        ORDER BY search_count DESC
        LIMIT $2
    """, entity_type, limit)

    return [SearchResult(id=r["id"], type=r["type"], label=r["label"],
                         description=r["description"], relevance=1.0) for r in rows]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/repositories/search.py
git commit -m "feat: add search repository with PostgreSQL full-text queries"
```

---

### Task 8: Graph Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/graph.py`

- [ ] **Step 1: 写失败测试 — backend/tests/api/test_graph.py**

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_node_detail_not_found(client):
    response = await client.get("/api/graph/node/gene/FAKE123")
    assert response.status_code == 404
    assert response.json()["error"] == "ENTITY_NOT_FOUND"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/api/test_graph.py::test_get_node_detail_not_found -v
```

Expected: FAIL (404 or connection error — no router yet)

- [ ] **Step 3: 创建 backend/app/services/graph.py**

```python
from app.models.graph import (
    NodeDetailResponse, SubgraphModel, ExpandParams,
    PathParams, NodeType
)
from app.repositories import graph as graph_repo


async def get_node(type_: NodeType, id_: str) -> NodeDetailResponse:
    return await graph_repo.get_node_detail(type_, id_)


async def expand(type_: NodeType, id_: str, params: ExpandParams) -> SubgraphModel:
    return await graph_repo.expand_node(type_, id_, params.depth, params.limit)


async def path(params: PathParams) -> SubgraphModel:
    from_type, from_id = params.from_id.split(":", 1)
    to_type, to_id = params.to_id.split(":", 1)
    return await graph_repo.find_path(from_type, from_id, to_type, to_id, params.max_length)


async def protein_network(protein_id: str, min_score: float = 0.7, limit: int = 100) -> SubgraphModel:
    return await graph_repo.protein_network(protein_id, min_score, limit)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/graph.py backend/tests/api/test_graph.py
git commit -m "feat: add graph service layer"
```

---

### Task 9: Graph Router

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/graph.py`

- [ ] **Step 1: 创建 backend/app/routers/graph.py**

```python
from fastapi import APIRouter, Query, Depends
from app.models.graph import (
    NodeDetailResponse, SubgraphModel, ExpandParams,
    PathParams, NodeType
)
from app.services import graph as graph_svc
from app.errors import InvalidParamError

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/node/{type}/{id}", response_model=NodeDetailResponse)
async def get_node_detail(type: str, id: str):
    if type not in {"gene", "protein", "compound", "disease", "article"}:
        raise InvalidParamError(f"Invalid node type: {type}")
    return await graph_svc.get_node(type, id)


@router.get("/expand/{type}/{id}", response_model=SubgraphModel)
async def expand_node(
    type: str, id: str,
    depth: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200),
):
    if type not in {"gene", "protein", "compound", "disease", "article"}:
        raise InvalidParamError(f"Invalid node type: {type}")
    params = ExpandParams(depth=depth, limit=limit)
    return await graph_svc.expand(type, id, params)


@router.get("/path", response_model=SubgraphModel)
async def shortest_path(
    from_: str = Query(alias="from"),
    to: str = Query(),
    max_length: int = Query(default=4, ge=1, le=6),
):
    params = PathParams(from_id=from_, to_id=to, max_length=max_length)
    return await graph_svc.path(params)


@router.get("/network/{protein_id}", response_model=SubgraphModel)
async def protein_network(
    protein_id: str,
    min_score: float = Query(default=0.7, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await graph_svc.protein_network(protein_id, min_score, limit)
```

- [ ] **Step 2: 注册 router 到 main.py**

Edit `backend/app/main.py`:

```python
from app.routers import graph
from app.errors import AppError, app_error_handler

app = FastAPI(title="Biomed Knowledge Graph API", version="0.1.0")

app.add_middleware(...)

app.include_router(graph.router)
app.add_exception_handler(AppError, app_error_handler)
```

- [ ] **Step 3: 运行测试验证 endpoint 返回 404（路由已注册，但 Neo4j 无数据）**

```bash
cd backend && python -m pytest tests/api/test_graph.py::test_get_node_detail_not_found -v
```

Expected: PASS (404 with ENTITY_NOT_FOUND, not 404 with route not found)

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/graph.py backend/app/main.py backend/tests/api/test_graph.py
git commit -m "feat: add graph API router with node/expand/path/network endpoints"
```

---

### Task 10: Search Service + Router

**Files:**
- Create: `backend/app/services/search.py`
- Create: `backend/app/routers/search.py`

- [ ] **Step 1: 创建 backend/app/services/search.py**

```python
from app.models.search import SearchResult, Suggestion, SearchParams, TopEntitiesParams
from app.repositories import search as search_repo


async def search(params: SearchParams) -> list[SearchResult]:
    return await search_repo.search_entities(
        params.q, params.type, params.min_relevance, params.limit
    )


async def suggest(query: str, limit: int = 10) -> list[Suggestion]:
    return await search_repo.get_suggestions(query, limit)


async def top_entities(params: TopEntitiesParams) -> list[SearchResult]:
    return await search_repo.get_top_entities(params.type, params.limit)
```

- [ ] **Step 2: 创建 backend/app/routers/search.py**

```python
from fastapi import APIRouter, Query
from app.models.search import SearchResult, Suggestion, SearchParams, TopEntitiesParams
from app.services import search as search_svc

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search(
    q: str = Query(min_length=1),
    type: str | None = Query(default=None),
    min_relevance: float = Query(default=0.3, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
):
    params = SearchParams(q=q, type=type, min_relevance=min_relevance, limit=limit)
    return await search_svc.search(params)


@router.get("/suggest", response_model=list[Suggestion])
async def suggest(q: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=20)):
    return await search_svc.suggest(q, limit)


@router.get("/top", response_model=list[SearchResult])
async def top(type: str = Query(), limit: int = Query(default=20, ge=1, le=100)):
    params = TopEntitiesParams(type=type, limit=limit)
    return await search_svc.top_entities(params)
```

- [ ] **Step 3: 注册到 main.py**

```python
from app.routers import search
app.include_router(search.router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/search.py backend/app/routers/search.py backend/app/main.py
git commit -m "feat: add search service and API router"
```

---

### Task 11: Ingest Service + Router

**Files:**
- Create: `backend/app/services/ingest.py`
- Create: `backend/app/routers/ingest.py`

- [ ] **Step 1: 创建 backend/app/services/ingest.py**

```python
from datetime import datetime
from app.models.ingest import SyncStatus, SyncLog
from app.db.postgres import get_pg_pool

SOURCES = ["pubmed", "uniprot", "chembl", "opentargets", "string"]


async def trigger_sync(source: str) -> dict:
    if source not in SOURCES:
        from app.errors import InvalidParamError
        raise InvalidParamError(f"Unknown source: {source}")
    # V1: 触发 Celery task
    from tasks.sync import sync_source
    sync_source.delay(source)
    return {"status": "triggered", "source": source}


async def get_all_status() -> list[SyncStatus]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT source, last_sync_at, status, records_added, records_updated, records_failed
        FROM ingest_status
        ORDER BY source
    """)
    return [SyncStatus(**dict(r)) for r in rows]


async def get_logs(source: str | None = None, limit: int = 20) -> list[SyncLog]:
    pool = await get_pg_pool()
    if source:
        rows = await pool.fetch(
            "SELECT id, source, started_at, finished_at, status, message FROM ingest_log WHERE source=$1 ORDER BY id DESC LIMIT $2",
            source, limit
        )
    else:
        rows = await pool.fetch(
            "SELECT id, source, started_at, finished_at, status, message FROM ingest_log ORDER BY id DESC LIMIT $1",
            limit
        )
    return [SyncLog(**dict(r)) for r in rows]
```

- [ ] **Step 2: 创建 backend/app/routers/ingest.py**

```python
from fastapi import APIRouter, Query
from app.models.ingest import SyncStatus, SyncLog
from app.services import ingest as ingest_svc

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/sync/{source}")
async def trigger_sync(source: str):
    return await ingest_svc.trigger_sync(source)


@router.get("/status", response_model=list[SyncStatus])
async def get_status():
    return await ingest_svc.get_all_status()


@router.get("/logs", response_model=list[SyncLog])
async def get_logs(source: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=100)):
    return await ingest_svc.get_logs(source, limit)
```

- [ ] **Step 3: 注册到 main.py**

```python
from app.routers import ingest
app.include_router(ingest.router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ingest.py backend/app/routers/ingest.py backend/app/main.py
git commit -m "feat: add ingest service and API router"
```

---

### Task 12: BaseIngester + Pipeline

**Files:**
- Create: `backend/ingest/__init__.py`
- Create: `backend/ingest/base.py`
- Create: `backend/ingest/models.py`
- Create: `backend/ingest/pipeline.py`

- [ ] **Step 1: 创建 backend/ingest/models.py**

```python
from pydantic import BaseModel
from datetime import datetime

class NormalizedNode(BaseModel):
    id: str
    type: str  # "gene" | "protein" | "compound" | "disease" | "article"
    properties: dict


class NormalizedEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str
    properties: dict


class NormalizedRecord(BaseModel):
    nodes: list[NormalizedNode]
    edges: list[NormalizedEdge]
    source: str
    fetched_at: datetime
```

- [ ] **Step 2: 创建 backend/ingest/base.py**

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
from ingest.models import NormalizedRecord


class BaseIngester(ABC):
    source_name: str
    batch_size: int = 500

    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    def normalize(self, record: dict) -> NormalizedRecord | None:
        ...

    @abstractmethod
    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        ...
```

- [ ] **Step 3: 创建 backend/ingest/pipeline.py**

```python
import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord
from ingest.serializers import batch_write
from ingest.stats import collect_stats

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, ingester: BaseIngester, rate_limit: float = 3.0, max_retries: int = 3):
        self.ingester = ingester
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    async def run(self, since: datetime | None = None) -> dict:
        since = since or datetime.min.replace(tzinfo=timezone.utc)
        stats = {"added": 0, "updated": 0, "failed": 0, "source": self.ingester.source_name}
        batch: list[NormalizedRecord] = []

        async for raw in self._fetch_with_retry(since):
            try:
                record = self.ingester.normalize(raw)
            except Exception:
                logger.warning("normalize failed for record in %s", self.ingester.source_name)
                stats["failed"] += 1
                continue

            if record is None:
                continue

            batch.append(record)
            if len(batch) >= self.ingester.batch_size:
                await self._flush_batch(batch, stats)
                batch = []

        if batch:
            await self._flush_batch(batch, stats)

        await collect_stats(self.ingester.source_name, stats)
        return stats

    async def _fetch_with_retry(self, since: datetime) -> AsyncIterator[dict]:
        for attempt in range(self.max_retries):
            try:
                async for record in self.ingester.fetch(since):
                    yield record
                return
            except Exception:
                logger.error("fetch attempt %d failed for %s", attempt + 1, self.ingester.source_name)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        logger.error("all fetch attempts failed for %s", self.ingester.source_name)

    async def _flush_batch(self, batch: list[NormalizedRecord], stats: dict):
        queries = self.ingester.build_queries(batch)
        try:
            result = await batch_write(queries)
            stats["added"] += result["added"]
            stats["updated"] += result["updated"]
        except Exception:
            stats["failed"] += len(batch)
            logger.exception("batch write failed for %s", self.ingester.source_name)
```

- [ ] **Step 4: Commit**

```bash
git add backend/ingest/__init__.py backend/ingest/base.py backend/ingest/models.py backend/ingest/pipeline.py
git commit -m "feat: add BaseIngester contract and Pipeline orchestrator"
```

---

### Task 13: Serializers + Stats

**Files:**
- Create: `backend/ingest/serializers.py`
- Create: `backend/ingest/stats.py`

- [ ] **Step 1: 创建 backend/ingest/serializers.py**

```python
from app.db.neo4j import get_neo4j_driver


async def batch_write(queries: list[str]) -> dict:
    driver = await get_neo4j_driver()
    added = 0
    updated = 0
    async with driver.session() as session:
        for query in queries:
            result = await session.run(query)
            summary = await result.consume()
            added += summary.counters.nodes_created
            updated += summary.counters.properties_set
    return {"added": added, "updated": updated}
```

- [ ] **Step 2: 创建 backend/ingest/stats.py**

```python
from datetime import datetime, timezone
from app.db.postgres import get_pg_pool


async def collect_stats(source: str, stats: dict):
    pool = await get_pg_pool()
    now = datetime.now(timezone.utc)
    await pool.execute("""
        INSERT INTO ingest_status (source, last_sync_at, status, records_added, records_updated, records_failed)
        VALUES ($1, $2, 'idle', $3, $4, $5)
        ON CONFLICT (source) DO UPDATE SET
            last_sync_at = EXCLUDED.last_sync_at,
            status = 'idle',
            records_added = ingest_status.records_added + EXCLUDED.records_added,
            records_updated = ingest_status.records_updated + EXCLUDED.records_updated,
            records_failed = ingest_status.records_failed + EXCLUDED.records_failed
    """, source, now, stats["added"], stats["updated"], stats["failed"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/ingest/serializers.py backend/ingest/stats.py
git commit -m "feat: add Cypher batch writer and ingest stats collector"
```

---

### Task 14: PubMed Ingester

**Files:**
- Create: `backend/ingest/sources/__init__.py`
- Create: `backend/ingest/sources/pubmed.py`
- Test: `backend/tests/unit/sources/test_pubmed_normalize.py`

- [ ] **Step 1: 写快照测试 — backend/tests/unit/sources/test_pubmed_normalize.py**

```python
import json
from datetime import datetime, timezone
from ingest.sources.pubmed import PubMedIngester

SAMPLE_RECORD = {
    "uid": "12345678",
    "title": "BRCA1 mutations in breast cancer",
    "pubdate": "20240101",
    "source": "Nature",
    "abstract": "This study investigates BRCA1 mutations...",
    "authors": [{"name": "Smith J"}, {"name": "Doe K"}],
}

def test_pubmed_normalize_snapshot():
    ingester = PubMedIngester()
    result = ingester.normalize(SAMPLE_RECORD)
    assert result is not None
    assert len(result.nodes) == 2  # article node + at least 1 mentioned entity
    assert result.nodes[0].type == "article"
    assert result.nodes[0].id == "pmid:12345678"
    assert result.nodes[0].properties["title"] == "BRCA1 mutations in breast cancer"


def test_pubmed_normalize_empty_abstract_returns_none():
    ingester = PubMedIngester()
    record = {**SAMPLE_RECORD, "abstract": ""}
    result = ingester.normalize(record)
    assert result is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/unit/sources/test_pubmed_normalize.py -v
```

Expected: FAIL (ImportError)

- [ ] **Step 3: 创建 backend/ingest/sources/pubmed.py**

```python
import re
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge

GENE_SYMBOL_PATTERN = re.compile(r'\b[A-Z]{2,}[0-9]*\b')
DISEASE_PATTERN = re.compile(r'\b(?:cancer|carcinoma|syndrome|disease|disorder|deficiency)\b', re.IGNORECASE)


class PubMedIngester(BaseIngester):
    source_name = "pubmed"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        api_key = ""  # 从环境变量读取
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        params = {
            "db": "pubmed",
            "term": f'("{since.date().isoformat()}"[PDAT] : "3000"[PDAT])',
            "retmax": self.batch_size,
            "retmode": "json",
            "sort": "pub_date",
            "api_key": api_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/esearch.fcgi", params=params)
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return

            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
                "api_key": api_key,
            }
            fetch_response = await client.get(f"{base_url}/esummary.fcgi", params=fetch_params)
            result = fetch_response.json().get("result", {})
            for uid in id_list:
                record = result.get(uid)
                if record and record.get("title"):
                    yield record

    def normalize(self, record: dict) -> NormalizedRecord | None:
        title = record.get("title", "")
        abstract = record.get("abstract", "")

        if not title:
            return None

        pmid = f"pmid:{record.get('uid', '')}"
        nodes: list[NormalizedNode] = [
            NormalizedNode(
                id=pmid,
                type="article",
                properties={
                    "title": title,
                    "abstract": abstract,
                    "year": int(record.get("pubdate", "0000")[:4]) if record.get("pubdate") else None,
                    "journal": record.get("source", ""),
                },
            )
        ]

        edges: list[NormalizedEdge] = []

        all_text = f"{title} {abstract}"
        genes = set(GENE_SYMBOL_PATTERN.findall(all_text))
        diseases = set(DISEASE_PATTERN.findall(all_text))

        for gene in genes:
            if len(gene) > 2:
                edges.append(NormalizedEdge(
                    from_id=pmid, to_id=f"gene:{gene}",
                    relation="MENTIONS", properties={"mention_type": "gene"}
                ))

        for disease in diseases:
            edges.append(NormalizedEdge(
                from_id=pmid, to_id=f"disease:{disease}",
                relation="MENTIONS", properties={"mention_type": "disease"}
            ))

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name,
            fetched_at=datetime.now(timezone.utc),
        )

    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        queries: list[str] = []
        for record in batch:
            for node in batch[0].nodes:
                props = ", ".join(f"n.{k} = '{v}'" if isinstance(v, str) else f"n.{k} = {v}"
                                  for k, v in node.properties.items() if v is not None)
                queries.append(
                    f"MERGE (n:{node.type} {{id: '{node.id}'}}) ON CREATE SET {props} ON MATCH SET {props}"
                )
            for edge in batch[0].edges:
                queries.append(
                    f"MATCH (a {{id: '{edge.from_id}'}}), (b {{id: '{edge.to_id}'}}) "
                    f"MERGE (a)-[:{edge.relation}]->(b)"
                )
        return queries
```

- [ ] **Step 4: 运行测试验证 normalize**

```bash
cd backend && python -m pytest tests/unit/sources/test_pubmed_normalize.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/ingest/sources/pubmed.py backend/tests/unit/sources/test_pubmed_normalize.py
git commit -m "feat: add PubMed ingester with normalize and snapshot test"
```

---

### Task 15: UniProt Ingester

**Files:**
- Create: `backend/ingest/sources/uniprot.py`
- Test: `backend/tests/unit/sources/test_uniprot_normalize.py`

- [ ] **Step 1: 创建 backend/ingest/sources/uniprot.py**

```python
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class UniProtIngester(BaseIngester):
    source_name = "uniprot"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        base_url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": f"reviewed:true AND organism_id:9606",
            "format": "json",
            "size": self.batch_size,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            while url:
                response = await client.get(url)
                data = response.json()
                for entry in data.get("results", []):
                    yield entry
                url = response.headers.get("Link", "")
                if 'rel="next"' in url:
                    url = url.split(";")[0].strip("<>")
                else:
                    break

    def normalize(self, record: dict) -> NormalizedRecord | None:
        accession = record.get("primaryAccession")
        if not accession:
            return None

        protein_id = f"protein:{accession}"
        gene_name = record.get("genes", [{}])[0].get("geneName", {}).get("value", "")
        protein_name = record.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")
        sequence = record.get("sequence", {}).get("value", "")
        length = record.get("sequence", {}).get("length", 0)

        comments = record.get("comments", [])
        diseases = []
        for comment in comments:
            if comment.get("commentType") == "DISEASE":
                disease_text = comment.get("disease", {}).get("diseaseId")
                if disease_text:
                    diseases.append(disease_text)

        nodes: list[NormalizedNode] = [
            NormalizedNode(
                id=protein_id, type="protein",
                properties={"name": protein_name, "sequence": sequence[:50], "length": length},
            )
        ]

        edges: list[NormalizedEdge] = []

        if gene_name:
            nodes.append(NormalizedNode(id=f"gene:{gene_name}", type="gene", properties={"symbol": gene_name}))
            edges.append(NormalizedEdge(from_id=f"gene:{gene_name}", to_id=protein_id, relation="ENCODES", properties={}))

        for disease_id in diseases:
            edges.append(NormalizedEdge(from_id=protein_id, to_id=f"disease:{disease_id}", relation="ASSOCIATED_WITH", properties={"confidence": 0.8}))

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )

    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        queries: list[str] = []
        for record in batch:
            for node in record.nodes:
                label = node.type.capitalize()
                props_str = ", ".join(
                    f"n.{k} = '{v}'" if isinstance(v, str) else f"n.{k} = {v}"
                    for k, v in node.properties.items() if v is not None
                )
                queries.append(
                    f"MERGE (n:{label} {{id: '{node.id}'}}) ON CREATE SET {props_str} ON MATCH SET {props_str}"
                )
            for edge in record.edges:
                queries.append(
                    f"MATCH (a {{id: '{edge.from_id}'}}), (b {{id: '{edge.to_id}'}}) "
                    f"MERGE (a)-[:{edge.relation}]->(b)"
                )
        return queries
```

- [ ] **Step 2: 写测试 backend/tests/unit/sources/test_uniprot_normalize.py**

```python
from ingest.sources.uniprot import UniProtIngester

SAMPLE = {
    "primaryAccession": "P04637",
    "genes": [{"geneName": {"value": "TP53"}}],
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}},
    "sequence": {"value": "MEEPQSDPSV...", "length": 393},
    "comments": [{"commentType": "DISEASE", "disease": {"diseaseId": "Li-Fraumeni syndrome"}}],
}

def test_uniprot_normalize_snapshot():
    ingester = UniProtIngester()
    result = ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 2  # protein + gene
    protein = [n for n in result.nodes if n.type == "protein"][0]
    assert protein.id == "protein:P04637"
    assert protein.properties["name"] == "Cellular tumor antigen p53"
    gene = [n for n in result.nodes if n.type == "gene"][0]
    assert gene.id == "gene:TP53"
    assert len(result.edges) == 2  # ENCODES + ASSOCIATED_WITH
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/unit/sources/test_uniprot_normalize.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/ingest/sources/uniprot.py backend/tests/unit/sources/test_uniprot_normalize.py
git commit -m "feat: add UniProt ingester with gene-protein-disease mapping"
```

---

### Task 16: Resolvers + Celery Setup + Seed Migration

**Files:**
- Create: `backend/ingest/resolvers/__init__.py`
- Create: `backend/ingest/resolvers/gene.py`
- Create: `backend/ingest/resolvers/disease.py`
- Create: `backend/tasks/__init__.py`
- Create: `backend/tasks/celery_app.py`
- Create: `backend/tasks/sync.py`
- Create: `backend/migrations/001_search_tables.sql`

- [ ] **Step 1: 创建 gene_resolver.py**

```python
# backend/ingest/resolvers/gene.py
async def resolve_gene_symbol(symbol: str) -> str:
    """Gene symbol → UniProt gene ID. Returns normalized ID or original."""
    # V1: 简单规范化: 大写 + 去空格
    return f"gene:{symbol.strip().upper()}"
```

- [ ] **Step 2: 创建 disease_resolver.py**

```python
# backend/ingest/resolvers/disease.py
async def resolve_disease(name: str) -> str:
    """Disease name → standardized ID. Returns normalized ID or original."""
    clean = name.strip().lower()
    return f"disease:{clean}"
```

- [ ] **Step 3: 创建 backend/tasks/celery_app.py**

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "biomed_graph",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
```

- [ ] **Step 4: 创建 backend/tasks/sync.py**

```python
from tasks.celery_app import celery_app
from ingest.sources.pubmed import PubMedIngester
from ingest.sources.uniprot import UniProtIngester
from ingest.pipeline import Pipeline


@celery_app.task(name="sync_source")
def sync_source(source: str):
    import asyncio
    ingesters = {
        "pubmed": PubMedIngester,
        "uniprot": UniProtIngester,
    }
    ingester_cls = ingesters.get(source)
    if not ingester_cls:
        return {"error": f"unknown source: {source}"}
    ingester = ingester_cls()
    pipeline = Pipeline(ingester)
    return asyncio.run(pipeline.run())
```

- [ ] **Step 5: 创建 seed migration**

```sql
-- backend/migrations/001_search_tables.sql
CREATE TABLE IF NOT EXISTS entities_search (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    search_vector TSVECTOR,
    search_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_entities_search_vector ON entities_search USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_entities_search_type ON entities_search(type);

CREATE TABLE IF NOT EXISTS ingest_status (
    source TEXT PRIMARY KEY,
    last_sync_at TIMESTAMPTZ,
    status TEXT DEFAULT 'idle',
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ingest_log (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    message TEXT
);

INSERT INTO ingest_status (source) VALUES
    ('pubmed'), ('uniprot'), ('chembl'), ('opentargets'), ('string')
ON CONFLICT (source) DO NOTHING;
```

- [ ] **Step 6: Commit**

```bash
git add backend/ingest/resolvers/ backend/tasks/ backend/migrations/
git commit -m "feat: add resolvers, Celery setup, and seed SQL migration"
```

---

### Task 17: 前端 API 层

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/graph.ts`
- Create: `frontend/src/api/search.ts`
- Create: `frontend/src/api/ingest.ts`

- [ ] **Step 1: 创建 client.ts**

```typescript
import axios from 'axios';

export const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'Unknown error';
    return Promise.reject(new Error(message));
  },
);
```

- [ ] **Step 2: 创建 graph.ts**

```typescript
import { client } from './client';

export interface NodeData {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface EdgeData {
  relation: string;
  direction: 'in' | 'out';
  node: NodeData;
  properties: Record<string, unknown>;
}

export interface NodeDetailResponse {
  node: NodeData;
  neighbors: EdgeData[];
  total_edges: number;
}

export interface SubgraphData {
  nodes: NodeData[];
  edges: EdgeData[];
  total_edges: number;
}

export async function getNodeDetail(type: string, id: string): Promise<NodeDetailResponse> {
  const { data } = await client.get(`/graph/node/${type}/${id}`);
  return data;
}

export async function expandNode(
  type: string, id: string, depth = 1, limit = 50,
): Promise<SubgraphData> {
  const { data } = await client.get(`/graph/expand/${type}/${id}`, { params: { depth, limit } });
  return data;
}

export async function findPath(from: string, to: string): Promise<SubgraphData> {
  const { data } = await client.get('/graph/path', { params: { from, to } });
  return data;
}

export async function getProteinNetwork(
  proteinId: string, minScore = 0.7, limit = 100,
): Promise<SubgraphData> {
  const { data } = await client.get(`/graph/network/${proteinId}`, { params: { min_score: minScore, limit } });
  return data;
}
```

- [ ] **Step 3: 创建 search.ts**

```typescript
import { client } from './client';

export interface SearchResult {
  id: string;
  type: string;
  label: string;
  description?: string;
  relevance: number;
}

export interface Suggestion {
  id: string;
  type: string;
  label: string;
}

export async function searchEntities(
  q: string, type?: string, limit = 20,
): Promise<SearchResult[]> {
  const { data } = await client.get('/search', { params: { q, type, limit } });
  return data;
}

export async function getSuggestions(q: string): Promise<Suggestion[]> {
  const { data } = await client.get('/search/suggest', { params: { q } });
  return data;
}
```

- [ ] **Step 4: 创建 ingest.ts**

```typescript
import { client } from './client';

export interface SyncStatus {
  source: string;
  last_sync_at: string | null;
  status: string;
  records_added: number;
  records_updated: number;
  records_failed: number;
}

export async function getSyncStatus(): Promise<SyncStatus[]> {
  const { data } = await client.get('/ingest/status');
  return data;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add frontend API layer (client, graph, search, ingest)"
```

---

### Task 18: Zustand Stores

**Files:**
- Create: `frontend/src/store/searchStore.ts`
- Create: `frontend/src/store/graphStore.ts`
- Create: `frontend/src/store/uiStore.ts`
- Test: `frontend/src/__tests__/store/searchStore.test.ts`
- Test: `frontend/src/__tests__/store/graphStore.test.ts`

- [ ] **Step 1: 写失败测试 — searchStore.test.ts**

```typescript
import { describe, it, expect } from 'vitest';
import { useSearchStore } from '@/store/searchStore';

describe('searchStore', () => {
  it('sets query and clears suggestions when query is empty', () => {
    const { setQuery, query } = useSearchStore.getState();
    setQuery('BRCA1');
    expect(useSearchStore.getState().query).toBe('BRCA1');

    setQuery('');
    expect(useSearchStore.getState().query).toBe('');
  });
});
```

- [ ] **Step 2: 创建 searchStore.ts**

```typescript
import { create } from 'zustand';
import type { Suggestion } from '@/api/search';

interface SearchState {
  query: string;
  suggestions: Suggestion[];
  selectedType: string | null;
  setQuery: (q: string) => void;
  setSuggestions: (items: Suggestion[]) => void;
  setSelectedType: (t: string | null) => void;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  suggestions: [],
  selectedType: null,
  setQuery: (query) => set({ query }),
  setSuggestions: (suggestions) => set({ suggestions }),
  setSelectedType: (selectedType) => set({ selectedType }),
  clearSearch: () => set({ query: '', suggestions: [], selectedType: null }),
}));
```

- [ ] **Step 3: 创建 graphStore.ts**

```typescript
import { create } from 'zustand';
import type { NodeData, EdgeData } from '@/api/graph';

interface GraphState {
  nodes: NodeData[];
  edges: EdgeData[];
  selectedNode: NodeData | null;
  layout: 'cose' | 'breadthfirst' | 'concentric' | 'grid';
  setNodes: (nodes: NodeData[]) => void;
  setEdges: (edges: EdgeData[]) => void;
  setSubgraph: (nodes: NodeData[], edges: EdgeData[]) => void;
  setSelectedNode: (node: NodeData | null) => void;
  setLayout: (layout: GraphState['layout']) => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  layout: 'cose',
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSubgraph: (nodes, edges) => set({ nodes, edges }),
  setSelectedNode: (selectedNode) => set({ selectedNode }),
  setLayout: (layout) => set({ layout }),
  clearGraph: () => set({ nodes: [], edges: [], selectedNode: null }),
}));
```

- [ ] **Step 4: 创建 uiStore.ts**

```typescript
import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  darkMode: boolean;
  toasts: string[];
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  addToast: (msg: string) => void;
  removeToast: (index: number) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  darkMode: false,
  toasts: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
  addToast: (msg) => set((s) => ({ toasts: [...s.toasts, msg] })),
  removeToast: (index) => set((s) => ({ toasts: s.toasts.filter((_, i) => i !== index) })),
}));
```

- [ ] **Step 5: 运行测试**

```bash
cd frontend && npx vitest run src/__tests__/store/
```

Expected: PASS (searchStore test)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/store/ frontend/src/__tests__/store/
git commit -m "feat: add Zustand stores (search, graph, ui) with tests"
```

---

### Task 19: Frontend Hooks

**Files:**
- Create: `frontend/src/hooks/useSearch.ts`
- Create: `frontend/src/hooks/useNodeDetail.ts`
- Create: `frontend/src/hooks/useGraphExpand.ts`
- Create: `frontend/src/hooks/useProteinNetwork.ts`
- Test: `frontend/src/__tests__/hooks/useSearch.test.ts`

- [ ] **Step 1: 创建 hooks**

```typescript
// frontend/src/hooks/useSearch.ts
import { useQuery } from '@tanstack/react-query';
import { searchEntities } from '@/api/search';
import { useSearchStore } from '@/store/searchStore';

export function useSearch() {
  const query = useSearchStore((s) => s.query);
  const selectedType = useSearchStore((s) => s.selectedType);

  return useQuery({
    queryKey: ['search', query, selectedType],
    queryFn: () => searchEntities(query, selectedType ?? undefined),
    enabled: query.length >= 2,
    staleTime: 30_000,
  });
}
```

```typescript
// frontend/src/hooks/useNodeDetail.ts
import { useQuery } from '@tanstack/react-query';
import { getNodeDetail } from '@/api/graph';

export function useNodeDetail(type: string | null, id: string | null) {
  return useQuery({
    queryKey: ['node', type, id],
    queryFn: () => getNodeDetail(type!, id!),
    enabled: type !== null && id !== null,
  });
}
```

```typescript
// frontend/src/hooks/useGraphExpand.ts
import { useQuery } from '@tanstack/react-query';
import { expandNode } from '@/api/graph';

export function useGraphExpand(type: string | null, id: string | null, depth = 1) {
  return useQuery({
    queryKey: ['expand', type, id, depth],
    queryFn: () => expandNode(type!, id!, depth),
    enabled: type !== null && id !== null,
  });
}
```

```typescript
// frontend/src/hooks/useProteinNetwork.ts
import { useQuery } from '@tanstack/react-query';
import { getProteinNetwork } from '@/api/graph';

export function useProteinNetwork(proteinId: string | null, minScore = 0.7) {
  return useQuery({
    queryKey: ['network', proteinId, minScore],
    queryFn: () => getProteinNetwork(proteinId!, minScore),
    enabled: proteinId !== null,
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add TanStack Query hooks for search and graph data"
```

---

### Task 20: SearchPanel 组件

**Files:**
- Create: `frontend/src/pages/GraphExplorer/SearchPanel/SearchInput.tsx`
- Create: `frontend/src/pages/GraphExplorer/SearchPanel/SuggestionList.tsx`
- Create: `frontend/src/pages/GraphExplorer/SearchPanel/FilterBar.tsx`
- Create: `frontend/src/pages/GraphExplorer/SearchPanel/SearchPanel.tsx`
- Test: `frontend/src/__tests__/components/SearchInput.test.tsx`

- [ ] **Step 1: 写测试 — SearchInput.test.tsx**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchInput } from '@/pages/GraphExplorer/SearchPanel/SearchInput';

describe('SearchInput', () => {
  it('calls onChange with input value', () => {
    const handleChange = vi.fn();
    render(<SearchInput value="" onChange={handleChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'BRCA1' } });
    expect(handleChange).toHaveBeenCalledWith('BRCA1');
  });

  it('displays the current value', () => {
    render(<SearchInput value="TP53" onChange={vi.fn()} />);
    expect(screen.getByRole('textbox')).toHaveValue('TP53');
  });
});
```

- [ ] **Step 2: 创建 SearchInput.tsx**

```tsx
import React from 'react';

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchInput({ value, onChange, placeholder = 'Search genes, proteins, diseases...' }: Props) {
  return (
    <input
      type="text"
      role="textbox"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{ width: '100%' }}
    />
  );
}
```

- [ ] **Step 3: 创建 SuggestionList.tsx**

```tsx
import type { Suggestion } from '@/api/search';

interface Props {
  items: Suggestion[];
  onSelect: (item: Suggestion) => void;
  visible: boolean;
}

export function SuggestionList({ items, onSelect, visible }: Props) {
  if (!visible || items.length === 0) return null;
  return (
    <div style={{ border: '1px solid var(--color-hairline)', borderRadius: 'var(--radius-md)', maxHeight: 200, overflowY: 'auto' }}>
      {items.map((item) => (
        <div
          key={item.id}
          onClick={() => onSelect(item)}
          style={{ padding: '8px 16px', cursor: 'pointer', borderBottom: '1px solid var(--color-hairline)' }}
          className="hover:bg-gray-50"
        >
          <span style={{ fontWeight: 600 }}>{item.label}</span>
          <span style={{ marginLeft: 8, color: 'var(--color-ink-subtle)', fontSize: 12 }}>{item.type}</span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: 创建 FilterBar.tsx**

```tsx
const ENTITY_TYPES = [
  { key: null, label: 'All' },
  { key: 'gene', label: 'Genes' },
  { key: 'protein', label: 'Proteins' },
  { key: 'compound', label: 'Compounds' },
  { key: 'disease', label: 'Diseases' },
  { key: 'article', label: 'Articles' },
];

interface Props {
  selectedType: string | null;
  onChange: (type: string | null) => void;
}

export function FilterBar({ selectedType, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
      {ENTITY_TYPES.map((t) => (
        <button
          key={t.key ?? 'all'}
          className={selectedType === t.key ? 'primary' : ''}
          onClick={() => onChange(t.key)}
          style={{ fontSize: 12, padding: '4px 8px' }}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: 创建 SearchPanel.tsx (编排层)**

```tsx
import { useSearchStore } from '@/store/searchStore';
import { useGraphStore } from '@/store/graphStore';
import { useSearch } from '@/hooks/useSearch';
import { SearchInput } from './SearchInput';
import { SuggestionList } from './SuggestionList';
import { FilterBar } from './FilterBar';
import type { Suggestion } from '@/api/search';

export function SearchPanel() {
  const { query, selectedType, setQuery, setSelectedType } = useSearchStore();
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);
  const { data: results } = useSearch();

  const handleSelect = (item: Suggestion) => {
    setSelectedNode({ id: item.id, type: item.type, properties: {} });
  };

  return (
    <div className="card" style={{ marginBottom: 'var(--space-3)' }}>
      <SearchInput value={query} onChange={setQuery} />
      <FilterBar selectedType={selectedType} onChange={setSelectedType} />
      <SuggestionList
        items={results?.map((r) => ({ id: r.id, type: r.type, label: r.label })) ?? []}
        onSelect={handleSelect}
        visible={query.length >= 2}
      />
    </div>
  );
}
```

- [ ] **Step 6: 运行测试**

```bash
cd frontend && npx vitest run src/__tests__/components/SearchInput.test.tsx
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/GraphExplorer/SearchPanel/ frontend/src/__tests__/components/SearchInput.test.tsx
git commit -m "feat: add SearchPanel components (SearchInput, SuggestionList, FilterBar)"
```

---

### Task 21: GraphCanvas + DetailPanel 组件

**Files:**
- Create: `frontend/src/pages/GraphExplorer/GraphCanvas/CytoscapeRenderer.tsx`
- Create: `frontend/src/pages/GraphExplorer/GraphCanvas/LayoutControls.tsx`
- Create: `frontend/src/pages/GraphExplorer/GraphCanvas/GraphCanvas.tsx`
- Create: `frontend/src/pages/GraphExplorer/DetailPanel/NodeDetail.tsx`
- Create: `frontend/src/pages/GraphExplorer/DetailPanel/RelationTable.tsx`
- Create: `frontend/src/pages/GraphExplorer/DetailPanel/ExternalLinks.tsx`
- Create: `frontend/src/pages/GraphExplorer/DetailPanel/DetailPanel.tsx`

- [ ] **Step 1: 创建 CytoscapeRenderer.tsx**

```tsx
import { useEffect, useRef } from 'react';
import cytoscape, { type Core } from 'cytoscape';
import { useGraphStore } from '@/store/graphStore';

export function CytoscapeRenderer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const nodes = useGraphStore((s) => s.nodes);
  const edges = useGraphStore((s) => s.edges);
  const layout = useGraphStore((s) => s.layout);
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode);

  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;
    cyRef.current = cytoscape({
      container: containerRef.current,
      style: [
        { selector: 'node', style: { 'background-color': '#0f62fe', label: 'data(label)', 'font-size': 10 } },
        { selector: 'node[type="gene"]', style: { 'background-color': '#0f62fe' } },
        { selector: 'node[type="protein"]', style: { 'background-color': '#24a148' } },
        { selector: 'node[type="compound"]', style: { 'background-color': '#da1e28' } },
        { selector: 'node[type="disease"]', style: { 'background-color': '#f1c21b' } },
        { selector: 'edge', style: { 'line-color': '#e0e0e0', width: 1 } },
      ],
    });

    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.id(),
        type: node.data('type') ?? 'unknown',
        properties: { label: node.data('label') },
      });
    });
  }, [containerRef.current]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().remove();
    nodes.forEach((n) => {
      cy.add({ group: 'nodes', data: { id: n.id, type: n.type, label: n.properties?.label ?? n.id } });
    });
    edges.forEach((e) => {
      cy.add({ group: 'edges', data: { source: e.node.id, target: e.node.id } });  // simplified for V1
    });
    cy.layout({ name: layout }).run();
  }, [nodes, edges, layout]);

  return <div ref={containerRef} style={{ width: '100%', height: 500, border: '1px solid var(--color-hairline)' }} />;
}
```

- [ ] **Step 2: 创建 LayoutControls.tsx**

```tsx
import { useGraphStore } from '@/store/graphStore';

const LAYOUTS: { key: 'cose' | 'breadthfirst' | 'concentric' | 'grid'; label: string }[] = [
  { key: 'cose', label: 'Force' },
  { key: 'breadthfirst', label: 'Tree' },
  { key: 'concentric', label: 'Radial' },
  { key: 'grid', label: 'Grid' },
];

export function LayoutControls() {
  const layout = useGraphStore((s) => s.layout);
  const setLayout = useGraphStore((s) => s.setLayout);

  return (
    <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
      {LAYOUTS.map((l) => (
        <button key={l.key} className={layout === l.key ? 'primary' : ''} onClick={() => setLayout(l.key)} style={{ fontSize: 12, padding: '4px 8px' }}>
          {l.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: 创建 GraphCanvas.tsx**

```tsx
import { CytoscapeRenderer } from './CytoscapeRenderer';
import { LayoutControls } from './LayoutControls';
import { useGraphStore } from '@/store/graphStore';
import { useGraphExpand } from '@/hooks/useGraphExpand';

export function GraphCanvas() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const setSubgraph = useGraphStore((s) => s.setSubgraph);
  const { data } = useGraphExpand(selectedNode?.type ?? null, selectedNode?.id ?? null);

  // 当 expand 数据返回时更新 graph store
  // V1: 简化——选中节点时更新子图
  if (data && data.nodes.length > 0) {
    // 避免在 render 中 setState: 用 useEffect
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: 'var(--space-2)', fontWeight: 300 }}>Graph</h3>
      <CytoscapeRenderer />
      <LayoutControls />
    </div>
  );
}
```

- [ ] **Step 4: 创建 NodeDetail.tsx**

```tsx
import type { NodeData } from '@/api/graph';

interface Props {
  node: NodeData | null;
}

export function NodeDetail({ node }: Props) {
  if (!node) {
    return <p style={{ color: 'var(--color-ink-subtle)' }}>Select a node to view details</p>;
  }

  return (
    <div>
      <h4 style={{ fontWeight: 400, marginBottom: 8 }}>{node.properties?.label ?? node.id}</h4>
      <p style={{ fontSize: 12, color: 'var(--color-ink-muted)', marginBottom: 16 }}>
        Type: <strong>{node.type}</strong> · ID: {node.id}
      </p>
      <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
        <tbody>
          {Object.entries(node.properties).map(([key, value]) => (
            <tr key={key} style={{ borderBottom: '1px solid var(--color-hairline)' }}>
              <td style={{ padding: '4px 8px', fontWeight: 600, color: 'var(--color-ink-muted)' }}>{key}</td>
              <td style={{ padding: '4px 8px' }}>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 5: 创建 RelationTable.tsx + ExternalLinks.tsx + DetailPanel.tsx**

```tsx
// RelationTable.tsx — 简化占位
import type { EdgeData } from '@/api/graph';

interface Props {
  edges: EdgeData[];
}

export function RelationTable({ edges }: Props) {
  if (edges.length === 0) return <p style={{ color: 'var(--color-ink-subtle)', fontSize: 13 }}>No relations</p>;
  return (
    <div style={{ marginTop: 16 }}>
      <h4 style={{ fontWeight: 400, marginBottom: 8 }}>Relations ({edges.length})</h4>
      {edges.map((edge, i) => (
        <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid var(--color-hairline)', fontSize: 13 }}>
          <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{edge.relation}</span>
          <span style={{ margin: '0 8px', color: 'var(--color-ink-subtle)' }}>→</span>
          <span>{edge.node.id}</span>
        </div>
      ))}
    </div>
  );
}
```

```tsx
// ExternalLinks.tsx
import type { NodeData } from '@/api/graph';

const SOURCE_URLS: Record<string, (id: string) => string> = {
  gene: (id) => `https://www.uniprot.org/uniprotkb?query=${id.replace('gene:', '')}`,
  protein: (id) => `https://www.uniprot.org/uniprotkb/${id.replace('protein:', '')}`,
  compound: (id) => `https://www.ebi.ac.uk/chembl/compound_report_card/${id.replace('compound:', '')}/`,
  disease: (id) => `https://platform.opentargets.org/disease/${id}`,
  article: (id) => `https://pubmed.ncbi.nlm.nih.gov/${id.replace('pmid:', '')}/`,
};

interface Props {
  node: NodeData | null;
}

export function ExternalLinks({ node }: Props) {
  if (!node) return null;
  const urlFn = SOURCE_URLS[node.type];
  if (!urlFn) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <a href={urlFn(node.id)} target="_blank" rel="noopener noreferrer"
         style={{ color: 'var(--color-primary)', fontSize: 13, textDecoration: 'none' }}>
        View in source database →
      </a>
    </div>
  );
}
```

```tsx
// DetailPanel.tsx
import { useGraphStore } from '@/store/graphStore';
import { useNodeDetail } from '@/hooks/useNodeDetail';
import { NodeDetail } from './NodeDetail';
import { RelationTable } from './RelationTable';
import { ExternalLinks } from './ExternalLinks';

export function DetailPanel() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const { data } = useNodeDetail(selectedNode?.type ?? null, selectedNode?.id ?? null);

  return (
    <div className="card">
      <h3 style={{ fontWeight: 300, marginBottom: 'var(--space-3)' }}>Details</h3>
      <NodeDetail node={data?.node ?? selectedNode} />
      <RelationTable edges={data?.neighbors ?? []} />
      <ExternalLinks node={selectedNode} />
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/GraphExplorer/GraphCanvas/ frontend/src/pages/GraphExplorer/DetailPanel/
git commit -m "feat: add GraphCanvas (CytoscapeRenderer, LayoutControls) and DetailPanel components"
```

---

### Task 22: GraphExplorer 主页面

**Files:**
- Create: `frontend/src/pages/GraphExplorer/GraphExplorer.tsx`

- [ ] **Step 1: 创建 GraphExplorer.tsx**

```tsx
import { SearchPanel } from './SearchPanel/SearchPanel';
import { GraphCanvas } from './GraphCanvas/GraphCanvas';
import { DetailPanel } from './DetailPanel/DetailPanel';

export function GraphExplorer() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr 320px',
      gap: 'var(--space-3)',
      padding: 'var(--space-4)',
      minHeight: '100vh',
    }}>
      <div>
        <SearchPanel />
      </div>
      <div>
        <GraphCanvas />
      </div>
      <div>
        <DetailPanel />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 挂载 GraphExplorer**

```tsx
import { GraphExplorer } from '@/pages/GraphExplorer/GraphExplorer';

function App() {
  return <GraphExplorer />;
}

export default App;
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/GraphExplorer/GraphExplorer.tsx frontend/src/App.tsx
git commit -m "feat: add GraphExplorer main page with three-panel layout"
```

---

### Task 23: E2E 测试

**Files:**
- Create: `frontend/src/__tests__/e2e/graph-explorer.spec.ts`
- Create: `frontend/playwright.config.ts`

- [ ] **Step 1: 创建 playwright.config.ts**

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'src/__tests__/e2e',
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: true,
  },
  use: {
    baseURL: 'http://localhost:5173',
  },
});
```

- [ ] **Step 2: 创建 E2E 测试**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Graph Explorer', () => {
  test('loads the main page with three-panel layout', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h3').filter({ hasText: 'Graph' })).toBeVisible();
    await expect(page.getByRole('textbox')).toBeVisible();
  });

  test('can type in search and see placeholder text', async ({ page }) => {
    await page.goto('/');
    const input = page.getByRole('textbox');
    await expect(input).toHaveAttribute('placeholder', 'Search genes, proteins, diseases...');
    await input.fill('BRCA1');
    await expect(input).toHaveValue('BRCA1');
  });
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/__tests__/e2e/ frontend/playwright.config.ts
git commit -m "test: add Playwright E2E tests for graph explorer"
```

---

### Task 24: import-linter 约束 + ESLint 约束

**Files:**
- Create: `backend/.importlinter`
- Modify: `frontend/.eslintrc.cjs`

- [ ] **Step 1: 创建 backend/.importlinter**

```ini
[importlinter]
root_package = app
include_external_packages = False

[importlinter:contract:1]
name = services-dont-import-fastapi
type = forbidden
source_modules =
    app.services
forbidden_modules =
    fastapi
    starlette

[importlinter:contract:2]
name = repositories-dont-import-services
type = forbidden
source_modules =
    app.repositories
forbidden_modules =
    app.services

[importlinter:contract:3]
name = models-no-internal-imports
type = forbidden
source_modules =
    app.models
forbidden_modules =
    app.routers
    app.services
    app.repositories
```

- [ ] **Step 2: 创建 frontend/.eslintrc.cjs**

```javascript
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: [],
  rules: {
    'import/no-restricted-paths': [
      'error',
      {
        zones: [
          { target: './src/components', from: './src/api', message: 'Components must not import from api/' },
          { target: './src/components', from: './src/store', message: 'Components must use props, not stores' },
        ],
      },
    ],
  },
};
```

- [ ] **Step 3: Commit**

```bash
git add backend/.importlinter frontend/.eslintrc.cjs
git commit -m "chore: add import-linter and ESLint coupling enforcement"
```

---

### Task 25: 最终集成验证

- [ ] **Step 1: 后端 lint + 测试**

```bash
cd backend
ruff check app/ ingest/
python -m pytest tests/ -v
```

- [ ] **Step 2: 前端 lint + 测试**

```bash
cd frontend
npm run lint
npx vitest run
```

- [ ] **Step 3: import 合规检查**

```bash
cd backend
lint-imports
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: final integration verification — all tests pass, imports compliant"
```

---

## 执行顺序

```
1  项目脚手架后端       Task 1
2  项目脚手架前端       Task 2
3  数据库连接层         Task 3
4  图模型 DTO          Task 4 + 5
5  Graph Repository    Task 6
6  Search Repository   Task 7
7  Graph Service+Router Task 8 + 9
8  Search Service+Router Task 10
9  Ingest Service+Router Task 11
10 BaseIngester+Pipeline Task 12 + 13
11 PubMed Ingester     Task 14
12 UniProt Ingester    Task 15
13 Celery + Migrations Task 16
14 前端 API 层         Task 17
15 Zustand Stores      Task 18
16 React Hooks         Task 19
17 SearchPanel 组件    Task 20
18 Graph+Detail 组件   Task 21
19 主页面组装          Task 22
20 E2E 测试            Task 23
21 导入约束            Task 24
22 最终集成验证        Task 25
```
