
import asyncio
import json
import random
import time
from datetime import datetime

# Try importing aiokafka
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    print("Error: aiokafka not installed. Please pip install aiokafka")
    exit(1)

# Kafka Configuration
KAFKA_SERVER = "localhost:29092"
STATUS_SERVER = "localhost:29092"

# Topics (Matches default config in app/config.py)
TOPIC_CMDB = "cmdb-cis"
TOPIC_ALERT = "skb-alerts"
TOPIC_PERF = "skb-performance"
TOPIC_LOG = "skb-logs"

# Test CI Identifier
TEST_CI_ID = "server-test-integrated-01"

async def produce_messages():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_SERVER)
    try:
        await producer.start()
        print(f"Connected to Kafka at {KAFKA_SERVER}")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return

    # ==========================================
    # Step 1: Ensure CI exists in CMDB
    # ==========================================
    print(f"\n[1/4] Ensuring CI '{TEST_CI_ID}' exists in CMDB...")
    cmdb_msg = {
        "op": "create",
        "type_code": "server",
        "identifier": TEST_CI_ID,
        "data": {
            "vendor": "VirtualBox",
            "model": "VM",
            "management_ip": "10.0.0.101",
            "cpu_count": 4,
            "memory_gb": 16,
            "os": "Ubuntu 22.04 LTS",
            "location": "Test-Zone"
        }
    }
    await producer.send_and_wait(TOPIC_CMDB, json.dumps(cmdb_msg).encode('utf-8'))
    print(f" -> Sent CMDB creation message for {TEST_CI_ID}")
    
    # Wait a bit for CMDB processing (if consumer is running)
    await asyncio.sleep(2)

    # ==========================================
    # Step 2: Send Alert Data
    # ==========================================
    print(f"\n[2/4] Sending Alert data linked to {TEST_CI_ID}...")
    alert_msg = {
        "alert_id": f"alert-{int(time.time())}",
        "ci_identifier": TEST_CI_ID,
        "level": "warning",
        "title": "High Memory Usage Detected",
        "content": "Memory usage is above 85% for the last 5 minutes.",
        "source": "prometheus",
        "tags": {"environment": "test", "region": "cn-north-1"},
        "alert_time": datetime.now().isoformat()
    }
    await producer.send_and_wait(TOPIC_ALERT, json.dumps(alert_msg).encode('utf-8'))
    print(f" -> Sent Alert: {alert_msg['title']}")

    # ==========================================
    # Step 3: Send Performance Metrics
    # ==========================================
    print(f"\n[3/4] Sending Performance Metrics linked to {TEST_CI_ID}...")
    metrics = [
        {"name": "cpu_usage", "value": random.uniform(20, 45), "unit": "%"},
        {"name": "memory_usage", "value": random.uniform(60, 90), "unit": "%"},
        {"name": "disk_io_read", "value": random.uniform(100, 500), "unit": "IOPS"}
    ]
    
    for m in metrics:
        metric_msg = {
            "ci_identifier": TEST_CI_ID,
            "metric_name": m["name"],
            "value": m["value"],
            "unit": m["unit"],
            "tags": {"host": "test-host-01"},
            "timestamp": datetime.now().isoformat()
        }
        await producer.send_and_wait(TOPIC_PERF, json.dumps(metric_msg).encode('utf-8'))
        print(f" -> Sent Metric: {m['name']} = {m['value']:.2f} {m['unit']}")

    # ==========================================
    # Step 4: Send Logs
    # ==========================================
    print(f"\n[4/4] Sending Logs linked to {TEST_CI_ID}...")
    log_messages = [
        {"level": "info", "msg": "Application process started successfully."},
        {"level": "info", "msg": "Connection established to database."},
        {"level": "warning", "msg": "Slow query detected on users table (230ms)."},
        {"level": "error", "msg": "Failed to sync cache to secondary node."}
    ]
    
    for l in log_messages:
        log_msg = {
            "ci_identifier": TEST_CI_ID,
            "level": l["level"],
            "message": l["msg"],
            "source": "app-backend",
            "tags": {"app": "skb-core"},
            "timestamp": datetime.now().isoformat()
        }
        await producer.send_and_wait(TOPIC_LOG, json.dumps(log_msg).encode('utf-8'))
        print(f" -> Sent Log: [{l['level'].upper()}] {l['msg']}")

    await producer.stop()
    print("\nAll test data sent successfully! Check ES and InfluxDB for verification.")

if __name__ == "__main__":
    asyncio.run(produce_messages())
