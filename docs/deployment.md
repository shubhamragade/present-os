# Present OS Deployment Guide

## ✅ System Verification Status
All core systems verified and working:
- **Task Agent**: ✅ Working
- **Calendar Agent**: ✅ Working  
- **Weather Agent**: ✅ Working
- **XP Agent**: ✅ Working
- **Voice System**: ✅ Working (Murf TTS + Whisper STT)
- **Email Agent**: ✅ Working
- **Finance Agent**: ✅ Working
- **Focus Agent**: ✅ Working
- **Contact Agent**: ✅ Working
- **Browser/Research Agent**: ✅ Working

---

## Quick Start (Local Development)

### 1. Backend Server
```bash
cd present-os
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # macOS/Linux

uvicorn app.api:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Frontend Server
```bash
cd present_os_frontend
npm run dev
```

- **Backend**: http://localhost:8080
- **Frontend**: http://localhost:5173

---

## Production Deployment Options

### Option 1: Docker Compose (Recommended)
```bash
cd infra
docker-compose up -d
```

### Option 2: Manual Deployment

#### Backend (Python/FastAPI)
```bash
pip install -r requirements.txt
uvicorn app.api:app --host 0.0.0.0 --port 8080
```

#### Frontend (Vite/React)
```bash
cd present_os_frontend
npm install
npm run build
# Serve the dist/ folder with nginx or any static host
```

---

## Environment Variables Required

Create a `.env` file with:

```env
# Core
OPENAI_API_KEY=your_openai_key

# Notion Integration
NOTION_TOKEN=your_notion_token
NOTION_DB_TASKS_ID=your_tasks_db_id
NOTION_DB_QUESTS_ID=your_quests_db_id
NOTION_DB_XP_ID=your_xp_db_id
NOTION_DB_CONTACTS_ID=your_contacts_db_id

# Google/Gmail
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
GMAIL_USER_EMAIL=your_email

# Voice (TTS/STT)
MURF_API_KEY=your_murf_key
MURF_VOICE_ID=en-US-marcus

# Weather
WEATHER_API_KEY=your_weather_key

# Optional
PINECONE_API_KEY=your_pinecone_key
FIREFLIES_API_KEY=your_fireflies_key
TELEGRAM_BOT_TOKEN=your_telegram_token
```

---

## Cloud Deployment Platforms

### Vercel (Frontend)
1. Push to GitHub
2. Connect to Vercel
3. Set build command: `npm run build`
4. Set output directory: `dist`

### Railway/Render (Backend)
1. Push to GitHub
2. Connect to Railway/Render
3. Set start command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### AWS/GCP/Azure
Use the Kubernetes manifests in `infra/k8s/` or Terraform in `infra/terraform/`

---

## Health Check Endpoints

- `GET /api/status` - Full system status
- `GET /api/energy` - Energy/WHOOP status
- `POST /api/chat` - Main chat endpoint

---

## Post-Deployment Checklist

- [ ] Verify all API keys are set
- [ ] Test chat functionality
- [ ] Test voice input/output
- [ ] Verify Notion sync
- [ ] Test calendar integration
- [ ] Verify email functionality
