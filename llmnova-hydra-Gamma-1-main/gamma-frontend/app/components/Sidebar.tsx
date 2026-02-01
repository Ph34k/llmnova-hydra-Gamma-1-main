"use client";

import { useState } from 'react';
import { MessageSquare, Code, Layout, Activity, Terminal as TerminalIcon, Settings } from 'lucide-react';

interface SidebarProps {
    activeView: string;
    setActiveView: (view: string) => void;
}

const SidebarItem = ({ icon: Icon, label, id, active, onClick }: any) => (
    <button
        onClick={() => onClick(id)}
        className={`w-full p-3 flex flex-col items-center gap-1 transition-colors ${
            active ? 'text-cyan-400 bg-neutral-900 border-l-2 border-cyan-400' : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900/50'
        }`}
    >
        <Icon size={20} />
        <span className="text-[10px] uppercase font-bold tracking-wider">{label}</span>
    </button>
);

export default function Sidebar({ activeView, setActiveView }: SidebarProps) {
    return (
        <div className="w-16 h-full bg-neutral-950 border-r border-neutral-800 flex flex-col items-center py-4">
             <div className="mb-6 text-cyan-500 font-bold text-xl">Γ</div>

             <div className="flex-1 w-full space-y-2">
                 <SidebarItem icon={MessageSquare} label="Chat" id="chat" active={activeView === 'chat'} onClick={setActiveView} />
                 <SidebarItem icon={Code} label="Code" id="code" active={activeView === 'code'} onClick={setActiveView} />
                 <SidebarItem icon={Layout} label="Preview" id="preview" active={activeView === 'preview'} onClick={setActiveView} />
                 <div className="h-px bg-neutral-800 w-1/2 mx-auto my-2" />
                 <SidebarItem icon={Activity} label="Dash" id="dashboard" active={activeView === 'dashboard'} onClick={setActiveView} />
                 <SidebarItem icon={TerminalIcon} label="Term" id="terminal" active={activeView === 'terminal'} onClick={setActiveView} />
             </div>

             <div className="w-full">
                <SidebarItem icon={Settings} label="Config" id="settings" active={activeView === 'settings'} onClick={setActiveView} />
             </div>
        </div>
    );
}
