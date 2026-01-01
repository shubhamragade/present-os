# tools/notion_schema/add_status_to_maps.py
# Adds missing Status property to POS MAPs DB

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
MAPS_DB_ID = os.getenv("NOTION_DB_MAPS_ID")

if not TOKEN:
    print("ERROR: NOTION_TOKEN missing")
    raise SystemExit(1)

if not MAPS_DB_ID:
    print("ERROR: NOTION_DB_MAPS_ID missing")
    raise SystemExit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

payload = {
    "properties": {
        "Status": {
            "select": {
                "options": [
                    {"name": "Not Started", "color": "gray"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Blocked", "color": "red"},
                    {"name": "Completed", "color": "green"}
                ]
            }
        }
    }
}

resp = requests.patch(
    f"https://api.notion.com/v1/databases/{MAPS_DB_ID}",
    headers=HEADERS,
    json=payload
)

print("HTTP", resp.status_code)
print(resp.text)
