# CMDB Kafka 数据同步集成指南

本指南旨在帮助系统集成人员了解如何通过 Kafka 消息队列将外部配置项数据自动同步到 IOKB CMDB 系统中。

## 1. 核心特性

*   **实时同步**：支持通过 Kafka Topic 实时接收配置项变更（增、删、改）。
*   **自动标识**：支持配置“唯一标识生成规则”（如 `{hostname}-{ip}`），当数据源无法提供全局唯一 ID 时，系统可根据规则自动生成，无需人工干预。
*   **自动建表**：无需预先创建 CI，系统根据消息中的 `type_code` 自动归类。

## 2. 环境配置

确保您的应用已连接到 Kafka 集群。默认配置如下：

*   **Bootstrap Servers**: 由环境变量 `KAFKA_BOOTSTRAP_SERVERS` 指定 (默认 `kafka:9092`)
*   **Topic**: 由环境变量 `CMDB_KAFKA_TOPIC` 指定 (默认 `cmdb-cis`)
*   **Group ID**: 默认 `cmdb-consumer-group`

## 3. 数据接入流程

### 第一步：定义配置项类型 (UI)

在开始推送数据前，建议先在 CMDB 前端定义好配置项类型及其属性。

1.  进入 **CMDB - 配置项类型管理** 页面。
2.  新建或编辑一个类型（例如 `server`）。
3.  **重要**：在 **唯一标识生成规则** 栏中，输入生成规则模板。
    *   **规则示例**：`{hostname}-{ip}` 或 `{serial_number}`
    *   **作用**：当 Kafka 消息中 [identifier](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/service.py#362-370) 字段为空时，系统将从 [data](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/database.py#51-62) 中提取对应的属性值（`hostname` 和 [ip](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/frontend/src/lib/api.ts#447-455)），按格式组合成唯一标识。
4.  保存配置。

### 第二步：推送 Kafka 消息

向指定 Topic 发送 JSON 格式的消息。

#### 消息格式规范

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| [op](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/kafka.py#94-101) | string | 是 | 操作类型，支持 [create](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/service.py#315-352) (自动判断是否存在则更新), [update](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/service.py#166-194), [delete](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/service.py#195-211) |
| `type_code` | string | 是 | 配置项类型编码，需与 UI 定义的一致 (如 `server`, `switch`) |
| [identifier](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/cmdb/service.py#362-370) | string | **否** | 全局唯一标识。**如果留空，系统将尝试根据规则自动生成** |
| [data](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/database.py#51-62) | object | 是 | 配置项属性字典，Key 需与类型定义的属性名一致 |

#### 示例 1: 标准推送 (自带 ID)

适用于数据源本身有稳定唯一 ID 的场景。

```json
{
    "op": "create",
    "type_code": "server",
    "identifier": "server-A-001",
    "data": {
        "hostname": "web-01",
        "ip": "192.168.1.10",
        "status": "active",
        "cpu": 4,
        "memory": 16
    }
}
```

#### 示例 2: 自动标识推送 (无 ID)

适用于数据源没有全局 ID，但有业务属性组合（如主机名+IP）可唯一确定资源的场景。
*前提：在 UI 中为 `server` 类型配置了规则 `{hostname}-{ip}`*

```json
{
    "op": "create",
    "type_code": "server",
    "identifier": "",  // 留空
    "data": {
        "hostname": "web-01",
        "ip": "192.168.1.10",
        "manufacturer": "Dell"
    }
}
// 系统将自动生成 ID: web-01-192.168.1.10
```

#### 示例 3: 删除操作

```json
{
    "op": "delete",
    "type_code": "server",
    "identifier": "server-A-001" // 删除时必须明确指定 ID (或通过规则能推导出的 ID)
}
```

## 4. 验证与调试

### 使用测试脚本验证

系统内置了一个 Python 测试脚本，可用于验证集成链路。

1.  进入项目根目录。
2.  运行脚本：
    ```bash
    # 确保本地 Kafka 可访问 (localhost:29092)
    python3 scripts/test_kafka_cmdb.py
    ```
3.  脚本将发送 3 条测试数据：
    *   一条带 ID 的创建消息。
    *   一条无 ID 的创建消息（测试自动生成）。
    *   一条更新消息。

### 常见问题

*   **数据未显示**：
    *   检查后端服务是否启动 ([main.py](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/main.py) 或 Docker `skb-api`)。
    *   检查 Kafka 连接配置 ([docker-compose.yml](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/docker-compose.yml))。
    *   检查日志：`docker-compose logs -f skb-api`，搜索 `Kafka consumer` 关键字。
*   **Identifier 生成失败**：
    *   查看后端日志中的 `WARNING` 信息。
    *   确认消息的 [data](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/app/core/database.py#51-62) 中是否包含了规则所需的所有属性（例如规则为 `{ip}` 但数据中缺了 [ip](file:///Users/admin/Desktop/%E6%BE%9C%E8%88%9F/python/skb/frontend/src/lib/api.ts#447-455)）。
    *   确认 UI 中是否正确配置了规则。

## 5. Python 客户端示例

```python
from aiokafka import AIOKafkaProducer
import json
import asyncio

async def send_cmdb_data():
    producer = AIOKafkaProducer(bootstrap_servers='localhost:29092')
    await producer.start()
    
    msg = {
        "op": "create",
        "type_code": "database",
        "identifier": "", # Let system generate
        "data": {
            "instance_name": "mysql-prod-01",
            "port": 3306
        }
    }
    
    await producer.send_and_wait("cmdb-cis", json.dumps(msg).encode('utf-8'))
    await producer.stop()

asyncio.run(send_cmdb_data())
```
