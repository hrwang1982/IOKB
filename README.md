# 智能运维知识库系统 (IOKB)

**Intelligent Operations Knowledge Base** — 面向金融行业运维领域的智能化解决方案，集成 RAG 知识库、CMDB 配置管理、智能告警分析、多模态文档处理等能力，帮助运维团队快速定位故障、检索知识、管理 IT 资产。

---

## ✨ 核心功能

### 🔍 RAG 智能知识库
- 支持多种文档格式上传解析（PDF、Word、Excel、图片、视频、音频）
- OCR 图片文字识别（PaddleOCR-VL）、ASR 语音转写
- 多模态 VL 模型支持（图片理解、视频分析）
- 向量化语义检索 + Rerank 精排
- 基于大模型的知识问答，支持溯源查看引用来源

### 🖥️ CMDB 配置管理数据库
- 16+ 预置 CI 类型（服务器、存储、网络、数据库、中间件、K8s 集群/节点/Pod、Docker、VMware 等）
- 支持自定义 CI 类型和属性扩展
- CI 关系拓扑管理（依赖、包含、连接、运行于、部署于、属于）
- 拓扑可视化展示（Dagre 布局）
- 通过 Kafka 实现 CMDB 数据实时同步
- 性能指标（InfluxDB 时序数据）、告警、日志的关联查看

### 🚨 智能告警分析
- Kafka 实时消费告警/性能/日志数据
- Elasticsearch 存储与检索
- **大模型驱动的智能分析**：
  - 自动关联 CI 信息、性能数据、日志和相关告警
  - LLM 根因分析、影响范围评估、解决建议
  - 知识库检索方案推荐
- 分析结果缓存，避免重复分析

### 📊 运维仪表盘
- CI 数量统计、告警趋势可视化
- 今日问答统计
- 各维度数据概览

### 🔐 用户与权限管理
- JWT Token 认证（Access Token + Refresh Token）
- RBAC 角色权限控制
- 可选 LDAP / SSO 集成
- 多租户支持

### ⚙️ 系统配置管理
- LLM / Embedding / Rerank / OCR / ASR / VL 模型统一配置
- 支持多提供商切换（阿里云、OpenAI、本地部署等）
- 通过 YAML 文件管理模块参数
- 可观测性监控

---

## 🏗️ 技术架构

### 后端
| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI (Python 3.10+) |
| ORM | SQLAlchemy 2.0 (异步) |
| 关系数据库 | MySQL 8.0+ |
| 搜索引擎 | Elasticsearch 8.x |
| 时序数据库 | InfluxDB 2.7 |
| 消息队列 | Kafka (Confluent) |
| 缓存 | Redis 7.x |
| 认证 | JWT (python-jose) + LDAP |

### AI / ML
| 组件 | 技术 |
|------|------|
| 大语言模型 | 通义千问 (Qwen-Turbo) / OpenAI 兼容 |
| 向量模型 | text-embedding-v3 (阿里云) |
| Rerank 模型 | GTE-Rerank (阿里云) |
| OCR | PaddleOCR-VL |
| ASR | Paraformer-v2 (阿里云) |
| 多模态 | Qwen-VL-Max (阿里云) |
| RAG 框架 | LangChain |

### 前端
| 组件 | 技术 |
|------|------|
| 框架 | Next.js 14 |
| 语言 | TypeScript |
| UI 组件 | Radix UI + TailwindCSS |
| 状态管理 | Zustand + SWR |
| 图表 | Recharts |
| 表单 | React Hook Form + Zod |

---

## 📁 项目结构

```
skb/
├── app/                            # 后端应用代码
│   ├── main.py                     # FastAPI 应用入口 & 生命周期管理
│   ├── config.py                   # 全局配置（Pydantic Settings）
│   ├── api/                        # API 路由层
│   │   ├── auth.py                 #   认证接口
│   │   ├── knowledge.py            #   知识库管理 & 问答
│   │   ├── cmdb.py                 #   CMDB 配置项管理
│   │   ├── alert.py                #   告警查询 & 智能分析
│   │   ├── dashboard.py            #   仪表盘统计
│   │   ├── llm.py                  #   大模型配置管理
│   │   ├── config.py               #   系统配置
│   │   └── observability.py        #   可观测性
│   ├── core/                       # 核心业务逻辑
│   │   ├── database.py             #   数据库连接管理
│   │   ├── rag/                    #   RAG 知识库引擎
│   │   │   ├── parser.py           #     文档解析（PDF/Word/Excel/图片/视频/音频）
│   │   │   ├── splitter.py         #     文本分割
│   │   │   ├── embedder.py         #     向量化
│   │   │   ├── retriever.py        #     语义检索
│   │   │   ├── reranker.py         #     结果精排
│   │   │   ├── qa.py               #     知识问答
│   │   │   ├── ocr.py              #     OCR 识别
│   │   │   └── multimodal.py       #     多模态处理
│   │   ├── cmdb/                   #   CMDB 模块
│   │   │   ├── service.py          #     CMDB 核心服务
│   │   │   ├── ci_types.py         #     CI 类型定义
│   │   │   ├── es_storage.py       #     ES 存储（告警/日志）
│   │   │   ├── influxdb.py         #     InfluxDB 时序数据
│   │   │   ├── kafka.py            #     Kafka 同步管理
│   │   │   ├── kafka_consumer.py   #     Kafka 消费者
│   │   │   ├── socket_server.py    #     Socket 服务
│   │   │   └── sync.py             #     数据同步
│   │   ├── alert/                  #   告警分析模块
│   │   │   ├── analyzer.py         #     告警上下文分析
│   │   │   ├── llm_analyzer.py     #     LLM 智能分析
│   │   │   ├── processor.py        #     告警处理
│   │   │   └── recommender.py      #     方案推荐
│   │   └── llm/                    #   LLM 网关
│   │       └── gateway.py          #     多模型统一调用
│   ├── models/                     # 数据库模型 (SQLAlchemy)
│   │   ├── user.py                 #   用户 & 角色模型
│   │   ├── knowledge.py            #   知识库 & 文档模型
│   │   ├── cmdb.py                 #   CI & 关系模型
│   │   └── alert.py                #   告警模型
│   ├── auth/                       # 认证授权模块
│   │   ├── jwt.py                  #   JWT Token 管理
│   │   ├── rbac.py                 #   RBAC 权限控制
│   │   ├── ldap.py                 #   LDAP 集成
│   │   ├── user_service.py         #   用户服务
│   │   └── dependencies.py         #   FastAPI 依赖注入
│   ├── services/                   # 公共服务
│   │   └── document_processor.py   #   文档处理服务
│   └── utils/                      # 工具函数
├── frontend/                       # 前端应用 (Next.js)
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/             #   登录页
│   │   │   └── (dashboard)/        #   主控台布局
│   │   │       ├── dashboard/      #     仪表盘
│   │   │       ├── knowledge/      #     知识库管理
│   │   │       ├── cmdb/           #     CMDB 管理
│   │   │       ├── alerts/         #     告警中心
│   │   │       ├── admin/          #     用户管理
│   │   │       └── settings/       #     系统设置
│   │   └── components/             #   公共组件
│   ├── package.json
│   └── tailwind.config.ts
├── config/                         # 模块配置文件 (YAML)
│   ├── alert.yaml                  #   告警分析配置 & Prompt 模板
│   ├── cmdb.yaml                   #   CMDB 模块配置
│   ├── rag.yaml                    #   RAG 知识库配置
│   └── auth.yaml                   #   认证授权配置
├── scripts/                        # 工具脚本
│   ├── generate_cmdb_mock_data.py  #   CMDB 模拟数据生成
│   ├── init_cmdb_attributes.py     #   CI 属性初始化
│   └── ...
├── tests/                          # 测试用例
│   ├── unit/                       #   单元测试
│   └── integration/                #   集成测试
├── storage/                        # 文件存储目录
├── docker-compose.yml              # Docker Compose 编排
├── Dockerfile                      # 后端 Docker 镜像
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量模板
└── pytest.ini                      # 测试配置
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose（推荐）

### 方式一：Docker Compose 一键部署（推荐）

**1. 克隆项目并配置环境变量**

```bash
git clone <repo-url> && cd skb
cp .env.example .env
# 编辑 .env 文件，配置 LLM API Key 等必要参数
```

**2. 启动所有服务**

```bash
docker-compose up -d
```

这将启动以下服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| `skb-api` | 8000 | 后端 API 服务 |
| `skb-frontend` | 3000 | 前端应用 |
| `mysql` | 3306 | MySQL 数据库 |
| `elasticsearch` | 9200 | Elasticsearch |
| `kafka` | 9092 / 29092 | Kafka 消息队列 |
| `redis` | 6379 | Redis 缓存 |
| `influxdb` | 8086 | InfluxDB 时序数据库 |
| `dozzle` | 8888 | Docker 日志查看器 |

**3. 访问系统**

- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 方式二：本地开发

**1. 安装后端依赖**

```bash
pip install -r requirements.txt
```

**2. 安装前端依赖**

```bash
cd frontend && npm install
```

**3. 配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，确保数据库和中间件连接信息正确
```

**4. 启动后端服务**

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**5. 启动前端服务**

```bash
cd frontend
npm run dev
```

---

## ⚙️ 配置说明

所有配置通过 `.env` 文件管理，主要配置项包括：

| 配置分类 | 关键变量 | 说明 |
|----------|----------|------|
| **LLM 大模型** | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL_NAME` | 支持 aliyun / openai / local 等 |
| **向量模型** | `EMBEDDING_PROVIDER`, `EMBEDDING_API_KEY` | 文档向量化 |
| **Rerank** | `RERANK_PROVIDER`, `RERANK_API_KEY` | 检索结果精排 |
| **OCR** | `OCR_PROVIDER`, `OCR_DEPLOY_MODE` | 图片文字识别 |
| **ASR** | `ASR_PROVIDER`, `ASR_MODEL_NAME` | 语音转写 |
| **VL 多模态** | `VL_PROVIDER`, `VL_MODEL_NAME` | 图片理解/视频分析 |
| **数据库** | `MYSQL_*`, `ES_*`, `INFLUXDB_*` | 各数据库连接 |
| **消息队列** | `KAFKA_*` | Kafka 配置 |
| **认证** | `JWT_*`, `LDAP_*`, `SSO_*` | 认证方式配置 |

> 详细配置请参考 [.env.example](./.env.example) 文件中的注释说明。

模块级别的细粒度配置通过 `config/` 目录下的 YAML 文件管理：
- `alert.yaml` — 告警分析参数、LLM Prompt 模板、告警级别定义
- `cmdb.yaml` — CI 类型、关系类型、索引配置、拓扑参数
- `rag.yaml` — RAG 检索参数、分割策略
- `auth.yaml` — 认证授权细节配置

---

## 📖 API 文档

启动后端服务后，可通过以下地址访问自动生成的 API 文档：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

### API 模块概览

| 前缀 | 模块 | 功能 |
|------|------|------|
| `/api/v1/auth` | 认证 | 登录、注册、Token 刷新、用户管理 |
| `/api/v1/knowledge` | 知识库 | 知识库 CRUD、文档上传/解析、知识问答 |
| `/api/v1/cmdb` | CMDB | CI 管理、关系管理、拓扑查询、性能/告警/日志查询 |
| `/api/v1/alert` | 告警 | 告警查询、智能分析、方案推荐 |
| `/api/v1/dashboard` | 仪表盘 | 统计数据 |
| `/api/v1/llm` | 大模型 | LLM 模型配置管理 |
| `/api/v1/system` | 系统 | 系统参数配置 |
| `/api/v1/observability` | 可观测性 | 系统监控 |

---

## 🧪 测试

```bash
# 运行全部测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/
```

---

## 📚 相关文档

- [CMDB 数据接入 Kafka](./README-cmdb2kafka.md) — CMDB 数据通过 Kafka 同步的详细说明
- [如何初始化 CI 类型及属性](./README-如何初始化CI类型及属性.md) — CI 类型和属性的初始化指南
- [接入告警/性能/日志数据](./README-接入告警-性能-日志数据.md) — 告警、性能指标、日志数据接入说明

---

## 📄 License

MIT License
