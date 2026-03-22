/**
 * LivePreview Component - IDE-like workspace for code generation
 * 
 * Features:
 * - Split pane: Code editor on left, live preview on right
 * - File tabs for multiple files
 * - Terminal output
 * - Desktop/Mobile preview toggle
 * - Real-time updates as AI generates code
 */

import React, { useState, useEffect, useRef } from 'react'
import { 
  Code, 
  Eye, 
  Monitor, 
  Smartphone, 
  Terminal,
  Play,
  X,
  FileCode,
  FolderOpen,
  ChevronRight,
  RotateCcw,
  ExternalLink,
  Maximize2,
  Minimize2
} from 'lucide-react'
import './LivePreview.css'

// Syntax highlighting helper
const highlightCode = (code, language) => {
  if (!code) return ''
  
  // Basic syntax highlighting
  const keywords = ['const', 'let', 'var', 'function', 'async', 'await', 'return', 'if', 'else', 'for', 'while', 'import', 'export', 'from', 'class', 'extends']
  const strings = /(["'`])(?:(?!\1)[^\\]|\\.)*?\1/g
  const comments = /\/\/.*$|\/\*[\s\S]*?\*\//gm
  const functions = /\b([a-zA-Z_]\w*)\s*\(/g
  const numbers = /\b\d+\.?\d*\b/g
  
  let highlighted = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Highlight strings
  highlighted = highlighted.replace(strings, '<span class="code-string">$&</span>')
  
  // Highlight comments
  highlighted = highlighted.replace(comments, '<span class="code-comment">$&</span>')
  
  // Highlight keywords
  keywords.forEach(kw => {
    const regex = new RegExp(`\\b${kw}\\b`, 'g')
    highlighted = highlighted.replace(regex, `<span class="code-keyword">${kw}</span>`)
  })
  
  // Highlight numbers
  highlighted = highlighted.replace(numbers, '<span class="code-number">$&</span>')
  
  return highlighted
}

export default function LivePreview({ 
  project = null, // { name: 'MantiBank', files: [{name, content, language}] }
  onClose,
  isFullscreen = false,
  onToggleFullscreen
}) {
  const [activeFile, setActiveFile] = useState(0)
  const [previewMode, setPreviewMode] = useState('desktop') // 'desktop' | 'mobile'
  const [terminalOutput, setTerminalOutput] = useState([
    { type: 'command', text: '$ npm install express helmet cors' },
    { type: 'output', text: 'added 187 packages in 4.2s' },
    { type: 'success', text: '✔ Dependencies installed' },
    { type: 'command', text: '$ node server.js' },
    { type: 'success', text: '✔ Server running on :3001' },
  ])
  const [showTerminal, setShowTerminal] = useState(true)
  
  const iframeRef = useRef(null)

  // Demo files if no project provided
  const defaultFiles = [
    {
      name: 'server.js',
      language: 'javascript',
      content: `// Express server
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

const app = express();
app.use(helmet());
app.use(cors());

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(3001, () => {
  console.log('Server running on :3001');
});`
    },
    {
      name: 'App.jsx',
      language: 'jsx',
      content: `import React from 'react';
import './App.css';

function App() {
  return (
    <div className="app">
      <header>
        <h1>MantiBank</h1>
      </header>
      <main>
        <div className="balance-card">
          <p>Total Balance</p>
          <h2>₹ 2,45,830.00</h2>
        </div>
      </main>
    </div>
  );
}

export default App;`
    },
    {
      name: 'index.html',
      language: 'html',
      content: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Manti Bank</title>
  <link rel="stylesheet" href="styles/main.css">
</head>
<body>
  <div id="root"></div>
  <script src="App.js"></script>
</body>
</html>`
    }
  ]

  const files = project?.files || defaultFiles
  const projectName = project?.name || 'New Project'

  const currentFile = files[activeFile]

  // Generate line numbers
  const getLineNumbers = (content) => {
    const lines = content.split('\n').length
    return Array.from({ length: lines }, (_, i) => i + 1)
  }

  return (
    <div className={`live-preview ${isFullscreen ? 'fullscreen' : ''}`}>
      {/* Header */}
      <div className="preview-header-bar">
        <div className="header-left">
          <span className="project-indicator">●</span>
          <span className="project-name">{projectName} /</span>
          <span className="badge badge-blue">IDE mode</span>
          <span className="badge badge-green">{files.length} files</span>
        </div>
        <div className="header-right">
          <div className="live-indicator">
            <span className="live-dot"></span>
            Live preview
          </div>
          <button className="icon-btn" onClick={onToggleFullscreen}>
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button className="icon-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="preview-main">
        {/* Code Pane */}
        <div className="code-pane">
          {/* File tabs */}
          <div className="file-tabs">
            {files.map((file, idx) => (
              <button
                key={idx}
                className={`file-tab ${activeFile === idx ? 'active' : ''}`}
                onClick={() => setActiveFile(idx)}
              >
                <FileCode size={12} />
                {file.name}
              </button>
            ))}
          </div>

          {/* Code editor */}
          <div className="code-editor">
            <div className="line-numbers">
              {getLineNumbers(currentFile.content).map(n => (
                <div key={n} className="line-number">{n}</div>
              ))}
            </div>
            <pre 
              className="code-content"
              dangerouslySetInnerHTML={{ 
                __html: highlightCode(currentFile.content, currentFile.language) 
              }}
            />
          </div>

          {/* Terminal */}
          {showTerminal && (
            <div className="terminal-pane">
              <div className="terminal-header">
                <Terminal size={12} />
                <span>Terminal</span>
                <button className="terminal-toggle" onClick={() => setShowTerminal(false)}>
                  <X size={12} />
                </button>
              </div>
              <div className="terminal-output">
                {terminalOutput.map((line, idx) => (
                  <div key={idx} className={`terminal-line ${line.type}`}>
                    {line.type === 'command' && <span className="prompt">$</span>}
                    {line.type === 'success' && <span className="success-icon">✔</span>}
                    <span>{line.text.replace(/^\$ /, '')}</span>
                  </div>
                ))}
                <div className="terminal-line command">
                  <span className="prompt">$</span>
                  <span className="cursor"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="pane-divider" />

        {/* Preview Pane */}
        <div className="preview-pane">
          {/* Preview header */}
          <div className="preview-controls">
            <div className="browser-dots">
              <span className="dot red" />
              <span className="dot yellow" />
              <span className="dot green" />
            </div>
            <div className="url-bar">localhost:3000 — {projectName}</div>
            <div className="preview-toggles">
              <button 
                className={`preview-toggle ${previewMode === 'desktop' ? 'active' : ''}`}
                onClick={() => setPreviewMode('desktop')}
              >
                <Monitor size={14} /> Desktop
              </button>
              <button 
                className={`preview-toggle ${previewMode === 'mobile' ? 'active' : ''}`}
                onClick={() => setPreviewMode('mobile')}
              >
                <Smartphone size={14} /> Mobile
              </button>
            </div>
          </div>

          {/* Preview content */}
          <div className={`preview-content ${previewMode}`}>
            {previewMode === 'mobile' && (
              <div className="phone-frame">
                <div className="phone-notch" />
                <div className="phone-screen">
                  <DemoApp projectName={projectName} />
                </div>
              </div>
            )}
            {previewMode === 'desktop' && (
              <div className="desktop-preview">
                <DemoApp projectName={projectName} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Demo App Preview (mock banking app)
function DemoApp({ projectName }) {
  return (
    <div className="demo-app">
      <nav className="demo-nav">
        <div className="demo-logo">
          <span className="logo-icon">M</span>
          {projectName}
        </div>
        <div className="demo-links">
          <span className="active">Dashboard</span>
          <span>Transfer</span>
          <span>History</span>
        </div>
      </nav>
      <main className="demo-main">
        <div className="balance-card">
          <div className="balance-label">Total Balance</div>
          <div className="balance-amount">₹ 2,45,830.00</div>
          <div className="balance-info">
            <span>Account: •••• 4821</span>
            <span>IFSC: MANT0001234</span>
          </div>
        </div>
        <div className="quick-actions">
          <button className="qa-btn">💳 Pay</button>
          <button className="qa-btn">↔️ Transfer</button>
          <button className="qa-btn">📥 Deposit</button>
          <button className="qa-btn">📈 Invest</button>
        </div>
        <div className="transactions">
          <h3>Recent Transactions</h3>
          <div className="txn">
            <span className="txn-icon">🏠</span>
            <div className="txn-info">
              <div>Amazon Pay</div>
              <small>Today, 2:14 PM</small>
            </div>
            <span className="txn-amount negative">- ₹1,299</span>
          </div>
          <div className="txn">
            <span className="txn-icon">💰</span>
            <div className="txn-info">
              <div>Salary credit</div>
              <small>Mar 22, 9:00 AM</small>
            </div>
            <span className="txn-amount positive">+ ₹75,000</span>
          </div>
        </div>
      </main>
    </div>
  )
}
