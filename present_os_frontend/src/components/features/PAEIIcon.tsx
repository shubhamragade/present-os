import clsx from 'clsx';
import type { PAEIRole } from '../../types';

interface PAEIIconProps {
    role: PAEIRole;
    size?: "sm" | "md" | "lg";
    isActive?: boolean;
}

export const PAEIIcon = ({ role, size = "md", isActive = false }: PAEIIconProps) => {
    const sizeClasses = {
        sm: "w-6 h-6 text-xs",
        md: "w-8 h-8 text-sm",
        lg: "w-12 h-12 text-base"
    };

    const colors = {
        P: "bg-producer text-white",
        A: "bg-admin text-white",
        E: "bg-entrepreneur text-white",
        I: "bg-integrator text-black"
    };

    return (
        <div
            className={clsx(
                "rounded-full flex items-center justify-center font-bold shadow-lg transition-transform",
                sizeClasses[size],
                colors[role],
                isActive ? "scale-110 ring-2 ring-white" : "opacity-50 scale-90 grayscale"
            )}
        >
            {role}
        </div>
    );
};
