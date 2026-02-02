"use client";

import { useState, useEffect } from 'react';
import { Folder, FileCode, ChevronRight, ChevronDown, RefreshCw } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  path: string;
}

export default function Workspace({ ws }: { ws: WebSocket | null }) {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("// Select a file to view content");

  // Simulate file fetch (In real app, fetch from backend)
  const fetchFiles = async () => {
    // This would call a backend API to list files
    // For demo, we might wait for WS updates
  };

  // Listen for file updates via WS
  useEffect(() => {
    if (!ws) return;

    const handleMsg = (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        if (data.type === 'file_update') {
            // Refresh file list or update content if selected
            console.log("File update received", data);
            // Quick hack: just assume data contains file info
        }
    };

    ws.addEventListener('message', handleMsg);
    return () => ws.removeEventListener('message', handleMsg);
  }, [ws]);

  return (
    <div className="flex h-full border-l border-neutral-800 bg-neutral-950">
      {/* File Tree */}
      <div className="w-64 bg-neutral-900/50 border-r border-neutral-800 flex flex-col">
        <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
            <span className="text-xs font-bold text-neutral-500 uppercase tracking-widest">Workspace</span>
            <RefreshCw size={14} className="text-neutral-600 cursor-pointer hover:text-cyan-400" />
        </div>
        <div className="p-2 overflow-y-auto flex-1 font-mono text-sm text-neutral-400">
           {/* Mock Tree */}
           <div className="pl-2 py-1 hover:bg-neutral-800 cursor-pointer flex items-center gap-2">
              <Folder size={14} className="text-cyan-600" /> <span>src</span>
           </div>
           <div className="pl-6 py-1 hover:bg-neutral-800 cursor-pointer flex items-center gap-2 text-neutral-300">
              <FileCode size={14} className="text-yellow-600" /> <span>main.py</span>
           </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        <div className="h-10 border-b border-neutral-800 flex items-center px-4 bg-neutral-900">
            <span className="text-sm text-neutral-300">{selectedFile || "No file selected"}</span>
        </div>
        <div className="flex-1">
             <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={fileContent}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, monospace',
                    padding: { top: 20 }
                }}
             />
        </div>
      </div>
    </div>
  );
}
