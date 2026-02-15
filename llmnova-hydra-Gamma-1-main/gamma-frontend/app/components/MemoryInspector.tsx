"use client";

import { useState } from 'react';
import { Database, Search } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function MemoryInspector() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/brain/memory/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, limit: 5 })
            });
            if (res.ok) {
                setResults(await res.json());
            }
        } catch (e) {
            console.error("Memory search error:", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-6 h-full flex flex-col">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Database size={18} className="text-blue-500" /> Long Term Memory
            </h2>

            <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search knowledge base..."
                    className="flex-1 bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
                <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded flex items-center justify-center disabled:opacity-50"
                >
                    <Search size={16} />
                </button>
            </form>

            <div className="flex-1 overflow-y-auto space-y-3 min-h-0">
                {results.length === 0 && !loading && (
                    <p className="text-neutral-500 italic text-sm text-center mt-4">No results found.</p>
                )}
                {results.map((item, idx) => (
                    <div key={idx} className="bg-neutral-900 border border-neutral-800 p-3 rounded hover:border-neutral-700 transition-colors">
                        <p className="text-sm text-neutral-300 mb-2 whitespace-pre-wrap">{item.content}</p>
                        <div className="flex justify-between items-center text-[10px] text-neutral-600 uppercase">
                            <span>Source: {item.source_uri || "Unknown"}</span>
                            {item.score && <span>Score: {item.score.toFixed(2)}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
