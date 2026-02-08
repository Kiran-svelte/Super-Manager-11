/**
 * Super Manager - Clean, User-Friendly Chat Interface
 * Simple, trustworthy design focused on usability
 */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { 
  Send, Check, X, Loader2, Bot, User, MessageSquare,
  Search, Mail, Calendar, ShoppingCart, AlertCircle,
  Shield, Lock, Zap, Settings
} from 'lucide-react'
import AISettings from './components/AISettings'
import './styles/clean-theme.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-11-production.up.railway.app'

// =============================================================================
// Helpers
// =============================================================================

const formatTime = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(date)
}

const parseLinks = (text) => {
  if (!text) return text
  const urlRegex = /(https?:\/\/[^\s<>"]+)/g
  const parts = text.split(urlRegex)
  
  return parts.map((part, i) => {
    if (part.match(urlRegex)) {
      // Clean URL (remove trailing punctuation)
      const cleanUrl = part.replace(/[.,;:!?)]+$/, '')
      const displayUrl = cleanUrl.length > 50 
        ? cleanUrl.replace(/^https?:\/\//, '').substring(0, 40) + '...' 
        : cleanUrl.replace(/^https?:\/\//, '')
      return (
        <a 
          key={i} 
          href={cleanUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="chat-link"
          onClick={(e) => e.stopPropagation()}
        >
          {displayUrl}
        </a>
      )
    }
    return part
  })
}

// =============================================================================
// Quick Actions
// =============================================================================

const quickActions = [
  { icon: Mail, text: 'Send an email' },
  { icon: Calendar, text: 'Schedule meeting' },
  { icon: Search, text: 'Search the web' },
  { icon: ShoppingCart, text: 'Find products' },
]

function QuickActions({ onSelect }) {
  return (
    <div className="quick-actions">
      {quickActions.map((action, i) => (
        <button 
          key={i}
          className="quick-action"
          onClick={() => onSelect(action.text)}
        >
          <action.icon />
          {action.text}
        </button>
      ))}
    </div>
  )
}

// =============================================================================
// Welcome Screen
// =============================================================================

function WelcomeScreen({ onActionClick }) {
  return (
    <div className="welcome">
      <div className="welcome-icon">
        <MessageSquare />
      </div>
      <h2>How can I help you today?</h2>
      <p>
        I can help with emails, meetings, web searches, and more. 
        Just type your request or choose an option below.
      </p>
      <QuickActions onSelect={onActionClick} />
    </div>
  )
}

// =============================================================================
// Message Component
// =============================================================================

function Message({ message, isLast, onConfirm, loading }) {
  const { role, text, status, timestamp } = message
  const showConfirm = status === 'confirm' && isLast && !loading
  
  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? <User /> : role === 'error' ? <AlertCircle /> : <Bot />}
      </div>
      <div className="message-content">
        <div className="message-bubble">
          {typeof text === 'string' ? parseLinks(text) : text}
        </div>
        
        {showConfirm && (
          <div className="confirm-actions">
            <button 
              className="confirm-btn yes" 
              onClick={() => onConfirm(true)}
            >
              <Check /> Yes, proceed
            </button>
            <button 
              className="confirm-btn no" 
              onClick={() => onConfirm(false)}
            >
              <X /> Cancel
            </button>
          </div>
        )}
        
        {timestamp && (
          <div className="message-time">
            {formatTime(new Date(timestamp))}
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Typing Indicator
// =============================================================================

function TypingIndicator() {
  return (
    <div className="typing">
      <div className="message-avatar" style={{ 
        background: 'var(--primary-100)', 
        color: 'var(--primary-600)' 
      }}>
        <Bot style={{ width: 18, height: 18 }} />
      </div>
      <div className="typing-dots">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  )
}

// =============================================================================
// Main App
// =============================================================================

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [userId, setUserId] = useState(null)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(null)

  // Generate or load user ID
  useEffect(() => {
    let id = localStorage.getItem('super_manager_user_id')
    if (!id) {
      id = 'user_' + Math.random().toString(36).substring(2, 15)
      localStorage.setItem('super_manager_user_id', id)
    }
    setUserId(id)
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Focus input
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Send message
  const sendMessage = useCallback(async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    
    setInput('')
    setLoading(true)
    
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    
    const userMessage = {
      role: 'user',
      text: msg,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
        signal: abortRef.current.signal
      })
      
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      
      const data = await res.json()
      setSessionId(data.session_id)
      
      const aiMessage = {
        role: 'ai',
        text: data.message,
        type: data.type,
        status: data.status,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      
    } catch (err) {
      if (err.name === 'AbortError') return
      
      setMessages(prev => [...prev, {
        role: 'error',
        text: err.message === 'Failed to fetch' 
          ? 'Unable to connect. Please check your connection and try again.'
          : `Something went wrong. Please try again.`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, loading, sessionId])

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage()
  }

  const handleConfirm = (yes) => {
    sendMessage(yes ? 'yes' : 'no')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">
            <Zap />
          </div>
          <div className="header-info">
            <h1>Super Manager</h1>
            <span>Your AI Assistant</span>
          </div>
        </div>
        <div className="header-actions">
          <button 
            className="settings-btn" 
            onClick={() => setShowSettings(true)}
            title="AI Settings"
          >
            <Settings size={18} />
          </button>
          <div className="header-status">
            <span className="status-indicator" />
            Online
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="messages">
        {messages.length === 0 ? (
          <WelcomeScreen onActionClick={(text) => {
            setInput(text)
            inputRef.current?.focus()
          }} />
        ) : (
          <>
            {messages.map((msg, i) => (
              <Message
                key={i}
                message={msg}
                isLast={i === messages.length - 1}
                onConfirm={handleConfirm}
                loading={loading}
              />
            ))}
            {loading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-area">
        <form className="input-form" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="input-field"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={loading}
              rows={1}
            />
          </div>
          <button 
            type="submit" 
            className="send-btn"
            disabled={!input.trim() || loading}
          >
            {loading ? <Loader2 className="spinner" /> : <Send />}
          </button>
        </form>
      </div>

      {/* Trust Footer */}
      <footer className="trust-footer">
        <div className="trust-item">
          <Shield />
          <span>Secure</span>
        </div>
        <div className="trust-item">
          <Lock />
          <span>Private</span>
        </div>
        <div className="trust-item">
          <Zap />
          <span>AI Powered</span>
        </div>
      </footer>

      {/* AI Settings Modal */}
      {showSettings && (
        <AISettings 
          userId={userId}
          onClose={() => setShowSettings(false)}
          onSave={(data) => {
            setShowSettings(false)
            // Show success message
            setMessages(prev => [...prev, {
              role: 'ai',
              text: `✅ AI email configured! I can now sign up for services and get API keys autonomously.`,
              timestamp: new Date().toISOString()
            }])
          }}
        />
      )}
    </div>
  )
}

export default App
