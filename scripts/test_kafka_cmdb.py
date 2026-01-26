import asyncio
import json
import random
from datetime import datetime

# Try importing aiokafka
try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    print("Error: aiokafka not installed. Please pip install aiokafka")
    exit(1)

KAFKA_SERVER = "localhost:29092"
TOPIC = "cmdb-cis"

async def produce_messages():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_SERVER)
    try:
        await producer.start()
        print(f"Connected to Kafka at {KAFKA_SERVER}")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return

    # Sample Data 1: Server with explicit identifier (Standard case)
    # 模拟正常的服务器数据，带有明确的 identifier
    msg1 = {
        "op": "create",
        "type_code": "server",
        "identifier": "server-test-001",
        "data": {
            "vendor": "Dell",
            "model": "PowerEdge R740",
            "serial_number": f"SN{random.randint(10000, 99999)}",
            "management_ip": "192.168.10.101",
            "cpu_count": 2,
            "memory_gb": 64,
            "os": "Linux",
            "location": "DC-A-01"
        }
    }

    # Sample 2: Server WITHOUT identifier (Testing auto-generation rule)
    # 模拟缺少 identifier 的数据，测试是否能根据 {management_ip} 自动生成
    # 注意：这里我们故意不传 identifier 字段
    msg2 = {
        "op": "create",
        "type_code": "server",
        "identifier": "", # Empty or missing
        "data": {
            "vendor": "HP",
            "model": "ProLiant DL380",
            "serial_number": f"SN{random.randint(10000, 99999)}",
            "management_ip": "192.168.10.102",  # Should become the identifier
            "cpu_count": 4,
            "memory_gb": 128,
            "location": "DC-B-02"
        }
    }
    
    # Sample 3: Server update (Testing update logic)
    # 更新第一台服务器的数据
    msg3 = {
        "op": "update",
        "type_code": "server",
        "identifier": "server-test-001",
        "data": {
            "memory_gb": 128, # Upgraded
            "status_desc": "Upgraded memory on " + datetime.now().strftime("%Y-%m-%d")
        }
    }

    messages = [msg1, msg2, msg3]

    print(f"Sending {len(messages)} messages to topic '{TOPIC}'...")

    for i, msg in enumerate(messages):
        key = msg.get("identifier") or msg.get("data", {}).get("management_ip", "unknown")
        print(f"[{i+1}] Sending: type={msg['type_code']}, id={msg['identifier'] or '(auto)'}")
        
        try:
            await producer.send_and_wait(
                TOPIC, 
                json.dumps(msg).encode('utf-8'),
                key=key.encode('utf-8') if key else None
            )
            print(f"    -> Sent successfully")
        except Exception as e:
            print(f"    -> Failed: {e}")

    await producer.stop()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(produce_messages())
