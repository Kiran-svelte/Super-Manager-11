import React, { useState, useRef, useEffect } from 'react'
import { Send, Check, X, Loader, PanelRightOpen, PanelRightClose } from 'lucide-react'
import TaskPanel from './components/TaskPanel'
import './App.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-api.onrender.com'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [pendingConfirm, setPendingConfirm] = useState(false)
  const [showTaskPanel, setShowTaskPanel] = useState(true)
  const [taskRefreshTrigger, setTaskRefreshTrigger] = useState(0)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    
    setInput('')
    setLoading(true)
    setPendingConfirm(false)
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId })
      })
      
      const data = await res.json()
      setSessionId(data.session_id)
      
      // Add AI response
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: data.message,
        type: data.type,
        status: data.status,
        need: data.need
      }])
      
      // Check if confirmation needed
      if (data.status === 'confirm') {
        setPendingConfirm(true)
      }
      
      // Trigger task panel refresh when task is confirmed
      if (data.status === 'done' || data.status === 'success') {
        setTaskRefreshTrigger(prev => prev + 1)
      }
      
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'error', 
        text: 'Connection failed. Try again.' 
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    send()
  }

  const confirm = (yes) => {
    send(yes ? 'yes' : 'no')
  }

  return (
    <div className={`app-container ${showTaskPanel ? 'with-panel' : ''}`}>
      <div className="chat-section">
        <header>
          <div className="header-left">
            <h1>Super Manager</h1>
            <span>AI Assistant</span>
          </div>
          <button 
            className="panel-toggle" 
            onClick={() => setShowTaskPanel(!showTaskPanel)}
            title={showTaskPanel ? 'Hide Tasks' : 'Show Tasks'}
          >
            {showTaskPanel ? <PanelRightClose size={20} /> : <PanelRightOpen size={20} />}
          </button>
        </header>

        <main>
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Hi! How can I help?</h2>
              <p>Try: "Schedule a meeting", "Send email to...", "Remind me to..."</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === 'user' ? (
                <div className="bubble user-bubble">{m.text}</div>
              ) : m.role === 'error' ? (
                <div className="bubble error-bubble">{m.text}</div>
              ) : (
                <div className="bubble ai-bubble">
                  <div className="ai-text">{m.text}</div>
                  
                  {/* Confirmation buttons */}
                  {m.status === 'confirm' && i === messages.length - 1 && pendingConfirm && (
                    <div className="confirm-btns">
                      <button className="yes" onClick={() => confirm(true)} disabled={loading}>
                        <Check size={16} /> Yes
                      </button>
                      <button className="no" onClick={() => confirm(false)} disabled={loading}>
                        <X size={16} /> No
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="msg ai">
              <div className="bubble ai-bubble loading">
                <Loader className="spin" size={20} />
              </div>
            </div>
          )}

          <div ref={endRef} />
        </main>

        <footer>
          <form onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              disabled={loading}
              autoFocus
            />
            <button type="submit" disabled={!input.trim() || loading}>
              <Send size={20} />
            </button>
          </form>
        </footer>
      </div>
      
      {showTaskPanel && (
        <div className="task-section">
          <TaskPanel refreshTrigger={taskRefreshTrigger} />
        </div>
      )}
    </div>
  )
}

export default App
