/**
 * Super Manager - Clean, User-Friendly Chat Interface
 * With real-time SSE streaming and agent step visualization
 */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send, Check, X, Loader2, Bot, User, MessageSquare,
  Search, Mail, Calendar, ShoppingCart, AlertCircle,
  Shield, Lock, Zap, Settings, ChevronDown, ChevronRight,
  Brain, Wrench, Eye
} from 'lucide-react'
import AISettings from './components/AISettings'
import './styles/clean-theme.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-api.onrender.com'

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
// Agent Steps - Shows thinking/tool progress
// =============================================================================

function AgentSteps({ steps }) {
  const [expanded, setExpanded] = useState(false)

  if (!steps || steps.length === 0) return null

  const stepIcons = {
    thinking: Brain,
    tool_call: Wrench,
    tool_result: Eye,
    error: AlertCircle,
  }

  const stepLabels = {
    thinking: 'Thinking',
    tool_call: 'Using tool',
    tool_result: 'Result',
    error: 'Error',
  }

  return (
    <div className="agent-steps">
      <button
        onClick={() => setExpanded(!expanded)}
        className="steps-toggle"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>{steps.length} step{steps.length !== 1 ? 's' : ''} taken</span>
      </button>
      {expanded && (
        <div className="steps-list">
          {steps.map((step, i) => {
            const Icon = stepIcons[step.type] || Brain
            return (
              <div key={i} className={`step step-${step.type}`}>
                <div className="step-icon">
                  <Icon size={14} />
                </div>
                <div className="step-body">
                  <span className="step-label">{stepLabels[step.type] || step.type}</span>
                  <span className="step-content">
                    {step.content?.length > 200
                      ? step.content.substring(0, 200) + '...'
                      : step.content}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Live Steps - Shows steps as they stream in
// =============================================================================

function LiveSteps({ steps }) {
  if (!steps || steps.length === 0) return null

  const lastStep = steps[steps.length - 1]

  const stepIcons = {
    thinking: Brain,
    tool_call: Wrench,
    tool_result: Eye,
    error: AlertCircle,
  }

  const Icon = stepIcons[lastStep.type] || Brain

  return (
    <div className="live-steps">
      <div className={`live-step step-${lastStep.type}`}>
        <div className="live-step-icon">
          <Icon size={14} />
        </div>
        <span className="live-step-text">
          {lastStep.content?.length > 150
            ? lastStep.content.substring(0, 150) + '...'
            : lastStep.content}
        </span>
      </div>
      {steps.length > 1 && (
        <div className="live-steps-count">
          {steps.length} steps so far...
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Message Component
// =============================================================================

function Message({ message, isLast, onConfirm, onOptionClick, loading }) {
  const { role, text, status, options, ui_components, proof, need, steps, timestamp, _building } = message
  const showConfirm = status === 'confirm' && isLast && !loading

  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? <User /> : role === 'error' ? <AlertCircle /> : <Bot />}
      </div>
      <div className="message-content">
        {/* Show live steps while building */}
        {_building && steps && steps.length > 0 && (
          <LiveSteps steps={steps} />
        )}

        {/* Show message bubble (hide when building unless there's actual text) */}
        {(!_building || (text && text !== 'Thinking...')) && (
          <div className="message-bubble">
            {typeof text === 'string' ? parseLinks(text) : text}
          </div>
        )}

        {/* Show completed agent steps */}
        {!_building && steps && steps.length > 0 && (
          <AgentSteps steps={steps} />
        )}

        {/* Options buttons (AI-provided choices) */}
        {options && options.length > 0 && isLast && !loading && (
          <div className="options-group">
            {options.map((opt, i) => (
              <button
                key={i}
                className="option-btn"
                onClick={() => onOptionClick(opt.value || opt.label)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Missing info indicator */}
        {need && need.length > 0 && isLast && (
          <div className="need-info">
            <span className="need-label">Still need:</span>
            {need.map((item, i) => (
              <span key={i} className="need-tag">{item}</span>
            ))}
          </div>
        )}

        {/* Confirmation buttons */}
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

        {/* Button group from tools */}
        {ui_components && ui_components.type === 'button_group' && ui_components.buttons && (
          <div className="tool-buttons">
            {ui_components.buttons.map((btn, i) => (
              <a
                key={i}
                href={btn.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`tool-btn tool-btn-${btn.style || 'primary'}`}
              >
                {btn.label}
              </a>
            ))}
          </div>
        )}

        {/* Image gallery */}
        {ui_components && ui_components.type === 'image_gallery' && ui_components.images && (
          <div className="image-gallery">
            {ui_components.images.map((img, i) => (
              <div key={i} className="image-card">
                <img src={img.url} alt={img.alt || `Image ${i + 1}`} loading="lazy" />
                {img.downloadable && (
                  <a href={img.url} target="_blank" rel="noopener noreferrer" className="download-btn">
                    Download
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Execution proof */}
        {proof && proof.proof_id && (
          <div className="proof-badge">
            <Shield size={12} />
            <span>Verified: {proof.proof_id}</span>
          </div>
        )}

        {timestamp && !_building && (
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

  // Send message with SSE streaming
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

    const steps = []
    let finalAnswer = ''
    let uiComponents = null
    let confirmStatus = null
    let streamWorked = false

    try {
      // Try SSE streaming first
      const res = await fetch(`${API}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId, user_id: userId }),
        signal: abortRef.current.signal
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      streamWorked = true

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue

          let event
          try {
            event = JSON.parse(line.slice(6))
          } catch {
            continue
          }

          if (event.type === 'thinking' || event.type === 'tool_call' || event.type === 'tool_result') {
            steps.push(event)
            // Show live progress
            setMessages(prev => {
              const updated = [...prev]
              const lastMsg = updated[updated.length - 1]
              if (lastMsg?.role === 'ai' && lastMsg?._building) {
                return [
                  ...updated.slice(0, -1),
                  { ...lastMsg, steps: [...steps] }
                ]
              } else {
                return [
                  ...updated,
                  {
                    role: 'ai',
                    text: 'Thinking...',
                    steps: [...steps],
                    _building: true,
                    timestamp: new Date().toISOString()
                  }
                ]
              }
            })
          } else if (event.type === 'answer') {
            finalAnswer = event.content
          } else if (event.type === 'confirm_needed') {
            finalAnswer = event.content
            confirmStatus = 'confirm'
            if (event.data?.ui_components) {
              uiComponents = event.data.ui_components
            }
          } else if (event.type === 'error') {
            finalAnswer = event.content || 'An error occurred.'
          } else if (event.type === 'done') {
            if (event.session_id) setSessionId(event.session_id)
          }
        }
      }

      // Replace building message with final
      setMessages(prev => {
        const updated = prev.filter(m => !m._building)
        updated.push({
          role: 'ai',
          text: finalAnswer || 'No response received.',
          steps: steps.length > 0 ? steps : null,
          status: confirmStatus,
          ui_components: uiComponents,
          timestamp: new Date().toISOString()
        })
        return updated
      })

    } catch (err) {
      if (err.name === 'AbortError') return

      // Fallback to non-streaming endpoint
      if (!streamWorked) {
        try {
          const res = await fetch(`${API}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, session_id: sessionId, user_id: userId }),
            signal: abortRef.current.signal
          })

          if (!res.ok) throw new Error(`Server error: ${res.status}`)

          const data = await res.json()
          setSessionId(data.session_id)

          // Remove any building messages
          setMessages(prev => {
            const cleaned = prev.filter(m => !m._building)
            return [...cleaned, {
              role: 'ai',
              text: data.message,
              type: data.type,
              status: data.status,
              steps: data.steps || null,
              options: data.options || null,
              ui_components: data.ui_components || null,
              proof: data.proof || null,
              need: data.need || null,
              timestamp: new Date().toISOString()
            }]
          })
        } catch (fallbackErr) {
          if (fallbackErr.name === 'AbortError') return
          setMessages(prev => {
            const cleaned = prev.filter(m => !m._building)
            return [...cleaned, {
              role: 'error',
              text: fallbackErr.message === 'Failed to fetch'
                ? 'Unable to connect. Please check your connection and try again.'
                : 'Something went wrong. Please try again.',
              timestamp: new Date().toISOString()
            }]
          })
        }
      } else {
        // Stream started but errored mid-way
        setMessages(prev => {
          const cleaned = prev.filter(m => !m._building)
          if (finalAnswer) {
            return [...cleaned, {
              role: 'ai',
              text: finalAnswer,
              steps: steps.length > 0 ? steps : null,
              timestamp: new Date().toISOString()
            }]
          }
          return [...cleaned, {
            role: 'error',
            text: 'Connection interrupted. Please try again.',
            timestamp: new Date().toISOString()
          }]
        })
      }
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, loading, sessionId, userId])

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage()
  }

  const handleConfirm = (yes) => {
    sendMessage(yes ? 'yes' : 'no')
  }

  const handleOptionClick = (value) => {
    sendMessage(value)
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
                onOptionClick={handleOptionClick}
                loading={loading}
              />
            ))}
            {loading && !messages.some(m => m._building) && <TypingIndicator />}
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
            setMessages(prev => [...prev, {
              role: 'ai',
              text: 'AI email configured! I can now sign up for services and get API keys autonomously.',
              timestamp: new Date().toISOString()
            }])
          }}
        />
      )}
    </div>
  )
}

export default App
