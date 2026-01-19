# 智能运维知识库系统 (SKB)

Smart Knowledge Base - 面向金融行业运维领域的智能化解决方案

## 功能特性

- 🔍 **RAG知识库** - 支持多种文档格式解析、OCR识别、语义检索
- 🖥️ **CMDB配置管理** - 统一管理IT资产和配置项拓扑
- 🚨 **智能告警分析** - 大模型驱动的故障定位和方案推荐
- 🔐 **用户权限管理** - 多租户、RBAC权限控制

## 技术栈

- **后端**: FastAPI (Python 3.10+)
- **数据库**: MySQL (关系型), Elasticsearch (向量), InfluxDB (时序)
- **消息队列**: Kafka
- **OCR**: PaddleOCR-VL
- **向量模型**: qianwen3-embedding, qianwen3-rerank
- **前端**: React + Ant Design

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+
- Elasticsearch 8.x
- Kafka 3.x
- Redis 7.x

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

复制环境配置模板并修改：

```bash
cp .env.example .env
```

### 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 访问API文档

启动后访问: http://localhost:8000/docs

## 项目结构

```
skb/
├── app/                    # 应用代码
│   ├── api/               # API路由
│   ├── core/              # 核心业务逻辑
│   ├── auth/              # 认证授权
│   ├── models/            # 数据库模型
│   └── services/          # 业务服务
├── web/                    # 前端代码
├── tests/                  # 测试
└── docs/                   # 文档
```

## 开发文档

详见 [docs/](./docs/) 目录

## License

MIT License
