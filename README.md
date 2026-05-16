# Biomed Knowledge Graph

面向生物医学研究者的开放知识图谱平台。集成 **PubMed、UniProt、ChEMBL、Open Targets、STRING** 五个公开数据源，提供基因-蛋白-化合物-疾病-文献的统一查询与交互式可视化。

## 架构

```
Neo4j (图数据库) ← FastAPI (后端) → React + Cytoscape.js (前端)
       ↑                  ↑                  ↑
  Celery Pipeline    Router→Service→Repo   Zustand + TanStack Query
       ↑
  PubMed / UniProt / ChEMBL / Open Targets / STRING
```

**核心原则：** 高内聚低耦合，严格单向依赖。后端 Router → Service → Repository → DB Driver，前端 Page → hooks → api。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，15 个路由
│   │   ├── config.py            # 环境配置 (BIOMED_* 前缀)
│   │   ├── db/                  # Neo4j + PostgreSQL 连接层
│   │   ├── models/              # Pydantic DTO (graph, search, ingest)
│   │   ├── repositories/        # Cypher 查询 + SQL 查询封装
│   │   ├── services/            # 纯业务逻辑 (不 import FastAPI)
│   │   ├── routers/             # HTTP 端点 (参数校验 + 序列化)
│   │   └── errors.py            # 异常类 + 全局 handler
│   ├── ingest/
│   │   ├── base.py              # BaseIngester 抽象契约
│   │   ├── pipeline.py          # 编排器 (调度/重试/限流)
│   │   ├── sources/             # 5 个数据源实现
│   │   ├── resolvers/           # 实体 ID 标准化
│   │   ├── serializers.py       # 批量 Cypher 写入
│   │   └── stats.py             # 同步统计
│   ├── tasks/                   # Celery 定时任务
│   ├── migrations/              # SQL 建表脚本
│   └── tests/                   # pytest (9 单元 + 快照测试)
├── frontend/
│   ├── src/
│   │   ├── api/                 # 纯 TS 函数 (axios 封装, 不 import React)
│   │   ├── store/               # 3 独立 Zustand stores
│   │   ├── hooks/               # TanStack Query 封装
│   │   ├── pages/GraphExplorer/ # 三栏布局 (SearchPanel | GraphCanvas | DetailPanel)
│   │   └── styles/              # IBM Carbon CSS 设计 token
│   └── src/__tests__/           # Vitest + Playwright E2E
└── docs/superpowers/
    ├── specs/                    # 设计文档
    └── plans/                    # 实施计划
```

## 快速开始

### 环境要求

- Python 3.12+ / Node.js 20+
- Neo4j 5.x / PostgreSQL 16 / Redis 7+

### 1. 数据库

```bash
# PostgreSQL
createdb biomed
psql biomed < backend/migrations/001_search_tables.sql

# Neo4j (Community Edition)
# 设置密码后创建约束:
# cypher: CREATE CONSTRAINT unique_gene IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE
```

### 2. 后端

```bash
cd backend
pip install -e ".[dev]"

# 设置环境变量 (或创建 .env)
export BIOMED_NEO4J_PASSWORD=yourpassword
export BIOMED_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/biomed

# 启动 API
uvicorn app.main:app --reload --port 8000

# 启动 Celery worker (新终端)
celery -A tasks.celery_app worker --loglevel=info
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 4. 首次数据同步

```bash
# 触发 5 个数据源同步
curl -X POST http://localhost:8000/api/ingest/sync/pubmed
curl -X POST http://localhost:8000/api/ingest/sync/uniprot
curl -X POST http://localhost:8000/api/ingest/sync/chembl
curl -X POST http://localhost:8000/api/ingest/sync/opentargets
curl -X POST http://localhost:8000/api/ingest/sync/string

# 查看同步状态
curl http://localhost:8000/api/ingest/status
```

## API 端点

### 图谱查询

| 端点 | 说明 |
|------|------|
| `GET /api/graph/node/{type}/{id}` | 节点详情 + 1 跳邻居 |
| `GET /api/graph/expand/{type}/{id}` | N 跳子图 (?depth=1&limit=50) |
| `GET /api/graph/path?from=G:BRCA1&to=D:BreastCancer` | 最短路径 |
| `GET /api/graph/network/{protein_id}` | 蛋白互作网络 |

### 搜索

| 端点 | 说明 |
|------|------|
| `GET /api/search?q=BRCA1&type=gene` | 全文搜索 |
| `GET /api/search/suggest?q=BRC` | 自动补全 |
| `GET /api/search/top?type=disease` | 热门实体 |

### 数据管理

| 端点 | 说明 |
|------|------|
| `POST /api/ingest/sync/{source}` | 触发同步 |
| `GET /api/ingest/status` | 同步状态 |
| `GET /api/ingest/logs?source=pubmed` | 同步日志 |

## 图模型

```
Gene ──[:ENCODES]──→ Protein
Gene ──[:TARGETS]──→ Disease
Protein ──[:INTERACTS_WITH]──→ Protein
Protein ──[:ASSOCIATED_WITH]──→ Disease
Compound ──[:BINDS_TO]──→ Protein
Compound ──[:TREATS]──→ Disease
Article ──[:MENTIONS]──→ Gene / Protein / Disease
```

## 测试

```bash
# 后端 (9 tests)
cd backend && pytest tests/ -v

# 前端单元 (6 tests)
cd frontend && npx vitest run

# 前端 E2E (3 tests)
cd frontend && npx playwright test
```

## 设计系统

使用 **IBM Carbon** 设计语言 — 白色画布、IBM Blue `#0f62fe` 单色强调、IBM Plex Sans 字体、0-4px 硬朗圆角。

## 数据源

| 数据源 | 维护方 | 内容 | 同步频率 |
|--------|--------|------|---------|
| PubMed | NIH/NCBI | 3600万+ 文献, MeSH | 日 |
| UniProt | EMBL-EBI/SIB | 2.3亿+ 蛋白, 疾病注释 | 周 |
| ChEMBL | EMBL-EBI | 240万+ 化合物, 活性 | 周 |
| Open Targets | EMBL-EBI/Welcome | 靶点-疾病关联 | 周 |
| STRING | CPR/EMBL | 200亿+ 蛋白互作 | 周 |

## License

MIT
