from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
import asyncio
import logging

from app.integrations.notion_client import NotionClient
from app.graph.state import PresentOSState
from app.graph.graph_executor import build_presentos_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("presentos.api")

app = FastAPI(title="Present OS Backend", version="1.0")

# Initialize core components
graph = build_presentos_graph()
notion = NotionClient.from_env()

# Store active WebSocket connections
connected_clients: set[WebSocket] = set()


class ChatRequest(BaseModel):
    message: str = ""


async def broadcast_xp_award(xp_amount: int, paei: str, avatar: str):
    """Safely broadcast XP award to all connected clients"""
    if not connected_clients:
        return

    message = {
        "type": "xp_award",
        "xp": xp_amount,
        "paei": paei,
        "avatar": avatar,
        "timestamp": datetime.now().isoformat()
    }

    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.add(client)

    # Clean up dead connections
    for client in disconnected:
        connected_clients.discard(client)
        logger.info("Removed disconnected WebSocket client")


async def broadcast_agent_activity(agent_name: str, action: str):
    """Safely broadcast agent activity updates"""
    if not connected_clients:
        return

    message = {
        "type": "agent_activity",
        "agent": agent_name,
        "action": action,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.add(client)

    for client in disconnected:
        connected_clients.discard(client)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Proper WebSocket handler with disconnect handling"""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket connected: {websocket.client}")

    try:
        # Keep connection alive - we only broadcast TO clients, no need to process incoming
        while True:
            # Wait for any message (keeps connection alive), but ignore content
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                # Ignore non-disconnect exceptions (e.g. timeout)
                continue
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info("WebSocket connection closed and cleaned up")


@app.get("/api/status")
async def status():
    """Initial load - real data from Notion"""
    try:
        xp_data = notion.get_xp_summary()
        tasks = notion.get_tasks(status_filter=None, limit=10)
        active_quest = notion.get_active_quest()

        quest_data = {
            "name": active_quest.get("name", "No active quest") if active_quest else "No active quest",
            "purpose": active_quest.get("purpose", "") if active_quest else "",
            "progress": active_quest.get("progress", 0) if active_quest else 0
        }

        total_xp = sum(xp_data.get(k, 0) for k in ["P", "A", "E", "I"])
        paei_levels = {
            "P": min((xp_data.get("P", 0) // 20) + 1, 10),
            "A": min((xp_data.get("A", 0) // 20) + 1, 10),
            "E": min((xp_data.get("E", 0) // 20) + 1, 10),
            "I": min((xp_data.get("I", 0) // 20) + 1, 10),
        }

        hour = datetime.now().hour
        greeting = (
            "Good morning! Ready to flow today? 🌅" if 5 <= hour < 12 else
            "Good afternoon! Energy and conditions looking good. 🌞" if 12 <= hour < 17 else
            "Good evening! Time to align and reflect. 🌇" if 17 <= hour < 22 else
            "Still up? I'm here with you. 🌙"
        )

        return {
            "greeting": greeting,
            "updated_state": {
                "xp_data": xp_data,
                "paei_levels": paei_levels,
                "active_quest": quest_data,
                "whoop_energy": {
                    "recovery": 82,
                    "strain": 14,
                    "level": "high",
                    "advice": "Perfect for deep work or surfing 🌊"
                },
                "weather_advisory": {
                    "condition": "☀️ Perfect kite conditions",
                    "time": "in 2 hours",
                    "details": "Wind: 12-15 knots | Waves: 3-4 ft",
                    "icon": "🌊"
                },
                "todays_plan": ["Deep work", "Email review", "Team sync"],
                "tasks": tasks,
                "notifications": [
                    {"title": "🎯 Quest Active", "message": quest_data["name"], "time": "Today", "read": False}
                ],
                "agents": [
                    {"name": "Task Agent", "status": "🟢 Running", "last_action": "Just now"},
                    {"name": "XP Agent", "status": "🟢 Active", "last_action": "Just now"}
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error in /api/status: {e}")
        return {
            "greeting": "Welcome back! 🌊",
            "updated_state": {
                "xp_data": {"P": 0, "A": 0, "E": 0, "I": 0, "total": 0, "streak": 0},
                "paei_levels": {"P": 1, "A": 1, "E": 1, "I": 1},
                "active_quest": {"name": "No active quest", "purpose": "", "progress": 0},
                "tasks": [],
                "notifications": [],
                "agents": []
            }
        }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint - full agent orchestration"""
    try:
        logger.info(f"Processing message: {request.message}")

        # Broadcast thinking state
        await broadcast_agent_activity("Parent Agent", f"Thinking about: {request.message[:40]}...")

        # Create and run state
        state = PresentOSState()
        state.input_text = request.message
        result_state = graph.invoke(state)

        response = result_state.final_response or "All set! 🌊"

        # Extract XP award if any
        xp_award = 0
        paei_role = "P"
        avatar = "Warrior"

        if result_state.parent_decision:
            instructions = result_state.parent_decision.get("instructions", [])
            for instr in instructions:
                if instr.get("agent") == "xp_agent":
                    payload = instr.get("payload", {})
                    xp_award = payload.get("amount", 10)
                    paei_role = payload.get("paei", "P")
                    avatar = payload.get("avatar", "Warrior")
                    await broadcast_xp_award(xp_award, paei_role, avatar)
                    break

        # Refresh real data
        tasks = notion.get_tasks(status_filter="To Do", limit=10)
        xp_data = notion.get_xp_summary()

        paei_levels = {
            "P": min(xp_data.get("P", 0) // 20 + 1, 10),
            "A": min(xp_data.get("A", 0) // 20 + 1, 10),
            "E": min(xp_data.get("E", 0) // 20 + 1, 10),
            "I": min(xp_data.get("I", 0) // 20 + 1, 10),
        }

        active_quest = notion.get_active_quest()
        quest_data = {
            "name": active_quest.get("name", "No active quest") if active_quest else "No active quest",
            "purpose": active_quest.get("purpose", "") if active_quest else "",
            "progress": active_quest.get("progress", 0) if active_quest else 0
        }

        # XP notification
        notifications = []
        if xp_award > 0:
            notifications.append({
                "title": f"🎮 +{xp_award} XP Awarded!",
                "message": f"{avatar} avatar gained {xp_award} {paei_role} XP",
                "time": "Just now",
                "read": False
            })

        return {
            "response": response,
            "paei": paei_role,
            "xp_awarded": xp_award,
            "avatar": avatar,
            "updated_state": {
                "xp_data": xp_data,
                "paei_levels": paei_levels,
                "active_quest": quest_data,
                "whoop_energy": {
                    "recovery": 82,
                    "strain": 14,
                    "level": "high",
                    "advice": "Perfect for deep work or surfing 🌊"
                },
                "weather_advisory": {
                    "condition": "☀️ Perfect kite conditions",
                    "time": "in 2 hours",
                    "details": "Wind: 12-15 knots | Waves: 3-4 ft",
                    "icon": "🌊"
                },
                "todays_plan": ["Deep work", "Email review", "Team sync"],
                "tasks": tasks,
                "notifications": notifications,
                "agents": [
                    {"name": "Task Agent", "status": "🟢 Running", "last_action": "Just now"},
                    {"name": "Calendar Agent", "status": "🟡 Idle", "last_action": "5m ago"},
                    {"name": "XP Agent", "status": "🟢 Active", "last_action": "Just now"},
                    {"name": "Email Agent", "status": "🟢 Processing", "last_action": "1m ago"},
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error in /api/chat: {e}")
        return {
            "response": "I encountered an error. Please try again.",
            "paei": "P",
            "xp_awarded": 0,
            "avatar": "Warrior",
            "updated_state": {}
        }


@app.get("/api/xp/award")
async def award_xp(amount: int = 10, paei: str = "P", avatar: str = "Warrior"):
    """Test endpoint for XP awards"""
    await broadcast_xp_award(amount, paei, avatar)
    return {"status": "XP awarded", "amount": amount, "paei": paei, "avatar": avatar}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)