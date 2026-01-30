import os
import sys
from dotenv import load_dotenv
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.integrations.notion_client import NotionClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_alignment():
    load_dotenv()
    
    try:
        client = NotionClient.from_env()
        print("--- Notion Alignment Verification ---")
        
        # Test Task Creation
        print("\nTesting Task Creation...")
        task_data = {
            "title": "Verification Task (Schema Aligned)",
            "priority": "High",
            "paei": "E",  # Should map to "Entrepreneur"
            "status": "todo",  # Should map to "Pending"
            "source": "PresentOS"  # Should map to "Manual"
        }
        task_res = client.create_task(task_data)
        print(f"✅ Task created with ID: {task_res.get('id')}")
        
        # Test XP Creation
        print("\nTesting XP Creation...")
        xp_res = client.create_xp(
            amount=50.0,
            paei="I",  # Should map to "Integrator"
            reason="Verification of schema alignment"
        )
        print(f"✅ XP entry created with ID: {xp_res.get('id')}")
        
        # Verify Retrieval Mappings
        print("\nVerifying Retrieval Mappings...")
        tasks = client.get_tasks(limit=1)
        if tasks:
            t = tasks[0]
            print(f"Task retrieved: {t['name']}")
            print(f"Mapped Status: {t['status']}")  # Should be 'pending' (mapped from 'Pending')
            print(f"Priority: {t['priority']}")
        
        print("\nVerification Complete!")
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_alignment()
