import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  Send, Check, X, Settings, Bot, Mail, Calendar, 
  Ticket, Shield, ExternalLink, AlertCircle, Globe, Image, 
  Zap, Sparkles, ChevronDown, ChevronUp, Search, 
  MessageSquare, Clock, CheckCircle2, XCircle, Code2,
  ArrowRight, Cpu, Brain, Workflow, ListTodo, Plug
} from 'lucide-react'
import TaskPanel from './components/TaskPanel'
import AISettings from './components/AISettings'
import IntegrationsHub from './components/IntegrationsHub'
import UIComponentRenderer from './components/InteractiveUI'
import './App.css'

import { apiUrl } from './lib/apiBase'

const stepIcons = {
  thinking: Brain, action: Zap, code_exec: Code2, action_result: CheckCircle2,
  answer: MessageSquare, ask: MessageSquare, confirm_needed: Shield,
  step_progress: Workflow, error: XCircle,
}
const stepLabels = {
  thinking: 'Reasoning', action: 'Executing', code_exec: 'Running Code',
  action_result: 'Result', answer: 'Response', ask: 'Question',
  confirm_needed: 'Needs Approval', step_progress: 'Progress', error: 'Error',
}

function AgentSteps({ steps }) {
  const [expanded, setExpanded] = useState(false)
  const meaningful = steps.filter(s => s.type !== 'step_progress' && s.content?.trim())
  if (!meaningful.length) return null
  return (
    <div className="agent-steps">
      <button className="steps-toggle" onClick={() => setExpanded(!expanded)}>
        <Workflow size={14} />
        <span>{meaningful.length} step{meaningful.length > 1 ? 's' : ''} taken</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div className="steps-list" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}>
            {meaningful.map((step, idx) => {
              const Icon = stepIcons[step.type] || Zap
              return (
                <motion.div key={idx} className={`step-item step-${step.type}`} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }}>
                  <div className="step-icon"><Icon size={12} /></div>
                  <div className="step-body">
                    <span className="step-label">{stepLabels[step.type] || step.type}</span>
                    <span className="step-text">{step.content?.length > 300 ? step.content.slice(0, 300) + '...' : step.content}</span>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [pendingConfirm, setPendingConfirm] = useState(false)
  const [showTaskPanel, setShowTaskPanel] = useState(false)
  const [taskRefreshTrigger, setTaskRefreshTrigger] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [showIntegrations, setShowIntegrations] = useState(false)
  const [hasAIIdentity, setHasAIIdentity] = useState(null)
  const [userId, setUserId] = useState(null)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    let id = localStorage.getItem('super_manager_user_id')
    if (!id) { id = 'user_' + Math.random().toString(36).substring(2, 15); localStorage.setItem('super_manager_user_id', id) }
    setUserId(id)
  }, [])

  useEffect(() => {
    if (!userId) return
    const check = async () => {
      try {
        const res = await fetch(apiUrl(`/api/identity/status/${userId}`))
        const data = await res.json()
        setHasAIIdentity(data.has_identity)
      } catch { setHasAIIdentity(false) }
    }
    check()
  }, [userId])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { if (!loading) inputRef.current?.focus() }, [loading, messages])

  

  const send = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput(''); setLoading(true); setPendingConfirm(false)
    setMessages(prev => [...prev, { role: 'user', text: msg, timestamp: new Date() }])
    try {
      const res = await fetch(apiUrl('/api/chat'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg, session_id: sessionId, user_id: userId }) })
      const data = await res.json()
      setSessionId(data.session_id)
      setMessages(prev => [...prev, { role: 'ai', text: data.message, type: data.type, status: data.status, need: data.need, ui_components: data.ui_components, proof: data.proof, result: data.result, steps: data.steps, options: data.options, timestamp: new Date(), responseTime: data.response_time_ms }])
      const needsIntegration = Array.isArray(data.steps) && data.steps.some(s => {
        const d = s?.data || {}
        return d.requires_connection || d.required_integration || (d._meta && d._meta.error === 'integration_required')
      })
      if (needsIntegration) setShowIntegrations(true)
      if (data.status === 'confirm') setPendingConfirm(true)
      if (data.status === 'done' || data.status === 'success') setTaskRefreshTrigger(prev => prev + 1)
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', text: 'Connection failed. Check if server is running.', timestamp: new Date() }])
    } finally { setLoading(false) }
  }

  const handleAction = async (action, buttonId, metadata) => {
    if (loading) return; setLoading(true)
    try {
      const res = await fetch(apiUrl('/api/chat/action'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action, button_id: buttonId, metadata, session_id: sessionId, user_id: userId }) })
      const data = await res.json()
      if (data.action === 'redirect' && data.url) { window.open(data.url, '_blank'); setLoading(false); return }
      setSessionId(data.session_id)
      setMessages(prev => [...prev, { role: 'ai', text: data.message, type: data.type, status: data.status, ui_components: data.ui_components, proof: data.proof, result: data.result, timestamp: new Date(), responseTime: data.response_time_ms }])
      const needsIntegration = Array.isArray(data.steps) && data.steps.some(s => {
        const d = s?.data || {}
        return d.requires_connection || d.required_integration || (d._meta && d._meta.error === 'integration_required')
      })
      if (needsIntegration) setShowIntegrations(true)
      if (data.status === 'done' || data.status === 'success') setTaskRefreshTrigger(prev => prev + 1)
    } catch { setMessages(prev => [...prev, { role: 'error', text: 'Failed to process action.' }]) }
    finally { setLoading(false) }
  }

  const handleSubmit = (e) => { e.preventDefault(); send() }
  const confirm = (yes) => send(yes ? 'yes' : 'no')
  const fmtTime = d => d ? new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''

  return (
    <div className="super-app">
      {/* Animated Background */}
      <div className="bg-gradient" />
      <div className="bg-grid" />
      <div className="bg-orb bg-orb-1" />
      <div className="bg-orb bg-orb-2" />
      <div className="bg-orb bg-orb-3" />

      <div className={`app-layout ${showTaskPanel ? 'with-panel' : ''}`}>
        <div className="chat-container">
          {/* Header */}
          <header className="chat-header">
            <div className="header-brand">
              <div className="brand-icon"><Sparkles size={22} /></div>
              <div><h1>Super Manager</h1><span className="header-subtitle">Your AI Assistant</span></div>
            </div>
            <div className="header-controls">
              <button className="icon-btn" onClick={() => setShowIntegrations(true)} title="Integrations"><Plug size={18} /></button>
              <button className="icon-btn" onClick={() => setShowSettings(true)} title="Settings"><Settings size={18} /></button>
              <button className={`icon-btn ${showTaskPanel ? 'active' : ''}`} onClick={() => setShowTaskPanel(!showTaskPanel)} title="Tasks"><ListTodo size={18} /></button>
              <div className="status-badge"><span className="status-dot-live" />Online</div>
            </div>
          </header>

          {/* Messages */}
          <main className="chat-messages">
            {messages.length === 0 && (
              <motion.div className="welcome-section" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
                <div className="welcome-glow" />
                <motion.div className="welcome-avatar" animate={{ boxShadow: ['0 0 20px rgba(99,102,241,0.3)', '0 0 40px rgba(99,102,241,0.5)', '0 0 20px rgba(99,102,241,0.3)'] }} transition={{ duration: 3, repeat: Infinity }}>
                  <Brain size={40} />
                </motion.div>
                <h2 className="welcome-title">What can I do for you?</h2>
                <p className="welcome-desc">I execute tasks autonomously — emails, meetings, web research, image generation, and more.</p>
                <div className="quick-grid">
                  {[
                    { icon: Mail, label: 'Send Email', msg: 'Send an email to ', color: '#6366f1' },
                    { icon: Calendar, label: 'Create Meeting', msg: 'Create a Zoom meeting for tomorrow 3pm with ', color: '#8b5cf6' },
                    { icon: Search, label: 'Web Research', msg: 'Search the web for ', color: '#06b6d4' },
                    { icon: Image, label: 'Generate Image', msg: 'Generate an image of ', color: '#f43f5e' },
                    { icon: Globe, label: 'Browse Website', msg: 'Browse and extract info from ', color: '#10b981' },
                    { icon: Ticket, label: 'Book Tickets', msg: 'Find and book tickets for ', color: '#f59e0b' },
                  ].map((item, i) => (
                    <motion.button key={i} className="quick-card" onClick={() => { setInput(item.msg); inputRef.current?.focus() }}
                      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i + 0.3, duration: 0.4 }}
                      whileHover={{ y: -4, scale: 1.02 }} whileTap={{ scale: 0.98 }} style={{ '--card-accent': item.color }}>
                      <div className="quick-card-icon" style={{ background: `${item.color}20`, color: item.color }}><item.icon size={20} /></div>
                      <span>{item.label}</span>
                      <ArrowRight size={14} className="quick-arrow" />
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}

            <AnimatePresence>
              {messages.map((m, i) => (
                <motion.div key={i} className={`message message-${m.role}`} initial={{ opacity: 0, y: 16, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.3 }}>
                  {m.role === 'user' ? (
                    <div className="msg-row msg-row-user">
                      <div className="msg-bubble msg-user"><span>{m.text}</span></div>
                    </div>
                  ) : m.role === 'error' ? (
                    <div className="msg-row">
                      <div className="msg-avatar msg-avatar-error"><AlertCircle size={14} /></div>
                      <div className="msg-bubble msg-error">{m.text}</div>
                    </div>
                  ) : (
                    <div className="msg-row">
                      <div className="msg-avatar msg-avatar-ai"><Sparkles size={14} /></div>
                      <div className="msg-bubble msg-ai">
                        <div className="msg-ai-content">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" />
                            }}
                          >
                            {m.text || ''}
                          </ReactMarkdown>
                        </div>

                        {m.steps && m.steps.length > 1 && <AgentSteps steps={m.steps} />}

                        {m.ui_components && <div className="msg-ui-components"><UIComponentRenderer component={m.ui_components} onAction={handleAction} onMessage={send} loading={loading} /></div>}
                        {m.steps && m.steps.some(s => s.name === 'human_fallback') && (
                          <div className="msg-ui-components">
                            <HumanFallback 
                              data={m.steps.find(s => s.name === 'human_fallback').data} 
                              onComplete={() => send('I have completed the manual steps. Please proceed.')} 
                              onDismiss={() => send('I cannot complete these steps right now.')} 
                            />
                          </div>
                        )}
                        {m.type === 'human_fallback' && m.context && (
                          <div className="msg-ui-components">
                            <HumanFallback 
                              data={{context: m.context}} 
                              onComplete={() => send('I have completed the manual steps. Please proceed.')} 
                              onDismiss={() => send('I cannot complete these steps right now.')} 
                            />
                          </div>
                        )}


                        {m.options && m.options.length > 0 && (
                          <div className="msg-options">
                            {m.options.map((opt, idx) => (
                              <motion.button key={idx} className="option-chip" onClick={() => send(opt.label || opt.value || opt)} disabled={loading} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                                {opt.label || opt.value || opt}
                              </motion.button>
                            ))}
                          </div>
                        )}

                        {m.proof && (
                          <div className="msg-proof">
                            <Shield size={14} /><span>Verified • {m.proof.proof_id}</span>
                            {m.proof.verification_url && <a href={m.proof.verification_url} target="_blank" rel="noopener noreferrer">Verify <ExternalLink size={11} /></a>}
                          </div>
                        )}

                        {m.status === 'confirm' && !m.ui_components && i === messages.length - 1 && pendingConfirm && (
                          <div className="msg-confirm">
                            <motion.button className="confirm-btn confirm-yes" onClick={() => confirm(true)} disabled={loading} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}><Check size={16} /> Approve</motion.button>
                            <motion.button className="confirm-btn confirm-no" onClick={() => confirm(false)} disabled={loading} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}><X size={16} /> Cancel</motion.button>
                          </div>
                        )}

                        {m.responseTime && <div className="msg-meta"><Clock size={11} /> {m.responseTime < 1000 ? `${Math.round(m.responseTime)}ms` : `${(m.responseTime/1000).toFixed(1)}s`}</div>}
                      </div>
                    </div>
                  )}
                  {m.timestamp && <div className={`msg-time ${m.role === 'user' ? 'msg-time-right' : 'msg-time-left'}`}>{fmtTime(m.timestamp)}</div>}
                </motion.div>
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div className="message message-ai" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="msg-row">
                  <div className="msg-avatar msg-avatar-ai"><Sparkles size={14} /></div>
                  <div className="msg-bubble msg-ai msg-typing">
                    <div className="typing-dots">
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: 0 }} />
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }} />
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }} />
                    </div>
                    <span className="typing-label">Processing...</span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={endRef} />
          </main>

          {/* Input */}
          <footer className="chat-footer">
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)} placeholder="Type your message..." disabled={loading} autoFocus />
                <motion.button type="submit" disabled={!input.trim() || loading} className="send-btn" whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}><Send size={18} /></motion.button>
              </div>
            </form>
            <div className="footer-meta">
              <span><Shield size={11} /> Secure</span>
              <span className="sep">•</span>
              <span><Cpu size={11} /> AI Powered</span>
              <span className="sep">•</span>
              <span><Zap size={11} /> Real-time</span>
            </div>
          </footer>
        </div>

        <AnimatePresence>
          {showTaskPanel && (
            <motion.div className="task-panel-wrap" initial={{ width: 0, opacity: 0 }} animate={{ width: 380, opacity: 1 }} exit={{ width: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                <TaskPanel userId={userId} refreshTrigger={taskRefreshTrigger} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {showSettings && <AISettings userId={userId} onClose={() => setShowSettings(false)} onSave={() => { setHasAIIdentity(true); setShowSettings(false) }} />}
      {showIntegrations && <div className="modal-overlay" style={{position:"fixed", top:0, left:0, right:0, bottom:0, background:"rgba(0,0,0,0.7)", zIndex:999, display:"flex", alignItems:"center", justifyContent:"center"}} onClick={(e) => { if(e.target.className === "modal-overlay") setShowIntegrations(false); }}><div style={{position:"relative"}}><button onClick={()=>setShowIntegrations(false)} style={{position:"absolute", top:10, right:15, background:"none", border:"none", color:"#fff", cursor:"pointer", fontSize:"20px"}}>×</button><IntegrationsHub userId={userId} /></div></div>}
    </div>
  )
}

export default App
