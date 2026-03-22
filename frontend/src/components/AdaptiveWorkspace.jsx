/**
 * AdaptiveWorkspace - Task-specific dynamic workspace
 * 
 * Dynamically assembles panels based on task type:
 * - CODE: File tree + Editor + Terminal + Live Preview
 * - MEETING: Time slots + Attendees + Video tiles
 * - TRADE: Price chart + Order + Confirm block
 * - SHOPPING: Products + Checkout
 * - TRAVEL: Flights + Seat map
 * - VIDEO: Preview + Timeline + AI tools
 * - SOCIAL: Post preview + Publish settings
 * - BROWSER: Step tracker + Browser view (fallback)
 */

import React, { useState, useEffect, useRef } from 'react'
import './AdaptiveWorkspace.css'

// Task type configurations
const TASK_CONFIGS = {
  code: {
    icon: '📄',
    label: 'Code IDE',
    badges: [{ type: 'purple', text: 'IDE' }, { type: 'green', text: 'Live' }],
    panels: ['files', 'editor', 'preview'],
    hasLiveIndicator: true
  },
  meeting: {
    icon: '📞',
    label: 'Meeting',
    badges: [{ type: 'purple', text: 'Meeting' }, { type: 'blue', text: 'Jitsi ready' }],
    panels: ['calendar', 'video'],
    hasLiveIndicator: true
  },
  trade: {
    icon: '📈',
    label: 'Trade',
    badges: [{ type: 'red', text: 'High risk' }, { type: 'purple', text: 'Confirm needed' }],
    panels: ['chart', 'order'],
    hasLiveIndicator: true
  },
  shopping: {
    icon: '🛍️',
    label: 'Shopping',
    badges: [{ type: 'green', text: 'Low risk' }],
    panels: ['products', 'checkout']
  },
  travel: {
    icon: '✈️',
    label: 'Travel',
    badges: [{ type: 'amber', text: 'Medium risk' }],
    panels: ['flights', 'seatmap']
  },
  video: {
    icon: '🎬',
    label: 'Video',
    badges: [{ type: 'purple', text: 'Video mode' }, { type: 'amber', text: 'AI editing' }],
    panels: ['videoPreview', 'timeline', 'aiTools'],
    hasLiveIndicator: true
  },
  social: {
    icon: '📷',
    label: 'Social',
    badges: [{ type: 'purple', text: 'Social' }, { type: 'green', text: 'AI drafted' }],
    panels: ['postPreview', 'publishSettings']
  },
  browser: {
    icon: '🔍',
    label: 'Browser',
    badges: [{ type: 'blue', text: 'Browser mode' }, { type: 'amber', text: 'AI navigating' }],
    panels: ['stepTracker', 'browserView']
  }
}

// ============================================================================
// CODE IDE PANELS
// ============================================================================
function FilesPanel({ files, activeFile, onSelectFile }) {
  const defaultFiles = [
    { name: 'backend/', type: 'folder' },
    { name: 'server.js', type: 'file', active: true },
    { name: 'middleware.js', type: 'file' },
    { name: 'routes.js', type: 'file' },
    { name: 'frontend/', type: 'folder' },
    { name: 'App.js', type: 'file', new: true },
    { name: 'package.json', type: 'file' }
  ]
  const fileList = files || defaultFiles

  return (
    <div className="aw-panel" style={{ width: 140 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">📁</span>
        <span className="aw-ph-title">Files</span>
      </div>
      <div className="aw-panel-body">
        {fileList.map((f, i) => (
          <div
            key={i}
            className={`aw-ftree-item ${f.type === 'folder' ? 'folder' : ''} ${f.active ? 'active' : ''}`}
            onClick={() => onSelectFile?.(f)}
          >
            <span>{f.type === 'folder' ? '📁' : '📄'}</span>
            <span className={f.new ? 'new' : ''}>{f.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function EditorPanel({ code, filename, terminalOutput }) {
  const defaultCode = `// MantiBank — secure Express server
const express = require('express');
const helmet  = require('helmet');
const cors    = require('cors');
const app = express();
app.use(helmet());
app.use(cors({ origin: process.env.ORIGINS }));
app.listen(3001);`

  const defaultTerminal = [
    { type: 'success', text: '✔ npm install done' },
    { type: 'command', text: '$ node server.js' },
    { type: 'success', text: '✔ MantiBank running :3001' },
    { type: 'prompt', text: '$ ' }
  ]

  return (
    <div className="aw-panel" style={{ flex: 1, minWidth: 0 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">✏️</span>
        <span className="aw-ph-title">{filename || 'server.js'}</span>
        <span className="aw-badge purple" style={{ fontSize: 8 }}>active</span>
      </div>
      <div className="aw-panel-body" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="aw-code-editor">
          <pre>{code || defaultCode}</pre>
        </div>
        <div className="aw-terminal">
          {(terminalOutput || defaultTerminal).map((line, i) => (
            <div key={i} className={`term-line ${line.type}`}>
              {line.text}
              {line.type === 'prompt' && <span className="term-cursor" />}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function LivePreviewPanel({ preview }) {
  return (
    <div className="aw-panel" style={{ flex: 1, minWidth: 0 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">🖼️</span>
        <span className="aw-ph-title">Live preview — localhost:3000</span>
        <div className="aw-live-dot" />
        <span style={{ fontSize: 8, color: '#3fb950' }}>running</span>
      </div>
      <div className="aw-panel-body">
        <div className="aw-bank-preview">
          <div className="bank-nav">
            <div className="bank-logo">
              <div className="bank-icon">M</div>
              Manti Bank
            </div>
            <div className="bank-links">
              <span>Home</span><span>Transfer</span><span>History</span>
            </div>
          </div>
          <div className="bank-body">
            <div className="balance-card">
              <div className="balance-label">Total balance</div>
              <div className="balance-amount">₹2,45,830</div>
              <div className="balance-account">MANTI •••• 4821</div>
            </div>
            <div className="quick-actions">
              <div className="qa-btn">📅 Pay</div>
              <div className="qa-btn">🔄 Send</div>
              <div className="qa-btn">💳 Deposit</div>
              <div className="qa-btn">📈 Invest</div>
            </div>
            <div className="txn-list">
              <div className="txn-header">Transactions</div>
              <div className="txn-item">
                <div className="txn-icon" style={{ background: '#e8f0fe' }}>🏠</div>
                <div className="txn-info">
                  <div className="txn-name">Amazon</div>
                  <div className="txn-date">Today</div>
                </div>
                <div className="txn-amount negative">-₹1,299</div>
              </div>
              <div className="txn-item">
                <div className="txn-icon" style={{ background: '#e8f5e9' }}>💰</div>
                <div className="txn-info">
                  <div className="txn-name">Salary</div>
                  <div className="txn-date">Mar 22</div>
                </div>
                <div className="txn-amount positive">+₹75,000</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// MEETING PANELS
// ============================================================================
function CalendarPanel({ slots, attendees }) {
  const defaultSlots = [
    { time: '9:00 AM', status: 'gone' },
    { time: '10:00 AM', status: 'selected' },
    { time: '11:00 AM', status: 'available' },
    { time: '2:00 PM', status: 'available' },
    { time: '3:00 PM', status: 'gone' },
    { time: '4:00 PM', status: 'available' }
  ]

  const defaultAttendees = [
    { name: 'You', initials: 'YO', status: 'Available', color: '#7c3aed' },
    { name: 'Raj Kumar', initials: 'RK', status: 'Checking...', color: '#1f6feb' }
  ]

  return (
    <div className="aw-panel" style={{ flex: 1 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">📅</span>
        <span className="aw-ph-title">Time slots — tomorrow</span>
      </div>
      <div className="aw-panel-body">
        <div className="slot-grid">
          {(slots || defaultSlots).map((slot, i) => (
            <div key={i} className={`slot ${slot.status}`}>{slot.time}</div>
          ))}
        </div>
        <div className="aw-divider" />
        <div className="aw-section">Attendees</div>
        {(attendees || defaultAttendees).map((att, i) => (
          <div key={i} className="attendee">
            <div className="att-avatar" style={{ background: `${att.color}44`, color: att.color }}>
              {att.initials}
            </div>
            <div>
              <div className="att-name">{att.name}</div>
              <div className="att-status">{att.status}</div>
            </div>
          </div>
        ))}
        <div className="aw-section" style={{ marginTop: 6 }}>Platform</div>
        <div className="platform-row">
          <div className="slot selected">Jitsi</div>
          <div className="slot">Zoom</div>
          <div className="slot">Meet</div>
        </div>
        <button className="confirm-btn">Confirm &amp; send invites</button>
      </div>
    </div>
  )
}

function VideoTilesPanel() {
  return (
    <div className="aw-panel" style={{ flex: 1 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">📹</span>
        <span className="aw-ph-title">Live meeting preview</span>
        <div className="aw-live-dot" />
        <span style={{ fontSize: 8, color: '#3fb950' }}>Jitsi</span>
      </div>
      <div className="aw-panel-body">
        <div className="cam-grid">
          <div className="cam">
            <div className="cam-live">LIVE</div>
            <span style={{ fontSize: 18 }}>👤</span>
            <div className="cam-name">You</div>
          </div>
          <div className="cam">
            <span style={{ fontSize: 18 }}>👤</span>
            <div className="cam-name">Raj Kumar</div>
          </div>
        </div>
        <div className="meet-controls">
          <div className="mc">🎙️</div>
          <div className="mc">🎬</div>
          <div className="mc green">📞</div>
          <div className="mc red">▼</div>
        </div>
        <div className="aw-divider" />
        <div className="aw-section">Recording &amp; sharing</div>
        <div className="rec-options">
          <div className="slot selected">📹 Record</div>
          <div className="slot selected">📋 Transcript</div>
          <div className="slot">📥 Auto-email</div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// BROWSER FALLBACK PANEL (No API case)
// ============================================================================
function StepTrackerPanel({ steps }) {
  const defaultSteps = [
    { status: 'ok', text: 'Found insurer: Tata AIG (from your email)' },
    { status: 'ok', text: 'Opened tataaig.com, logged in' },
    { status: 'run', text: 'Navigating to renewal page...' },
    { status: 'td', text: 'Fill vehicle details' },
    { status: 'td', text: 'Show you quote — confirm before paying' }
  ]

  return (
    <div className="aw-panel" style={{ flex: 1 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">🔍</span>
        <span className="aw-ph-title">What I'm doing</span>
      </div>
      <div className="aw-panel-body">
        <div className="browser-notice">
          No direct API for this. I'm opening the site and doing it myself. You just watch.
        </div>
        <div className="steps-list">
          {(steps || defaultSteps).map((step, i) => (
            <div key={i} className="step-item">
              <div className={`step-dot ${step.status}`}>
                {step.status === 'ok' ? '✓' : step.status === 'run' ? '▪' : ''}
              </div>
              <span>{step.text}</span>
            </div>
          ))}
        </div>
        <div className="aw-divider" />
        <div className="aw-section">From your memory</div>
        <div className="memory-fields">
          <div className="mem-field"><span className="mem-label">Policy</span><span className="mem-value">TTA-2024-MH-99201</span></div>
          <div className="mem-field"><span className="mem-label">Vehicle</span><span className="mem-value">MH12 AB 1234</span></div>
          <div className="mem-field"><span className="mem-label">Insurer</span><span className="mem-value">Tata AIG</span></div>
        </div>
      </div>
    </div>
  )
}

function BrowserViewPanel() {
  return (
    <div className="aw-panel" style={{ flex: 1.2 }}>
      <div className="aw-panel-header">
        <span className="aw-ph-icon">🌐</span>
        <span className="aw-ph-title">Browser — live view</span>
        <span className="ai-cursor-badge">AI cursor active</span>
      </div>
      <div className="aw-panel-body">
        <div className="browser-bar">
          <div className="browser-dots">
            <span className="dot red" />
            <span className="dot yellow" />
            <span className="dot green" />
          </div>
          <div className="browser-url">tataaig.com/renew-policy</div>
        </div>
        <div className="browser-content">
          <div className="bf-row">
            <div className="bf-label">Policy no.</div>
            <div className="bf-input active">TTA-2024-MH-99201 |</div>
          </div>
          <div className="bf-row">
            <div className="bf-label">Reg. no.</div>
            <div className="bf-input">MH12 AB 1234</div>
          </div>
          <div className="bf-row">
            <div className="bf-label">Mobile</div>
            <div className="bf-input">+91 98XXXXXXXX</div>
          </div>
          <div className="bf-row" style={{ justifyContent: 'flex-end', marginTop: 4 }}>
            <button className="bf-btn">Continue</button>
          </div>
          <div className="browser-note">
            After renewal, I'll save the new policy number and remind you 30 days before next year's expiry — automatically.
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// CAPTCHA FALLBACK (Human-in-the-loop)
// ============================================================================
function CaptchaFallback({ captchaUrl, onSolved, onCancel }) {
  const [solving, setSolving] = useState(false)

  const handleOpenCaptcha = () => {
    window.open(captchaUrl, '_blank', 'width=500,height=600')
    setSolving(true)
  }

  return (
    <div className="captcha-fallback">
      <div className="captcha-header">
        <span className="captcha-icon">🔐</span>
        <h3>Human verification needed</h3>
      </div>
      <p className="captcha-desc">
        The site requires CAPTCHA verification. I can't solve this automatically, 
        but you can help by clicking below.
      </p>
      {!solving ? (
        <div className="captcha-actions">
          <button className="captcha-btn primary" onClick={handleOpenCaptcha}>
            Open CAPTCHA in new tab
          </button>
          <button className="captcha-btn secondary" onClick={onCancel}>
            Cancel task
          </button>
        </div>
      ) : (
        <div className="captcha-waiting">
          <div className="captcha-spinner" />
          <p>Waiting for you to complete the CAPTCHA...</p>
          <button className="captcha-btn secondary" onClick={() => onSolved?.()}>
            I've completed it
          </button>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// TASK PANEL (Right sidebar)
// ============================================================================
function TaskPanel({ tasks, activeTask, onSelectTask }) {
  if (!tasks?.length) return null

  const dotColors = { ok: 'ts-ok', run: 'ts-run', td: 'ts-td' }
  const fillColors = { CODE: 'pf-g', MEETING: 'pf-p', TRADE: 'pf-b', SHOPPING: 'pf-a' }

  return (
    <div className="aw-task-panel">
      <div className="tp-head">
        <span>Tasks</span>
        <span className="tp-live">● live</span>
      </div>
      <div className="tp-list">
        {tasks.map((task, i) => (
          <div
            key={i}
            className={`t-item ${task.id === activeTask ? 'active' : ''}`}
            onClick={() => onSelectTask?.(task)}
          >
            <div className="t-name">
              <span>{task.icon}</span>
              {task.label}
            </div>
            <div className="t-type">{task.type}</div>
            <div className="t-bar">
              <div className={`t-fill ${fillColors[task.type] || 'pf-p'}`} style={{ width: `${task.pct}%` }} />
            </div>
            {task.id === activeTask && task.steps && (
              <div className="t-steps">
                {task.steps.map((step, j) => (
                  <div key={j} className="tstep">
                    <div className={`ts-dot ${dotColors[step[0]]}`}>
                      {step[0] === 'ok' ? '✓' : step[0] === 'run' ? '▪' : ''}
                    </div>
                    <span>{step[1]}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// HOME STATE (Blank workspace)
// ============================================================================
function HomeState({ onTaskSelect }) {
  const examples = [
    { task: 'code', text: 'build a banking app' },
    { task: 'meeting', text: 'schedule a meeting tomorrow' },
    { task: 'trade', text: 'buy 0.1 BTC now' },
    { task: 'shopping', text: 'book me a shirt for weekend' },
    { task: 'travel', text: 'fly me to Goa Friday' },
    { task: 'video', text: 'edit my product video' },
    { task: 'social', text: 'post launch on instagram' },
    { task: 'browser', text: 'renew my car insurance' }
  ]

  return (
    <div className="aw-home">
      <div className="home-logo">S</div>
      <div className="home-title">Nothing running yet.</div>
      <div className="home-sub">
        Give me any task. A workspace will open automatically — built for exactly that task, with every panel it needs.
      </div>
      <div className="task-examples">
        <div className="ex-label">Click any of these to see how the workspace assembles:</div>
        <div className="ex-row">
          {examples.slice(0, 3).map((ex, i) => (
            <div key={i} className="ex-pill" onClick={() => onTaskSelect?.(ex.task, ex.text)}>
              {ex.text}
            </div>
          ))}
        </div>
        <div className="ex-row">
          {examples.slice(3, 6).map((ex, i) => (
            <div key={i} className="ex-pill" onClick={() => onTaskSelect?.(ex.task, ex.text)}>
              {ex.text}
            </div>
          ))}
        </div>
        <div className="ex-row">
          {examples.slice(6).map((ex, i) => (
            <div key={i} className="ex-pill" onClick={() => onTaskSelect?.(ex.task, ex.text)}>
              {ex.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// THINKING STATE (Shown during workspace assembly)
// ============================================================================
function ThinkingState({ taskType, message }) {
  const thinkTexts = {
    code: ['Understood: code task, full stack app', 'Assembling: file tree + editor + terminal + live preview'],
    meeting: ['Understood: schedule meeting, tomorrow', 'Assembling: time slots + attendees + live video tiles'],
    trade: ['Understood: financial trade, HIGH RISK', 'Risk check: irreversible money action — confirm required'],
    shopping: ['Understood: shopping, apparel', 'Memory recall: size M, minimal style preference'],
    travel: ['Understood: travel, flight booking', 'Memory recall: window seat preference'],
    video: ['Understood: video editing task', 'Assembling: video preview + timeline + AI tools panel'],
    social: ['Understood: social media post', 'Assembling: post preview + publish controls'],
    browser: ['Understood: no API found', 'Falling back to browser automation']
  }

  const blockLabels = {
    code: ['File tree', 'Code editor', 'Terminal', 'Live preview'],
    meeting: ['Time slots', 'Attendee list', 'Video tiles', 'Recording'],
    trade: ['Live price chart', 'Order details', 'Confirm block'],
    shopping: ['Product results', 'Checkout block'],
    travel: ['Flight list', 'Seat map', 'Booking summary'],
    video: ['Video preview', 'Timeline editor', 'AI tools panel'],
    social: ['Post preview', 'Publish settings'],
    browser: ['Step tracker', 'Browser live view']
  }

  return (
    <div className="aw-thinking">
      <div className="think-box">
        <div className="think-logo">S</div>
        <div className="think-label">Thinking...</div>
      </div>
      <div className="think-steps">
        {(thinkTexts[taskType] || []).map((text, i) => (
          <div key={i} className="think-step">{text}</div>
        ))}
      </div>
      <div className="think-blocks">
        <div className="blocks-label">Assembling workspace panels:</div>
        <div className="blocks-row">
          {(blockLabels[taskType] || []).map((label, i) => (
            <div key={i} className={`think-block color-${i % 4}`}>{label}</div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function AdaptiveWorkspace({
  currentTask = null, // { type: 'code', message: 'build a banking app', data: {} }
  tasks = [],
  messages = [],
  onSendMessage,
  onTaskSelect,
  showCaptcha = false,
  captchaUrl = '',
  onCaptchaSolved,
  onCaptchaCancel
}) {
  const [state, setState] = useState('home') // 'home' | 'thinking' | 'workspace'
  const [taskType, setTaskType] = useState(null)
  const [input, setInput] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (currentTask) {
      setState('thinking')
      setTaskType(currentTask.type)
      // After 1.5s, show workspace
      const timer = setTimeout(() => setState('workspace'), 1500)
      return () => clearTimeout(timer)
    } else {
      setState('home')
      setTaskType(null)
    }
  }, [currentTask])

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage?.(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleExampleClick = (type, text) => {
    setInput(text)
    onTaskSelect?.(type, text)
  }

  const config = taskType ? TASK_CONFIGS[taskType] : null

  const renderWorkspace = () => {
    if (!taskType) return null

    switch (taskType) {
      case 'code':
        return (
          <>
            <FilesPanel />
            <EditorPanel />
            <LivePreviewPanel />
          </>
        )
      case 'meeting':
        return (
          <>
            <CalendarPanel />
            <VideoTilesPanel />
          </>
        )
      case 'browser':
        return (
          <>
            <StepTrackerPanel />
            <BrowserViewPanel />
          </>
        )
      default:
        return (
          <div className="aw-panel" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', color: '#8b949e' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>{config?.icon}</div>
              <div>{config?.label} workspace</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>Panels: {config?.panels?.join(', ')}</div>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="adaptive-workspace">
      {/* Top Bar */}
      <div className="aw-topbar">
        <div className="aw-logo">S</div>
        <div className="aw-brand">Super Manager</div>
        <div className="aw-online">
          <div className="aw-sdot" />
          <span>{currentTask ? `Working on: ${currentTask.message?.slice(0, 30)}...` : 'Waiting for a task...'}</span>
        </div>
      </div>

      <div className="aw-body">
        {/* Chat Column - Always visible */}
        <div className="aw-chat-col">
          <div className="aw-chat-msgs">
            <div className="aw-msg ai">
              <div className="aw-bub">Hey. Tell me what you need done. I'll figure out the rest.</div>
              <div className="aw-mts">Now</div>
            </div>
            {messages.map((msg, i) => (
              <div key={i} className={`aw-msg ${msg.role === 'user' ? 'user' : 'ai'}`}>
                <div className="aw-bub">{msg.text}</div>
                <div className="aw-mts">{msg.time || 'Now'}</div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="aw-chat-input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="what do you want done?"
            />
          </div>
        </div>

        {/* Workspace Area */}
        <div className="aw-ws-area">
          {state === 'home' && <HomeState onTaskSelect={handleExampleClick} />}
          {state === 'thinking' && <ThinkingState taskType={taskType} />}
          {state === 'workspace' && (
            <>
              {/* Workspace Header */}
              <div className="aw-ws-header">
                <span style={{ fontSize: 12 }}>{config?.icon}</span>
                <span className="aw-wsh-label">{currentTask?.message || 'Task'}</span>
                {config?.badges?.map((b, i) => (
                  <span key={i} className={`aw-badge ${b.type}`}>{b.text}</span>
                ))}
                {config?.hasLiveIndicator && (
                  <div className="aw-live-ind">
                    <div className="aw-live-dot" />
                    live
                  </div>
                )}
              </div>

              {/* Panels */}
              <div className="aw-panels">
                {showCaptcha ? (
                  <CaptchaFallback
                    captchaUrl={captchaUrl}
                    onSolved={onCaptchaSolved}
                    onCancel={onCaptchaCancel}
                  />
                ) : (
                  renderWorkspace()
                )}
              </div>
            </>
          )}
        </div>

        {/* Task Panel (Right) */}
        {tasks.length > 0 && (
          <TaskPanel tasks={tasks} activeTask={currentTask?.id} onSelectTask={onTaskSelect} />
        )}
      </div>
    </div>
  )
}
