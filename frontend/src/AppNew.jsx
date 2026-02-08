/**
 * Super Manager - Modern Chat Interface
 * Glassmorphism UI with animations and real-time interactions
 */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { 
  Send, Check, X, Loader2, Bot, User, Sparkles, 
  Search, Mail, Calendar, ShoppingCart, AlertCircle,
  ChevronRight, Zap, MessageCircle
} from 'lucide-react'
import { GradientOrbs, MouseSpotlight, GridPattern } from './components/AnimatedBackground'
import { ToastProvider, useToast } from './components/Toast'
import './styles/theme.css'
import './styles/app.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-11-production.up.railway.app'

// =============================================================================
// Helper Functions
// =============================================================================

const formatTime = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(date)
}

const parseLinks = (text) => {
  // Convert URLs to clickable links
  const urlRegex = /(https?:\/\/[^\s]+)/g
  return text.split(urlRegex).map((part, i) => {
    if (part.match(urlRegex)) {
      return (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer">
          {part.length > 50 ? part.substring(0, 47) + '...' : part}
        </a>
      )
    }
    return part
  })
}

// =============================================================================
// Suggestion Chips Component
// =============================================================================

const suggestions = [
  { icon: Search, text: 'Search for something' },
  { icon: Mail, text: 'Send an email' },
  { icon: Calendar, text: 'Schedule a meeting' },
  { icon: ShoppingCart, text: 'Find products online' },
]

function SuggestionChips({ onSelect }) {
  return (
    <div className="welcome-suggestions">
      {suggestions.map((item, i) => (
        <button 
          key={i}
          className="suggestion-chip"
          onClick={() => onSelect(item.text)}
          style={{ animationDelay: `${0.1 + i * 0.1}s` }}
        >
          <item.icon />
          {item.text}
        </button>
      ))}
    </div>
  )
}

// =============================================================================
// Welcome Screen Component
// =============================================================================

function WelcomeScreen({ onSuggestionClick }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">
        <Sparkles />
      </div>
      <h2 className="welcome-title">Hello! I'm Super Manager</h2>
      <p className="welcome-subtitle">
        Your AI assistant for emails, meetings, web search, and more. 
        Just tell me what you need help with.
      </p>
      <SuggestionChips onSelect={onSuggestionClick} />
    </div>
  )
}

// =============================================================================
// Message Component
// =============================================================================

function Message({ message, isLast, onConfirm, loading }) {
  const { role, text, status, timestamp } = message
  
  const showConfirmButtons = status === 'confirm' && isLast && !loading
  
  const Icon = useMemo(() => {
    if (role === 'user') return User
    if (role === 'error') return AlertCircle
    return Bot
  }, [role])
  
  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        <Icon />
      </div>
      <div className="message-bubble">
        <div className="message-content">
          {typeof text === 'string' ? parseLinks(text) : text}
        </div>
        {timestamp && (
          <div className="message-time">
            {formatTime(new Date(timestamp))}
          </div>
        )}
        
        {showConfirmButtons && (
          <div className="confirm-buttons">
            <button 
              className="confirm-btn yes" 
              onClick={() => onConfirm(true)}
              disabled={loading}
            >
              <Check /> Yes, proceed
            </button>
            <button 
              className="confirm-btn no" 
              onClick={() => onConfirm(false)}
              disabled={loading}
            >
              <X /> Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Typing Indicator Component
// =============================================================================

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="message-avatar" style={{ 
        background: 'linear-gradient(135deg, var(--accent-500), var(--accent-600))'
      }}>
        <Bot style={{ width: 18, height: 18, color: 'white' }} />
      </div>
      <div className="typing-bubble">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </div>
  )
}

// =============================================================================
// Main App Component
// =============================================================================

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [pendingConfirm, setPendingConfirm] = useState(false)
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const abortControllerRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Send message handler
  const sendMessage = useCallback(async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    
    // Clear input immediately
    setInput('')
    setLoading(true)
    setPendingConfirm(false)
    
    // Abort any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    
    // Add user message
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
        body: JSON.stringify({ 
          message: msg, 
          session_id: sessionId 
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`)
      }
      
      const data = await res.json()
      setSessionId(data.session_id)
      
      // Add AI response
      const aiMessage = {
        role: 'ai',
        text: data.message,
        type: data.type,
        status: data.status,
        need: data.need,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      
      // Check if confirmation needed
      if (data.status === 'confirm') {
        setPendingConfirm(true)
      }
      
    } catch (err) {
      if (err.name === 'AbortError') return
      
      const errorMessage = {
        role: 'error',
        text: err.message === 'Failed to fetch' 
          ? 'Unable to connect to server. Please check your connection and try again.'
          : `Something went wrong: ${err.message}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, loading, sessionId])

  // Handle form submit
  const handleSubmit = useCallback((e) => {
    e.preventDefault()
    sendMessage()
  }, [sendMessage])

  // Handle confirmation
  const handleConfirm = useCallback((yes) => {
    sendMessage(yes ? 'yes' : 'no')
  }, [sendMessage])

  // Handle suggestion click
  const handleSuggestion = useCallback((text) => {
    setInput(text)
    inputRef.current?.focus()
  }, [])

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }, [sendMessage])

  return (
    <>
      {/* Background Effects */}
      <GradientOrbs />
      <MouseSpotlight />
      <GridPattern />
      
      <div className="app-container">
        {/* Header */}
        <header className="app-header">
          <div className="header-brand">
            <div className="header-logo">
              <Zap />
            </div>
            <div>
              <h1 className="header-title">Super Manager</h1>
              <span className="header-subtitle">AI Assistant</span>
            </div>
          </div>
          <div className="header-status">
            <span className="status-dot"></span>
            Online
          </div>
        </header>

        {/* Chat Container */}
        <div className="chat-container">
          {/* Messages */}
          <div className="messages-container">
            {messages.length === 0 ? (
              <WelcomeScreen onSuggestionClick={handleSuggestion} />
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

          {/* Input Area */}
          <div className="input-area">
            <form className="input-form" onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <textarea
                  ref={inputRef}
                  className="chat-input"
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
                className="send-button"
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                {loading ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Send />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}

// Wrap App with ToastProvider
function AppWithProviders() {
  return (
    <ToastProvider>
      <App />
    </ToastProvider>
  )
}

export default AppWithProviders
