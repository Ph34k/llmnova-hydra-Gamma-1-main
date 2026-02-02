"use client";

import { useState, useRef, useEffect } from 'react';
import NeuralInterface from './components/NeuralInterface';
import Workspace from './components/Workspace';
import PreviewPane from './components/PreviewPane';
import { PanelRightOpen, PanelLeftOpen, Layout } from 'lucide-react';

export default function Home() {
  const ws = useRef<WebSocket | null>(null);
  const [layout, setLayout] = useState<'split' | 'full-chat' | 'preview'>('split');

  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GAMMA_API_KEY;
    if (!apiKey) {
      console.warn("NEXT_PUBLIC_GAMMA_API_KEY is not set. WebSocket connection will likely fail.");
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL
        ? `${process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws')}/ws/chat`
        : 'ws://localhost:8000/ws/chat';
    
    const wsUrl = `${baseUrl}?token=${apiKey || 'dev'}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => console.log("WebSocket connection established.");
    ws.current.onclose = () => console.log("WebSocket connection closed.");
    ws.current.onerror = (error) => console.error("WebSocket error:", error);

    return () => {
        ws.current?.close();
    };
  }, []);

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-black text-white relative">
        {/* Layout Controls */}
        <div className="absolute top-4 right-4 z-50 flex bg-neutral-900 rounded-lg border border-neutral-700 p-1">
            <button onClick={() => setLayout('full-chat')} className={`p-2 rounded ${layout === 'full-chat' ? 'bg-neutral-700' : 'hover:bg-neutral-800'}`}>
                <PanelLeftOpen size={16} />
            </button>
            <button onClick={() => setLayout('split')} className={`p-2 rounded ${layout === 'split' ? 'bg-neutral-700' : 'hover:bg-neutral-800'}`}>
                <Layout size={16} />
            </button>
            <button onClick={() => setLayout('preview')} className={`p-2 rounded ${layout === 'preview' ? 'bg-neutral-700' : 'hover:bg-neutral-800'}`}>
                <PanelRightOpen size={16} />
            </button>
        </div>

      {/* Left: Chat / Neural Interface */}
      <div className={`${layout === 'full-chat' ? 'w-full' : layout === 'split' ? 'w-1/3' : 'hidden'} h-full border-r border-neutral-800 transition-all duration-300`}>
        <NeuralInterface ws={ws.current} />
      </div>

      {/* Center: Workspace / Code */}
      <div className={`${layout === 'full-chat' ? 'hidden' : layout === 'split' ? 'w-1/3' : 'w-1/2'} h-full border-r border-neutral-800 transition-all duration-300`}>
        <Workspace ws={ws.current} />
      </div>

      {/* Right: Live Preview */}
      <div className={`${layout === 'preview' ? 'w-1/2' : 'w-1/3'} h-full transition-all duration-300`}>
        <PreviewPane />
      </div>
    </main>
  );
}
