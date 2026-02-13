import asyncio
import sys
import os
import random
from datetime import datetime, timedelta

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.core.database import init_db, async_session_maker
from app.core.cmdb.service import ci_service, relationship_service, ci_type_service
from app.core.cmdb.influxdb import influxdb_service
from app.core.cmdb.es_storage import log_storage_service, alert_storage_service
from app.models.alert import Alert, AlertAnalysis
from app.models.cmdb import CI
from loguru import logger
from sqlalchemy import select

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# Mock Data Configuration
MOCK_CONFIG = {
    "web": {"count": 2, "type": "server", "prefix": "web", "ip_base": "192.168.1"},
    "app": {"count": 2, "type": "server", "prefix": "app", "ip_base": "192.168.2"},
    "db":  {"count": 2, "type": "server", "prefix": "db", "ip_base": "192.168.3"},
    "nas": {"count": 1, "type": "storage", "prefix": "nas", "ip_base": "192.168.4"},
    "biz": {"count": 1, "type": "application", "prefix": "network-banking", "ip_base": None}
}

METRIC_CONFIG = {
    "cpu_usage": {"min": 10, "max": 90, "unit": "%"},
    "memory_usage": {"min": 30, "max": 80, "unit": "%"},
    "disk_usage": {"min": 20, "max": 70, "unit": "%"},
    "network_throughput": {"min": 100, "max": 1000, "unit": "Mbps"}
}

async def create_cis(db):
    """Create CIs based on configuration"""
    created_cis = {}
    
    for role, config in MOCK_CONFIG.items():
        created_cis[role] = []
        for i in range(1, config["count"] + 1):
            if role == "biz":
                name = "Network Banking System"
                identifier = "network-banking"
            else:
                name = f"{config['prefix']}-{i:02d}"
                identifier = name 
            
            existing = await ci_service.get_by_identifier(db, identifier)
            if existing:
                logger.debug(f"CI {identifier} already exists.")
                created_cis[role].append(existing)
                continue
            
            attributes = {
                "status": "active"
            }
            
            if config["type"] == "server":
                attributes.update({
                    "hostname": name,
                    "management_ip": f"{config['ip_base']}.{100+i}",
                    "serial_number": f"SN-{name}-{random.randint(1000,9999)}",
                    "os_version": "Linux"
                })
            elif config["type"] == "storage":
                attributes.update({
                    "hostname": name,
                    "management_ip": f"{config['ip_base']}.{100+i}",
                    "storage_type": "NAS",
                    "total_capacity": 100,
                    "used_capacity": 50,
                    "available_capacity": 50
                })
            elif config["type"] == "application":
                attributes.update({
                    "app_code": identifier,
                    "app_name": name,
                    "level": "P0",
                    "description": "Core Online Banking Business System"
                })
            
            try:
                ci = await ci_service.create(
                    db=db,
                    type_code=config["type"],
                    name=name,
                    identifier=identifier,
                    attributes=attributes
                )
                created_cis[role].append(ci)
                logger.info(f"Created CI: {identifier}")
            except Exception as e:
                logger.error(f"Failed to create CI {identifier}: {e}")
                
    return created_cis

async def create_relationships(db, cis):
    """Create relationships between CIs"""
    # Web -> App
    if "web" in cis and "app" in cis:
        for web in cis["web"]:
            for app in cis["app"]:
                try:
                    await relationship_service.create(db, web.id, app.id, "connects_to")
                except ValueError:
                    pass

    # App -> DB
    if "app" in cis and "db" in cis:
        for app in cis["app"]:
            for db_ci in cis["db"]:
                try:
                    await relationship_service.create(db, app.id, db_ci.id, "connects_to")
                except ValueError:
                    pass

    # DB -> NAS
    if "db" in cis and "nas" in cis:
        nas = cis["nas"][0]
        for db_ci in cis["db"]:
            try:
                await relationship_service.create(db, db_ci.id, nas.id, "depends_on")
            except ValueError:
                pass
                
    # Biz App -> Infrastructure (runs_on)
    # The application 'runs_on' the servers. 
    # Or usually, the servers 'belong_to' the application cluster, or App 'contains' components.
    # Let's say Business App 'contains' or 'runs_on' isn't quite right directionally sometimes.
    # Let's use 'deployed_on' or 'runs_on'. App runs_on Server.
    # From relationship_service: "runs_on", "deployed_on" are available.
    if "biz" in cis:
        biz_app = cis["biz"][0]
        # Link all servers to this app
        for role in ["web", "app", "db"]:
            if role in cis:
                for server in cis[role]:
                    try:
                        # Application runs on Server? Or Component runs on Server.
                        # For a logical Business System, it might "comprise" or "contain" these CIs.
                        # Let's use 'contains' if available? Yes.
                        # Biz App [contains] Server
                        await relationship_service.create(db, biz_app.id, server.id, "contains")
                        logger.info(f"Created Relation: {biz_app.identifier} contains {server.identifier}")
                    except ValueError:
                        pass

async def generate_metrics(cis):
    """Generate 1-minute metrics for the last 6 hours"""
    logger.info("Starting metric generation...")
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=6)
    
    all_cis = []
    for role, role_cis in cis.items():
        if role == "biz": continue # Skip metrics for abstract app for now, or maybe generated TPS?
        all_cis.extend(role_cis)
        
    total_points = 0
    batch_points = []
    batch_size = 1000
    
    current_time = start_time
    while current_time <= end_time:
        for ci in all_cis:
            for metric, config in METRIC_CONFIG.items():
                value = random.uniform(config["min"], config["max"])
                if random.random() > 0.95:
                    value = value * 1.5
                
                point = {
                    "measurement": "ci_metrics",
                    "tags": {
                        "ci_identifier": ci.identifier,
                        "metric": metric,
                        "unit": config["unit"]
                    },
                    "fields": {
                        "value": value
                    },
                    "timestamp": current_time
                }
                batch_points.append(point)
                
                if len(batch_points) >= batch_size:
                    await influxdb_service.write_batch(batch_points)
                    total_points += len(batch_points)
                    batch_points = []
                    
        current_time += timedelta(minutes=1)
        
    if batch_points:
        await influxdb_service.write_batch(batch_points)
        total_points += len(batch_points)
        
    logger.info(f"Generated {total_points} metric points.")

async def generate_alerts(db, cis):
    """Generate mock alerts"""
    # Web Alert
    if cis.get("web"):
        web = cis["web"][0]
        alert_id = f"alert-web-{int(datetime.now().timestamp())}"
        alert = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
        if not alert.scalar_one_or_none():
            new_alert = Alert(
                alert_id=alert_id,
                ci_id=web.id,
                level="warning",
                title=f"High Response Time on {web.identifier}",
                content="Web server response time > 2s for 5 minutes",
                status="open",
                source="zabbix",
                alert_time=datetime.now() - timedelta(minutes=30)
            )
            db.add(new_alert)

    # App Alert
    if cis.get("app"):
        app = cis["app"][0]
        alert_id = f"alert-app-{int(datetime.now().timestamp())}"
        alert = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
        if not alert.scalar_one_or_none():
            new_alert = Alert(
                alert_id=alert_id,
                ci_id=app.id,
                level="critical",
                title=f"Service Down on {app.identifier}",
                content="Application process not running",
                status="open",
                source="prometheus",
                alert_time=datetime.now() - timedelta(minutes=15)
            )
            db.add(new_alert)

    # DB Alert
    if cis.get("db"):
        db_ci = cis["db"][0]
        alert_id = f"alert-db-{int(datetime.now().timestamp())}"
        alert = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
        if not alert.scalar_one_or_none():
            new_alert = Alert(
                alert_id=alert_id,
                ci_id=db_ci.id,
                level="warning",
                title=f"Slow Query on {db_ci.identifier}",
                content="Query execution time > 5s",
                status="open",
                source="monitor",
                alert_time=datetime.now() - timedelta(minutes=45)
            )
            db.add(new_alert)

    # Biz Alert
    if cis.get("biz"):
        biz = cis["biz"][0]
        alert_id = f"alert-biz-{int(datetime.now().timestamp())}"
        alert = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
        if not alert.scalar_one_or_none():
            new_alert = Alert(
                alert_id=alert_id,
                ci_id=biz.id,
                level="critical",
                title=f"Business Service Degraded",
                content="Online Banking login success rate < 95%",
                status="open",
                source="business-monitor",
                alert_time=datetime.now() - timedelta(minutes=10)
            )
            db.add(new_alert)
            logger.info(f"Created Alert for {biz.identifier}")
            
    await db.commit()

    # Sync to Elasticsearch (for Frontend Display)
    # Re-query all open alerts just created/existed to ensure ES has them
    # For simplicity, just push the ones we likely created or all recent ones.
    # Here we just iterate what we might have created above.
    
    # We can fetch all alerts from DB for the involved CIs and sync them.
    
    all_alerts = await db.execute(select(Alert))
    for alert in all_alerts.scalars().all():
        # Only sync recent ones or all? Sync all to be safe for this mock script.
        alert_data = {
            "alert_id": alert.alert_id,
            "ci_identifier": "", # Need to fetch CI identifier
            "ci_id": alert.ci_id,
            "level": alert.level,
            "title": alert.title,
            "content": alert.content,
            "status": alert.status,
            "source": alert.source,
            "alert_time": alert.alert_time.isoformat(),
            "created_at": alert.created_at.isoformat() if alert.created_at else datetime.now().isoformat()
        }
        
        # Fetch CI Identifier
        ci = await db.get(CI, alert.ci_id)
        if ci:
            alert_data["ci_identifier"] = ci.identifier
            
        await alert_storage_service.save_alert(alert_data)
        
    logger.info("Synced alerts to Elasticsearch.")


async def generate_logs(cis):
    """Generate mock logs for CIs"""
    logger.info("Starting log generation...")
    
    # Log Templates
    NGINX_LOGS = [
        {"level": "info", "msg": 'GET /api/v1/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'},
        {"level": "info", "msg": 'POST /api/v1/login HTTP/1.1" 200 456 "-" "Mozilla/5.0"'},
        {"level": "error", "msg": 'connect() failed (111: Connection refused) while connecting to upstream'},
        {"level": "warning", "msg": 'upstream response time 2.5s > 1.0s'},
    ]
    
    TOMCAT_LOGS = [
        {"level": "info", "msg": "Server startup in 12345 ms"},
        {"level": "info", "msg": "Deployment of web application archive [ROOT.war] has finished in [5,432] ms"},
        {"level": "error", "msg": "java.lang.OutOfMemoryError: Java heap space"},
        {"level": "warning", "msg": "Connection pool is full, waiting for connection"},
    ]
    
    MYSQL_LOGS = [
        {"level": "info", "msg": "Connect: root@localhost on skb using TCP/IP"},
        {"level": "warning", "msg": "Aborted connection 1234 to db: 'skb' user: 'root' host: 'localhost' (Got an error reading communication packets)"},
        {"level": "error", "msg": "InnoDB: Database page corruption on disk or a failed file read of page [page id: space=0, page number=123]"},
        {"level": "warning", "msg": "Slow query: SELECT * FROM larger_table WHERE non_indexed_col = 1 (5.2s)"},
    ]
    
    count = 0
    
    # Web Logs (Nginx)
    if "web" in cis:
        for web in cis["web"]:
            for _ in range(20):
                template = random.choice(NGINX_LOGS)
                log_data = {
                    "log_id": f"log-nginx-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}",
                    "ci_identifier": web.identifier,
                    "ci_id": web.id,
                    "log_level": template["level"],
                    "message": template["msg"],
                    "source": "nginx",
                    "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 60))
                }
                await log_storage_service.save_log(log_data)
                count += 1

    # App Logs (Tomcat)
    if "app" in cis:
        for app in cis["app"]:
            for _ in range(20):
                template = random.choice(TOMCAT_LOGS)
                log_data = {
                    "log_id": f"log-tomcat-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}",
                    "ci_identifier": app.identifier,
                    "ci_id": app.id,
                    "log_level": template["level"],
                    "message": template["msg"],
                    "source": "tomcat",
                    "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 60))
                }
                await log_storage_service.save_log(log_data)
                count += 1

    # DB Logs (MySQL)
    if "db" in cis:
        for db_ci in cis["db"]:
            for _ in range(20):
                template = random.choice(MYSQL_LOGS)
                log_data = {
                    "log_id": f"log-mysql-{int(datetime.now().timestamp())}-{random.randint(1000,9999)}",
                    "ci_identifier": db_ci.identifier,
                    "ci_id": db_ci.id,
                    "log_level": template["level"],
                    "message": template["msg"],
                    "source": "mysql",
                    "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 60))
                }
                await log_storage_service.save_log(log_data)
                count += 1
                
    logger.info(f"Generated {count} logs.")

async def main():
    logger.info("Initializing Data Generation...")
    
    await init_db()
    
    # Ensure ES indices exist
    await log_storage_service.init_index()
    await alert_storage_service.init_index()
    
    async with async_session_maker() as db:
        # 1. Create CIs
        cis = await create_cis(db)
        
        # 2. Create Relations
        await create_relationships(db, cis)
        
        # 3. Alerts
        await generate_alerts(db, cis)
        
        # 4. Logs
        await generate_logs(cis)
        
        # 5. Metrics (Async write to Influx)
        await generate_metrics(cis)

    # Close ES client
    await log_storage_service.close()
    await alert_storage_service.close()
    
    logger.info("Data Generation Completed!")

if __name__ == "__main__":
    asyncio.run(main())
