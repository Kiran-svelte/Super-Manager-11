import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Square, Check, X, Loader, Sparkles, Zap, Calendar, Mail, Bell, CreditCard } from 'lucide-react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'https://super-manager-api.onrender.com/api'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [currentResponse, setCurrentResponse] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [pendingAction, setPendingAction] = useState(null)
  
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentResponse])

  // STREAMING CHAT - tokens appear instantly!
  const sendMessage = useCallback(async (messageText) => {
    const text = messageText || input.trim()
    if (!text || isStreaming) return
    
    setIsStreaming(true)
    setCurrentResponse('')
    setInput('')
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date()
    }])
    
    abortControllerRef.current = new AbortController()
    
    try {
      const response = await fetch(`${API_BASE}/stream/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
        signal: abortControllerRef.current.signal
      })
      
      if (!response.ok) throw new Error('Connection failed')
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let newSessionId = sessionId
      let hasAction = false
      let actionType = null
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'token') {
                fullResponse += data.content
                setCurrentResponse(fullResponse)
              } else if (data.type === 'done') {
                newSessionId = data.session_id
                hasAction = data.has_action
                actionType = data.action_type
              }
            } catch (e) {}
          }
        }
      }
      
      // Clean response - extract message if JSON
      let displayMessage = fullResponse
      if (fullResponse.trim().startsWith('{')) {
        try {
          const parsed = JSON.parse(fullResponse)
          displayMessage = parsed.message || fullResponse
        } catch (e) {}
      }
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: displayMessage,
        timestamp: new Date(),
        hasAction,
        actionType
      }])
      
      setSessionId(newSessionId)
      setCurrentResponse('')
      
      if (hasAction) {
        setPendingAction({ type: actionType })
      }
      
    } catch (err) {
      if (err.name !== 'AbortError') {
        setMessages(prev => [...prev, {
          role: 'error',
          content: 'Connection failed. Try again.',
          timestamp: new Date()
        }])
      }
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }, [sessionId, isStreaming, input])

  // Execute action with streaming
  const confirmAction = useCallback(async (confirmed) => {
    if (!sessionId || !pendingAction) return
    
    setIsStreaming(true)
    setCurrentResponse('')
    
    try {
      const response = await fetch(`${API_BASE}/stream/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, confirmed })
      })
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'status') {
                fullResponse += data.content
                setCurrentResponse(fullResponse)
              }
            } catch (e) {}
          }
        }
      }
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date()
      }])
      
      setCurrentResponse('')
      setPendingAction(null)
      
    } catch (err) {
      console.error(err)
    } finally {
      setIsStreaming(false)
    }
  }, [sessionId, pendingAction])

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setPendingAction(null)
    setCurrentResponse('')
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage()
  }

  return (
    <div className="streaming-app">
      {/* Header */}
      <header className="stream-header">
        <div className="header-left">
          <Sparkles className="icon" />
          <div>
            <h1>Super Manager</h1>
            <span>Instant AI Responses</span>
          </div>
        </div>
        <button onClick={clearChat} className="clear-btn">Clear</button>
      </header>

      {/* Messages */}
      <main className="stream-messages">
        {messages.length === 0 && !currentResponse && (
          <div className="welcome-screen">
            <Zap size={48} />
            <h2>What can I help you with?</h2>
            <p>I respond instantly - try me!</p>
            <div className="quick-btns">
              <button onClick={() => sendMessage("Schedule a meeting tomorrow at 2pm")}>
                <Calendar size={16} /> Meeting
              </button>
              <button onClick={() => sendMessage("Send email to john@test.com")}>
                <Mail size={16} /> Email
              </button>
              <button onClick={() => sendMessage("Remind me to call mom at 5pm")}>
                <Bell size={16} /> Reminder
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`msg ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="user-msg">{msg.content}</div>
            ) : msg.role === 'error' ? (
              <div className="error-msg">⚠️ {msg.content}</div>
            ) : (
              <div className="ai-msg">
                <div className="ai-avatar">AI</div>
                <div className="ai-content">
                  {msg.content}
                  
                  {msg.hasAction && idx === messages.length - 1 && pendingAction && (
                    <div className="action-btns">
                      <button className="yes-btn" onClick={() => confirmAction(true)} disabled={isStreaming}>
                        <Check size={16} /> Yes, do it
                      </button>
                      <button className="no-btn" onClick={() => confirmAction(false)} disabled={isStreaming}>
                        <X size={16} /> Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Streaming response */}
        {currentResponse && (
          <div className="msg assistant streaming">
            <div className="ai-msg">
              <div className="ai-avatar"><Loader className="spin" size={16} /></div>
              <div className="ai-content">
                {currentResponse}
                <span className="cursor">▊</span>
              </div>
            </div>
          </div>
        )}

        {/* Thinking */}
        {isStreaming && !currentResponse && (
          <div className="msg assistant">
            <div className="ai-msg">
              <div className="ai-avatar">AI</div>
              <div className="ai-content thinking">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      <footer className="stream-input">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything..."
            disabled={isStreaming}
            autoFocus
          />
          {isStreaming ? (
            <button type="button" onClick={stopStreaming} className="stop-btn">
              <Square size={18} />
            </button>
          ) : (
            <button type="submit" disabled={!input.trim()} className="send-btn">
              <Send size={18} />
            </button>
          )}
        </form>
      </footer>
    </div>
  )
}

export default App
