# 🎬 Present OS - Video Demo Script

## Pre-Recording Setup

1. **Start the backend server:**
   ```bash
   cd c:\present-os
   .\.venv\Scripts\Activate.ps1
   uvicorn app.api:app --host 0.0.0.0 --port 8080
   ```

2. **Start the frontend:**
   ```bash
   cd c:\present-os\present_os_frontend
   npm run dev
   ```

3. **Open browser:** http://localhost:5173

---

## 📝 Demo Script - Copy & Paste Examples

### 🎯 1. TASK AGENT
*Shows task creation and management*

```
Add task call mom tonight
```
**Expected:** Creates a task in Notion, shows confirmation with XP award

```
Create task review quarterly report due Friday
```
**Expected:** Creates task with due date

```
Show my tasks
```
**Expected:** Lists all pending tasks from Notion

---

### 📅 2. CALENDAR AGENT
*Shows scheduling and calendar management*

```
What's on my schedule today?
```
**Expected:** Shows today's calendar events from Google Calendar

```
Schedule team meeting tomorrow at 3 PM
```
**Expected:** Creates calendar event

```
Block deep work tomorrow morning 9 to 11
```
**Expected:** Creates a focus block on calendar

---

### ⛅ 3. WEATHER AGENT
*Shows weather information*

```
What's the weather in Pune?
```
**Expected:** Shows current weather with temperature, conditions

```
Is it good weather for outdoor work today?
```
**Expected:** Weather-based activity recommendation

```
Weather forecast for Mumbai
```
**Expected:** Weather info for different city

---

### 🎮 4. XP AGENT
*Shows gamification and XP system*

```
Show my XP status
```
**Expected:** Shows P, A, E, I XP scores and levels

```
What's my current level?
```
**Expected:** Shows avatar level and progress

```
How much XP do I have?
```
**Expected:** XP breakdown by category

---

### 📧 5. EMAIL AGENT (Full Functionality)
*Shows all email capabilities*

#### 5a. Check/Read Emails
```
Check my emails
```
**Expected:** Shows recent unread emails with subjects

```
Show unread emails
```
**Expected:** Lists all unread messages

```
Any important emails today?
```
**Expected:** Prioritized email summary

```
How many emails do I have?
```
**Expected:** Email count and summary

---

#### 5b. Email Triage (AI Prioritization)
```
Triage my inbox
```
**Expected:** AI categorizes emails by priority and action needed

```
Which emails need my attention?
```
**Expected:** Lists actionable emails (meetings, deadlines, urgent items)

```
Summarize my emails
```
**Expected:** Brief summary of each email

---

#### 5c. Draft Emails
```
Draft a reply to the last email saying thank you
```
**Expected:** Creates Gmail draft with thank you message

```
Draft an email to John about project update
```
**Expected:** Drafts personalized email based on contact preferences

```
Compose email to team about Friday meeting
```
**Expected:** Creates draft with meeting details

---

#### 5d. Send Emails
```
Send email to john@example.com saying Hello, checking in on the project status
```
**Expected:** Sends email directly (requires confirmation)

```
Email my team about the deadline extension
```
**Expected:** Identifies team contacts, drafts and prepares to send

```
Reply to the last email with thanks and confirm the meeting
```
**Expected:** Replies in thread, confirms meeting attendance

---

#### 5e. Smart Email Sender (RAG-Powered)
*Uses memory to personalize emails*

```
Send follow-up email to Sarah about the proposal
```
**Expected:** 
- Checks last email to Sarah
- Uses contact preferences from Notion
- Applies preferred tone (formal/casual)
- Adds personalization from past interactions

```
Email my VIP contacts about the new product launch
```
**Expected:**
- Filters VIP relationships
- Checks communication history
- Avoids spam (won't email if contacted recently)
- Personalizes per contact

---

#### 5f. Email Task Extraction
```
Check emails and create tasks from action items
```
**Expected:**
- Scans inbox
- Extracts deadlines and action items
- Creates tasks in Notion automatically



---

### 🎯 6. FOCUS AGENT
*Shows focus/deep work features*

```
Start a 25 minute focus session
```
**Expected:** Initiates Pomodoro-style focus session

```
I need deep work time tomorrow
```
**Expected:** Suggests and blocks focus time

```
Block time for concentration this afternoon
```
**Expected:** Creates focus block on calendar

---

### 💰 7. FINANCE AGENT
*Shows budget and finance tracking*

```
Show my budget summary
```
**Expected:** Shows spending categories and budget status

```
What bills are due this month?
```
**Expected:** Lists upcoming bills/expenses

```
Track my expenses
```
**Expected:** Expense overview

---

### 👤 8. CONTACT AGENT
*Shows contact management*

```
Show contact for John
```
**Expected:** Retrieves contact information from Notion

```
Who is my contact at Microsoft?
```
**Expected:** Searches contacts by company

```
Add note to John: met at tech conference
```
**Expected:** Updates contact with note

---

### 🔍 9. RESEARCH/BROWSE AGENT
*Shows web research capabilities*

```
Research best practices for API design 2026
```
**Expected:** Web search results and summary

```
Find information about AI productivity tools
```
**Expected:** Research summary with sources

```
Look up latest trends in no-code platforms
```
**Expected:** Trend analysis and findings

---

### 📊 10. PLAN REPORT AGENT
*Shows daily planning*

```
What's my plan for today?
```
**Expected:** Consolidated daily plan with tasks, events, weather

```
Give me a morning briefing
```
**Expected:** Morning summary with priorities

```
Good morning, what should I focus on?
```
**Expected:** Prioritized focus recommendations

---

### 🎤 11. VOICE SYSTEM (Murf TTS)
*Shows voice input/output*

**Demo Steps:**
1. Click the 🎤 Mic button (it will pulse/glow)
2. Speak: "What's on my schedule today?"
3. Click mic again to stop
4. Wait for AI to respond with voice!

**Voice queries to try:**
- "Add task buy groceries"
- "What's the weather?"
- "Show my XP status"

---

### 📱 12. TELEGRAM BOT
*Shows mobile/Telegram integration*

**Setup (run in separate terminal):**
```bash
cd c:\present-os
.\.venv\Scripts\Activate.ps1
python scripts/run_telegram_bot.py
```

**Demo Steps:**
1. Open Telegram app on phone
2. Search for your bot: `@YourBotName`
3. Send `/start` to get connected
4. Send messages directly to interact with PresentOS!

**Telegram messages to try:**
```
/start
```
**Expected:** Welcome message with your Chat ID

```
What's on my schedule today?
```
**Expected:** Shows calendar events via Telegram

```
Add task call team tomorrow
```
**Expected:** Creates task, confirms via Telegram

```
Check my emails
```
**Expected:** Email summary sent to Telegram

```
Weather in Pune
```
**Expected:** Weather info via Telegram

```
Show my XP status
```
**Expected:** XP scores via Telegram

**Note:** Your Telegram Bot Token is already configured in `.env`:
- `TELEGRAM_BOT_TOKEN=your_token`
- `TELEGRAM_CHAT_ID=your_chat_id`

---

## 🎬 Recommended Recording Flow

1. **Intro** (30 sec)
   - Show the PresentOS dashboard
   - Briefly explain the system

2. **Task Demo** (1 min)
   - Add a task, show it appears

3. **Calendar Demo** (1 min)
   - Check schedule, create event

4. **Weather Demo** (30 sec)
   - Quick weather check

5. **XP/Gamification Demo** (30 sec)
   - Show XP status and levels

6. **Email Demo** (1 min)
   - Check emails

7. **Focus Demo** (30 sec)
   - Start focus session

8. **Research Demo** (1 min)
   - Do a web research query

9. **Voice Demo** (1 min)
   - Use mic for voice input
   - Show AI speaks back

10. **Conclusion** (30 sec)
    - Show final dashboard state

---

## 📋 Quick Copy-Paste List

```
Good morning, what's on my schedule today?
Add task call client about project feedback
Schedule team sync Friday at 2 PM
What's the weather in Pune?
Show my XP status
Check my emails
Start a 25 minute focus session
Show my budget summary
Research latest AI trends in productivity
What's my plan for today?
```

---

## ✅ Checklist Before Recording

- [ ] Backend server running (port 8080)
- [ ] Frontend running (port 5173)
- [ ] Screen recorder ready
- [ ] Microphone ready (for voice demo)
- [ ] Browser at http://localhost:5173
- [ ] Demo script open on side screen
