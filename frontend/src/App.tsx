import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  MessageSquare, Plus, Search, Settings, Send,
  Database, Zap, BrainCircuit, PanelRight, ChevronLeft,
  Copy, ThumbsUp, ThumbsDown, Monitor, Hash,
  ChevronRight, Circle, Server, FolderPlus, AlertTriangle, Trash2
} from 'lucide-react';
import { api, Session, Fact, StatusResponse, SourceEntry } from './api';

// --- Types de UI ---
type MessageSource = 'memory' | 'reasoning' | 'no_model' | 'user';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source?: MessageSource;
  conversationId?: number | null;
  timestamp: string;
  feedback?: 'up' | 'down' | null;
}

function mapSource(apiSource: string): MessageSource {
  if (apiSource === 'memoria_local') return 'memory';
  if (apiSource === 'modelo_ia') return 'reasoning';
  return 'no_model';
}

function formatTime(iso: string): string {
  try {
    // El backend guarda fechas como 'YYYY-MM-DD HH:MM:SS' (hora local del server, que es local del usuario).
    const d = new Date(iso.replace(' ', 'T'));
    if (isNaN(d.getTime())) return '';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [isLeftPanelOpen, setIsLeftPanelOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [sources, setSources] = useState<SourceEntry[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- Carga inicial ---
  useEffect(() => {
    (async () => {
      try {
        const existing = await api.listSessions();
        let sessionList = existing;
        if (sessionList.length === 0) {
          const created = await api.createSession('Nueva charla');
          sessionList = [created];
        }
        setSessions(sessionList);
        setActiveSessionId(sessionList[0].id);
      } catch (err) {
        setLoadError('No se pudo conectar con el backend local. ¿Está corriendo el servidor?');
      }
      refreshStatus();
      refreshFacts();
      refreshSources();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Cargar mensajes cuando cambia la sesión activa ---
  useEffect(() => {
    if (activeSessionId === null) return;
    (async () => {
      try {
        const rows = await api.getMessages(activeSessionId);
        const msgs: Message[] = [];
        for (const row of rows) {
          msgs.push({
            id: `${row.id}-u`,
            role: 'user',
            content: row.user_input,
            timestamp: formatTime(row.created_at),
          });
          msgs.push({
            id: `${row.id}-a`,
            role: 'assistant',
            content: row.assistant_response,
            conversationId: row.id,
            timestamp: formatTime(row.created_at),
          });
        }
        setMessages(msgs);
      } catch {
        setLoadError('No se pudieron cargar los mensajes de esta charla.');
      }
    })();
  }, [activeSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await api.getStatus());
    } catch {
      /* el backend puede tardar un instante en levantar; se reintenta con el polling */
    }
  }, []);

  const refreshFacts = useCallback(async () => {
    try {
      setFacts(await api.listFacts());
    } catch {
      /* noop */
    }
  }, []);

  const refreshSources = useCallback(async () => {
    try {
      setSources(await api.listSources());
    } catch {
      /* noop */
    }
  }, []);

  // Refresca el estado del motor cada 10s (para reflejar si Ollama se prendió/apagó).
  useEffect(() => {
    const interval = setInterval(refreshStatus, 10000);
    return () => clearInterval(interval);
  }, [refreshStatus]);

  const handleNewChat = async () => {
    try {
      const created = await api.createSession('Nueva charla');
      setSessions(prev => [created, ...prev]);
      setActiveSessionId(created.id);
      setMessages([]);
    } catch {
      setLoadError('No se pudo crear una nueva charla.');
    }
  };

  const handleDeleteSession = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteSession(id);
      const remaining = sessions.filter(s => s.id !== id);
      setSessions(remaining);
      if (activeSessionId === id) {
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
        } else {
          const created = await api.createSession('Nueva charla');
          setSessions([created]);
          setActiveSessionId(created.id);
          setMessages([]);
        }
      }
    } catch {
      setLoadError('No se pudo borrar la charla.');
    }
  };

  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || activeSessionId === null || isSending) return;

    const userMsg: Message = {
      id: `local-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsSending(true);

    try {
      const result = await api.sendMessage(activeSessionId, content);
      const assistantMsg: Message = {
        id: `local-${Date.now()}-a`,
        role: 'assistant',
        content: result.answer,
        source: mapSource(result.source),
        conversationId: result.conversation_id,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, assistantMsg]);

      // Refrescar sesiones (por si esta era "Nueva charla" y quedó actualizada de orden), hechos y estado.
      setSessions(prev => {
        const touched = prev.find(s => s.id === activeSessionId);
        if (!touched) return prev;
        const rest = prev.filter(s => s.id !== activeSessionId);
        return [{ ...touched, updated_at: new Date().toISOString() }, ...rest];
      });
      refreshStatus();
      refreshFacts();
    } catch (err) {
      const errorMsg: Message = {
        id: `local-${Date.now()}-err`,
        role: 'assistant',
        content: 'No se pudo contactar al backend local. Verificá que el servidor esté corriendo.',
        source: 'no_model',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const handleFeedback = async (msg: Message, useful: boolean) => {
    if (!msg.conversationId) return;
    try {
      await api.sendFeedback(msg.conversationId, useful);
      setMessages(prev =>
        prev.map(m => (m.id === msg.id ? { ...m, feedback: useful ? 'up' : 'down' } : m))
      );
      refreshStatus();
    } catch {
      /* noop */
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard?.writeText(text).catch(() => {});
  };

  const handleAddSource = async () => {
    const path = window.prompt('Ruta de la carpeta a indexar (ej: C:\\\\Users\\\\vos\\\\Documentos\\\\notas):');
    if (!path || !path.trim()) return;
    try {
      const result = await api.addSource(path.trim());
      await refreshSources();
      if (result.files_indexed === 0) {
        window.alert(`No se encontraron archivos de texto (.txt/.md) para indexar en: ${result.path}`);
      }
    } catch {
      window.alert('No se pudo indexar esa ruta. Verificá que exista y sea accesible.');
    }
  };

  const handleDeleteSource = async (id: number) => {
    try {
      await api.deleteSource(id);
      await refreshSources();
    } catch {
      /* noop */
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderContent = (content: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);
    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const fenced = part.replace(/^```(\w*)\n?/, '').replace(/```$/, '');
        const langMatch = part.match(/^```(\w+)/);
        const lang = langMatch ? langMatch[1] : 'texto';
        return (
          <div key={index} className="my-3 rounded-lg overflow-hidden border border-panel-border bg-[#0d0d0f]">
            <div className="flex justify-between items-center px-4 py-2 bg-panel border-b border-panel-border text-xs text-zinc-400 font-mono">
              <span>{lang}</span>
              <button
                className="flex items-center gap-1 hover:text-white transition-colors"
                onClick={() => handleCopy(fenced)}
              >
                <Copy size={12} /> Copiar
              </button>
            </div>
            <pre className="p-4 overflow-x-auto text-sm font-mono text-zinc-300">
              <code>{fenced}</code>
            </pre>
          </div>
        );
      }
      const boldParts = part.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={index}>
          {boldParts.map((bp, i) => {
            if (bp.startsWith('**') && bp.endsWith('**')) {
              return <strong key={i} className="font-semibold text-white">{bp.slice(2, -2)}</strong>;
            }
            return bp;
          })}
        </span>
      );
    });
  };

  const filteredSessions = sessions.filter(s =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const ollamaAvailable = status?.ollama.available ?? false;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground font-sans selection:bg-accent/30">

      {/* LEFT SIDEBAR - HISTORY */}
      <aside
        className={`${isLeftPanelOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full'}
        transition-all duration-300 ease-in-out flex flex-col border-r border-panel-border bg-panel shrink-0`}
      >
        <div className="p-3 flex items-center justify-between border-b border-panel-border">
          <button
            onClick={handleNewChat}
            className="flex-1 flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-sm font-medium py-2 px-3 rounded-md transition-colors mr-2"
          >
            <Plus size={16} /> Nueva charla
          </button>
          <button
            onClick={() => setIsLeftPanelOpen(false)}
            className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md transition-colors md:hidden"
          >
            <ChevronLeft size={16} />
          </button>
        </div>

        <div className="px-3 py-2">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-2.5 text-zinc-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar chats..."
              className="w-full bg-background border border-panel-border rounded-md py-1.5 pl-8 pr-3 text-sm focus:outline-none focus:border-zinc-600 transition-colors placeholder:text-zinc-600 text-zinc-300"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-6">
          <div>
            <h3 className="px-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Recientes</h3>
            <div className="space-y-0.5">
              {filteredSessions.map(item => (
                <button
                  key={item.id}
                  onClick={() => setActiveSessionId(item.id)}
                  className={`group w-full text-left px-2 py-2 rounded-md text-sm truncate flex items-center gap-2 transition-colors ${
                    item.id === activeSessionId
                      ? 'bg-zinc-800 text-white'
                      : 'hover:bg-zinc-800/50 text-zinc-300 hover:text-white'
                  }`}
                >
                  <MessageSquare size={14} className="text-zinc-500 shrink-0" />
                  <span className="truncate flex-1">{item.title}</span>
                  <span
                    role="button"
                    onClick={(e) => handleDeleteSession(item.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 transition-opacity shrink-0"
                    title="Borrar charla"
                  >
                    <Trash2 size={13} />
                  </span>
                </button>
              ))}
              {filteredSessions.length === 0 && (
                <p className="px-2 text-xs text-zinc-600">Sin resultados.</p>
              )}
            </div>
          </div>
        </div>

        <div className="p-3 border-t border-panel-border">
          <button className="w-full flex items-center gap-3 px-2 py-2 rounded-md hover:bg-zinc-800/50 text-sm text-zinc-300 transition-colors">
            <Settings size={16} /> Configuración Local
          </button>
        </div>
      </aside>

      {/* CENTER - CHAT PANEL */}
      <main className="flex-1 flex flex-col min-w-0 relative bg-background">

        {/* HEADER */}
        <header className="h-14 border-b border-panel-border bg-background/80 backdrop-blur-sm flex items-center justify-between px-4 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            {!isLeftPanelOpen && (
              <button
                onClick={() => setIsLeftPanelOpen(true)}
                className="p-1.5 text-zinc-400 hover:text-white hover:bg-panel rounded-md transition-colors"
                title="Mostrar historial"
              >
                <ChevronRight size={18} />
              </button>
            )}
            <h1 className="font-semibold text-zinc-200 flex items-center gap-2">
              OmniLocal-Core
              <span className="text-xs bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
                v{status?.engine.version ?? '0.1.0'}
              </span>
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div
              className="flex items-center gap-2 text-xs font-medium bg-panel px-2.5 py-1.5 rounded-full border border-panel-border"
              title={ollamaAvailable ? `Modelo: ${status?.ollama.model}` : 'Ollama no disponible: solo memoria'}
            >
              <Circle size={10} className={ollamaAvailable ? 'fill-ai text-ai' : 'fill-emerald-500 text-emerald-500'} />
              <span className={ollamaAvailable ? 'text-zinc-300' : 'text-emerald-400'}>
                {ollamaAvailable ? 'Modelo Activo' : 'Solo Memoria'}
              </span>
            </div>

            <button
              onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
              className={`p-1.5 rounded-md transition-colors ${isRightPanelOpen ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-panel'}`}
              title="Panel Cognitivo"
            >
              <PanelRight size={18} />
            </button>
          </div>
        </header>

        {loadError && (
          <div className="mx-4 mt-3 flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            <AlertTriangle size={14} /> {loadError}
          </div>
        )}

        {/* CHAT MESSAGES */}
        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 lg:px-12 scroll-smooth pb-32">
          <div className="max-w-3xl mx-auto space-y-8">
            {messages.length === 0 && !loadError && (
              <div className="text-center text-zinc-600 text-sm mt-20">
                Escribí algo para empezar. Si ya le enseñaste algo con "Hechos", te va a responder
                sin usar el modelo de IA.
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded bg-panel border border-panel-border flex items-center justify-center shrink-0 mt-1">
                    <Monitor size={16} className="text-zinc-400" />
                  </div>
                )}

                <div className={`group flex flex-col gap-1 max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-zinc-800 text-zinc-100 rounded-br-sm'
                        : 'bg-transparent text-zinc-300 text-[15px] leading-relaxed'
                    }`}
                  >
                    {renderContent(msg.content)}
                  </div>

                  <div className={`flex items-center gap-3 text-xs text-zinc-500 mt-1 px-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <span>{msg.timestamp}</span>

                    {msg.role === 'assistant' && msg.source === 'memory' && (
                      <span className="flex items-center gap-1 text-emerald-400/80 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">
                        <Database size={10} /> Recuperado de memoria
                      </span>
                    )}
                    {msg.role === 'assistant' && msg.source === 'reasoning' && (
                      <span className="flex items-center gap-1 text-ai/80 bg-ai/10 px-1.5 py-0.5 rounded border border-ai/20">
                        <BrainCircuit size={10} /> Generado por el modelo
                      </span>
                    )}
                    {msg.role === 'assistant' && msg.source === 'no_model' && (
                      <span className="flex items-center gap-1 text-amber-400/80 bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">
                        <AlertTriangle size={10} /> Sin modelo disponible
                      </span>
                    )}

                    {msg.role === 'assistant' && (
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <button onClick={() => handleCopy(msg.content)} className="hover:text-white transition-colors" title="Copiar">
                          <Copy size={14} />
                        </button>
                        {msg.conversationId && (
                          <>
                            <button
                              onClick={() => handleFeedback(msg, true)}
                              className={`transition-colors ${msg.feedback === 'up' ? 'text-emerald-400' : 'hover:text-emerald-400'}`}
                              title="Útil"
                            >
                              <ThumbsUp size={14} />
                            </button>
                            <button
                              onClick={() => handleFeedback(msg, false)}
                              className={`transition-colors ${msg.feedback === 'down' ? 'text-red-400' : 'hover:text-red-400'}`}
                              title="No útil"
                            >
                              <ThumbsDown size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {isSending && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 rounded bg-panel border border-panel-border flex items-center justify-center shrink-0 mt-1">
                  <Monitor size={16} className="text-zinc-400" />
                </div>
                <div className="px-4 py-3 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* INPUT AREA */}
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background to-transparent pt-10">
          <div className="max-w-3xl mx-auto relative group">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe un mensaje al motor local..."
              className="w-full bg-panel border border-panel-border focus:border-zinc-600 rounded-xl pl-4 pr-12 py-3.5 text-[15px] resize-none focus:outline-none transition-colors shadow-lg placeholder:text-zinc-500"
              rows={1}
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isSending}
              className="absolute right-3 bottom-3 p-1.5 bg-white text-black rounded-lg disabled:opacity-30 disabled:bg-zinc-700 disabled:text-zinc-500 hover:bg-zinc-200 transition-colors flex items-center justify-center"
            >
              <Send size={16} />
            </button>
            <div className="text-center mt-2 text-[10px] text-zinc-500 font-medium">
              OmniLocal-Core procesa todo localmente. Tus datos no salen de tu red.
            </div>
          </div>
        </div>
      </main>

      {/* RIGHT SIDEBAR - CONTEXTO & MEMORIA */}
      <aside
        className={`${isRightPanelOpen ? 'w-72 border-l' : 'w-0 border-transparent'}
        transition-all duration-300 ease-in-out flex flex-col border-panel-border bg-[#0a0a0c] shrink-0 overflow-hidden`}
      >
        <div className="p-4 border-b border-panel-border bg-panel/30 whitespace-nowrap flex items-center gap-2">
          <BrainCircuit size={16} className="text-ai" />
          <h2 className="font-semibold text-sm">Contexto & Memoria</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6 min-w-[16rem]">

          {/* Hechos guardados */}
          <div>
            <h3 className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Zap size={12} /> Hechos Guardados
            </h3>
            <div className="space-y-2">
              {facts.length === 0 && (
                <p className="text-xs text-zinc-600">Todavía no le enseñaste nada explícito.</p>
              )}
              {facts.slice(0, 20).map(fact => (
                <div key={fact.id} className="bg-panel border border-panel-border rounded-lg p-2.5 text-xs hover:border-zinc-700 transition-colors group relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-1 h-full bg-emerald-500/20 group-hover:bg-emerald-500/50 transition-colors" />
                  <div className="font-mono text-zinc-500 mb-1">{fact.category} · {Math.round(fact.confidence * 100)}%</div>
                  <div className="text-zinc-300">{fact.detail}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Estado del motor */}
          <div>
            <h3 className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Server size={12} /> Estado del Motor
            </h3>
            <div className="bg-panel border border-panel-border rounded-lg p-3 space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-zinc-500">Modelo</span>
                <span className="font-mono text-zinc-300">{status?.ollama.model ?? '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">IA local</span>
                <span className={`font-mono ${ollamaAvailable ? 'text-emerald-400' : 'text-zinc-500'}`}>
                  {ollamaAvailable ? 'disponible' : 'no disponible'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Memorias guardadas</span>
                <span className="font-mono text-zinc-300">{status?.memory_count ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Feedback</span>
                <span className="font-mono text-zinc-300">
                  {status?.feedback.useful ?? 0} útil / {status?.feedback.not_useful ?? 0} no útil
                </span>
              </div>
            </div>
          </div>

          {/* Fuentes locales */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
                <Hash size={12} /> Fuentes Locales
              </h3>
              <button
                onClick={handleAddSource}
                className="text-zinc-500 hover:text-white transition-colors"
                title="Agregar carpeta local"
              >
                <FolderPlus size={14} />
              </button>
            </div>
            <div className="flex flex-col gap-1.5">
              {sources.length === 0 && (
                <p className="text-xs text-zinc-600">Sin fuentes registradas todavía.</p>
              )}
              {sources.map(src => (
                <div
                  key={src.id}
                  className="group flex items-center justify-between px-2 py-1 rounded bg-zinc-800 text-[10px] text-zinc-400 border border-zinc-700"
                  title={src.path}
                >
                  <span className="truncate">{src.path} ({src.file_count})</span>
                  <span
                    role="button"
                    onClick={() => handleDeleteSource(src.id)}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 transition-opacity shrink-0 ml-1"
                  >
                    <Trash2 size={11} />
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </aside>
    </div>
  );
}
