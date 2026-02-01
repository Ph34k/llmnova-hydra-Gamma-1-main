"use client";

import { useState } from 'react';
import { Settings, Save, AlertTriangle } from 'lucide-react';

export default function ConfigPage() {
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('gpt-4o');
    const [temperature, setTemperature] = useState(0.7);

    // Mock save
    const handleSave = () => {
        alert("Settings saved (Local Only - Requires Backend Config Persistence to be fully effective)");
    };

    return (
        <div className="h-full w-full bg-neutral-950 p-8">
            <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <Settings className="text-gray-400" /> Configuration
            </h1>

            <div className="max-w-2xl bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-6">

                {/* Warning */}
                <div className="bg-yellow-900/20 border border-yellow-800/50 p-4 rounded-lg flex items-start gap-3">
                    <AlertTriangle className="text-yellow-500 shrink-0" size={20} />
                    <p className="text-sm text-yellow-200/80">
                        Some settings require restarting the backend service to take effect.
                        Currently, LLM configuration is loaded from <code>.env</code> file.
                    </p>
                </div>

                <div>
                    <label className="block text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2">LLM Provider Model</label>
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-neutral-300 focus:border-cyan-500 outline-none"
                    >
                        <option value="gpt-4o">GPT-4o (OpenAI)</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                        <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                    </select>
                </div>

                <div>
                    <label className="block text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2">OpenAI API Key (Override)</label>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk-..."
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-neutral-300 focus:border-cyan-500 outline-none font-mono"
                    />
                </div>

                <div>
                     <label className="block text-xs font-bold text-neutral-500 uppercase tracking-wider mb-2 flex justify-between">
                        <span>Temperature</span>
                        <span>{temperature}</span>
                     </label>
                     <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={temperature}
                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        className="w-full h-2 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                     />
                </div>

                <div className="pt-4 border-t border-neutral-800">
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                        <Save size={18} /> Save Configuration
                    </button>
                </div>
            </div>
        </div>
    );
}
