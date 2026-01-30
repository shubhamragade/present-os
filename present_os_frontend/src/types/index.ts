

export type PAEIRole = "P" | "A" | "E" | "I";

export interface XPBalance {
    P: number;
    A: number;
    E: number;
    I: number;
}

export interface Message {
    id: string;
    role: "user" | "system";
    content: string;
    timestamp: string;
    xpAwarded?: Partial<XPBalance>;
    actions?: {
        type: "calendar" | "email" | "task" | "focus";
        label: string;
    }[];
    activePAEI?: PAEIRole;
}

export interface Quest {
    id: string;
    name: string;
    progress: number; // 0-100
    status: "active" | "completed" | "blocked";
    purpose?: string;
}

export interface Task {
    id: string;
    title: string;
    due?: string;
    status: "pending" | "done";
    questId?: string;
}

export interface PresentOSState {
    // PAEI
    currentRole: PAEIRole;
    xp: XPBalance;

    // Chat
    messages: Message[];
    isListening: boolean;
    isSpeaking: boolean;

    // Context
    activeQuest: Quest | null;
    tasks: Task[];

    // Actions
    sendMessage: (text: string, fromVoice?: boolean) => Promise<void>;
    toggleVoice: () => void | Promise<void>;
    setTasks: (tasks: Task[]) => void;
    setActiveQuest: (quest: Quest | null) => void;

    // Internal Voice Refs
    mediaRecorder?: any;
    audioChunks?: any[];
}
