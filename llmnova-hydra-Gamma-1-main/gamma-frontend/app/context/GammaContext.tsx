"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

interface GammaContextType {
    ws: WebSocket | null;
    sessionId: string | null;
    setSessionId: (id: string | null) => void;
    previewUrl: string;
    setPreviewUrl: (url: string) => void;
    systemStatus: any;
    setSystemStatus: (status: any) => void;
}

const GammaContext = createContext<GammaContextType | undefined>(undefined);

export const GammaProvider = ({ children }: { children: React.ReactNode }) => {
    const ws = useRef<WebSocket | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>("http://localhost:3000");
    const [systemStatus, setSystemStatus] = useState<any>(null);

    useEffect(() => {
        const apiKey = process.env.NEXT_PUBLIC_GAMMA_API_KEY;
        const baseUrl = process.env.NEXT_PUBLIC_API_URL
            ? `${process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws')}/ws/chat`
            : 'ws://localhost:8000/ws/chat';

        const wsUrl = `${baseUrl}?token=${apiKey || 'dev'}`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => console.log("WS Connected");
        ws.current.onclose = () => console.log("WS Closed");

        const handleMessage = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'session_info') {
                    setSessionId(data.sessionId);
                } else if (data.type === 'preview_update') {
                    setPreviewUrl(data.url);
                }
            } catch (e) {}
        };

        ws.current.addEventListener('message', handleMessage);

        return () => {
            ws.current?.close();
        };
    }, []);

    // Periodic system status poll
    useEffect(() => {
        const poll = setInterval(async () => {
            try {
                const res = await fetch('http://localhost:8000/api/system/status');
                if (res.ok) setSystemStatus(await res.json());
            } catch (e) {}
        }, 5000);
        return () => clearInterval(poll);
    }, []);

    return (
        <GammaContext.Provider value={{
            ws: ws.current,
            sessionId,
            setSessionId,
            previewUrl,
            setPreviewUrl,
            systemStatus,
            setSystemStatus
        }}>
            {children}
        </GammaContext.Provider>
    );
};

export const useGamma = () => {
    const context = useContext(GammaContext);
    if (!context) throw new Error("useGamma must be used within GammaProvider");
    return context;
};
