import urllib.request
import json

BASE_URL = "http://localhost:8000/api/v1"

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def http_post(url, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def test_admin_tracking_endpoints():
    print("--- 1. Testing GET /admin/tracking/shipments/TLX-DEMO-100001 ---")
    status, res1 = http_get(f"{BASE_URL}/admin/tracking/shipments/TLX-DEMO-100001")
    print("Status:", status)
    print("Response snippet:", json.dumps(res1, indent=2)[:350])

    print("\n--- 2. Testing GET /admin/drivers ---")
    status, res2 = http_get(f"{BASE_URL}/admin/drivers")
    print("Status:", status)
    drivers = res2.get("drivers", [])
    print(f"Found {len(drivers)} drivers.")

    if drivers:
        drv_id = drivers[0]["driver_id"]
        print(f"\n--- 3. Testing GET /admin/tracking/drivers/{drv_id} ---")
        status, res3 = http_get(f"{BASE_URL}/admin/tracking/drivers/{drv_id}")
        print("Status:", status)
        print("Response snippet:", json.dumps(res3, indent=2)[:400])

        print(f"\n--- 4. Posting new live driver location for {drv_id} ---")
        payload = {
            "driver_id": drv_id,
            "vehicle_id": "KA-01-EQ-9900",
            "shipment_id": "TLX-DEMO-100001",
            "latitude": 12.3050,
            "longitude": 76.6550,
            "accuracy": 4.5,
            "source": "gps_telemetry_live",
            "mode": "live",
            "is_mock": False,
            "location_name": "Mysore Ring Road Junction"
        }
        status, res4 = http_post(f"{BASE_URL}/admin/tracking/driver-locations", payload)
        print("Status:", status)
        print("Response:", res4)

        print(f"\n--- 5. Re-fetching driver tracking to verify updated location ---")
        status, res5 = http_get(f"{BASE_URL}/admin/tracking/drivers/{drv_id}")
        print("Status:", status)
        print("Response snippet:", json.dumps(res5, indent=2)[:450])

if __name__ == "__main__":
    test_admin_tracking_endpoints()
