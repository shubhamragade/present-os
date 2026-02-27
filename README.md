# 🌌 Present OS

Present OS is a comprehensive multi-agent AI Operating System designed to optimize personal productivity, health, and flow. It acts as a central hub, intelligently integrating various aspects of your digital life through specialized AI agents.

## ❗ Problem Statement

In today's fast-paced digital environment, individuals face overwhelming cognitive load due to fragmented tools. Managing tasks, emails, calendars, and contacts across disconnected platforms leads to constant context switching, reduced focus, and decreased productivity. There is a critical need for an intelligent, centralized system that not only consolidates these workflows but actively assists in managing them, freeing users to focus on high-impact work and personal growth.

## 🎯 Our Approach

Present OS solves this fragmentation through a unified, multi-agent artificial intelligence ecosystem. Rather than relying on static applications, we deploy specialized AI agents, coordinated by a central intelligence, to autonomously handle distinct domains of your life. 

By integrating natural language processing, voice interaction, and gamification (PAEI tracking), Present OS transforms routine digital management into an engaging, conversational, and highly automated experience. It acts as a proactive digital twin, anticipating needs and executing tasks seamlessly.

## 🏗️ System Architecture & Workflow

The system is built on a scalable, modern **Client-Server architecture** driven by AI orchestration:

- **Backend (Intelligence Engine):** A robust Python FastAPI server leveraging LangGraph and LangChain to orchestrate multiple AI agent workflows.
- **Frontend (User Interface):** A responsive, modern dashboard built with React and Vite for visual management.
- **Data & Memory Layer:** Utilizes Notion as the primary structured database (tasks, contacts, logs) and Pinecone for vector memory, enabling long-term contextual recall.

### 🔄 System Workflow
1. **Interaction:** Users input requests via text chat, voice (Whisper/ElevenLabs), or external channels like Telegram.
2. **Orchestration (Parent Agent):** The central Parent Agent analyzes the user's intent, context, and historical data to determine the best course of action.
3. **Delegation:** The task is routed to one or more specialized agents (Task, Calendar, Email, Contact).
4. **Execution:** Specialized agents interact with third-party APIs (Google Workspace, Notion, Fireflies) to execute actions.
5. **Feedback & Gamification:** The system returns the result to the user, updates the persistent memory, and adjusts the user's 'PAEI' (Producer, Admin, Entrepreneur, Integrator) stats and XP progression.

## ✨ Key Agents & Features

- **🧠 Parent Agent:** The central orchestrator giving high-level direction and managing agent delegation.
- **✅ Task Agent:** Intelligently manages to-do lists, priorities, and project tracking in Notion.
- **📅 Calendar Agent:** Schedules meetings, resolves conflicts, and manages time blocks securely via Google Calendar.
- **📧 Email Agent:** Drafts, summarizes, and prioritizes emails directly within Gmail.
- **👥 Contact Agent:** Acts as a smart CRM, managing your "tribes" and relationship details.
- **🎮 XP & Gamification:** Tracks your 'PAEI' stats to gamify productivity and maintain flow.
- **🎙️ Voice & Chat:** Universal access via conversational text chat and high-quality voice interactions.
- **🔌 Rich Integrations:** Deep hooks into Fireflies (meetings), Telegram (bot interface), Weather APIs, and more.

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Git**
- Relevant API Keys (OpenAI, Notion, Google Cloud, Pinecone, etc.)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd present-os
   ```

2. **Environment Setup:**
   - Copy `.env.example` to a new `.env` file in the root directory.
   - Fill in all the required API keys and configuration variables.

### 🏃‍♂️ Running Locally

#### 1. Backend (Python API)
Open a terminal in the project root:
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\Activate
# Mac/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.api:app --reload --port 8000
```
*The backend API and Swagger docs will be available at `http://localhost:8000/docs`.*

#### 2. Frontend (React Dashboard)
Open a new terminal and navigate to the frontend folder:
```bash
cd present_os_frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The dashboard will be running at `http://localhost:5173`.*

### 🐳 Running with Docker
For a containerized setup, ensure Docker is running, then execute:
```bash
docker-compose -f infra/docker-compose.yml up --build
```

## 🤝 Contributing
Contributions make the open-source community an amazing place to learn, inspire, and create.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request