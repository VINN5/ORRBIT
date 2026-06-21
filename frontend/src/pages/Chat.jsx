import { useState, useRef, useEffect } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useAuth } from '../context/AuthContext'
import { sendMessage } from '../api/client'

const DOMAIN_LABELS = {
  computing:      '💻 Computing',
  finance:        '💰 Finance',
  health:         '🏥 Health',
  legal:          '⚖️ Legal',
  mental_health:  '🧠 Mental Health',
  business:       '💼 Business',
  history:        '📚 History',
  astronomy:      '🚀 Astronomy',
  sports:         '⚽ Sports',
  technology:     '📱 Technology',
  general:        '🌍 General',
  system:         '⚠️ System',
}

const SUGGESTIONS = [
  'Explain how black holes form',
  'What is compound interest?',
  'Give me 5 Python best practices',
  'How do I manage stress better?',
]

export default function Chat() {
  const { user, logout } = useAuth()
  const [theme, setTheme]       = useState('dark')
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)
  const sessionId = useRef(`session_${Date.now()}`)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend(text) {
    const query = text || input.trim()
    if (!query || loading) return

    setInput('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', content: query }])
    setLoading(true)

    try {
      const data = await sendMessage(query, sessionId.current)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer, domain: data.domain },
      ])
    } catch (err) {
      setError('Failed to reach Orrbit. Is the server running?')
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div style={styles.shell}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarTop}>
          <div style={styles.brand}>
            <div style={styles.mark}>✦</div>
            <span style={styles.brandName}>Orrbit</span>
          </div>
          <button style={styles.newChatBtn} onClick={() => setMessages([])}>
            + New chat
          </button>
        </div>

        <div style={styles.sidebarBottom}>
          <button
            style={styles.themeBtn}
            onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
          >
            {theme === 'dark' ? '☀ Light mode' : '☾ Dark mode'}
          </button>
          <div style={styles.userRow}>
            <div style={styles.avatar}>{user?.username?.[0]?.toUpperCase() || '?'}</div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={styles.username}>{user?.username || 'Guest'}</div>
              <div style={styles.userEmail}>{user?.email || ''}</div>
            </div>
            <button style={styles.logoutBtn} onClick={logout} title="Log out">
              ⎋
            </button>
          </div>
        </div>
      </aside>

      {/* Main chat */}
      <main style={styles.main}>
        <div style={styles.scrollArea}>
          <div style={styles.thread}>
            {isEmpty && (
              <div style={styles.hero}>
                <div style={styles.heroText}>Ask anything.</div>
                <p style={styles.heroSub}>
                  Orrbit routes your question to the right expert automatically.
                </p>
                <div style={styles.chips}>
                  {SUGGESTIONS.map((s) => (
                    <button key={s} style={styles.chip} onClick={() => handleSend(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <Message key={i} msg={msg} />
            ))}

            {loading && <Typing />}

            {error && <div style={styles.errorBox}>{error}</div>}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div style={styles.inputBar}>
          <div style={styles.inputWrap}>
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Message Orrbit..."
              style={styles.textarea}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              style={{
                ...styles.sendBtn,
                opacity: !input.trim() || loading ? 0.35 : 1,
              }}
            >
              ↑
            </button>
          </div>
          <div style={styles.hint}>Enter to send · Shift+Enter for new line</div>
        </div>
      </main>
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start', gap: 6, animation: 'fadeUp 0.3s ease' }}>
      {!isUser && msg.domain && (
        <span style={styles.badge}>{DOMAIN_LABELS[msg.domain] || msg.domain}</span>
      )}
      <div
        style={{
          maxWidth: '78%',
          padding: '13px 17px',
          borderRadius: isUser ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
          background: isUser ? 'var(--accent)' : 'var(--surface)',
          border: isUser ? 'none' : '1px solid var(--border)',
          color: isUser ? '#0e0e0e' : 'var(--text)',
        }}
      >
        {isUser ? (
          <span style={{ fontSize: 14.5 }}>{msg.content}</span>
        ) : (
          <div
            className="markdown"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(msg.content)) }}
          />
        )}
      </div>
    </div>
  )
}

function Typing() {
  return (
    <div style={{ display: 'flex', gap: 5, padding: '13px 17px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '4px 16px 16px 16px', width: 'fit-content' }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', animation: `pulse 1.1s ${i * 0.15}s infinite` }} />
      ))}
    </div>
  )
}

const styles = {
  shell: { display: 'flex', height: '100vh', background: 'var(--bg)' },

  sidebar: {
    width: 260,
    flexShrink: 0,
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 20,
    background: 'var(--bg2)',
  },
  sidebarTop: { display: 'flex', flexDirection: 'column', gap: 20 },
  brand: { display: 'flex', alignItems: 'center', gap: 10 },
  mark: { width: 30, height: 30, borderRadius: 8, background: 'var(--accent)', color: '#0e0e0e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15 },
  brandName: { fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--text)' },
  newChatBtn: { padding: '10px 14px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)', fontSize: 13.5, textAlign: 'left' },

  sidebarBottom: { display: 'flex', flexDirection: 'column', gap: 12 },
  themeBtn: { padding: '10px 14px', background: 'transparent', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text-2)', fontSize: 13 },
  userRow: { display: 'flex', alignItems: 'center', gap: 10, paddingTop: 12, borderTop: '1px solid var(--border)' },
  avatar: { width: 32, height: 32, borderRadius: '50%', background: 'var(--accent-dim)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, flexShrink: 0 },
  username: { fontSize: 13, color: 'var(--text)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  userEmail: { fontSize: 11, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  logoutBtn: { background: 'transparent', border: 'none', color: 'var(--text-2)', fontSize: 16, flexShrink: 0 },

  main: { flex: 1, display: 'flex', flexDirection: 'column' },
  scrollArea: { flex: 1, overflowY: 'auto' },
  thread: { maxWidth: 720, margin: '0 auto', padding: '40px 24px', display: 'flex', flexDirection: 'column', gap: 22, minHeight: '100%' },

  hero: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 28, paddingTop: 60 },
  heroText: { fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 46, color: 'var(--text)' },
  heroSub: { fontSize: 13.5, color: 'var(--text-2)', textAlign: 'center' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', maxWidth: 480 },
  chip: { padding: '9px 15px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 20, color: 'var(--text-2)', fontSize: 13 },

  badge: { fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em', padding: '3px 9px', borderRadius: 12, background: 'var(--accent-dim)', color: 'var(--accent)' },
  errorBox: { fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--danger)', padding: '12px 14px', background: 'rgba(192,57,43,0.08)', border: '1px solid rgba(192,57,43,0.2)', borderRadius: 'var(--radius)' },

  inputBar: { padding: '16px 24px 22px', borderTop: '1px solid var(--border)' },
  inputWrap: { maxWidth: 720, margin: '0 auto', display: 'flex', gap: 10, alignItems: 'flex-end', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 12px 12px 18px' },
  textarea: { flex: 1, background: 'transparent', border: 'none', resize: 'none', color: 'var(--text)', fontSize: 14.5, lineHeight: 1.6, maxHeight: 140 },
  sendBtn: { width: 36, height: 36, borderRadius: 10, border: 'none', background: 'var(--accent)', color: '#0e0e0e', fontSize: 16, flexShrink: 0 },
  hint: { textAlign: 'center', marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--text-3)' },
}
