import { create } from 'zustand';
import type { PresentOSState, Message } from '../types';

// MOCK DATA
const INITIAL_MESSAGES: Message[] = [
    {
        id: "1",
        role: "system",
        content: "Welcome, sir. I am online and ready to synchronize.",
        timestamp: new Date().toISOString(),
        activePAEI: "A"
    }
];

export const usePresentOS = create<PresentOSState>((set) => ({
    // State
    currentRole: "P",
    xp: { P: 125, A: 80, E: 200, I: 50 },
    messages: INITIAL_MESSAGES,
    isListening: false,
    isSpeaking: false,
    activeQuest: {
        id: "q1",
        name: "Launch PresentOS MVP",
        progress: 65,
        status: "active"
    },
    tasks: [
        { id: "t1", title: "Refactor backend tests", status: "done", questId: "q1" },
        { id: "t2", title: "Implement frontend UI", status: "pending", questId: "q1" },
        { id: "t3", title: "Deploy to staging", status: "pending", questId: "q1" },
    ],

    // Voice State (Extended)
    mediaRecorder: null as MediaRecorder | null,
    audioChunks: [] as Blob[],
    voiceMode: false, // Track if last input was via voice

    // Actions
    sendMessage: async (text: string, fromVoice: boolean = false) => {
        // Optimistic user update
        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: text,
            timestamp: new Date().toISOString()
        };

        set(state => ({ messages: [...state.messages, userMsg], voiceMode: fromVoice }));

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();

            const responseMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "system",
                content: data.response,
                timestamp: new Date().toISOString(),
                activePAEI: data.paei,
                xpAwarded: data.xp_awarded > 0 ? { [data.paei]: data.xp_awarded } : undefined,
                actions: data.updated_state?.tasks?.length > 0 ? [{ type: "task", label: "Tasks Updated" }] : []
            };

            set(state => ({
                messages: [...state.messages, responseMsg],
                xp: data.updated_state?.xp_data || state.xp,
                activeQuest: data.updated_state?.active_quest || state.activeQuest,
                tasks: data.updated_state?.tasks || state.tasks
            }));

            // TTS Synthesis - ONLY if in voice mode (user spoke via mic)
            if (fromVoice && data.response) {
                try {
                    const ttsResponse = await fetch('/api/voice/tts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: data.response })
                    });

                    if (ttsResponse.ok) {
                        const audioBlob = await ttsResponse.blob();
                        const url = URL.createObjectURL(audioBlob);
                        const audio = new Audio(url);
                        set({ isSpeaking: true });
                        audio.onended = () => {
                            set({ isSpeaking: false });
                            URL.revokeObjectURL(url);
                        };
                        await audio.play();
                    }
                } catch (ttsError) {
                    console.error("TTS Error:", ttsError);
                    // Continue even if TTS fails
                }
            }

        } catch (error) {
            console.error("Chat Error:", error);
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "system",
                content: "System connection interrupted. Please check backend status.",
                timestamp: new Date().toISOString(),
                activePAEI: "A"
            };
            set(state => ({ messages: [...state.messages, errorMsg] }));
        }
    },

    toggleVoice: async () => {
        const state = usePresentOS.getState();

        if (!state.isListening) {
            // Start Recording
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const recorder = new MediaRecorder(stream);
                const chunks: Blob[] = [];

                recorder.ondataavailable = (e) => chunks.push(e.data);
                recorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('file', blob, 'voice.webm');

                    // Send to STT
                    const res = await fetch('/api/voice/stt', { method: 'POST', body: formData });
                    const data = await res.json();
                    if (data.text) {
                        // Pass true to indicate this came from voice
                        state.sendMessage(data.text, true);
                    }
                    stream.getTracks().forEach(t => t.stop());
                };

                recorder.start();
                set({ isListening: true, mediaRecorder: recorder, audioChunks: chunks });
            } catch (err) {
                console.error("Mic Access Denied:", err);
            }
        } else {
            // Stop Recording
            state.mediaRecorder?.stop();
            set({ isListening: false, mediaRecorder: null });
        }
    },

    setTasks: (tasks) => set({ tasks }),
    setActiveQuest: (quest) => set({ activeQuest: quest })
}));

