# 生物医学知识图谱平台 — 设计文档

## 概述

面向生物医学研究者的公开 Web 平台，集成 PubMed、UniProt、ChEMBL、Open Targets、STRING 五个免费公开数据源，提供基因-蛋白-化合物-疾病-文献的统一知识图谱查询与可视化。

**V1 不做用户登录/注册系统**，纯开放浏览查询。

---

## 架构原则 — 高内聚低耦合

### 分层隔离规则

```
┌──────────────────────────────────────────────────────────┐
│                       前端 (React)                        │
│  Page → hooks → api    store ← components (props only)   │
├──────────────────────────────────────────────────────────┤
│                    后端 (FastAPI)                         │
│  Router → Service → Repository → DB Driver               │
│  每层只依赖下一层，不跨层调用                                │
├──────────────────────────────────────────────────────────┤
│                    数据摄入 (Celery)                       │
│  Pipeline → BaseIngester (抽象) ← sources/* (实现)       │
│  编排层只认契约，不认具体数据源                               │
└──────────────────────────────────────────────────────────┘
```

### 耦合约束

| 规则 | 说明 |
|------|------|
| **单向依赖** | 上层依赖下层，下层绝不 import 上层 |
| **接口隔离** | 每层通过抽象/接口通信，不依赖具体实现 |
| **模块孤岛** | 一个模块只能 import 同层模块和直接下层，禁止跨层 import |
| **数据边界** | 跨层传递 DTO/ValueObject，不直接透传 ORM 对象或原始 dict |
| **无循环** | 任意两个模块之间不得形成 import 环 |

### 模块职责边界 (内聚性)

| 模块 | 只处理自己的事 | 不处理 |
|------|-------------|--------|
| `api/` | HTTP 请求序列化/反序列化 | 不做业务逻辑 |
| `services/` | 纯业务逻辑 | 不调 HTTP/数据库驱动 |
| `repositories/` | 数据库查询/写入 | 不做业务判断 |
| `ingest/sources/` | 单一数据源的拉取/清洗/转换 | 不做跨源合并或编排 |
| `ingest/pipeline.py` | 调度/重试/限流 | 不关心具体数据格式 |
| `ingest/resolvers/` | 实体 ID 标准化 | 不关心数据来源 |
| `components/` | 纯渲染 + props 驱动事件 | 不调 api/，不读写 store |
| `hooks/` | 数据获取/状态协调 | 不做 UI 渲染 |
| `store/` | 纯状态管理 | 不做数据获取 |

### 违规检测

- 后端: 用 `import-linter` 检查层间 import 合规性
- 前端: 用 ESLint `import/no-restricted-paths` 禁止 components → api, store → api
- CI 阻断: 违规 import 导致构建失败

---

## 1. 架构总览

```
┌──────────────────────────────────────────────────────────┐
│                      前端 (React)                         │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────────┐  │
│  │ 搜索面板 │  │ 图谱画布  │  │ 详情面板 (基因/蛋白/药物) │  │
│  │ 实体搜索 │  │ Cytoscape│  │ 文献列表/属性/置信度      │  │
│  │ 筛选条件 │  │ 交互式图  │  │ 外部链接跳转源数据库     │  │
│  └─────────┘  └──────────┘  └────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│                    后端 (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ /api/graph/* │  │ /api/search/*│  │ /api/ingest/* │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│         │                  │                 │           │
│    ┌────┴──────┐    ┌──────┴─────┐    ┌──────┴──────┐    │
│    │ Neo4j Driver│   │ PostgreSQL │    │   Celery    │    │
│    └────────────┘    └────────────┘    └─────────────┘    │
├──────────────────────────────────────────────────────────┤
│                    数据层                                 │
│  ┌──────┐  ┌─────────┐  ┌────────┐  ┌───────────┐       │
│  │Neo4j │  │PostgreSQL│  │ Celery │  │   Redis   │       │
│  │ 图谱 │  │ 元数据    │  │ 异步   │  │ 消息队列   │       │
│  └──────┘  └─────────┘  └────────┘  └───────────┘       │
├──────────────────────────────────────────────────────────┤
│                 外部数据源 (Celery 定时拉取)               │
│  ┌──────┐ ┌───────┐ ┌──────┐ ┌───────────┐ ┌────────┐  │
│  │PubMed│ │UniProt│ │ChEMBL│ │OpenTargets│ │ STRING │  │
│  └──────┘ └───────┘ └──────┘ └───────────┘ └────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 技术选型

| 层 | 选型 | 理由 |
|----|------|------|
| 图数据库 | Neo4j Community | 最成熟图数据库，Cypher 表达力强，生物信息学社区广泛使用 |
| 关系数据库 | PostgreSQL + pgvector | 元数据/用户/缓存，预留语义搜索 |
| 后端 | Python FastAPI | 无缝对接 Biopython/BioServices，异步数据拉取 |
| 异步任务 | Celery + Redis | 定时同步 5 个外部数据源 |
| 前端 | React 18 + TypeScript | 组件化，生态丰富 |
| 图可视化 | Cytoscape.js | STRING 也在用，专门面向生物网络，布局算法丰富 |
| 前端设计 | IBM Carbon (DESIGN.md) | 企业级科学严谨风，信息密度高，数据场景适配 |

---

## 2. 图模型

### 节点类型

| 节点 | 核心属性 | 数据来源 |
|------|---------|----------|
| Gene | id, symbol, name, organism, synonyms | UniProt, PubMed |
| Protein | id, name, sequence, length, domains | UniProt |
| Compound | id, name, smiles, mw, logp | ChEMBL |
| Disease | id, name, icd_code, synonyms | Open Targets, UniProt |
| Article | pmid, title, year, journal, abstract | PubMed |

### 关系类型

| 关系 | 起点 → 终点 | 属性 | 数据来源 |
|------|-------------|------|----------|
| `[:ENCODES]` | Gene → Protein | — | UniProt |
| `[:INTERACTS_WITH]` | Protein → Protein | score, evidence | STRING (score ≥ 0.7) |
| `[:BINDS_TO]` | Compound → Protein | ic50, ki, assay_type | ChEMBL |
| `[:TARGETS]` | Gene → Disease | score, evidence_sources | Open Targets |
| `[:ASSOCIATED_WITH]` | Protein → Disease | confidence | UniProt |
| `[:TREATS]` | Compound → Disease | phase, status | ChEMBL |
| `[:MENTIONS]` | Article → Gene/Protein/Disease | mention_count, relevance | PubMed |

---

## 3. API 设计

### 图谱查询

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/graph/node/:type/:id` | GET | 节点详情 + 1 跳邻居 |
| `/api/graph/expand/:type/:id` | GET | N 跳子图 (?depth=1&limit=50, max depth=3) |
| `/api/graph/path` | GET | 两节点间最短路径 |
| `/api/graph/network/:protein_id` | GET | 蛋白互作网络 (?min_score=0.7&limit=100) |

### 搜索

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search?q=&type=` | GET | 全局搜索 (PostgreSQL 全文索引) |
| `/api/search/suggest?q=` | GET | 自动补全 |
| `/api/search/top?type=` | GET | 热门实体列表 |

### 数据管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/ingest/sync/:source` | POST | 手动触发同步 |
| `/api/ingest/status` | GET | 同步状态/时间戳 |
| `/api/ingest/logs?source=` | GET | 同步日志 |

### 导出

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/export/graph?format=json` | GET | 当前子图 JSON |
| `/api/export/graph?format=csv` | GET | CSV 边表 |

### 约束

- 所有 Cypher 参数化，禁止字符串拼接
- expand 默认 depth=1 limit=50，最大 depth=3
- 搜索加 min_relevance 过滤

### 后端分层架构

```
routers/         ← HTTP 层: 参数校验, 序列化, 调用 service, 返回 Response
  └── graph.py      依赖 → services/graph.py
  └── search.py     依赖 → services/search.py
  └── ingest.py     依赖 → services/ingest.py

services/        ← 业务层: 纯逻辑, 不 import fastapi/starlette
  └── graph.py      依赖 → repositories/graph.py
  └── search.py     依赖 → repositories/search.py
  └── ingest.py     依赖 → ingest/sources/* (通过 BaseIngester)

repositories/    ← 数据层: 封装 Neo4j Driver / PostgreSQL, 只暴露查询方法
  └── graph.py      import neo4j
  └── search.py     import asyncpg

models/          ← 共享 DTO: 跨层传递的 pydantic 模型
  └── graph.py      NodeModel, EdgeModel, SubgraphModel
  └── search.py     SearchResult, Suggestion
```

**依赖方向 (严格单向):**

```
routers/ ──▶ services/ ──▶ repositories/ ──▶ neo4j / asyncpg
    │            │              │
    └────────────┴──────────────┴──▶ models/ (纯数据, 无依赖)
```

**关键约束:**
- `services/` 不 import `fastapi` / `starlette` / `Response`
- `repositories/` 不 import `services/` 或 `routers/`
- `models/` 不 import 任何项目内模块
- 跨层只传 DTO / pydantic model，不传 dict 或 ORM 对象

---

## 4. 前端架构

### 组件分层

```
pages/
└── GraphExplorer/           ← 编排层
    ├── SearchPanel/         ← 搜索 (SearchInput, SuggestionList, FilterBar)
    ├── GraphCanvas/         ← 图谱 (CytoscapeRenderer, NodeContextMenu, LayoutControls, MiniMap)
    └── DetailPanel/         ← 详情 (NodeDetail, RelationTable, ExternalLinks)
```

### 状态管理 (3 独立 Zustand store)

```
store/
├── searchStore.ts    ← 搜索词/建议/筛选
├── graphStore.ts     ← 当前子图/选中节点/布局
└── uiStore.ts        ← 侧栏展开/暗色模式/Toast
```

Store 互不 import，不直接通信。

### 数据获取层

```
api/                    ← 纯 TS 函数，不 import React
├── client.ts           ← axios 实例
├── graph.ts / search.ts / ingest.ts

hooks/                  ← 唯一可同时触达 api + store 的层
├── useGraphExpand.ts / useNodeDetail.ts / useSearch.ts / useSyncStatus.ts
```

### 依赖方向

```
Page ──▶ hooks/ ──▶ api/
  │         │
  ├──▶ store/
  └──▶ components/ (纯 props, 不调 api/store)
```

---

## 5. 数据摄入管道

### 每个数据源独立 pipeline

```
ingest/
├── base.py              ← BaseIngester 抽象类
├── pipeline.py          ← 编排器
├── sources/             ← pubmed.py, uniprot.py, chembl.py, opentargets.py, string.py
├── resolvers/           ← gene_resolver.py, disease_resolver.py, compound_resolver.py
├── serializers.py       ← 批量 Cypher 写入
└── stats.py             ← 同步统计
```

### BaseIngester 契约

```python
class BaseIngester(ABC):
    source_name: str
    batch_size: int = 500
    
    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[dict]: ...
    
    @abstractmethod
    def normalize(self, record: dict) -> NormalizedRecord | None: ...
    
    @abstractmethod
    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]: ...
```

### 关键约束

- 每个 Ingester 独立模块，增删源不改其他模块
- normalize() 不调外部网络
- 批量写入幂等 (MERGE + ON CREATE SET)
- Resolver 层与 source 层解耦
- 速率限制: 3 req/s，失败指数退避重试 3 次

---

## 6. 错误处理

### 分层策略

| 层 | 策略 |
|----|------|
| 前端 | Toast 用户友好消息，不暴露内部错误 |
| API | 统一 HTTP 状态码 + `{"error": "CODE", "message": "...", "request_id": "..."}` |
| 服务层 | 抛出业务异常 (GraphTimeoutError, EntityNotFound, ResolutionFailed) |
| 接入层 | 记录原始异常 + 转换为业务异常向上抛 |

### API 错误码

| 状态码 | code | 场景 |
|--------|------|------|
| 400 | INVALID_PARAM | depth>3, limit>200 |
| 404 | ENTITY_NOT_FOUND | 基因不存在于任何源 |
| 408 | GRAPH_TIMEOUT | Cypher 超时 30s |
| 429 | RATE_LIMITED | API 限流，带 Retry-After |
| 502 | UPSTREAM_ERROR | 外部 API 故障 |
| 503 | INGEST_IN_PROGRESS | 同步中不可用 |

### Ingest 容错

- 单条 normalize 失败 → warn + skip，不阻塞整批
- API 调 3 次失败 → error + 延迟到下次 cron
- Resolver 消歧失败 → 保留原始 ID，标记 confidence=low
- 批量写入部分失败 → 事务回滚整批

---

## 7. 测试策略

### 测试金字塔

| 层 | 工具 | 测什么 | 不测什么 |
|----|------|--------|---------|
| ingest | pytest + mock HTTP | normalize 逻辑, build_queries 输出 | 不调真实外部 API |
| api | FastAPI TestClient + 真实 Neo4j test DB | 端点返回, 参数校验 | 不调真实 ingest |
| components | Vitest + RTL | 组件纯渲染, props 边界 | 不调真实 hooks |
| hooks | Vitest + MSW | loading/error/data 状态 | 不测组件渲染 |
| store | Vitest 纯 Zustand | 状态变更逻辑 | — |
| E2E | Playwright | 搜基因→展开→查疾病 完整链路 | 外部 API (用 MSW/seed) |

### 约束

- 单元测试不碰网络和数据库
- Cypher 语句必须用测试库验证
- 每个源的 normalize() 有独立快照测试
- E2E 用种子数据，不依赖实时数据

---

## 8. 数据源

### 第一版集成 5 个数据源

| 数据源 | 维护方 | 核心数据 | 同步频率 |
|--------|--------|----------|---------|
| PubMed | NIH/NCBI | 3600万+ 文献, MeSH 词表 | 日 |
| UniProt | EMBL-EBI/SIB | 2.3亿+ 蛋白, 功能注释, 疾病关联 | 周 |
| ChEMBL | EMBL-EBI | 240万+ 生物活性化合物, 药物靶点 | 周 |
| Open Targets | EMBL-EBI/Welcome | 靶点-疾病关联, 遗传证据 | 周 |
| STRING | CPR/EMBL | 5900万+ 蛋白, 200亿+ 相互作用 | 周 |

所有数据源提供 REST API，无认证或仅需简单注册。

---

## 9. 前端设计系统

使用 IBM Carbon 设计语言 (来源: awesome-design-md/design-md/ibm/DESIGN.md):

- 白色画布，IBM Blue `#0f62fe` 单色强调
- IBM Plex Sans 字体，display 用 light 300 weight
- 0-4px 方正硬朗圆角
- 细线边框卡片，无阴影
- 数据密集、科学严谨氛围
