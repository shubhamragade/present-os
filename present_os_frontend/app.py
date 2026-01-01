import streamlit as st
import os
import time
import json
from datetime import datetime
import requests
from streamlit_autorefresh import st_autorefresh

# ===================== CONFIG =====================
st.set_page_config(
    page_title="Present OS • Martin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== PATHS =====================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(PROJECT_DIR, "custom.css")

# Load CSS
try:
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("custom.css not found!")

# ===================== BACKEND URL =====================
API_URL = "http://localhost:8000"

# ===================== SESSION STATE =====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "xp_awards" not in st.session_state:
    st.session_state.xp_awards = []
if "agent_activities" not in st.session_state:
    st.session_state.agent_activities = []

# ===================== BACKEND CALLS =====================
def fetch_status():
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        st.warning("⚠️ Backend not connected")
        return None
    return None

def send_message(message):
    try:
        response = requests.post(
            f"{API_URL}/api/chat", 
            json={"message": message},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        st.error("Martin is thinking... try again")
        return None
    return None

def award_xp_test(amount=10, paei="P", avatar="Warrior"):
    try:
        response = requests.get(
            f"{API_URL}/api/xp/award",
            params={"amount": amount, "paei": paei, "avatar": avatar}
        )
        return response.json()
    except:
        return None

# ===================== XP POPUP COMPONENT =====================
def show_xp_popup(xp_amount, paei, avatar):
    paei_icons = {"P": "⚔️", "A": "📋", "E": "🚀", "I": "🤝"}
    icon = paei_icons.get(paei, "🎮")
    
    st.markdown(f"""
    <div class="xp-popup" id="xpPopup">
        {icon} +{xp_amount} {paei} XP!
        <br><span style="font-size:16px;">{avatar} leveled up!</span>
    </div>
    <script>
        setTimeout(() => {{
            const el = document.getElementById('xpPopup');
            if (el) el.remove();
        }}, 2500);
    </script>
    """, unsafe_allow_html=True)

# ===================== INITIALIZE WITH REAL BACKEND DATA =====================
if not st.session_state.initialized:
    status = fetch_status()
    if status:
        greeting = status.get("greeting", "Welcome back! 🌊")
        updated_state = status.get("updated_state", {})
        
        st.session_state.xp_data = updated_state.get("xp_data", {"P": 0, "A": 0, "E": 0, "I": 0, "total": 0, "streak": 0})
        st.session_state.paei_levels = updated_state.get("paei_levels", {"P": 1, "A": 1, "E": 1, "I": 1})
        st.session_state.active_quest = updated_state.get("active_quest", {"name": "No active quest", "purpose": "", "progress": 0})
        st.session_state.tasks = updated_state.get("tasks", [])
        st.session_state.notifications = updated_state.get("notifications", [])
        st.session_state.agents = updated_state.get("agents", [])
        st.session_state.whoop_energy = updated_state.get("whoop_energy", {"recovery": 82, "strain": 14, "level": "high", "advice": "Perfect for deep work or surfing 🌊"})
        st.session_state.weather_advisory = updated_state.get("weather_advisory", {"condition": "☀️ Perfect kite conditions", "time": "in 2 hours", "details": "Wind: 12-15 knots | Waves: 3-4 ft", "icon": "🌊"})
        st.session_state.todays_plan = updated_state.get("todays_plan", ["Deep work", "Email review", "Team sync"])
        
        # Only clean greeting (from /api/status) — not normal responses
        clean_greeting = str(greeting).replace("</div>", "").replace("<div", "").replace("class='martin-content'>", "").replace('class="martin-content">', "").strip()
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": clean_greeting, 
            "paei": "", 
            "xp": 0
        })
    else:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Good morning! I'm here. 🌊", 
            "paei": "", 
            "xp": 0
        })
    st.session_state.initialized = True

# ===================== TOP BAR =====================
col_logo, col_title, col_time, col_bell = st.columns([1, 4, 1, 1])

with col_logo:
    st.markdown("""
    <div style="text-align:center; padding-top:15px;">
        <div style="font-size:32px; animation: float 3s ease-in-out infinite;">🤖</div>
    </div>
    """, unsafe_allow_html=True)

with col_title:
    st.markdown("<h1 class='title'>Present OS • Martin</h1>", unsafe_allow_html=True)

with col_time:
    current_time = datetime.now().strftime("%I:%M %p")
    current_date = datetime.now().strftime("%b %d, %Y")
    st.markdown(f"""
    <div style="text-align:center; padding-top:15px;">
        <div style="font-size:20px; font-weight:700; color:#1E3A8A;">{current_time}</div>
        <div style="font-size:12px; color:#64748B;">{current_date}</div>
    </div>
    """, unsafe_allow_html=True)

with col_bell:
    unread_count = len([n for n in st.session_state.get("notifications", []) if not n.get("read", True)])
    bell_clicked = st.button("", key="bell_button", help=f"Notifications ({unread_count} unread)")
    
    st.markdown(f"""
    <div style='text-align:right; padding-top:15px; position:relative;'>
        <div class="bell-container">
            <div class="bell-btn">
                🔔
                {f'<span class="notification-badge">{unread_count}</span>' if unread_count > 0 else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===================== NOTIFICATIONS PANEL =====================
if bell_clicked:
    st.session_state.show_notifications = not st.session_state.get("show_notifications", False)

if st.session_state.get("show_notifications", False):
    notifications = st.session_state.get("notifications", [])
    notifications_html = ""

    if notifications:
        for i, n in enumerate(notifications):
            bg = "#F8FAFC" if n.get("read", True) else "#EFF6FF"
            border = "#D1D5DB" if n.get("read", True) else "#60A5FA"
            notifications_html += f"""
            <div style="background:{bg}; border-left:6px solid {border};
                        padding:16px; margin:12px 0; border-radius:12px;">
                <div style="font-weight:700;">{n.get("title","Notification")}</div>
                <div style="font-size:13px; margin-top:6px;">{n.get("message","")}</div>
                <div style="font-size:11px; color:#64748B; margin-top:6px;">{n.get("time","")}</div>
            </div>
            """
    else:
        notifications_html = "<div style='text-align:center; padding:40px; color:#94A3B8;'>🔕 No new notifications</div>"

    st.markdown(f"""
    <div class="notifications-panel">
        <div style="background:white; border-radius:20px; padding:24px; margin:10px 0 20px 0; box-shadow:0 12px 48px rgba(0,0,0,0.1); border:2px solid #E2E8F0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                <h3 style="margin:0;">📢 Notifications</h3>
                <span style="font-size:12px;">{len(notifications)} total</span>
            </div>
            {notifications_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Close Notifications", use_container_width=True):
        st.session_state.show_notifications = False
        st.rerun()

# ===================== SIDEBAR (UNCHANGED — YOUR BEAUTIFUL DESIGN) =====================
with st.sidebar:
    current_sidebar_time = datetime.now().strftime("%I:%M %p")
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:24px;">
        <div style="font-size:40px; margin-bottom:8px; animation: float 3s ease-in-out infinite;">🤖</div>
        <p class='subtitle'>Your calm co-pilot</p>
        <div class="current-time-indicator">
            ⏰ {current_sidebar_time}
        </div>
    </div>
    """, unsafe_allow_html=True)

    xp_data = st.session_state.get("xp_data", {"total": 0, "streak": 0})
    paei_levels = st.session_state.get("paei_levels", {"P": 1, "A": 1, "E": 1, "I": 1})
    
    st.markdown(f"""
    <div class='xp-display'>
        <h2>{xp_data.get('total', 0)}</h2>
        <p class='streak-display'>🔥 {xp_data.get('streak', 0)} day streak</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 class='section'>🧠 PAEI Balance</h3>", unsafe_allow_html=True)
    
    total_xp = sum([xp_data.get(k, 0) for k in ["P", "A", "E", "I"]]) or 1
    st.markdown(f"""
    <div class='paei-radial-container'>
        <div class='paei-wheel'>
            <div class='radial-slice P' style='clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 50%);'></div>
            <div class='radial-slice A' style='clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 50%); transform: rotate(90deg);'></div>
            <div class='radial-slice E' style='clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 50%); transform: rotate(180deg);'></div>
            <div class='radial-slice I' style='clip-path: polygon(50% 50%, 50% 0%, 100% 0%, 100% 100%, 50% 50%); transform: rotate(270deg);'></div>
            <div class='radial-center'>
                <div class='total'>{xp_data.get('total', 0)}</div>
                <div style='font-size:10px;'>Total XP</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(4)
    paei_info = [
        ("P", "⚔️ Warrior", "#FB923C", paei_levels.get("P", 1), xp_data.get("P", 0)),
        ("A", "📋 Organizer", "#22C55E", paei_levels.get("A", 1), xp_data.get("A", 0)),
        ("E", "🚀 Visionary", "#3B82F6", paei_levels.get("E", 1), xp_data.get("E", 0)),
        ("I", "🤝 Harmonizer", "#8B5CF6", paei_levels.get("I", 1), xp_data.get("I", 0))
    ]
    
    for i, (key, label, color, level, xp) in enumerate(paei_info):
        with cols[i]:
            st.markdown(f"""
            <div style='text-align:center;'>
                <div style='font-size:24px; margin-bottom:4px;'>{label.split()[0]}</div>
                <div style='font-size:11px; color:{color}; font-weight:700;'>Level {level}</div>
                <div style='font-size:10px; color:#64748B;'>{xp} XP</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<h3 class='section'>🏆 Active Quest</h3>", unsafe_allow_html=True)
    quest = st.session_state.get("active_quest", {})
    if quest and quest.get("name"):
        st.markdown(f"""
        <div class='quest-progress'>
            <div class='quest-name'>{quest.get('name', 'No Quest')}</div>
            <div class='quest-purpose'>{quest.get('purpose', '')}</div>
            <div style='font-size:12px; color:#64748B; margin-bottom:8px;'>Progress: {quest.get('progress', 0)}%</div>
            <div style='background:#E2E8F0; height:10px; border-radius:5px; overflow:hidden;'>
                <div style='background:linear-gradient(90deg, #3B82F6, #8B5CF6); width:{quest.get('progress', 0)}%; height:100%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; color:#94A3B8; padding:20px;'>No active quest</div>", unsafe_allow_html=True)

    st.markdown("<h3 class='section'>⚡ Energy & Recovery</h3>", unsafe_allow_html=True)
    whoop = st.session_state.get("whoop_energy", {})
    energy_color = "#10B981" if whoop.get("level") == "high" else "#FBBF24"
    st.markdown(f"""
    <div class='energy-card'>
        <div class='energy-header'>
            <span class='energy-icon'>⚡</span>
            <span class='energy-title'>Recovery</span>
        </div>
        <div class='energy-value'>{whoop.get('recovery', 0)}%</div>
        <div class='energy-stats'>
            <div class='stat-item'><span class='stat-label'>Strain</span><span class='stat-value'>{whoop.get('strain', 0)}/21</span></div>
            <div class='stat-item'><span class='stat-label'>Level</span><span class='stat-level' style='color:{energy_color};'>{whoop.get('level', 'medium').title()}</span></div>
        </div>
        <div class='energy-advice'>{whoop.get('advice', 'Ready to flow')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 class='section'>🌤️ Weather Advisory</h3>", unsafe_allow_html=True)
    weather = st.session_state.get("weather_advisory", {})
    if weather:
        st.markdown(f"""
        <div class='weather-card'>
            <div class='weather-header'>
                <span class='weather-icon'>{weather.get('icon', '☀️')}</span>
                <span class='weather-title'>{weather.get('condition', 'Good conditions')}</span>
            </div>
            <div class='weather-time'>{weather.get('time', '')}</div>
            <div class='weather-details'>{weather.get('details', '')}</div>
            <div class='weather-actions'>
                <div class='weather-action'>✅ Accept</div>
                <div class='weather-action'>⏰ Snooze</div>
                <div class='weather-action'>❌ Dismiss</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🤖 Live Agent Activity", expanded=True):
        agents = st.session_state.get("agents", [])
        if agents:
            for agent in agents:
                st.markdown(f"<div class='agent-item'><div class='agent-name'>{agent['name']}</div><div class='agent-status'>{agent['status']}</div></div>", unsafe_allow_html=True)
                st.caption(f"Last action: {agent['last_action']}")
        else:
            st.info("Agents starting up...")

    with st.expander("✅ Tasks (5)", expanded=True):
        tasks = st.session_state.get("tasks", [])
        if tasks:
            for task in tasks[:5]:
                emoji = {"P": "⚔️", "A": "📋", "E": "🚀", "I": "🤝"}.get(task.get("avatar", "P"), "📝")
                st.markdown(f"""
                <div class='task-item'>
                    <div style='display:flex; align-items:center; gap:12px;'>
                        <div class='task-avatar {task.get("avatar", "P")}'>{emoji}</div>
                        <div class='task-content'>
                            <div class='task-name'>{task.get('name', 'Task')}</div>
                            <div class='task-meta'>
                                <span>{task.get('quest', '')}</span>
                                <span>•</span>
                                <span>{task.get('xp', 0)} XP</span>
                            </div>
                        </div>
                        <div class='task-status'>{task.get('status', 'To Do')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tasks yet. Try: 'Martin, add a task'")

# ===================== MAIN CHAT AREA - CHANGED =====================
# Display all messages with Streamlit's native chat
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(message["content"])
    else:
        with st.chat_message("user"):
            st.write(message["content"])

# ===================== CHAT INPUT =====================
input_col1, input_col2, input_col3 = st.columns([6, 1, 1])

with input_col1:
    user_input = st.chat_input("🤖 Talk to Martin... (e.g., Schedule deep work, check surf)")

with input_col2:
    st.markdown("""
    <div style="margin-top:25px; text-align:center;">
        <button id="recordBtn" class="voice-btn">🎤</button>
        <p id="status" style="font-size:12px; margin-top:5px; color:#64748B;">Hold to speak</p>
    </div>
    """, unsafe_allow_html=True)

with input_col3:
    if st.button("🎮 Test XP", help="Test XP award animation"):
        award_xp_test(15, "P", "Warrior")
        show_xp_popup(15, "P", "Warrior")

# ===================== VOICE RECORDING JS (SAFE — NO AUTO-SEND) =====================
st.markdown("""
<script>
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const recordBtn = document.getElementById('recordBtn');
const status = document.getElementById('status');

recordBtn.addEventListener('mousedown', startRecording);
recordBtn.addEventListener('mouseup', stopRecording);
recordBtn.addEventListener('mouseleave', stopRecording);
recordBtn.addEventListener('touchstart', e => { e.preventDefault(); startRecording(); });
recordBtn.addEventListener('touchend', e => { e.preventDefault(); stopRecording(); });

async function startRecording() {
    try {
        status.textContent = "🎤 Recording...";
        recordBtn.style.background = "linear-gradient(135deg, #EF4444, #DC2626)";
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.start();
        isRecording = true;
    } catch (err) {
        status.textContent = "❌ Mic denied";
        setTimeout(() => status.textContent = "Hold to speak", 2000);
    }
}

function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    status.textContent = "✅ Recorded!";
    recordBtn.style.background = "linear-gradient(135deg, #10B981, #059669)";
    mediaRecorder.stop();
    mediaRecorder.onstop = () => {
        console.log("Audio recorded (ready for transcription)");
        setTimeout(() => {
            status.textContent = "Hold to speak";
            recordBtn.style.background = "linear-gradient(135deg, #3B82F6, #1D4ED8)";
        }, 3000);
    };
}
</script>
""", unsafe_allow_html=True)

# ===================== HANDLE CHAT INPUT - CHANGED =====================
if user_input and user_input.strip():
    message = user_input.strip()
    
    # Immediately show user message
    with st.chat_message("user"):
        st.write(message)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Show assistant thinking
    with st.chat_message("assistant"):
        typing = st.empty()
        
        # Typing effect
        for dots in ["Thinking", "Thinking.", "Thinking..", "Thinking..."]:
            typing.write(f"{dots} 🌊")
            time.sleep(0.35)
        
        # Send to backend
        api_response = send_message(message)
        
        if api_response and api_response.get("response"):
            martin_response = api_response["response"]
            
            # Update state
            updated_state = api_response.get("updated_state", {})
            for key, value in updated_state.items():
                st.session_state[key] = value
            
            # Show XP popup if awarded
            xp_awarded = api_response.get("xp_awarded", 0)
            if xp_awarded > 0:
                paei = api_response.get("paei", "P")
                avatar = api_response.get("avatar", "Warrior")
                show_xp_popup(xp_awarded, paei, avatar)
            
            # Display response
            typing.write(martin_response)
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": martin_response
            })
        else:
            # Fallback
            fallback = "All set! Let me know if you'd like to do anything else. 🌊"
            typing.write(fallback)
            st.session_state.messages.append({
                "role": "assistant",
                "content": fallback
            })

# ===================== FLOATING XP AWARDS =====================
if st.session_state.get("xp_awards"):
    for award in st.session_state.xp_awards[:3]:
        show_xp_popup(award["amount"], award["paei"], award["avatar"])
    st.session_state.xp_awards = st.session_state.xp_awards[3:]

# ===================== FOOTER =====================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    st.markdown("""
    <div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">
        Present OS • 🤖 Martin v1.0 • Made with ❤️
    </div>
    """, unsafe_allow_html=True)