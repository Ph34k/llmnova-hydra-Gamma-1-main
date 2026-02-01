"use client";

import { useState, useEffect } from 'react';
import { Maximize2, X, RefreshCw } from 'lucide-react';

interface PreviewPaneProps {
    url: string;
    setUrl: (url: string) => void;
}

export default function PreviewPane({ url, setUrl }: PreviewPaneProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [inputUrl, setInputUrl] = useState(url);

  useEffect(() => {
      setInputUrl(url);
  }, [url]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
          setUrl(inputUrl);
      }
  };

  if (!isOpen) {
      return (
        <div className="flex h-full items-center justify-center bg-neutral-900 border-l border-neutral-800 text-neutral-500">
             <div className="text-center">
                <button onClick={() => setIsOpen(true)} className="p-2 hover:text-white bg-neutral-800 rounded-full">
                    <Maximize2 size={20} />
                </button>
                <p className="text-xs mt-2">Open Preview</p>
             </div>
        </div>
      );
  }

  return (
    <div className="flex flex-col h-full bg-white border-l border-neutral-800">
      <div className="h-10 border-b border-neutral-200 bg-neutral-100 flex items-center justify-between px-4">
        <div className="flex items-center gap-2 bg-white px-3 py-1 rounded border border-neutral-300 w-3/4 focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500 transition-all">
           <div className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
           <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              className="text-xs text-neutral-600 font-mono w-full outline-none bg-transparent"
           />
        </div>
        <div className="flex items-center gap-2">
            <button onClick={() => setUrl(inputUrl)} className="text-neutral-500 hover:text-black" title="Refresh/Go">
                <RefreshCw size={14} />
            </button>
            <button onClick={() => setIsOpen(false)} className="text-neutral-500 hover:text-black" title="Close Preview">
                <X size={16} />
            </button>
        </div>
      </div>
      <div className="flex-1 relative">
         <iframe
            key={url} // Force re-render on url change to ensure reload
            src={url}
            className="w-full h-full border-none"
            title="Live Preview"
            sandbox="allow-forms allow-modals allow-popups allow-presentation allow-same-origin allow-scripts"
         />
      </div>
    </div>
  );
}
