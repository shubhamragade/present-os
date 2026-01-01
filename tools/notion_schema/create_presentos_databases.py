import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID")

if not NOTION_TOKEN:
    print("ERROR: NOTION_TOKEN missing in environment (.env).")
    raise SystemExit(1)
if not ROOT_PAGE_ID:
    print("ERROR: NOTION_ROOT_PAGE_ID missing in environment (.env).")
    raise SystemExit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

NOTION_BASE = "https://api.notion.com/v1"

# Simple retry wrapper for requests
def request_with_retries(method, url, headers=None, json_payload=None, retries=4, delay=1.5, timeout=30):
    last = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, headers=headers, json=json_payload, timeout=timeout)
            last = resp
            if 200 <= resp.status_code < 300:
                return resp
            print(f"[Attempt {attempt}] HTTP {resp.status_code} - {resp.text}")
        except Exception as e:
            last = e
            print(f"[Attempt {attempt}] Exception: {e}")
        time.sleep(delay)
    return last

def create_minimal_db(title):
    body = {
        "parent": {"type": "page_id", "page_id": ROOT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": {"Name": {"title": {}}}
    }
    resp = request_with_retries("POST", f"{NOTION_BASE}/databases", headers=HEADERS, json_payload=body)
    if not resp or not hasattr(resp, "status_code") or resp.status_code >= 300:
        raise Exception(f"Failed to create DB {title}: {getattr(resp, 'text', resp)}")
    data = resp.json()
    db_id = data["id"]
    print(f"Created DB '{title}' -> {db_id}")
    return db_id

def patch_database_properties(db_id, properties_payload, label):
    body = {"properties": properties_payload}
    resp = request_with_retries("PATCH", f"{NOTION_BASE}/databases/{db_id}", headers=HEADERS, json_payload=body)
    if not resp or not hasattr(resp, "status_code") or resp.status_code >= 300:
        print(f"Patch failed for {label}: {getattr(resp, 'text', resp)}")
        return False
    print(f"Patched {label}")
    return True

def get_database_properties(db_id):
    resp = request_with_retries("GET", f"{NOTION_BASE}/databases/{db_id}", headers=HEADERS)
    if not resp or not hasattr(resp, "status_code") or resp.status_code >= 300:
        return None
    return resp.json().get("properties", {})

# ---------- Phase 1: create minimal DBs ----------
print("\nPhase 1: creating minimal databases (title only)...\n")

dbs = {}
order = [
    ("tasks", "POS Tasks"),
    ("maps", "POS MAPs"),
    ("quests", "POS Quests"),
    ("xp", "POS XP Tracking"),
    ("contacts", "POS Contacts")
]

for key, title in order:
    dbs[key] = create_minimal_db(title)
    # small pause to allow Notion internal consistency
    time.sleep(1.2)

print("\nPhase 1 complete. DB IDs:")
print(json.dumps(dbs, indent=2))
time.sleep(1.5)

# ---------- Phase 2: add full properties, relations, and selects ----------
print("\nPhase 2: patching databases with full schema...\n")

# Helper property builders (dictionaries conforming to Notion create/update API)
def prop_title(): return {"title": {}}
def prop_rich_text(): return {"rich_text": {}}
def prop_date(): return {"date": {}}
def prop_number(): return {"number": {"format": "number"}}
def prop_checkbox(): return {"checkbox": {}}
def prop_email(): return {"email": {}}
def prop_phone(): return {"phone_number": {}}
def prop_select(options_list):
    return {"select": {"options": [{"name": o["name"], "color": o.get("color","default")} for o in options_list]}}
def prop_relation(target_db_id, dual_name=None):
    payload = {"relation": {"database_id": target_db_id}}
    if dual_name:
        payload["relation"]["dual_property"] = {"name": dual_name}
    return payload
def prop_status_empty(): return {"status": {}}

# --- Prepare full properties for each DB ---
# TASKS full properties (some relations added after map/quest/xp exist)
tasks_props = {
    "Name": prop_title(),
    "Description": prop_rich_text(),
    "Deadline": prop_date(),
    "Energy Level": prop_select([{"name":"Low","color":"green"},{"name":"Medium","color":"yellow"},{"name":"High","color":"red"}]),
    "Estimated Duration (min)": prop_number(),
    "PAEI": prop_select([
        {"name":"Producer","color":"red"},
        {"name":"Administrator","color":"blue"},
        {"name":"Entrepreneur","color":"purple"},
        {"name":"Integrator","color":"green"}
    ]),
    "Source": prop_select([
        {"name":"Voice","color":"blue"},
        {"name":"Telegram","color":"green"},
        {"name":"Email","color":"yellow"},
        {"name":"Fireflies","color":"red"},
        {"name":"Manual","color":"gray"}
    ]),
    "Status": prop_status_empty(),
    "Auto-Scheduled": prop_checkbox(),
    "Google Event ID": prop_rich_text(),
    "Fireflies Meeting ID": prop_rich_text(),
    "User": prop_rich_text(),
    "Priority": prop_select([{"name":"Low"},{"name":"Medium"},{"name":"High"}]),
    "Deep Work Required": prop_checkbox(),
    "Task Type": prop_select([{"name":"Admin"},{"name":"Creative"},{"name":"Routine"}])
}

# MAPS properties
maps_props = {
    "Name": prop_title(),
    "Description": prop_rich_text(),
    "Priority": prop_select([{"name":"Low"},{"name":"Medium"},{"name":"High"}]),
    "Status": prop_status_empty(),
    "Type": prop_select([{"name":"Planning"},{"name":"Execution"},{"name":"Learning"},{"name":"Outreach"}]),
    "XP Value": prop_number(),
    # Quest relation will be added as two-way below
}

# QUESTS properties
quests_props = {
    "Name": prop_title(),
    "Purpose": prop_rich_text(),
    "Result": prop_rich_text(),
    "Start Date": prop_date(),
    "End Date": prop_date(),
    "Category": prop_select([{"name":"Business"},{"name":"Health"},{"name":"Learning"},{"name":"Relationships"}]),
    "XP Target": prop_number(),
    "KPI": prop_rich_text(),
    "Status": prop_status_empty(),
    "User": prop_rich_text()
    # Related MAPs and Related Tasks relations will be added below
}

# XP properties
xp_props = {
    "Name": prop_title(),
    "Amount": prop_number(),
    "Date": prop_date(),
    "PAEI": prop_select([{"name":"P"},{"name":"A"},{"name":"E"},{"name":"I"}]),
    "Reason": prop_rich_text(),
    "Week Number": prop_number(),
    "Month Number": prop_number(),
    "XP Category": prop_select([{"name":"Completion"},{"name":"Consistency"},{"name":"Effort"}]),
    "XP Bonus": prop_number()
    # Task, MAP, Quest relations added below
}

# CONTACTS properties
contacts_props = {
    "Name": prop_title(),
    "Email": prop_email(),
    "Phone": prop_phone(),
    "Notes": prop_rich_text(),
    "Last Contacted": prop_date(),
    "Tone Preference": prop_select([{"name":"Formal"},{"name":"Casual"},{"name":"Friendly"},{"name":"Professional"}]),
    "Relationship Type": prop_select([{"name":"Work"},{"name":"Client"},{"name":"Friend"},{"name":"Family"}]),
    "Preferred Meeting Length (min)": prop_number(),
    "Importance Level": prop_select([{"name":"Low"},{"name":"Medium"},{"name":"High"}]),
    "Frequent Contact": prop_checkbox()
}

# Step: patch basic non-relation properties first
print("Patching non-relation properties (tasks, maps, quests, xp, contacts)...")
ok = patch_database_properties(dbs["tasks"], tasks_props, "POS Tasks (base props)")
if not ok: raise SystemExit(1)
time.sleep(0.8)

ok = patch_database_properties(dbs["maps"], maps_props, "POS MAPs (base props)")
if not ok: raise SystemExit(1)
time.sleep(0.8)

ok = patch_database_properties(dbs["quests"], quests_props, "POS Quests (base props)")
if not ok: raise SystemExit(1)
time.sleep(0.8)

ok = patch_database_properties(dbs["xp"], xp_props, "POS XP (base props)")
if not ok: raise SystemExit(1)
time.sleep(0.8)

ok = patch_database_properties(dbs["contacts"], contacts_props, "POS Contacts (base props)")
if not ok: raise SystemExit(1)
time.sleep(0.8)

# Validate presence
print("\nValidating created properties for each DB...")
for key in dbs:
    props = get_database_properties(dbs[key])
    if props is None:
        raise Exception(f"Failed to fetch properties for {key}")
    print(f"- {key} has {len(props)} properties")

time.sleep(1.2)

# Now add relations (two-way) using dual_property
print("\nAdding two-way relations (dual_property) now that all DBs exist...\n")

# Task <-> Map
if not patch_database_properties(dbs["tasks"], {"Map": prop_relation(dbs["maps"], dual_name="Tasks")}, "Tasks.Map relation"):
    raise SystemExit(1)
time.sleep(0.6)

# Task <-> Quest
if not patch_database_properties(dbs["tasks"], {"Quest": prop_relation(dbs["quests"], dual_name="Tasks")}, "Tasks.Quest relation"):
    raise SystemExit(1)
time.sleep(0.6)

# XP <-> Task
if not patch_database_properties(dbs["xp"], {"Task": prop_relation(dbs["tasks"], dual_name="XP")}, "XP.Task relation"):
    raise SystemExit(1)
time.sleep(0.6)

# XP <-> MAP
if not patch_database_properties(dbs["xp"], {"MAP": prop_relation(dbs["maps"], dual_name="XP")}, "XP.MAP relation"):
    raise SystemExit(1)
time.sleep(0.6)

# XP <-> Quest
if not patch_database_properties(dbs["xp"], {"Quest": prop_relation(dbs["quests"], dual_name="XP")}, "XP.Quest relation"):
    raise SystemExit(1)
time.sleep(0.6)

# MAP <-> Quest (dual)
if not patch_database_properties(dbs["maps"], {"Quest": prop_relation(dbs["quests"], dual_name="Maps")}, "Maps.Quest relation"):
    raise SystemExit(1)
time.sleep(0.6)

# Quest <-> MAPs (ensure Quest has relation to Maps too - dual should already have added, but patch to be safe)
if not patch_database_properties(dbs["quests"], {"Related MAPs": prop_relation(dbs["maps"], dual_name="Maps")}, "Quests.Related MAPs relation (safety)"):
    # Not fatal; proceed
    print("Warning: Quests.Related MAPs patch returned non-200. Proceeding but verify in Notion UI.")
time.sleep(0.6)

# Quest <-> Tasks (add relation on quests side as well)
if not patch_database_properties(dbs["quests"], {"Related Tasks": prop_relation(dbs["tasks"], dual_name="Tasks")}, "Quests.Related Tasks relation"):
    print("Warning: Quests.Related Tasks patch returned non-200. Proceeding but verify in Notion UI.")
time.sleep(0.6)

# Tasks <-> XP (ensure Task has XP relation - dual created earlier, but patch if not)
if not patch_database_properties(dbs["tasks"], {"Related XP": prop_relation(dbs["xp"], dual_name="Tasks_XP")}, "Tasks.Related XP relation"):
    print("Warning: Tasks.Related XP patch returned non-200. Verify manually.")
time.sleep(0.6)

# Final validation pass: list expected properties per DB
print("\nFinal validation pass (properties snapshot):")
expected = {
    "tasks": ["Name", "Description", "Deadline", "Energy Level", "Estimated Duration (min)",
              "PAEI", "Source", "Status", "Auto-Scheduled", "Google Event ID", "Fireflies Meeting ID",
              "User", "Priority", "Deep Work Required", "Task Type", "Map", "Quest", "Related XP"],
    "maps": ["Name", "Description", "Priority", "Status", "Type", "XP Value", "Quest", "Related Tasks"],
    "quests": ["Name", "Purpose", "Result", "Start Date", "End Date", "Category", "XP Target", "KPI", "Status", "User", "Related MAPs", "Related Tasks"],
    "xp": ["Name", "Amount", "Date", "PAEI", "Reason", "Week Number", "Month Number", "XP Category", "XP Bonus", "Task", "MAP", "Quest"],
    "contacts": ["Name", "Email", "Phone", "Notes", "Last Contacted", "Tone Preference", "Relationship Type", "Preferred Meeting Length (min)", "Importance Level", "Frequent Contact"]
}

all_ok = True
for key, props_list in expected.items():
    props = get_database_properties(dbs[key])
    names = list(props.keys()) if props else []
    missing = [p for p in props_list if p not in names]
    if missing:
        all_ok = False
        print(f"DB '{key}' missing properties: {missing}")
    else:
        print(f"DB '{key}' OK ({len(names)} properties)")

print("\nScript completed.")
if not all_ok:
    print("WARNING: Some properties are missing. Open Notion UI and verify the DBs. You may need to add the missing properties manually.")
else:
    print("SUCCESS: All expected properties appear present. Add these IDs to your .env file:")

for k, v in dbs.items():
    print(f"NOTION_DB_{k.upper()}_ID={v}")

print("\nNotes:")
print("- If a relation property is missing on either side, open the target DB in Notion and verify the relation. Dual relations sometimes need a manual confirm in the UI.")
print("- Status properties were created empty. Open each DB and set status options (Notion API does not accept status options at create time reliably).")
print("- Ensure integration (your NOTION_TOKEN) has access to the root page and each created DB so agents can read/write.")
