import clsx from 'clsx';
import type { Message } from '../../types';
import { Bot, User, Calendar, Mail, CheckSquare, Zap } from 'lucide-react';

interface Props {
    message: Message;
}

export const MessageBubble = ({ message }: Props) => {
    const isSystem = message.role === "system";

    const ActionIcon = ({ type }: { type: string }) => {
        switch (type) {
            case "calendar": return <Calendar className="w-3 h-3" />;
            case "email": return <Mail className="w-3 h-3" />;
            case "task": return <CheckSquare className="w-3 h-3" />;
            case "focus": return <Zap className="w-3 h-3" />;
            default: return null;
        }
    };

    return (
        <div className={clsx("flex gap-4 max-w-3xl mx-auto w-full", isSystem ? "justify-start" : "justify-end")}>
            {/* Avatar */}
            {isSystem && (
                <div className="w-8 h-8 rounded-full bg-surface border border-white/10 flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-primary" />
                </div>
            )}

            <div className={clsx("flex flex-col gap-1 max-w-[80%]", isSystem ? "items-start" : "items-end")}>
                {/* Bubble */}
                <div
                    className={clsx(
                        "px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed",
                        isSystem
                            ? "bg-surface border border-white/5 text-gray-200 rounded-tl-sm"
                            : "bg-primary text-white rounded-tr-sm"
                    )}
                >
                    {message.content}
                </div>

                {/* Metadata (System Only) */}
                {isSystem && (
                    <div className="flex items-center gap-3 px-1 mt-1">
                        {/* Context Actions */}
                        {message.actions?.map((action, i) => (
                            <div key={i} className="flex items-center gap-1.5 text-xs text-secondary bg-white/5 px-2 py-0.5 rounded-full border border-white/5">
                                <ActionIcon type={action.type} />
                                <span>{action.label}</span>
                            </div>
                        ))}

                        {/* XP Awarded */}
                        {message.xpAwarded && Object.entries(message.xpAwarded).map(([role, amount]) => (
                            <span key={role} className="text-xs font-mono text-integrator opacity-80">
                                +{amount} {role} Active
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {!isSystem && (
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 text-secondary" />
                </div>
            )}
        </div>
    );
};
