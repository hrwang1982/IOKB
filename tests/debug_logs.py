
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Need to set environment variable for config if needed, or rely on defaults
os.environ["ES_HOST"] = "localhost"

from app.core.cmdb.es_storage import log_storage_service, alert_storage_service

async def main():
    try:
        ci_identifier = "server-test-integrated-01"
        print(f"Checking logs for CI: {ci_identifier}")
        
        # 1. Search without time limit
        # The search_alerts function takes start_time and end_time, if None it checks all
        # Wait, search_logs is what we need
        logs, total = await log_storage_service.search_logs(
            ci_identifier=ci_identifier,
            limit=5
        )
        print(f"\n[Result] Total logs found (no time limit): {total}")
        for log in logs:
            ts = log.get('timestamp')
            msg = log.get('message', '')[:50]
            lvl = log.get('log_level')
            print(f" - [{ts}] {lvl}: {msg}...")
            
        if total == 0:
             print("\n[Analysis] No logs found. Checking available indices...")
             client = await log_storage_service.get_client()
             indices = await client.cat.indices(format="json")
             for idx in indices:
                if 'log' in idx['index']:
                    print(f" - Index: {idx['index']}, Docs: {idx['docs.count']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await log_storage_service.close()
        await alert_storage_service.close()

if __name__ == "__main__":
    asyncio.run(main())
