import { useRef, useEffect } from 'react';
import { usePresentOS } from '../../store/usePresentOS';
import { MessageBubble } from './MessageBubble';

export const ChatArea = () => {
    const { messages } = usePresentOS();
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-6">
            <div className="h-4" /> {/* Spacer */}

            {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
            ))}

            <div ref={bottomRef} className="h-4" />
        </div>
    );
};
