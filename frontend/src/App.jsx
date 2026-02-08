import React, { useState, useRef, useEffect } from 'react'
import { Send, Check, X, Loader, PanelRightOpen, PanelRightClose, Settings, Bot } from 'lucide-react'
import TaskPanel from './components/TaskPanel'
import OnboardingWizard from './components/OnboardingWizard'
import AISettings from './components/AISettings'
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
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [hasAIIdentity, setHasAIIdentity] = useState(null) // null = loading, false = no, true = yes
  const [userId, setUserId] = useState(null)
  const endRef = useRef(null)

  // Generate or load user ID
  useEffect(() => {
    let id = localStorage.getItem('super_manager_user_id')
    if (!id) {
      id = 'user_' + Math.random().toString(36).substring(2, 15)
      localStorage.setItem('super_manager_user_id', id)
    }
    setUserId(id)
  }, [])

  // Check if user has AI identity
  useEffect(() => {
    if (!userId) return

    const checkIdentity = async () => {
      try {
        const res = await fetch(`${API}/api/identity/status/${userId}`)
        const data = await res.json()
        setHasAIIdentity(data.has_identity)
        
        // Show onboarding for new users (first time only)
        if (!data.has_identity && !localStorage.getItem('onboarding_skipped')) {
          setShowOnboarding(true)
        }
      } catch (err) {
        console.error('Failed to check AI identity:', err)
        setHasAIIdentity(false)
      }
    }

    checkIdentity()
  }, [userId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleOnboardingComplete = (data) => {
    setHasAIIdentity(true)
    setShowOnboarding(false)
    setMessages(prev => [...prev, {
      role: 'ai',
      text: `🎉 Great! I now have my own email identity (${data.identity?.email}). I can:\n\n• Send emails on your behalf\n• Sign up for services autonomously\n• Get my own API keys\n\nWhat would you like me to do?`
    }])
  }

  const handleOnboardingSkip = () => {
    setShowOnboarding(false)
    localStorage.setItem('onboarding_skipped', 'true')
  }

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

  // Show onboarding wizard if needed
  if (showOnboarding) {
    return (
      <OnboardingWizard 
        userId={userId}
        onComplete={handleOnboardingComplete}
        onSkip={handleOnboardingSkip}
      />
    )
  }

  return (
    <div className={`app-container ${showTaskPanel ? 'with-panel' : ''}`}>
      <div className="chat-section">
        <header>
          <div className="header-left">
            <h1>Super Manager</h1>
            <span>AI Assistant {hasAIIdentity && '✓'}</span>
          </div>
          <div className="header-actions">
            <button 
              className="setup-btn"
              onClick={() => setShowSettings(true)}
              title="AI Settings"
            >
              <Bot size={18} />
            </button>
            <button 
              className="panel-toggle" 
              onClick={() => setShowTaskPanel(!showTaskPanel)}
              title={showTaskPanel ? 'Hide Tasks' : 'Show Tasks'}
            >
              {showTaskPanel ? <PanelRightClose size={20} /> : <PanelRightOpen size={20} />}
            </button>
          </div>
        </header>

        <main>
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Hi! How can I help?</h2>
              <p>Try: "Schedule a meeting", "Send email to...", "Remind me to..."</p>
              {!hasAIIdentity && (
                <button 
                  className="setup-identity-btn"
                  onClick={() => setShowOnboarding(true)}
                >
                  🤖 Set up AI Identity
                </button>
              )}
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
      
      {showSettings && (
        <AISettings 
          userId={userId}
          onClose={() => setShowSettings(false)}
          onSave={(data) => {
            setHasAIIdentity(true)
            setShowSettings(false)
          }}
        />
      )}
    </div>
  )
}

export default App
