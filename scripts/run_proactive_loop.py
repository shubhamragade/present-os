
"""
PresentOS Proactive Loop
Runs in background to:
1. Monitor XP balance
2. Send Telegram nudges for low PAEI roles
3. Detect uncompleted high-priority tasks
"""
import sys
import time
import logging
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.integrations.telegram_client import TelegramClient
from app.graph.state import PAEIRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PresentOS.Proactive")

def run_proactive_loop():
    logger.info("Starting Proactive Loop...")
    telegram = TelegramClient.create_from_env()
    
    if not telegram:
        logger.error("No Telegram token found! Exiting.")
        return

    # Simulation state
    xp_balance = {
        "P": 120,
        "A": 85,
        "E": 210,
        "I": 45  # Low Integrator
    }
    
    while True:
        logger.info("Scanning system state...")
        
        # 1. Check PAEI Balance (Simulated logic)
        total_xp = sum(xp_balance.values())
        if total_xp > 0:
            integrator_share = xp_balance["I"] / total_xp
            if integrator_share < 0.15:
                logger.info("Integrator score low (%.1f%%). Sending nudge...", integrator_share*100)
                
                msg = (
                    "🚨 **PAEI Balance Alert**\n\n"
                    "Integrator level is critical (only 10%).\n"
                    "• Relationships are lagging.\n"
                    "• Energy might crash if not recharged.\n\n"
                    "👉 *Suggestion:* Schedule coffee with a friend this weekend?\n"
                    "Reply 'Yes' to auto-schedule."
                )
                telegram.send_message(msg)
        
        # 2. Check Uncompleted Tasks (mock)
        hour = datetime.now().hour
        if hour == 18: # Evening check-in
             telegram.send_message(
                 "🌙 **Evening Check-in**\n"
                 "• 3 tasks completed today (+45 XP)\n"
                 "• 2 tasks remaining (moved to tomorrow)\n"
                 "• Recovery score: 42% (Warning)\n\n"
                 "Sleep well! 💤"
             )
        
        # Sleep for demo purposes (real system would sleep 1 hour)
        time.sleep(60) 

if __name__ == "__main__":
    run_proactive_loop()
