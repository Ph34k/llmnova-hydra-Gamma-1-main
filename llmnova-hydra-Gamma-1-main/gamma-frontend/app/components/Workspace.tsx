"use client";

import { useState, useEffect, useCallback } from 'react';
import { Folder, FileCode, ChevronRight, ChevronDown, RefreshCw, Save, Loader2 } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  path: string;
}

interface WorkspaceProps {
    ws: WebSocket | null;
    sessionId: string | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const FileTreeItem = ({ node, level, onSelect, expanded, toggleExpand }: any) => {
    const isExpanded = expanded.has(node.path);
    const isFile = node.type === 'file';

    return (
        <div>
            <div
                className={`py-1 hover:bg-neutral-800 cursor-pointer flex items-center gap-2 select-none ${isFile ? 'text-neutral-300' : 'text-neutral-400'}`}
                style={{ paddingLeft: `${level * 12 + 8}px` }}
                onClick={() => isFile ? onSelect(node) : toggleExpand(node.path)}
            >
                {!isFile && (
                    <span className="text-neutral-500">
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </span>
                )}
                {isFile ? <FileCode size={14} className="text-yellow-600" /> : <Folder size={14} className="text-cyan-600" />}
                <span className="truncate">{node.name}</span>
            </div>
            {!isFile && isExpanded && node.children && (
                <div>
                    {node.children.map((child: FileNode) => (
                        <FileTreeItem
                            key={child.path}
                            node={child}
                            level={level + 1}
                            onSelect={onSelect}
                            expanded={expanded}
                            toggleExpand={toggleExpand}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default function Workspace({ ws, sessionId }: WorkspaceProps) {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("// Select a file to view content");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchFiles = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
        const res = await fetch(`${API_URL}/api/files/list/${sessionId}`);
        if (res.ok) {
            const data = await res.json();
            setFiles(data);
        }
    } catch (e) {
        console.error("Failed to fetch files", e);
    } finally {
        setLoading(false);
    }
  }, [sessionId]);

  const fetchFileContent = async (path: string) => {
      if (!sessionId) return;
      try {
          const res = await fetch(`${API_URL}/api/files/read/${sessionId}?path=${encodeURIComponent(path)}`);
          if (res.ok) {
              const data = await res.json();
              setFileContent(data.content);
              setSelectedFile(path);
          }
      } catch (e) {
          console.error("Failed to read file", e);
      }
  };

  const saveFile = async () => {
      if (!sessionId || !selectedFile) return;
      setSaving(true);
      try {
          const res = await fetch(`${API_URL}/api/files/write/${sessionId}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ path: selectedFile, content: fileContent })
          });
          if (res.ok) {
              // Maybe show a toast?
              console.log("File saved successfully");
          }
      } catch (e) {
          console.error("Failed to save file", e);
      } finally {
          setSaving(false);
      }
  };

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  // Listen for file updates via WS
  useEffect(() => {
    if (!ws) return;

    const handleMsg = (event: MessageEvent) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'file_update') {
                fetchFiles();
            }
        } catch (e) {}
    };

    ws.addEventListener('message', handleMsg);
    return () => ws.removeEventListener('message', handleMsg);
  }, [ws, fetchFiles]);

  const toggleExpand = (path: string) => {
      const newExpanded = new Set(expandedFolders);
      if (newExpanded.has(path)) {
          newExpanded.delete(path);
      } else {
          newExpanded.add(path);
      }
      setExpandedFolders(newExpanded);
  };

  return (
    <div className="flex h-full border-l border-neutral-800 bg-neutral-950">
      {/* File Tree */}
      <div className="w-64 bg-neutral-900/50 border-r border-neutral-800 flex flex-col">
        <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
            <span className="text-xs font-bold text-neutral-500 uppercase tracking-widest">Workspace</span>
            <button onClick={fetchFiles} className="text-neutral-600 hover:text-cyan-400 transition-colors">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            </button>
        </div>
        <div className="py-2 overflow-y-auto flex-1 font-mono text-sm">
           {files.length === 0 && !loading && (
               <div className="p-4 text-neutral-600 italic text-xs">No files found.</div>
           )}
           {files.map(node => (
               <FileTreeItem
                    key={node.path}
                    node={node}
                    level={0}
                    onSelect={(n: FileNode) => fetchFileContent(n.path)}
                    expanded={expandedFolders}
                    toggleExpand={toggleExpand}
               />
           ))}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        <div className="h-10 border-b border-neutral-800 flex items-center justify-between px-4 bg-neutral-900">
            <span className="text-sm text-neutral-300 font-mono">{selectedFile || "No file selected"}</span>
            {selectedFile && (
                <button
                    onClick={saveFile}
                    disabled={saving}
                    className="flex items-center gap-2 text-xs bg-neutral-800 hover:bg-neutral-700 px-3 py-1 rounded text-neutral-300 transition-colors"
                >
                    {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                    Save
                </button>
            )}
        </div>
        <div className="flex-1 relative">
             <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                path={selectedFile || undefined}
                value={fileContent}
                onChange={(val) => setFileContent(val || "")}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, monospace',
                    padding: { top: 20 },
                    scrollBeyondLastLine: false,
                }}
             />
        </div>
      </div>
    </div>
  );
}
