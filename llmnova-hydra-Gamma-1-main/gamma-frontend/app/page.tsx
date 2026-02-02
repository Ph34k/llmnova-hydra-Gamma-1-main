"use client";

import { useState } from 'react';
import { GammaProvider, useGamma } from './context/GammaContext';
import Sidebar from './components/Sidebar';
import NeuralInterface from './components/NeuralInterface';
import Workspace from './components/Workspace';
import PreviewPane from './components/PreviewPane';
import Dashboard from './components/Dashboard';
import Terminal from './components/Terminal';
import SettingsPage from './components/Settings';

const MainLayout = () => {
    const { ws, sessionId, previewUrl, setPreviewUrl } = useGamma();
    const [activeView, setActiveView] = useState('chat'); // chat, code, preview, dashboard, terminal, settings
    const [secondaryView, setSecondaryView] = useState<string | null>('code'); // Split view support

    // Helper to determine layout
    const renderContent = () => {
        if (activeView === 'chat') {
            return (
                <div className="flex h-full w-full">
                    <div className={`${secondaryView ? 'w-1/3' : 'w-full'} border-r border-neutral-800`}>
                        <NeuralInterface ws={ws} sessionId={sessionId} />
                    </div>
                    {secondaryView && (
                        <div className="flex-1">
                             {secondaryView === 'code' && <Workspace ws={ws} sessionId={sessionId} />}
                             {secondaryView === 'preview' && <PreviewPane url={previewUrl} setUrl={setPreviewUrl} />}
                        </div>
                    )}
                </div>
            );
        }
        if (activeView === 'code') return <Workspace ws={ws} sessionId={sessionId} />;
        if (activeView === 'preview') return <PreviewPane url={previewUrl} setUrl={setPreviewUrl} />;
        if (activeView === 'dashboard') return <Dashboard />;
        if (activeView === 'terminal') return <Terminal />;
        if (activeView === 'settings') return <SettingsPage />;

        return null;
    };

    return (
        <main className="flex h-screen w-screen overflow-hidden bg-black text-white">
            <Sidebar activeView={activeView} setActiveView={(view) => {
                if (view === activeView) return;
                // Smart switching logic
                if (view === 'chat') setSecondaryView('code'); // Default split for chat
                else setSecondaryView(null);
                setActiveView(view);
            }} />
            <div className="flex-1 h-full relative">
                {renderContent()}
            </div>
        </main>
    );
};

export default function Home() {
  return (
    <GammaProvider>
        <MainLayout />
    </GammaProvider>
  );
}
