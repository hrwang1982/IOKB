核心接入方式
系统统一采用 Kafka 消息队列 进行异步数据接入。所有外部数据（告警、性能、日志）均通过向指定的 Kafka Topic 发送 JSON 格式消息来完成接入。

1. 告警数据接入 (Alerts)
接入方式: Kafka
默认 Topic: skb-alerts (可通过环境变量 KAFKA_ALERT_TOPIC 修改)
存储引擎: Elasticsearch (索引前缀 skb-alerts-*)
数据规范 (JSON):
json
{
  "alert_id": "alert-123",        // [可选] 告警唯一ID，若不填则使用 id 字段
  "ci_identifier": "server-01",   // [可选] 关联配置项标识，若不填则使用 host 字段
  "level": "warning",             // [可选] 级别: critical, warning, info
  "title": "CPU使用率过高",        // [可选] 标题，若不填则使用 name 字段
  "content": "CPU > 90%",         // [可选] 内容，若不填则使用 message 字段
  "source": "zabbix",             // [可选] 来源系统，默认为 kafka
  "tags": {"env": "prod"},        // [可选] 标签字典
  "alert_time": "2023-10-27T10:00:00" // [可选] ISO8601时间字符串，默认当前时间
}
2. 性能监控数据接入 (Metrics)
接入方式: Kafka
默认 Topic: skb-performance (可通过环境变量 KAFKA_PERFORMANCE_TOPIC 修改)
存储引擎: InfluxDB (Measurement: ci_metrics)
数据规范 (JSON):
json
{
  "ci_identifier": "server-01",   // [可选] 关联配置项标识，若不填则使用 host 字段
  "metric_name": "cpu_usage",     // [可选] 指标名，若不填则使用 metric 字段
  "value": 85.5,                  // [必填] 指标值 (数值类型)
  "unit": "%",                    // [可选] 单位
  "tags": {"cpu": "core0"},       // [可选] 维度标签
  "timestamp": "2023-10-27..."    // [可选] ISO8601时间字符串
}
3. 日志数据接入 (Logs)
接入方式: Kafka
默认 Topic: skb-logs (可通过环境变量 KAFKA_LOG_TOPIC 修改)
存储引擎: Elasticsearch (索引前缀 skb-logs-*)
数据规范 (JSON):
json
{
  "ci_identifier": "server-01",   // [可选] 关联配置项标识，若不填则使用 host 字段
  "level": "error",               // [可选] 日志级别
  "message": "Connection failed", // [可选] 日志内容，若不填则使用 log 字段
  "source": "nginx",              // [可选] 日志来源
  "tags": {},                     // [可选] 标签
  "timestamp": "2023-10-27..."    // [可选] ISO8601时间字符串
}