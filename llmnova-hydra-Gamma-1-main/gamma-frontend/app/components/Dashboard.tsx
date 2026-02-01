"use client";

import { useEffect, useState } from 'react';
import { Activity, Server, Calendar, Trash2, Pause, Play, Power } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const StatCard = ({ title, value, sub, icon: Icon, color }: any) => (
    <div className="bg-neutral-900 border border-neutral-800 p-4 rounded-xl flex items-start justify-between">
        <div>
            <h3 className="text-neutral-500 text-xs font-bold uppercase tracking-wider mb-1">{title}</h3>
            <div className="text-2xl font-mono text-white">{value}</div>
            <div className="text-neutral-600 text-xs mt-1">{sub}</div>
        </div>
        <div className={`p-2 rounded-lg bg-neutral-800 ${color}`}>
            <Icon size={20} />
        </div>
    </div>
);

export default function Dashboard() {
    const [system, setSystem] = useState<any>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [servers, setServers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [sysRes, jobRes, srvRes] = await Promise.all([
                fetch(`${API_URL}/api/system/status`),
                fetch(`${API_URL}/api/scheduler/jobs`),
                fetch(`${API_URL}/api/webdev/servers`)
            ]);

            if (sysRes.ok) setSystem(await sysRes.json());
            if (jobRes.ok) setJobs(await jobRes.json());
            if (srvRes.ok) setServers(await srvRes.json());
        } catch (e) {
            console.error("Dashboard fetch error", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleJobAction = async (id: string, action: 'pause' | 'resume' | 'delete') => {
        try {
            if (action === 'delete') {
                await fetch(`${API_URL}/api/scheduler/delete/${id}`, { method: 'DELETE' });
            } else {
                await fetch(`${API_URL}/api/scheduler/${action}/${id}`, { method: 'POST' });
            }
            fetchData();
        } catch (e) {
            console.error(e);
        }
    };

    const handleStopServer = async (port: number) => {
        try {
            await fetch(`${API_URL}/api/webdev/stop/${port}`, { method: 'POST' });
            fetchData();
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="h-full w-full bg-neutral-950 p-8 overflow-y-auto">
            <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <Activity className="text-cyan-500" /> System Dashboard
            </h1>

            {/* System Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <StatCard
                    title="CPU Usage"
                    value={`${system?.cpu_percent || 0}%`}
                    sub="System Total"
                    icon={Activity}
                    color="text-red-500"
                />
                <StatCard
                    title="Memory Usage"
                    value={`${system?.memory_percent || 0}%`}
                    sub="RAM Allocation"
                    icon={Server}
                    color="text-blue-500"
                />
                <StatCard
                    title="Active Jobs"
                    value={jobs.length}
                    sub="Scheduled Tasks"
                    icon={Calendar}
                    color="text-green-500"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Scheduler Widget */}
                <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Calendar size={18} className="text-purple-500" /> Scheduled Jobs
                    </h2>
                    {jobs.length === 0 ? (
                        <p className="text-neutral-500 italic text-sm">No active jobs.</p>
                    ) : (
                        <div className="space-y-3">
                            {jobs.map((job) => (
                                <div key={job.id} className="bg-neutral-900 p-3 rounded border border-neutral-800 flex items-center justify-between">
                                    <div>
                                        <div className="font-mono text-sm text-cyan-400">{job.func_name}</div>
                                        <div className="text-xs text-neutral-500">Next run: {new Date(job.next_run_time).toLocaleTimeString()}</div>
                                        <div className="text-[10px] text-neutral-600 uppercase mt-1 bg-neutral-800 inline-block px-1 rounded">{job.trigger_type}</div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => handleJobAction(job.id, 'delete')} className="p-2 hover:bg-red-900/50 text-neutral-500 hover:text-red-500 rounded"><Trash2 size={14} /></button>
                                        {/* Pause/Resume logic requires job state tracking which we simplified, adding generic buttons */}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Active Servers Widget */}
                <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Server size={18} className="text-green-500" /> Active Dev Servers
                    </h2>
                    {servers.length === 0 ? (
                        <p className="text-neutral-500 italic text-sm">No servers running.</p>
                    ) : (
                        <div className="space-y-3">
                            {servers.map((srv) => (
                                <div key={srv.port} className="bg-neutral-900 p-3 rounded border border-neutral-800 flex items-center justify-between">
                                    <div>
                                        <div className="font-mono text-sm text-green-400">Port {srv.port}</div>
                                        <div className="text-xs text-neutral-500">PID: {srv.pid}</div>
                                        <div className="text-xs text-neutral-500 truncate max-w-[200px]">{srv.command}</div>
                                    </div>
                                    <button
                                        onClick={() => handleStopServer(srv.port)}
                                        className="p-2 hover:bg-red-900/50 text-neutral-500 hover:text-red-500 rounded flex items-center gap-1 text-xs"
                                    >
                                        <Power size={14} /> Stop
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
