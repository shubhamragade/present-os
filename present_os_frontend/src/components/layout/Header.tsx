import { usePresentOS } from '../../store/usePresentOS';
import { PAEIIcon } from '../features/PAEIIcon';
import { NotificationBell } from '../features/NotificationBell';
import { Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';

export const Header = () => {
    const { xp, currentRole } = usePresentOS();
    const [energy, setEnergy] = useState({ recovery: 0, message: '', emoji: '🔋', level: 'medium' });

    useEffect(() => {
        const fetchEnergy = async () => {
            try {
                const res = await fetch('/api/energy');
                const data = await res.json();
                setEnergy(data);
            } catch (err) {
                console.error('Energy fetch failed:', err);
            }
        };

        fetchEnergy();
        const interval = setInterval(fetchEnergy, 30000); // Update every 30s
        return () => clearInterval(interval);
    }, []);

    return (
        <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-surface/50 backdrop-blur-md sticky top-0 z-10 w-full">
            {/* LEFT: Logo */}
            <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                <span className="font-bold tracking-tight text-lg">PresentOS</span>
            </div>

            {/* CENTER: Role Indicator */}
            <div className="flex items-center gap-4">
                <PAEIIcon role="P" isActive={currentRole === "P"} size="sm" />
                <PAEIIcon role="A" isActive={currentRole === "A"} size="sm" />
                <PAEIIcon role="E" isActive={currentRole === "E"} size="sm" />
                <PAEIIcon role="I" isActive={currentRole === "I"} size="sm" />
            </div>

            {/* RIGHT: Energy + Notification Bell + XP Stats */}
            <div className="flex items-center gap-6 text-sm font-medium text-secondary">
                {/* Energy Indicator */}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${energy.level === 'high' ? 'bg-green-500/10 text-green-400' :
                    energy.level === 'low' ? 'bg-red-500/10 text-red-400' :
                        'bg-yellow-500/10 text-yellow-400'
                    }`}>
                    <span className="text-base">{energy.emoji}</span>
                    <span className="font-semibold">{energy.recovery}%</span>
                    <span className="text-xs opacity-70">{energy.message}</span>
                </div>

                {/* Notification Bell */}
                <NotificationBell />

                {/* XP Stats */}
                <div className="flex gap-4">
                    <span className="text-producer">P: {xp.P}</span>
                    <span className="text-admin">A: {xp.A}</span>
                    <span className="text-entrepreneur">E: {xp.E}</span>
                    <span className="text-integrator">I: {xp.I}</span>
                </div>
            </div>
        </header>
    );
};
