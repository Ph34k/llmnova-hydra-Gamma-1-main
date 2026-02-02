"use client";

import { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu, Sparkles, Download, User, Bot, Wrench, Paperclip, File as FileIcon } from 'lucide-react';

interface NeuralInterfaceProps {
    ws: WebSocket | null;
}

const roleIcons: { [key: string]: React.ReactNode } = {
  user: <User size={14} />,
  assistant: <Bot size={14} />,
  'final-answer': <Bot size={14} />,
  'tool-call': <Wrench size={14} />,
  'tool-result': <Wrench size={14} />,
  'file-upload': <FileIcon size={14} />,
};

const roleStyles: { [key: string]: string } = {
  user: 'border-blue-500/50',
  assistant: 'border-cyan-500/50',
  'final-answer': 'border-green-500/50',
  'tool-call': 'border-yellow-500/50',
  'tool-result': 'border-purple-500/50',
  'file-upload': 'border-gray-500/50',
};

export default function NeuralInterface({ ws }: NeuralInterfaceProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [status, setStatus] = useState('disconnected');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!ws) return;

    const handleOpen = () => setStatus('ready');
    const handleClose = () => setStatus('disconnected');

    const handleMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      console.log("NI Received:", data);

      if (data.type === 'session_info') {
        setSessionId(data.sessionId);
      } else if (data.type === 'message') {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
      } else if (data.type === 'final-answer') {
        setMessages(prev => [...prev, { role: 'final-answer', content: data.content }]);
      } else if (data.type === 'tool_call') {
         setMessages(prev => [...prev, { role: 'tool-call', content: `Executing ${data.tool}...`, details: data.args }]);
      } else if (data.type === 'tool_result') {
         setMessages(prev => [...prev, { role: 'tool-result', content: `Result from ${data.tool}`, details: data.result }]);
      } else if (data.type === 'status') {
        setStatus(data.content);
      }
    };

    ws.addEventListener('open', handleOpen);
    ws.addEventListener('close', handleClose);
    ws.addEventListener('message', handleMessage);

    return () => {
      ws.removeEventListener('open', handleOpen);
      ws.removeEventListener('close', handleClose);
      ws.removeEventListener('message', handleMessage);
    };
  }, [ws]);

  const sendMessage = () => {
    if (!input.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    ws.send(JSON.stringify({ message: input }));
    setInput('');
  };

  const handleDownloadPdf = async () => {
    if (!sessionId) return;
    try {
      const response = await fetch(`http://localhost:8000/api/report/${sessionId}/pdf`);
      if (!response.ok) throw new Error('Failed to download PDF');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `relatorio_${sessionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("PDF Download Error:", error);
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !sessionId) return;

    setMessages(prev => [...prev, { role: 'file-upload', content: `Uploading file: ${file.name}` }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/api/files/upload/${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('File upload failed');
      
      const result = await response.json();
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.role === 'file-upload') {
            lastMsg.content = `File uploaded: ${result.filename}`;
        }
        return newMessages;
      });
       // Inform the agent by sending a message
      ws?.send(JSON.stringify({ message: `The user has uploaded the file: ${file.name}. You can now use your file system tools to read it.` }));

    } catch (error) {
      console.error("File Upload Error:", error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg.role === 'file-upload') {
            lastMsg.content = `Failed to upload file: ${file.name}`;
        }
        return newMessages;
      });
    }
  };

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-200 font-sans selection:bg-cyan-500/30">
      {/* Sidebar */}
      <div className="w-80 border-r border-neutral-800 p-4 hidden md:flex flex-col gap-4">
        <div className="flex items-center gap-2 text-cyan-400 font-bold tracking-wider mb-6">
          <Cpu className="w-6 h-6" />
          <span>GAMMA ENGINE</span>
        </div>
        <div className="bg-neutral-900/50 p-4 rounded-lg border border-neutral-800">
          <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-2">System Status</h3>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status === 'ready' ? 'bg-green-500' : status === 'disconnected' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'}`} />
            <span className="text-sm capitalize">{status.replace('_', ' ')}</span>
          </div>
        </div>
        <div className="flex-1 overflow-auto pr-2 space-y-2">
            <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-2">Working Memory</h3>
            {messages.map((msg, i) => (
                <div key={`mem-${i}`} className={`p-2 rounded-md border text-xs ${roleStyles[msg.role] || 'border-neutral-700'}`}>
                    <div className="flex items-center gap-2 text-neutral-400">
                        {roleIcons[msg.role] || <Bot size={14} />}
                        <span className="font-semibold capitalize">{msg.role.replace(/[-_]/g, ' ')}</span>
                    </div>
                    <p className="text-neutral-500 mt-1 truncate">{msg.content}</p>
                </div>
            ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-neutral-600">
              <Sparkles className="w-12 h-12 mb-4 text-neutral-800" />
              <p className="text-lg">How can Gamma assist you today?</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role !== 'user' && (
                <div className={`w-8 h-8 rounded flex items-center justify-center shrink-0 ${
                  msg.role === 'assistant' || msg.role === 'final-answer' ? 'bg-cyan-900/50 text-cyan-400' 
                  : msg.role === 'file-upload' ? 'bg-gray-700 text-gray-300'
                  : 'bg-neutral-800 text-neutral-400'
                }`}>
                  { msg.role === 'file-upload' ? <FileIcon size={16} /> : <Sparkles size={16} /> }
                </div>
              )}

              <div className={`max-w-2xl p-4 rounded-2xl ${
                msg.role === 'user'
                  ? 'bg-neutral-100 text-neutral-900 rounded-tr-sm'
                  : msg.role === 'tool-call' || msg.role === 'tool-result'
                    ? 'bg-neutral-900 border border-neutral-800 font-mono text-sm w-full'
                    : msg.role === 'file-upload'
                    ? 'bg-neutral-800/80 italic text-neutral-400 w-full'
                    : 'bg-neutral-900/30 border border-neutral-800/50 rounded-tl-sm'
              }`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.details && (
                  <pre className="mt-2 p-2 bg-black/50 rounded overflow-x-auto text-xs text-neutral-500">
                    {JSON.stringify(msg.details, null, 2)}
                  </pre>
                )}
                {msg.role === 'final-answer' && (
                  <div className="mt-4 pt-4 border-t border-neutral-800">
                    <button onClick={handleDownloadPdf} className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                      <Download size={14} />
                      Baixar Relatório em PDF
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6">
          <div className="relative bg-neutral-900 rounded-2xl border border-neutral-800 shadow-2xl focus-within:border-cyan-500/50 focus-within:shadow-cyan-900/20 transition-all">
            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
              placeholder="Ask Gamma anything, or attach a file..."
              className="w-full bg-transparent p-4 pl-12 min-h-[60px] max-h-[200px] outline-none resize-none text-neutral-200 placeholder:text-neutral-600"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="absolute bottom-3 left-3 p-2 bg-neutral-800 hover:bg-cyan-600 hover:text-white rounded-xl text-neutral-400 transition-colors"
            >
              <Paperclip size={18} />
            </button>
            <button
              onClick={sendMessage}
              disabled={status !== 'ready'}
              className="absolute bottom-3 right-3 p-2 bg-neutral-800 hover:bg-cyan-600 hover:text-white rounded-xl text-neutral-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="text-center mt-2">
            <p className="text-xs text-neutral-600">Gamma Engine v1.4 • Autonomous AI Architect</p>
          </div>
        </div>
      </div>
    </div>
  );
}
