import { usePresentOS } from '../../store/usePresentOS';
import { Target, CheckCircle2, Circle, Map as MapIcon } from 'lucide-react';
import clsx from 'clsx';
import { useEffect } from 'react';

export const Sidebar = () => {
    const { activeQuest, tasks, setTasks, setActiveQuest } = usePresentOS();

    useEffect(() => {
        const fetchLiveData = async () => {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                // Update tasks from backend
                if (data.updated_state?.tasks) {
                    setTasks(data.updated_state.tasks);
                }

                // Update active quest from backend
                if (data.updated_state?.active_quest) {
                    setActiveQuest(data.updated_state.active_quest);
                }
            } catch (err) {
                console.error('Failed to fetch live data:', err);
            }
        };

        fetchLiveData();
        const interval = setInterval(fetchLiveData, 60000); // Refresh every 60s
        return () => clearInterval(interval);
    }, [setTasks, setActiveQuest]);

    return (
        <aside className="w-80 border-l border-white/5 bg-surface/30 backdrop-blur-sm h-full flex flex-col p-6 gap-8 hidden lg:flex">

            {/* Active Quest */}
            {activeQuest && (
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-secondary uppercase tracking-wider">
                        <Target className="w-3 h-3" />
                        <span>Active Quest</span>
                    </div>

                    <div className="p-4 rounded-xl bg-gradient-to-br from-white/5 to-transparent border border-white/5">
                        <h3 className="font-semibold text-lg leading-tight mb-1">{activeQuest.name}</h3>
                        <div className="flex items-center justify-between text-xs text-secondary mt-3">
                            <span>Progress</span>
                            <span>{activeQuest.progress}%</span>
                        </div>
                        <div className="h-1 bg-white/10 rounded-full mt-1.5 overflow-hidden">
                            <div
                                className="h-full bg-primary rounded-full transition-all duration-500"
                                style={{ width: `${activeQuest.progress}%` }}
                            />
                        </div>
                        {activeQuest.purpose && (
                            <div className="flex items-center gap-1.5 mt-3 text-xs text-accent">
                                <MapIcon className="w-3 h-3" />
                                <span>{activeQuest.purpose}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Task List */}
            <div className="space-y-3 flex-1 overflow-hidden flex flex-col">
                <div className="flex items-center gap-2 text-xs font-bold text-secondary uppercase tracking-wider">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Upcoming Tasks ({tasks.length})</span>
                </div>

                <div className="flex-1 overflow-y-auto no-scrollbar space-y-2 pr-1">
                    {tasks.length === 0 ? (
                        <div className="text-center text-secondary text-sm py-8">
                            No upcoming tasks
                        </div>
                    ) : (
                        tasks.map(task => (
                            <div
                                key={task.id}
                                className="group flex gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/5 cursor-default"
                            >
                                <div className={clsx(
                                    "mt-0.5",
                                    task.status === "done" ? "text-green-500" : "text-secondary"
                                )}>
                                    {task.status === "done" ? <CheckCircle2 className="w-4 h-4" /> : <Circle className="w-4 h-4" />}
                                </div>
                                <div className="flex-1">
                                    <p className={clsx(
                                        "text-sm",
                                        task.status === "done" ? "text-secondary line-through" : "text-gray-200"
                                    )}>
                                        {task.title}
                                    </p>
                                    <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <span className="text-[10px] text-secondary bg-white/5 px-1.5 rounded">
                                            Notion
                                        </span>
                                        {task.due && (
                                            <span className="text-[10px] text-accent">
                                                Due: {new Date(task.due).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

        </aside>
    );
};
