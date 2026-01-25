import asyncio
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from app.core.database import init_db, async_session_maker
from app.core.cmdb.service import ci_service, ci_type_service
from app.core.cmdb.ci_types import SERVER_CI_TYPE

async def test_cmdb_validation():
    print("Initializing DB...")
    await init_db()
    
    async with async_session_maker() as db:
        print("Initializing preset types...")
        await ci_type_service.init_preset_types(db)
        
        # Test Case 1: Create Server with Invalid IP (Regex Fail)
        print("\nTest Case 1: Invalid IP Regex")
        try:
            await ci_service.create(
                db, 
                type_code="server", 
                name="TestServer", 
                identifier="server-test-01",
                attributes={
                    "serial_number": "SN001", 
                    "management_ip": "invalid-ip"
                }
            )
            print("FAILED: Should have raised ValueError for invalid IP")
        except ValueError as e:
            print(f"PASSED: Caught expected error: {e}")

        # Test Case 2: Create Server with Valid IP but missing required
        print("\nTest Case 2: Missing Required Attribute (serial_number)")
        try:
            await ci_service.create(
                db, 
                type_code="server", 
                name="TestServer2", 
                identifier="server-test-02",
                attributes={
                    "management_ip": "192.168.1.1"
                }
            )
            print("FAILED: Should have raised ValueError for missing serial_number")
        except ValueError as e:
            print(f"PASSED: Caught expected error: {e}")

        # Test Case 3: Create Limit Range (CPU count < 1)
        print("\nTest Case 3: Number Range Validation")
        try:
            await ci_service.create(
                db, 
                type_code="server", 
                name="TestServer3", 
                identifier="server-test-03",
                attributes={
                    "serial_number": "SN003", 
                    "management_ip": "192.168.1.3",
                    "cpu_count": 0
                }
            )
            print("FAILED: Should have raised ValueError for cpu_count < 1")
        except ValueError as e:
            print(f"PASSED: Caught expected error: {e}")

        # Test Case 4: Valid Creation
        print("\nTest Case 4: Valid Creation")
        try:
            ci = await ci_service.create(
                db, 
                type_code="server", 
                name="ValidServer", 
                identifier="server-valid-01",
                attributes={
                    "serial_number": "SN_VALID_01", 
                    "management_ip": "192.168.1.100",
                    "cpu_count": 2,
                    "memory_gb": 64
                }
            )
            print(f"PASSED: Created CI {ci.id} - {ci.name}")
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cmdb_validation())
