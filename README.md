# Biomed Knowledge Graph

面向生物医学研究者的开放知识图谱平台。集成 **UniProt、STRING、ChEMBL、Open Targets、PubMed** 五个公开数据源，提供基因-蛋白-化合物-疾病-文献的统一查询与交互式可视化。

## 架构

```
Neo4j (图数据库) ← FastAPI (后端) → React + Cytoscape.js (前端)
       ↑                  ↑                  ↑
  Celery Pipeline    Router→Service→Repo   Zustand + TanStack Query
       ↑
  UniProt / STRING / ChEMBL / Open Targets / PubMed
```

**核心原则：** 高内聚低耦合，严格单向依赖。后端 Router → Service → Repository → DB Driver，前端 Page → hooks → api。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，全局 error handler + request_id
│   │   ├── config.py            # 环境配置 (BIOMED_ 前缀，.env 自动加载)
│   │   ├── db/                  # Neo4j (basic_auth) + PostgreSQL (asyncpg pool)
│   │   ├── models/              # Pydantic DTO (graph, search, ingest)
│   │   ├── repositories/        # Cypher 查询 + SQL 全文搜索 + 分页/超时
│   │   ├── services/            # 纯业务逻辑 (不 import FastAPI)
│   │   ├── routers/             # HTTP 端点 (参数校验 + 序列化)
│   │   └── errors.py            # AppError 子类 + 全局 handler
│   ├── ingest/
│   │   ├── base.py              # BaseIngester + UNWIND 批量 build_queries
│   │   ├── pipeline.py          # 编排器 (fetch→normalize→flush, 重试+限流)
│   │   ├── sources/             # 5 个数据源 (uniprot, string, chembl, opentargets, pubmed)
│   │   ├── resolvers/           # 实体 ID 标准化
│   │   ├── serializers.py       # 批量 Cypher 写入 (安全标签/关系白名单)
│   │   ├── search_sync.py       # PG 搜索索引同步
│   │   └── stats.py             # 同步统计
│   ├── tasks/                   # Celery worker (solo pool for Windows)
│   ├── migrations/              # SQL 建表/索引
│   └── tests/                   # pytest 83 tests (unit + integration + snapshot, all pass)
├── frontend/
│   ├── src/
│   │   ├── api/                 # 纯 TS axios 封装 (EdgeData 含 source_id/target_id)
│   │   ├── store/               # Zustand (search, graph, ui, theme)
│   │   ├── hooks/               # TanStack Query + useCytoscapeState
│   │   ├── pages/GraphExplorer/ # 三栏布局 + 暗色/亮色主题 + anime.js 动画
│   │   └── styles/              # IBM Carbon 暗色主题 + light mode + prefers-reduced-motion
│   └── src/__tests__/           # Vitest + Playwright E2E
└── docs/
    ├── specs/                    # 设计文档
    └── plans/                    # 实施计划
```

## 数据状态

| 类型 | 节点数 | 边类型 | 边数 | 数据源 |
|------|--------|--------|------|--------|
| Gene | 20,200 | — | — | UniProt + OpenTargets |
| Protein | 23,090 | — | — | UniProt + STRING + ChEMBL |
| Compound | 941 | — | — | ChEMBL |
| Disease | 11 | — | — | OpenTargets |
| Article | 52 | — | — | PubMed |
| | | ENCODES | 19,425 | UniProt |
| | | INTERACTS_WITH | 49,919 | STRING |
| | | BINDS_TO | 500 | ChEMBL |
| | | TARGETS | 1,599 | OpenTargets |
| | | MENTIONS | 10 | PubMed |
| **Total** | **44,294** | | **71,453** | |

存储：Neo4j ~50MB + PostgreSQL ~16MB = ~66MB

## 快速开始

### 环境要求

- Python 3.10+ / Node.js 20+
- Docker (Neo4j 5.x, PostgreSQL 16, Redis 7)

### 1. 数据库

```bash
# 启动 Docker 容器
docker start biomed-postgres biomed-neo4j biomed-redis

# PostgreSQL 连接信息
# Host: localhost:5434, User: biomed, Pass: biomed123, DB: biomed

# Neo4j 连接信息
# bolt://localhost:7687, User: neo4j, Pass: password
```

### 2. 后端

```bash
cd backend
pip install -e ".[dev]"

# 创建 .env (参照 .env.example)
cp .env.example .env   # 编辑填入实际值

# 启动 API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 Celery worker (Windows)
cd backend && celery -A tasks.celery_app worker --loglevel=info --pool=solo
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 4. 首次数据同步

```bash
curl -X POST http://localhost:8000/api/ingest/sync/uniprot
curl -X POST http://localhost:8000/api/ingest/sync/string
curl -X POST http://localhost:8000/api/ingest/sync/chembl
curl -X POST http://localhost:8000/api/ingest/sync/opentargets
curl -X POST http://localhost:8000/api/ingest/sync/pubmed

# 查看同步状态
curl http://localhost:8000/api/ingest/status
```

## API 端点

### 图谱查询

| 端点 | 说明 |
|------|------|
| `GET /api/graph/node/{type}/{id}?limit=100` | 节点详情 + 邻居 (含 source_id/target_id) |
| `GET /api/graph/expand/{type}/{id}?depth=1&limit=50` | N 跳子图 |
| `GET /api/graph/path?from=gene:BRCA1&to=disease:EFO_0000305` | 最短路径 (timeout 30s) |
| `GET /api/graph/network/{protein_id}?min_score=0.7&limit=20` | 蛋白互作网络 |

### 搜索 (PostgreSQL 全文索引, 32,851 条)

| 端点 | 说明 |
|------|------|
| `GET /api/search?q=BRCA1&type=gene` | 全文搜索 |
| `GET /api/search/suggest?q=BRC` | 自动补全 |
| `GET /api/search/top?type=protein` | 热门实体 |

### 数据管理

| 端点 | 说明 |
|------|------|
| `POST /api/ingest/sync/{source}` | 触发 Celery 同步 |
| `GET /api/ingest/status` | 同步状态 |
| `GET /api/ingest/logs?source=pubmed` | 同步日志 |

### 健康检查

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 服务状态 |

## 图模型

```
Gene ──[:ENCODES]──→ Protein
Gene ──[:TARGETS]──→ Disease
Protein ──[:INTERACTS_WITH]──→ Protein
Compound ──[:BINDS_TO]──→ Protein
Article ──[:MENTIONS]──→ Gene / Disease
```

## 设计系统

- **暗色主题** (默认): 画布 `#0d1117`, IBM Blue `#0f62fe` 强调, IBM Plex Sans
- **亮色主题**: 画布 `#ffffff`, 通过 header toggle 切换, localStorage 持久化
- **节点颜色**: Gene 蓝 / Protein 绿 / Compound 红 / Disease 黄 / Article 灰
- **动画**: anime.js v4 (page load stagger, node entrance, tap ripple, search result slide)

## 命令

| 操作 | 命令 |
|------|------|
| 后端开发 | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| 前端开发 | `cd frontend && npm run dev` |
| 后端测试 | `cd backend && python -m pytest tests/ -v` (83 pass) |
| 前端测试 | `cd frontend && npx vitest run` |
| E2E 测试 | `cd frontend && npx playwright test` |
| Python lint | `cd backend && ruff check .` |
| TypeScript | `cd frontend && npx tsc -b` |
| Celery | `cd backend && celery -A tasks.celery_app worker --loglevel=info --pool=solo` |

## 已知限制

### 已解决
- ~~STRING/ChEMBL 蛋白 ID 与 UniProt accession 体系不统一~~ → 已解决（gene resolver `ingest/resolvers/gene.py`；target resolver 部分覆盖）
- ~~OpenTargets 仅取每疾病 1 页~~ → 已解决（完整分页）
- ~~UniProt ASSOCIATED_WITH 边未包含~~ → 已解决（UniProt ingester 解析疾病注释并创建边）
- ~~anime.js + cytoscape 未做代码分割~~ → 已解决（CytoscapeRenderer 通过 `React.lazy()` 懒加载）

### 待解决
- ~~无应用层测试~~ → 已解决（25 个集成测试，TestClient + mocked Neo4j/Postgres）
- `/api/ingest/sync` 端点未加认证保护
- 无速率限制中间件
- ~~docker-compose Redis 无持久化~~ → 已解决（AOF + volume）

## License

MIT
