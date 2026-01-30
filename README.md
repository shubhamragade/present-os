# Present OS

Present OS is a comprehensive multi-agent AI Operating System designed to optimize personal productivity, health, and flow. It acts as a central hub integrating various aspects of digital life through specialized AI agents.

## 🌟 System Overview

The system is built on a **Client-Server architecture**:
- **Backend**: A robust Python FastAPI server orchestrating multiple AI agents (LangGraph/LangChain).
- **Frontend**: A modern, responsive dashboard built with React and Vite.
- **Database**: Uses Notion as the primary database for tasks, contacts, and logs, alongside Pinecone for vector memory.

### Key Agents & Features
- **Parent Agent**: The central orchestrator giving high-level direction.
- **Task Agent**: Manages to-do lists, priorities, and projects in Notion.
- **Calendar Agent**: Schedules meetings and manages time blocks (Google Calendar).
- **Email Agent**: Drafts, summarizes, and prioritizes emails (Gmail).
- **Contact Agent**: Manages the "tribes" (CRM) and contact details.
- **XP & Gamification**: Tracks 'PAEI' (Producer, Admin, Entrepreneur, Integrator) stats to gamify productivity.
- **Voice & Chat**: Supports voice interaction via Whisper/ElevenLabs/Murf and text chat.
- **Integrations**: Fireflies (meetings), Telegram (bot interface), Weather APIs, and more.

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd present-os
   ```

2. **Environment Setup:**
   - Copy `.env.example` to `.env` in the root directory.
   - Fill in the required API keys (OpenAI, Notion, Google, etc.).

### 🏃‍♂️ Running Locally

#### 1. Backend (Python)
Navigate to the project root:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\Activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.api:app --reload --port 8000
```
The backend will be available at `http://localhost:8000`.

#### 2. Frontend (React)
Open a new terminal and navigate to the frontend folder:
```bash
cd present_os_frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
The frontend will typically run at `http://localhost:5173`.

### 🐳 Running with Docker
If you prefer using Docker:
```bash
docker-compose -f infra/docker-compose.yml up --build
```

## 🤝 Contributing
1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request