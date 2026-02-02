"use client";

import { useState } from 'react';
import { Maximize2, X } from 'lucide-react';

export default function PreviewPane({ url = "http://localhost:3000" }: { url?: string }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!isOpen) return null;

  return (
    <div className="flex flex-col h-full bg-white border-l border-neutral-800">
      <div className="h-10 border-b border-neutral-200 bg-neutral-100 flex items-center justify-between px-4">
        <div className="flex items-center gap-2 bg-white px-3 py-1 rounded border border-neutral-300 w-3/4">
           <div className="w-2 h-2 rounded-full bg-green-500" />
           <span className="text-xs text-neutral-600 font-mono truncate">{url}</span>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-neutral-500 hover:text-black">
           <X size={16} />
        </button>
      </div>
      <div className="flex-1 relative">
         <iframe
            src={url}
            className="w-full h-full border-none"
            title="Live Preview"
            sandbox="allow-scripts allow-same-origin"
         />
      </div>
    </div>
  );
}
