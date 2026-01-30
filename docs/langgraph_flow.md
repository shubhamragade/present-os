# PresentOS LangGraph Flow & Agents

The system uses a LangGraph-based orchestration where the **Parent Agent (Martin)** coordinates specialized agents to fulfill user requests.

## Key Agents and Examples

| Agent | Description | Example (Input → Output) |
| :--- | :--- | :--- |
| **Parent Agent (Martin)** | Orchestrates everything. | **User:** "Schedule meeting with team, research topic first."<br>**Output:** "Meeting scheduled 2pm (PAEI balanced). Research: [summary]. +10 XP." |
| **Email Agent** | Handles inbox, drafts, tone learning. | **User:** "Reply to bill."<br>**Output:** "Drafted/sent in your style. Task created. +10 Admin XP." |
| **Calendar Agent** | Syncs, auto-schedules contextually. | **User:** "Block deep work."<br>**Output:** "Blocked 9-12am (high energy). Rescheduled conflicts. +5 Producer XP." |
| **Task Agent** | Creates/links to RPM. | **User:** "Add task: Call mom."<br>**Output:** "Added under Quest 'Family'. Scheduled. +15 Integrator XP." |
| **Meeting Agent (Fireflies)** | Transcribes, extracts. | **Post-meeting:**<br>**Output:** "Summary: [key points]. Tasks created. +20 Producer XP." |
| **XP Agent** | Tracks/awards, balances PAEI. | **Proactive:**<br>**Output:** "Weekly: Producer up, Integrator low—suggest social task? +Total XP." |
| **Browse Agent** | Scrapes/researches (Playwright). | **User:** "Research AI trends."<br>**Output:** "Top 3 articles: [summaries]. Saved to Notion. +15 Entrepreneur XP." |
| **Finance Agent** | Tracks budgets, creates tasks. | **User:** "Check spending."<br>**Output:** "Over on dining—task created. +10 Admin XP." |
| **Weather/Surf Agent** | Environment checks. | **User:** "Check conditions."<br>**Output:** "Good surf—rescheduled work? Integrated with Calendar." |
| **Report Agent** | Summaries/insights. | **Proactive weekly:**<br>**Output:** "Tasks done: 25. PAEI balance: [details]. Recommendations." |
| **Focus Agent** | Manages sessions. | **User:** "Start focus."<br>**Output:** "90min block started. Notifications off. +10 Producer XP." |
| **Contact Agent** | Stores/retrieves context. | **User:** "Add note on Sarah."<br>**Output:** "Saved. Will use in future drafts." |
| **Voice Agent/Mode** | Natural TTS/STT (ElevenLabs). | **User speaks:** "Add task."<br>**System speaks back:** "Task added. +XP." (Natural voice via ElevenLabs). |
