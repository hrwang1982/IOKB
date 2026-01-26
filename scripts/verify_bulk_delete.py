import asyncio
import httpx
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

API_BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"  # Replace with valid credentials if needed
PASSWORD = "admin"

async def get_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return None
        return response.json()["access_token"]


async def get_types(client, token):
    response = await client.get(
        f"{API_BASE_URL}/cmdb/types",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        print("Available types:", [t['code'] for t in response.json()['items']])
        return response.json()['items']
    else:
        print(f"Failed to get types: {response.text}")
        return []

async def create_test_ci(client, token, index):
    ci_data = {
        "type_code": "physical_server", # Corrected from 'server' to 'physical_server' if that's the preset
        "name": f"verify-bulk-delete-{index}",
        "identifier": f"verify-bd-{index}",
        "attributes": {"hostname": f"host-{index}", "ip": f"192.168.1.{index}"}
    }
    # ... rest same
    response = await client.post(
        f"{API_BASE_URL}/cmdb/items",
        json=ci_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        print(f"Created CI {index}: {response.json()['id']}")
        return response.json()['id']
    else:
        print(f"Failed to create CI {index}: {response.text}")
        return None

async def verify_bulk_delete():
    token = await get_token()
    if not token:
        return

    async with httpx.AsyncClient() as client:
        # 0. Get available types
        types = await get_types(client, token)
        if not types:
            print("No CI types found. Cannot proceed.")
            return
        
        type_code = types[0]['code']
        print(f"Using CI type: {type_code}")

        import time
        ts = int(time.time())

        # 1. Create 3 test CIs
        created_ids = []
        for i in range(3):
            # Adapt attributes based on type if needed, but for now try generic ones
            
            # Simple creation
            ci_data = {
                "type_code": type_code, 
                "name": f"verify-bulk-delete-{ts}-{i}",
                "identifier": f"verify-bd-{ts}-{i}",
                "attributes": {} 
            }
            # Add some dummy attributes if it's a server
            if "server" in type_code or "db" in type_code:
                 ci_data["attributes"] = {"hostname": f"host-{ts}-{i}", "ip": f"192.168.1.{i}"}
            elif "storage" in type_code:
                 ci_data["attributes"] = {"storage_type": "SAN", "used_capacity": 100}

            
            response = await client.post(
                f"{API_BASE_URL}/cmdb/items",
                json=ci_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                print(f"Created CI {i}: {response.json()['id']}")
                created_ids.append(response.json()['id'])
            else:
                print(f"Failed to create CI {i}: {response.status_code} - {response.text}")
        
        
        if not created_ids:
            print("No CIs created, aborting.")
            return

        print(f"Created IDs: {created_ids}")

        # 2. Bulk Delete
        response = await client.request(
            "DELETE",
            f"{API_BASE_URL}/cmdb/items/batch",
            json=created_ids,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Bulk delete success! Deleted count: {result.get('deleted_count')}")
        else:
            print(f"Bulk delete failed: {response.text}")
            return

        # 3. Verify they are gone
        for cid in created_ids:
            response = await client.get(
                f"{API_BASE_URL}/cmdb/items/{cid}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 404 or response.json() is None:
                print(f"Verified CI {cid} is deleted.")
            else:
                print(f"Error: CI {cid} still exists!")

if __name__ == "__main__":
    asyncio.run(verify_bulk_delete())
