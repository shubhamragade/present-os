import os
import sys
from dotenv import load_dotenv
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.integrations.notion_client import NotionClient

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

def debug_notion():
    load_dotenv()
    
    print("--- Notion Debug ---")
    token = os.getenv("NOTION_TOKEN")
    print(f"Token present: {bool(token)}")
    
    db_ids = {
        "tasks": os.getenv("NOTION_DB_TASKS_ID"),
        "xp": os.getenv("NOTION_DB_XP_ID"),
        "contacts": os.getenv("NOTION_DB_CONTACTS_ID"),
        "quests": os.getenv("NOTION_DB_QUESTS_ID"),
        "maps": os.getenv("NOTION_DB_MAPS_ID"),
    }
    
    for k, v in db_ids.items():
        print(f"DB {k}: {v}")
        
    try:
        client = NotionClient.from_env()
        print("NotionClient initialized successfully.")
        
        print("\nChecking Tasks DB...")
        tasks = client.get_tasks(limit=5)
        print(f"Found {len(tasks)} tasks.")
        for t in tasks:
            print(f" - {t['name']} ({t['status']})")
            
        print("\nChecking Active Quest...")
        quest = client.get_active_quest()
        if quest:
            print(f"Active Quest: {quest['name']}")
        else:
            print("No active quest found.")
            
        print("\nChecking XP Summary...")
        xp = client.get_xp_summary()
        print(f"XP Summary: {xp}")
        
    except Exception as e:
        print(f"\n❌ Error during Notion debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_notion()
