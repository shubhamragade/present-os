# tools/notion_schema/fix_missing_props.py
# Fix missing Notion properties after initial DB creation
# - Adds Status as a select property for Tasks and Quests
# - Adds Related Tasks relation on Maps to Tasks DB (explicit)
# - Validates properties after patching
#
# Requires: NOTION_TOKEN and NOTION_ROOT_PAGE_ID in your .env
# Run: python tools/notion_schema/fix_missing_props.py

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("ERROR: NOTION_TOKEN missing in .env")
    raise SystemExit(1)

# Replace these with the DB IDs printed by your creation script
TASKS_DB_ID = os.getenv("NOTION_DB_TASKS_ID")
MAPS_DB_ID = os.getenv("NOTION_DB_MAPS_ID")
QUESTS_DB_ID = os.getenv("NOTION_DB_QUESTS_ID")

if not (TASKS_DB_ID and MAPS_DB_ID and QUESTS_DB_ID):
    print("ERROR: Please add NOTION_DB_TASKS_ID, NOTION_DB_MAPS_ID, NOTION_DB_QUESTS_ID to your .env")
    raise SystemExit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

BASE = "https://api.notion.com/v1"

def request_patch(path, payload, retries=3, delay=1.0):
    url = f"{BASE}{path}"
    last = None
    for i in range(retries):
        try:
            r = requests.patch(url, headers=HEADERS, json=payload, timeout=20)
            last = r
            if 200 <= r.status_code < 300:
                return r.json()
            print(f"[Attempt {i+1}] PATCH {r.status_code} - {r.text}")
        except Exception as e:
            last = e
            print(f"[Attempt {i+1}] Exception: {e}")
        time.sleep(delay)
    raise Exception(f"Failed PATCH to {url}: {getattr(last, 'text', last)}")

def get_props(db_id):
    r = requests.get(f"{BASE}/databases/{db_id}", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        raise Exception(f"Failed GET properties for {db_id}: {r.status_code} {r.text}")
    return r.json().get("properties", {})

# 1) Add Status as a select property (reliable)
status_select_options = [
    {"name": "Not Started", "color": "gray"},
    {"name": "In Progress", "color": "blue"},
    {"name": "Blocked", "color": "red"},
    {"name": "Completed", "color": "green"}
]

print("Patching Tasks DB to add 'Status' select...")
patch_payload = {"properties": {"Status": {"select": {"options": status_select_options}}}}
resp = request_patch(f"/databases/{TASKS_DB_ID}", patch_payload)
print("Tasks patched:", TASKS_DB_ID)
time.sleep(0.6)

print("Patching Quests DB to add 'Status' select...")
resp = request_patch(f"/databases/{QUESTS_DB_ID}", {"properties": {"Status": {"select": {"options": status_select_options}}}})
print("Quests patched:", QUESTS_DB_ID)
time.sleep(0.6)

# 2) Ensure Maps has Related Tasks relation explicitly
print("Patching Maps DB to add 'Related Tasks' relation to Tasks DB...")
relation_payload = {
    "properties": {
        "Related Tasks": {
            "relation": {
                "database_id": TASKS_DB_ID,
                "dual_property": {"name": "Map"}  # will create Map on Tasks if missing or link
            }
        }
    }
}
resp = request_patch(f"/databases/{MAPS_DB_ID}", relation_payload)
print("Maps patched:", MAPS_DB_ID)
time.sleep(0.6)

# 3) Safety: Ensure Tasks has Map relation (if not present)
props = get_props(TASKS_DB_ID)
if "Map" not in props:
    print("Tasks missing 'Map' relation. Patching Tasks with Map relation to Maps DB...")
    task_map_payload = {"properties": {"Map": {"relation": {"database_id": MAPS_DB_ID, "dual_property": {"name": "Related Tasks"}}}}}
    request_patch(f"/databases/{TASKS_DB_ID}", task_map_payload)
    print("Tasks.Map relation added.")
else:
    print("Tasks already has 'Map' relation.")

# 4) Final validation: list missing fields if any
expected = {
    TASKS_DB_ID: ["Name", "Description", "Deadline", "Energy Level", "Estimated Duration (min)",
                  "PAEI", "Source", "Status", "Auto-Scheduled", "Google Event ID",
                  "Fireflies Meeting ID", "User", "Priority", "Deep Work Required", "Task Type", "Map", "Quest", "Related XP"],
    MAPS_DB_ID: ["Name", "Description", "Priority", "Status", "Type", "XP Value", "Quest", "Related Tasks"],
    QUESTS_DB_ID: ["Name", "Purpose", "Result", "Start Date", "End Date", "Category", "XP Target", "KPI", "Status", "User", "Related MAPs", "Related Tasks"]
}

print("\nValidating DB properties now...")
all_ok = True
for db_id, expect_list in expected.items():
    props = get_props(db_id)
    names = list(props.keys())
    missing = [p for p in expect_list if p not in names]
    if missing:
        all_ok = False
        print(f"- DB {db_id} missing: {missing}")
    else:
        print(f"- DB {db_id} OK ({len(names)} properties)")

if not all_ok:
    print("\nWARNING: Some properties still missing. If so, open the Notion UI and verify:")
    print("- Make sure the integration has access to the DBs (Share -> invite integration).")
    print("- If 'Related' properties are missing on one side, open the target DB and manually confirm the relation was created.")
else:
    print("\nSUCCESS: All expected properties are present.")

print("\nDone.")
