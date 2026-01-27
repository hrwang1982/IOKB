
import asyncio
from datetime import datetime
from app.core.cmdb.es_storage import alert_storage_service

async def verify_alerts():
    print("Verifying Alert Retrieval from ES...")
    
    # Init client (normally handled by app startup, but we need it here)
    await alert_storage_service.get_client()
    
    ci_id = "server-test-integrated-01"
    print(f"Searching for alerts with ci_identifier='{ci_id}'...")
    
    alerts, total = await alert_storage_service.search_alerts(
        ci_identifier=ci_id,
        limit=10
    )
    
    print(f"Total found: {total}")
    for alert in alerts:
        print(f" - [{alert.get('alert_time')}] {alert.get('title')} ({alert.get('level')})")
        
    await alert_storage_service.close()

if __name__ == "__main__":
    asyncio.run(verify_alerts())
