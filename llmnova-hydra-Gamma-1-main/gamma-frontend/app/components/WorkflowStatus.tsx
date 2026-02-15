"use client";

import { useEffect, useState } from 'react';
import { GitMerge, Circle, CheckCircle, XCircle, Clock } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function WorkflowStatus() {
    const [workflows, setWorkflows] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);

    const fetchWorkflows = async () => {
        try {
            const res = await fetch(`${API_URL}/api/brain/workflows`);
            if (res.ok) {
                setWorkflows(await res.json());
            }
        } catch (e) {
            console.error("Workflow fetch error:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWorkflows();
        const interval = setInterval(fetchWorkflows, 2000); // Poll every 2s
        return () => clearInterval(interval);
    }, []);

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle size={14} className="text-green-500" />;
            case 'failed': return <XCircle size={14} className="text-red-500" />;
            case 'running': return <Clock size={14} className="text-yellow-500 animate-spin" />;
            default: return <Circle size={14} className="text-neutral-600" />;
        }
    };

    return (
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6 h-full overflow-y-auto">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <GitMerge size={18} className="text-orange-500" /> Active Workflows
            </h2>

            {loading && Object.keys(workflows).length === 0 ? (
                <p className="text-neutral-500 text-sm">Loading workflows...</p>
            ) : Object.keys(workflows).length === 0 ? (
                <p className="text-neutral-500 italic text-sm">No active workflows.</p>
            ) : (
                <div className="space-y-4">
                    {Object.entries(workflows).map(([id, wf]) => (
                        <div key={id} className="bg-neutral-900 border border-neutral-800 rounded p-3">
                            <div className="flex justify-between items-center mb-2">
                                <div className="font-mono text-sm text-orange-300">{wf.name}</div>
                                <div className="text-xs px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 capitalize">{wf.status}</div>
                            </div>

                            <div className="flex gap-2 items-center flex-wrap">
                                {wf.steps.map((step: any) => (
                                    <div key={step.id} className="flex items-center gap-1 bg-neutral-950 px-2 py-1 rounded border border-neutral-800">
                                        {getStatusIcon(step.status)}
                                        <span className="text-xs text-neutral-400">{step.id}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
