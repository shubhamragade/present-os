import { useState } from 'react';
import { Mic, Send } from 'lucide-react';
import { usePresentOS } from '../../store/usePresentOS';
import clsx from 'clsx';

export const InputBar = () => {
    const [input, setInput] = useState("");
    const { sendMessage, isListening, toggleVoice } = usePresentOS();

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim()) return;

        await sendMessage(input);
        setInput("");
    };

    return (
        <div className="p-6 pt-2 bg-gradient-to-t from-background via-background to-transparent sticky bottom-0 z-10 w-full max-w-4xl mx-auto">
            <div className="relative flex items-center gap-3 bg-surface border border-white/10 rounded-2xl p-2 pl-4 shadow-2xl shadow-black/50 ring-1 ring-white/5">

                <form onSubmit={handleSubmit} className="flex-1">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask PresentOS..."
                        className="w-full bg-transparent border-none outline-none text-white placeholder-secondary/50 h-10"
                        autoFocus
                    />
                </form>

                <div className="flex items-center gap-2 pr-1">
                    {/* Voice Toggle */}
                    <button
                        onClick={toggleVoice}
                        className={clsx(
                            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                            isListening ? "bg-accent text-white animate-pulse" : "hover:bg-white/10 text-secondary"
                        )}
                        title="Toggle Voice Mode"
                    >
                        <Mic className="w-5 h-5" />
                    </button>

                    {/* Send Button */}
                    <button
                        onClick={() => handleSubmit()}
                        disabled={!input.trim()}
                        className="w-10 h-10 rounded-xl bg-white/10 hover:bg-white/20 text-white flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                        <Send className="w-4 h-4 ml-0.5" />
                    </button>
                </div>
            </div>

            <div className="text-center mt-2">
                <span className="text-[10px] text-secondary/40 font-mono tracking-widest uppercase">
                    AI Operating System v1.0
                </span>
            </div>
        </div>
    );
};
