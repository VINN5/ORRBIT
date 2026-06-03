import { useState, useRef, useEffect } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const API_URL = 'http://localhost:8000'

const SUGGESTIONS = [
  { text: 'What is compound interest?', icon: '📈' },
  { text: 'Best way to invest $5,000?', icon: '💰' },
  { text: 'Explain quantum computing', icon: '⚛️' },
  { text: 'How does inflation affect savings?', icon: '🏦' },
]

function ThemeToggle({ theme, onToggle }) {
  return (
    <button onClick={onToggle} style={{
      display: 'flex', alignItems: 'center', gap: 8,
      background: 'var(--surface2)', border: '1px solid var(--border)',
      borderRadius: 20, padding: '6px 14px', cursor: 'pointer',
      fontFamily: '"DM Mono", monospace', fontSize: 11,
      color: 'var(--text-muted)', letterSpacing: '0.08em',
      transition: 'all 0.2s',
    }}>
      <span style={{ fontSize: 14 }}>{theme === 'dark' ? '☀️' : '🌙'}</span>
      {theme === 'dark' ? 'LIGHT' : 'DARK'}
    </button>
  )
}

function DomainBadge({ domain }) {
  const isFinance = domain === 'finance'
  return (
    <span style={{
      fontFamily: '"DM Mono", monospace',
      fontSize: '9px', fontWeight: 500,
      letterSpacing: '0.14em', textTransform: 'uppercase',
      padding: '3px 10px', borderRadius: '20px',
      background: isFinance ? 'var(--badge-finance-bg)' : 'var(--badge-general-bg)',
      color: isFinance ? 'var(--badge-finance-text)' : 'var(--badge-general-text)',
      border: `1px solid ${isFinance ? 'var(--badge-finance-border)' : 'var(--badge-general-border)'}`,
    }}>
      {isFinance ? '📊 Finance' : '🌐 General'}
    </span>
  )
}

function Message({ msg, index }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      gap: '8px',
      animation: `slideIn 0.35s cubic-bezier(0.34,1.56,0.64,1) both`,
    }}>
      {!isUser && msg.domain && <DomainBadge domain={msg.domain} />}
      <div style={{
        maxWidth: '75%', padding: '13px 18px',
        borderRadius: isUser ? '18px 18px 5px 18px' : '5px 18px 18px 18px',
        background: isUser ? 'var(--accent)' : 'var(--bubble-bg)',
        color: isUser ? '#ffffff' : 'var(--text)',
        fontFamily: '"Cabinet Grotesk", sans-serif',
        fontSize: '14.5px', lineHeight: '1.75',
        fontWeight: isUser ? 500 : 400,
        border: isUser ? 'none' : '1px solid var(--border)',
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        boxShadow: isUser ? 'var(--shadow-user)' : 'var(--shadow-bubble)',
      }}>
        {isUser ? msg.content : (
          <div
            className="markdown-body"
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(marked.parse(msg.content))
            }}
          />
        )}
      </div>
      <span style={{ fontFamily: '"DM Mono", monospace', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
        {isUser ? 'You' : 'Agent'} · {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '5px',
      padding: '13px 18px', background: 'var(--bubble-bg)',
      border: '1px solid var(--border)',
      borderRadius: '5px 18px 18px 18px', width: 'fit-content',
      boxShadow: 'var(--shadow-bubble)',
    }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'var(--accent)', display: 'inline-block',
          animation: `bounce 1.1s ${i * 0.18}s infinite`,
        }} />
      ))}
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [theme, setTheme] = useState('dark')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const isDark = theme === 'dark'

  const cssVars = isDark ? {
    '--bg': '#0c0c0f',
    '--surface': '#16161c',
    '--surface2': '#1e1e26',
    '--border': '#2a2a38',
    '--accent': '#7c6af7',
    '--accent-hover': '#6b58f0',
    '--text': '#e8e8f0',
    '--text-muted': '#5a5a72',
    '--bubble-bg': '#1e1e26',
    '--badge-finance-bg': 'rgba(99,179,237,0.12)',
    '--badge-finance-text': '#63b3ed',
    '--badge-finance-border': 'rgba(99,179,237,0.25)',
    '--badge-general-bg': 'rgba(154,127,234,0.12)',
    '--badge-general-text': '#a07ef0',
    '--badge-general-border': 'rgba(154,127,234,0.25)',
    '--shadow-user': '0 4px 20px rgba(124,106,247,0.3)',
    '--shadow-bubble': '0 2px 12px rgba(0,0,0,0.3)',
    '--gradient-hero': 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(124,106,247,0.15) 0%, transparent 70%)',
  } : {
    '--bg': '#f5f4f8',
    '--surface': '#ffffff',
    '--surface2': '#f0eff7',
    '--border': '#dddce8',
    '--accent': '#6c5ce7',
    '--accent-hover': '#5a4bd6',
    '--text': '#1a1a2e',
    '--text-muted': '#9999b8',
    '--bubble-bg': '#ffffff',
    '--badge-finance-bg': 'rgba(74,86,232,0.08)',
    '--badge-finance-text': '#4a56e8',
    '--badge-finance-border': 'rgba(74,86,232,0.2)',
    '--badge-general-bg': 'rgba(108,92,231,0.08)',
    '--badge-general-text': '#6c5ce7',
    '--badge-general-border': 'rgba(108,92,231,0.2)',
    '--shadow-user': '0 4px 20px rgba(108,92,231,0.2)',
    '--shadow-bubble': '0 2px 12px rgba(0,0,0,0.06)',
    '--gradient-hero': 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(108,92,231,0.08) 0%, transparent 70%)',
  }

  async function sendMessage(text) {
    const query = text || input.trim()
    if (!query || loading) return
    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', content: query }])
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, domain: data.domain }])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Cabinet+Grotesk:wght@400;500;700;800;900&family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body, #root { height: 100%; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(14px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-5px); opacity: 1; }
        }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes heroFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-6px); }
        }
        .chip:hover {
          transform: translateY(-2px) !important;
          border-color: var(--accent) !important;
          color: var(--accent) !important;
          box-shadow: 0 6px 20px rgba(108,92,231,0.15) !important;
        }
        .send-btn:hover:not(:disabled) { background: var(--accent-hover) !important; transform: scale(1.06); }
        .send-btn:disabled { opacity: 0.35; cursor: not-allowed; }
        .send-btn:active:not(:disabled) { transform: scale(0.95) !important; }
        textarea::placeholder { color: var(--text-muted); }
        textarea:focus { outline: none; }
        textarea { resize: none; }
        .markdown-body { font-family: "Cabinet Grotesk", sans-serif; font-size: 14.5px; line-height: 1.75; }
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { font-family: "Cabinet Grotesk", sans-serif; font-weight: 700; margin: 16px 0 8px; }
        .markdown-body h1 { font-size: 20px; }
        .markdown-body h2 { font-size: 17px; }
        .markdown-body h3 { font-size: 15px; }
        .markdown-body p { margin: 8px 0; }
        .markdown-body ul, .markdown-body ol { padding-left: 20px; margin: 8px 0; }
        .markdown-body li { margin: 4px 0; }
        .markdown-body code { font-family: "DM Mono", monospace; font-size: 13px; background: rgba(124,106,247,0.1); padding: 2px 6px; border-radius: 4px; }
        .markdown-body pre { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px; overflow-x: auto; margin: 12px 0; }
        .markdown-body pre code { background: none; padding: 0; font-size: 13px; }
        .markdown-body strong { font-weight: 700; }
        .markdown-body em { font-style: italic; }
        .markdown-body blockquote { border-left: 3px solid var(--accent); padding-left: 12px; color: var(--text-muted); margin: 8px 0; }
        .markdown-body table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
        .markdown-body th, .markdown-body td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
        .markdown-body th { background: var(--surface2); font-weight: 600; }
      `}</style>

      <div style={{
        ...cssVars, minHeight: '100vh', height: '100vh',
        display: 'flex', flexDirection: 'column',
        background: 'var(--bg)', color: 'var(--text)',
        fontFamily: '"Cabinet Grotesk", sans-serif',
        transition: 'background 0.35s, color 0.35s',
        position: 'relative',
      }}>
        <div style={{ position: 'fixed', inset: 0, background: 'var(--gradient-hero)', pointerEvents: 'none', zIndex: 0, transition: 'background 0.35s' }} />

        {/* Header */}
        <header style={{
          position: 'relative', zIndex: 10,
          padding: '14px 28px',
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'var(--surface)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: 'var(--accent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 17, color: '#fff', fontWeight: 800,
            }}>✦</div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.02em', lineHeight: 1.1 }}>AI Agent</div>
              <div style={{ fontFamily: '"DM Mono", monospace', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>MULTI-DOMAIN</div>
            </div>
          </div>
          <ThemeToggle theme={theme} onToggle={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />
        </header>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', position: 'relative', zIndex: 1 }}>
          <div style={{ maxWidth: 720, margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: 24, minHeight: '100%' }}>

            {isEmpty && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 36, paddingTop: 60, animation: 'fadeIn 0.5s ease' }}>
                <div style={{ textAlign: 'center', maxWidth: 480 }}>
                  <div style={{
                    fontFamily: '"Fraunces", serif', fontStyle: 'italic',
                    fontSize: 56, fontWeight: 300, lineHeight: 1.1,
                    letterSpacing: '-0.02em', marginBottom: 18,
                    animation: 'heroFloat 4s ease-in-out infinite',
                    background: isDark
                      ? 'linear-gradient(135deg, #e8e8f0 0%, #a07ef0 100%)'
                      : 'linear-gradient(135deg, #1a1a2e 0%, #6c5ce7 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}>
                    Ask anything.
                  </div>
                  <p style={{ fontFamily: '"DM Mono", monospace', fontSize: 13, color: 'var(--text-muted)', fontWeight: 300, lineHeight: 1.8 }}>
                    Powered by Groq · Routes automatically between{' '}
                    <span style={{ color: 'var(--badge-finance-text)' }}>financial analysis</span>
                    {' '}and{' '}
                    <span style={{ color: 'var(--badge-general-text)' }}>general knowledge</span>
                  </p>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', maxWidth: 520 }}>
                  {SUGGESTIONS.map(s => (
                    <button key={s.text} className="chip" onClick={() => sendMessage(s.text)} style={{
                      fontFamily: '"Cabinet Grotesk", sans-serif',
                      fontSize: 13, fontWeight: 500,
                      color: 'var(--text-muted)',
                      background: 'var(--surface)',
                      border: '1px solid var(--border)',
                      borderRadius: 24, padding: '9px 16px',
                      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 7,
                      boxShadow: 'var(--shadow-bubble)',
                      transition: 'all 0.18s cubic-bezier(0.34,1.56,0.64,1)',
                    }}>
                      <span>{s.icon}</span>{s.text}
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', maxWidth: 380, opacity: 0.3 }}>
                  <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
                  <span style={{ fontFamily: '"DM Mono"', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.12em', whiteSpace: 'nowrap' }}>START TYPING BELOW</span>
                  <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
                </div>
              </div>
            )}

            {messages.map((msg, i) => <Message key={i} msg={msg} index={i} />)}
            {loading && <TypingIndicator />}
            {error && (
              <div style={{ fontFamily: '"DM Mono", monospace', fontSize: 12, color: '#e06c75', padding: '12px 16px', background: 'rgba(224,108,117,0.08)', border: '1px solid rgba(224,108,117,0.2)', borderRadius: 12 }}>
                ⚠ {error} — is the FastAPI server running on port 8000?
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{ position: 'relative', zIndex: 10, padding: '16px 24px 24px', borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
          <div style={{ maxWidth: 720, margin: '0 auto' }}>
            <div style={{
              display: 'flex', gap: 10, alignItems: 'flex-end',
              background: 'var(--surface2)', border: '1.5px solid var(--border)',
              borderRadius: 18, padding: '12px 12px 12px 18px',
              boxShadow: isDark ? '0 0 0 1px rgba(124,106,247,0.04)' : '0 2px 20px rgba(0,0,0,0.05)',
            }}>
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={e => {
                  setInput(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 130) + 'px'
                }}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
                placeholder="Ask about finance, science, history, anything…"
                style={{
                  flex: 1, background: 'transparent', border: 'none',
                  fontFamily: '"Cabinet Grotesk", sans-serif',
                  fontSize: 15, color: 'var(--text)',
                  lineHeight: 1.6, fontWeight: 400, maxHeight: 130, overflow: 'auto',
                }}
              />
              <button
                className="send-btn"
                onClick={() => sendMessage()}
                disabled={!input.trim() || loading}
                style={{
                  width: 38, height: 38, borderRadius: 12, border: 'none',
                  background: 'var(--accent)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, transition: 'all 0.15s ease',
                }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 13V3M3 8l5-5 5 5" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div style={{ marginTop: 8, textAlign: 'center', fontFamily: '"DM Mono", monospace', fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
              ENTER TO SEND · SHIFT+ENTER FOR NEW LINE
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
