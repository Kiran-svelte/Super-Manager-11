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
import TaskAdaptiveWorkspace from './TaskAdaptiveWorkspace'


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

  // Initialize userId from localStorage
  useEffect(() => {
    let id = localStorage.getItem('super_manager_user_id')
    if (!id) { id = 'user_' + Math.random().toString(36).substring(2, 15); localStorage.setItem('super_manager_user_id', id) }
    setUserId(id)
  }, [])

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem('super_manager_session_id')
    const savedMessages = localStorage.getItem('super_manager_messages')
    if (savedSession) setSessionId(savedSession)
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages)
        // Restore timestamps as Date objects
        const restored = parsed.map(m => ({ ...m, timestamp: new Date(m.timestamp) }))
        setMessages(restored)
      } catch (e) { console.error('Failed to restore messages:', e) }
    }
  }, [])

  // Save chat to localStorage when messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('super_manager_messages', JSON.stringify(messages))
    }
    if (sessionId) {
      localStorage.setItem('super_manager_session_id', sessionId)
    }
  }, [messages, sessionId])

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
    <TaskAdaptiveWorkspace 
      messages={messages}
      input={input}
      setInput={setInput}
      send={send}
      loading={loading}
      AgentSteps={AgentSteps}
      UIComponentRenderer={UIComponentRenderer}
      sessionId={sessionId}
      // Settings, Integrations, TaskPanel props
      showSettings={showSettings}
      setShowSettings={setShowSettings}
      showIntegrations={showIntegrations}
      setShowIntegrations={setShowIntegrations}
      showTaskPanel={showTaskPanel}
      setShowTaskPanel={setShowTaskPanel}
      SettingsPanel={AISettings}
      IntegrationsPanel={IntegrationsHub}
      TaskPanelComponent={() => <TaskPanel refreshTrigger={taskRefreshTrigger} />}
    />
  )
}

export default App
