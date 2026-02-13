"use client";

import { useState, useRef, useEffect } from 'react';
import { Terminal as TerminalIcon, Send } from 'lucide-react';
import { useGamma } from '../context/GammaContext';

export default function Terminal() {
    const { ws, sessionId } = useGamma();
    const [history, setHistory] = useState<string[]>([]);
    const [input, setInput] = useState('');
    const outputRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom
    useEffect(() => {
        if (outputRef.current) {
            outputRef.current.scrollTop = outputRef.current.scrollHeight;
        }
    }, [history]);

    // Handle tool results from WS to display as "terminal output"
    useEffect(() => {
        if (!ws) return;

        const handleMsg = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'tool_call' && data.tool === 'run_bash') {
                    const args = JSON.parse(data.args);
                    setHistory(prev => [...prev, `$ ${args.command}`]);
                } else if (data.type === 'tool_result' && data.tool === 'run_bash') {
                    setHistory(prev => [...prev, data.result]);
                }
            } catch (e) {}
        };

        ws.addEventListener('message', handleMsg);
        return () => ws.removeEventListener('message', handleMsg);
    }, [ws]);

    const handleExecute = () => {
        if (!input.trim() || !ws) return;

        // We cheat a bit: we send a natural language request that forces the agent to run bash.
        // Or better: we implement a direct execution mode if the backend supported it.
        // For now, let's just append to local history as "User" and send to agent.
        // setHistory(prev => [...prev, `$ ${input}`]);

        const message = `Run the following bash command: ${input}`;
        ws.send(JSON.stringify({ message }));

        setInput('');
    };

    return (
        <div className="h-full w-full bg-neutral-950 p-6 flex flex-col font-mono">
            <div className="flex items-center gap-2 mb-4 text-neutral-400">
                <TerminalIcon size={18} />
                <span className="text-sm font-bold uppercase">System Terminal</span>
            </div>

            <div
                ref={outputRef}
                className="flex-1 bg-black border border-neutral-800 rounded-lg p-4 overflow-y-auto mb-4 text-sm"
            >
                {history.length === 0 && <div className="text-neutral-600 italic">No terminal activity yet...</div>}
                {history.map((line, i) => (
                    <div key={i} className={`whitespace-pre-wrap mb-1 ${line.startsWith('$') ? 'text-green-400 font-bold' : 'text-neutral-300'}`}>
                        {line}
                    </div>
                ))}
            </div>

            <div className="flex gap-2">
                <div className="flex-1 bg-neutral-900 border border-neutral-800 rounded-lg flex items-center px-4">
                    <span className="text-green-500 mr-2">$</span>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
                        className="bg-transparent border-none outline-none w-full text-white font-mono py-3"
                        placeholder="Enter bash command..."
                    />
                </div>
                <button
                    onClick={handleExecute}
                    className="bg-neutral-800 hover:bg-neutral-700 text-white p-3 rounded-lg border border-neutral-700"
                >
                    <Send size={18} />
                </button>
            </div>
            <p className="text-xs text-neutral-600 mt-2">
                Note: Commands are executed via the Agent's "run_bash" tool.
            </p>
        </div>
    );
}
