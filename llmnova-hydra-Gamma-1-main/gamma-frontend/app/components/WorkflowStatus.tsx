"use client";

import { useEffect, useState } from 'react';
import { GitMerge, CheckCircle, Circle, AlertCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function WorkflowStatus() {
    const [workflows, setWorkflows] = useState<any>({});

    useEffect(() => {
        const fetchWorkflows = async () => {
            // Mocking fetching workflow state - in real impl, create endpoint
            // const res = await fetch(`${API_URL}/api/workflows/state`);
            // setWorkflows(await res.json());
        };
        // fetchWorkflows(); // Disabled until endpoint exists
    }, []);

    return (
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <GitMerge size={18} className="text-orange-500" /> Active Workflows
            </h2>
            <p className="text-neutral-500 italic text-sm">Workflow visualization pending backend endpoint.</p>
        </div>
    );
}
