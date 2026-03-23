import React, { useEffect, useRef, useState } from "react";
import "./TaskWorkspace.css";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Settings, Plug, ListTodo, X } from 'lucide-react';

// Task type detection from message
function detectTaskType(message) {
  if (!message) return null;
  const text = message.toLowerCase();
  
  if (text.includes('build') || text.includes('code') || text.includes('app') || text.includes('website') || text.includes('create') && (text.includes('app') || text.includes('software'))) return 'code';
  if (text.includes('meeting') || text.includes('schedule') || text.includes('call') || text.includes('zoom') || text.includes('jitsi')) return 'meeting';
  if (text.includes('buy') || text.includes('trade') || text.includes('btc') || text.includes('stock') || text.includes('crypto')) return 'trade';
  if (text.includes('shop') || text.includes('order') || text.includes('shirt') || text.includes('buy') && !text.includes('btc')) return 'shopping';
  if (text.includes('flight') || text.includes('fly') || text.includes('travel') || text.includes('book') && text.includes('trip')) return 'flight';
  if (text.includes('video') || text.includes('edit') || text.includes('youtube')) return 'video';
  if (text.includes('post') || text.includes('instagram') || text.includes('social') || text.includes('facebook')) return 'social';
  if (text.includes('email') || text.includes('send') || text.includes('mail')) return 'email';
  return 'browser'; // fallback
}

// Task configurations
const TASK_CONFIG = {
  code: { icon: '📄', label: 'Code IDE', badges: [{ cls: 'bp', text: 'IDE' }, { cls: 'bg', text: 'Live' }] },
  meeting: { icon: '📞', label: 'Meeting', badges: [{ cls: 'bp', text: 'Meeting' }, { cls: 'bb', text: 'Jitsi ready' }] },
  trade: { icon: '📈', label: 'Trade', badges: [{ cls: 'br', text: 'High risk' }, { cls: 'bp', text: 'Confirm needed' }] },
  shopping: { icon: '🛍️', label: 'Shopping', badges: [{ cls: 'bg', text: 'Low risk' }] },
  flight: { icon: '✈️', label: 'Travel', badges: [{ cls: 'ba', text: 'Medium risk' }] },
  video: { icon: '🎬', label: 'Video Edit', badges: [{ cls: 'bp', text: 'Editor' }] },
  social: { icon: '📱', label: 'Social', badges: [{ cls: 'bp', text: 'Post' }] },
  email: { icon: '📧', label: 'Email', badges: [{ cls: 'bg', text: 'Send' }] },
  browser: { icon: '🌐', label: 'Browser', badges: [{ cls: 'ba', text: 'Fallback' }] }
};

// Extract code from AI response - check steps data, markdown, and result
function extractCodeFromResponse(messages) {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role === 'ai') {
      // 1. Check steps for code_exec events
      if (msg.steps && Array.isArray(msg.steps)) {
        for (let j = msg.steps.length - 1; j >= 0; j--) {
          const step = msg.steps[j];
          if (step.type === 'code_exec' && step.data?.code) {
            return { code: step.data.code, language: detectLanguage(step.data.code) };
          }
          // Also check confirm_needed for code
          if (step.type === 'confirm_needed' && step.data?.params?.code) {
            return { code: step.data.params.code, language: detectLanguage(step.data.params.code) };
          }
          if (step.type === 'confirm_needed' && step.data?.code) {
            return { code: step.data.code, language: detectLanguage(step.data.code) };
          }
        }
      }
      
      // 2. Check markdown code blocks in message text
      if (msg.text) {
        const codeBlockMatch = msg.text.match(/```(\w+)?\n([\s\S]*?)```/);
        if (codeBlockMatch) {
          return { code: codeBlockMatch[2], language: codeBlockMatch[1] || 'javascript' };
        }
      }
      
      // 3. Check result object
      if (msg.result?.code) {
        return { code: msg.result.code, language: detectLanguage(msg.result.code) };
      }
    }
  }
  return null;
}

// Detect programming language from code
function detectLanguage(code) {
  if (!code) return 'text';
  if (code.includes('const ') || code.includes('require(') || code.includes('import ') && code.includes('from ')) return 'javascript';
  if (code.includes('def ') || code.includes('import ') || code.includes('from flask')) return 'python';
  if (code.includes('<html') || code.includes('<!DOCTYPE')) return 'html';
  if (code.includes('{') && code.includes(':') && code.includes(';')) return 'css';
  return 'javascript';
}

// Extract files structure from AI response
function extractFilesFromResponse(messages, codeData) {
  const files = [];
  
  // If we detected language, suggest appropriate files
  if (codeData) {
    if (codeData.language === 'javascript') {
      files.push('server.js', 'package.json');
    } else if (codeData.language === 'python') {
      files.push('app.py', 'requirements.txt');
    } else if (codeData.language === 'html') {
      files.push('index.html', 'style.css');
    }
  }
  
  // Look for explicit file mentions
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role === 'ai' && msg.text) {
      const fileMatches = msg.text.match(/(?:create|file|generated?):\s*[`"]?([a-zA-Z0-9_\-./]+\.[a-zA-Z]+)[`"]?/gi);
      if (fileMatches) {
        fileMatches.forEach(m => {
          const name = m.match(/[a-zA-Z0-9_\-./]+\.[a-zA-Z]+/)?.[0];
          if (name && !files.includes(name)) files.push(name);
        });
      }
    }
  }
  
  return files.length > 0 ? files : ['index.js', 'package.json', 'README.md'];
}

// CODE WORKSPACE - Now uses AI-generated code with real terminal output
function CodeWorkspace({ taskMessage, messages, generatedCode, generatedFiles }) {
  const [activeFile, setActiveFile] = useState(generatedFiles[0] || 'index.js');
  
  // Extract terminal output from steps
  const terminalOutput = [];
  const lastAIMsg = messages.slice().reverse().find(m => m.role === 'ai' && m.steps);
  if (lastAIMsg?.steps) {
    lastAIMsg.steps.forEach(step => {
      if (step.type === 'code_exec') {
        terminalOutput.push({ type: 'cmd', text: '$ Executing code...' });
      } else if (step.type === 'action_result') {
        const success = step.data?._meta?.success;
        const error = step.data?._meta?.error;
        if (success) {
          terminalOutput.push({ type: 'ok', text: `✔ ${step.content}` });
        } else if (error) {
          terminalOutput.push({ type: 'err', text: `✗ ${error}` });
        } else {
          terminalOutput.push({ type: 'info', text: step.content });
        }
      }
    });
  }
  
  const code = generatedCode?.code || `// Waiting for AI to generate code...\n// Ask me to build something specific!`;
  const language = generatedCode?.language || 'javascript';
  
  return (
    <div className="panels">
      {/* File Tree */}
      <div className="panel" style={{width: '140px'}}>
        <div className="panel-header"><span className="ph-icon">📁</span><span className="ph-title">Files</span></div>
        <div className="panel-body">
          <div className="ftree-folder">📁 src/</div>
          {generatedFiles.map(f => (
            <div key={f} className={`ftree-item ${activeFile === f ? 'on' : ''}`} onClick={() => setActiveFile(f)}>
              📄 {f}
            </div>
          ))}
        </div>
      </div>
      
      {/* Editor + Terminal */}
      <div className="panel" style={{flex: 1, minWidth: 0}}>
        <div className="panel-header">
          <span className="ph-icon">✏️</span>
          <span className="ph-title">{activeFile}</span>
          <span className="badge bp" style={{fontSize: '8px'}}>{generatedCode ? 'AI Generated' : 'Waiting'}</span>
          <span className="badge bg" style={{fontSize: '8px', marginLeft: '4px'}}>{language}</span>
        </div>
        <div className="panel-body" style={{display: 'flex', flexDirection: 'column'}}>
          <div className="code-editor" style={{flex: 1, fontFamily: 'monospace', fontSize: '11px', lineHeight: 1.7, padding: '12px', whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflow: 'auto', maxHeight: '300px'}}>
            {code}
          </div>
          <div className="term" style={{borderTop: '0.5px solid #30363d', padding: '8px 12px', background: '#010409', fontFamily: 'monospace', fontSize: '10px', minHeight: '80px', maxHeight: '120px', overflow: 'auto'}}>
            {terminalOutput.length > 0 ? (
              terminalOutput.map((line, i) => (
                <div key={i}>
                  <span className={line.type === 'ok' ? 'tok' : line.type === 'err' ? 'terr' : line.type === 'cmd' ? 'tc' : 'tp2'}>
                    {line.text}
                  </span>
                </div>
              ))
            ) : (
              <>
                <div><span className="tp2">$ </span><span className="tc">Ready for execution</span></div>
                <div><span className="tp2">$ </span><span className="tcur"></span></div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Live Preview - Show based on language */}
      <div className="panel" style={{flex: 1, minWidth: 0}}>
        <div className="panel-header">
          <span className="ph-icon">👁️</span>
          <span className="ph-title">Preview</span>
          <div style={{display: 'flex', alignItems: 'center', gap: '3px', marginLeft: 'auto'}}>
            <div className={generatedCode ? "ldot" : "ldot-off"}></div>
            <span style={{fontSize: '8px', color: generatedCode ? '#3fb950' : '#8b949e'}}>{generatedCode ? 'ready' : 'waiting'}</span>
          </div>
        </div>
        <div className="panel-body">
          {generatedCode ? (
            <div style={{padding: '16px', height: '100%', display: 'flex', flexDirection: 'column', gap: '12px'}}>
              <div style={{background: '#161b22', border: '0.5px solid #30363d', borderRadius: '8px', padding: '12px'}}>
                <div style={{fontSize: '10px', color: '#8b949e', marginBottom: '8px'}}>Generated {language} code ready</div>
                <div style={{fontSize: '11px', color: '#e6edf3'}}>
                  {language === 'javascript' && '🚀 Express server ready to run on port 3000'}
                  {language === 'python' && '🐍 Python app ready to run'}
                  {language === 'html' && '🌐 HTML page ready to preview'}
                </div>
              </div>
              <div style={{background: '#0d419d22', border: '0.5px solid #1f6feb', borderRadius: '8px', padding: '12px'}}>
                <div style={{fontSize: '10px', color: '#58a6ff', marginBottom: '4px'}}>💡 Next steps:</div>
                <div style={{fontSize: '10px', color: '#8b949e'}}>
                  1. Copy the code to your project<br/>
                  2. Install dependencies<br/>
                  3. Run the application
                </div>
              </div>
            </div>
          ) : (
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8b949e', fontSize: '11px', flexDirection: 'column', gap: '8px'}}>
              <div style={{fontSize: '24px'}}>💻</div>
              <div>Ask AI to generate code</div>
              <div style={{fontSize: '10px', color: '#484f58'}}>e.g., "build a todo app" or "create a REST API"</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// MEETING WORKSPACE
function MeetingWorkspace({ taskMessage }) {
  const [selectedSlot, setSelectedSlot] = useState('10:00 AM');
  const [selectedPlatform, setSelectedPlatform] = useState('Jitsi');
  const slots = ['9:00 AM', '10:00 AM', '11:00 AM', '2:00 PM', '3:00 PM', '4:00 PM'];
  const takenSlots = ['9:00 AM', '3:00 PM'];
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">📅</span><span className="ph-title">Time slots — tomorrow</span></div>
        <div className="panel-body">
          <div className="slot-grid" style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', padding: '10px 12px'}}>
            {slots.map(s => (
              <div key={s} 
                className={`slot ${takenSlots.includes(s) ? 'gone' : ''} ${selectedSlot === s ? 'sel' : ''}`}
                onClick={() => !takenSlots.includes(s) && setSelectedSlot(s)}
                style={{padding: '6px', borderRadius: '5px', border: '0.5px solid #30363d', fontSize: '10px', cursor: takenSlots.includes(s) ? 'default' : 'pointer', textAlign: 'center', color: '#c9d1d9', textDecoration: takenSlots.includes(s) ? 'line-through' : 'none', background: selectedSlot === s ? '#7c3aed22' : 'transparent', borderColor: selectedSlot === s ? '#7c3aed' : '#30363d'}}>
                {s}
              </div>
            ))}
          </div>
          <div className="divider"></div>
          <div className="c-section">Attendees</div>
          <div className="attendee" style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '6px 12px', borderBottom: '0.5px solid #21262d'}}>
            <div style={{width: '22px', height: '22px', borderRadius: '50%', background: '#7c3aed44', color: '#d2a8ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', fontWeight: 500}}>YO</div>
            <div><div style={{fontSize: '10px', color: '#c9d1d9'}}>You</div><div style={{fontSize: '9px', color: '#8b949e'}}>● Available</div></div>
          </div>
          <div className="c-section" style={{marginTop: '6px'}}>Platform</div>
          <div style={{display: 'flex', gap: '5px', padding: '6px 12px'}}>
            {['Jitsi', 'Zoom', 'Meet'].map(p => (
              <div key={p} className={`slot ${selectedPlatform === p ? 'sel' : ''}`} 
                onClick={() => setSelectedPlatform(p)}
                style={{flex: 1, padding: '6px', borderRadius: '5px', border: '0.5px solid #30363d', fontSize: '10px', cursor: 'pointer', textAlign: 'center', background: selectedPlatform === p ? '#7c3aed22' : 'transparent', borderColor: selectedPlatform === p ? '#7c3aed' : '#30363d', color: selectedPlatform === p ? '#d2a8ff' : '#c9d1d9'}}>
                {p}
              </div>
            ))}
          </div>
          <button className="cfm-btn" style={{margin: '10px 12px', padding: '7px', background: '#7c3aed', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '10px', cursor: 'pointer', display: 'block', width: 'calc(100% - 24px)'}}>Confirm & send invites</button>
        </div>
      </div>
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header">
          <span className="ph-icon">📹</span><span className="ph-title">Live meeting preview</span>
          <div style={{display: 'flex', alignItems: 'center', gap: '3px', marginLeft: 'auto'}}><div className="ldot"></div><span style={{fontSize: '8px', color: '#3fb950'}}>Jitsi</span></div>
        </div>
        <div className="panel-body">
          <div className="cam-grid" style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', padding: '10px'}}>
            <div className="cam" style={{background: '#21262d', borderRadius: '8px', height: '72px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '3px', position: 'relative', border: '0.5px solid #30363d'}}>
              <div style={{position: 'absolute', top: '4px', left: '4px', background: '#f85149', color: '#fff', fontSize: '7px', padding: '1px 4px', borderRadius: '3px'}}>LIVE</div>
              <span style={{fontSize: '18px'}}>👤</span>
              <div style={{fontSize: '9px', color: '#8b949e'}}>You</div>
            </div>
            <div className="cam" style={{background: '#21262d', borderRadius: '8px', height: '72px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '3px', border: '0.5px solid #30363d'}}>
              <span style={{fontSize: '18px'}}>👤</span>
              <div style={{fontSize: '9px', color: '#8b949e'}}>Guest</div>
            </div>
          </div>
          <div className="meet-controls" style={{display: 'flex', justifyContent: 'center', gap: '8px', padding: '8px'}}>
            <div className="mc" style={{width: '26px', height: '26px', borderRadius: '50%', background: '#21262d', border: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', cursor: 'pointer'}}>🎤</div>
            <div className="mc" style={{width: '26px', height: '26px', borderRadius: '50%', background: '#21262d', border: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', cursor: 'pointer'}}>📹</div>
            <div className="mc" style={{width: '26px', height: '26px', borderRadius: '50%', background: '#3fb950', border: '0.5px solid #3fb950', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', cursor: 'pointer'}}>📞</div>
            <div className="mc" style={{width: '26px', height: '26px', borderRadius: '50%', background: '#f85149', border: '0.5px solid #f85149', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', cursor: 'pointer'}}>⬇</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// TRADE WORKSPACE
function TradeWorkspace({ taskMessage }) {
  const [side, setSide] = useState('buy');
  const bars = [35, 42, 38, 55, 48, 62, 58, 45, 52, 68, 55, 48];
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">📈</span><span className="ph-title">BTC/USDT live</span></div>
        <div className="panel-body">
          <div className="chart-bars" style={{display: 'flex', alignItems: 'flex-end', gap: '1px', height: '50px', padding: '0 12px', marginTop: '6px'}}>
            {bars.map((h, i) => (
              <div key={i} className={`bar ${i % 2 === 0 ? 'bar-up' : 'bar-dn'}`} style={{flex: 1, height: `${h}%`, borderRadius: '1px 1px 0 0', background: i % 2 === 0 ? '#3fb950' : '#f85149'}}></div>
            ))}
          </div>
          <div className="price-big" style={{fontSize: '20px', color: '#e6edf3', fontWeight: 500, padding: '0 12px', marginTop: '6px'}}>$67,420</div>
          <div className="price-chg" style={{fontSize: '10px', padding: '0 12px 8px', color: '#3fb950'}}>+2.4% (24h)</div>
          <div className="order-row" style={{display: 'flex', gap: '5px', padding: '10px 12px'}}>
            <div className={`order-side ${side === 'buy' ? 'buy-side' : ''}`} 
              onClick={() => setSide('buy')}
              style={{flex: 1, padding: '6px', borderRadius: '6px', textAlign: 'center', fontSize: '10px', cursor: 'pointer', border: '0.5px solid', background: side === 'buy' ? '#23863622' : '#21262d', borderColor: side === 'buy' ? '#238636' : '#30363d', color: side === 'buy' ? '#3fb950' : '#8b949e'}}>
              Buy
            </div>
            <div className={`order-side ${side === 'sell' ? 'sell-side' : ''}`}
              onClick={() => setSide('sell')}
              style={{flex: 1, padding: '6px', borderRadius: '6px', textAlign: 'center', fontSize: '10px', cursor: 'pointer', border: '0.5px solid', background: side === 'sell' ? '#f8514922' : '#21262d', borderColor: side === 'sell' ? '#f85149' : '#30363d', color: side === 'sell' ? '#f85149' : '#8b949e'}}>
              Sell
            </div>
          </div>
          <div className="confirm-wrap" style={{margin: '0 12px 10px', background: '#f8514911', border: '0.5px solid #f85149', borderRadius: '8px', padding: '9px 10px'}}>
            <div className="cw-title" style={{fontSize: '11px', color: '#f85149', fontWeight: 500, marginBottom: '6px'}}>⚠️ High risk trade - Confirm required</div>
            <div className="cw-row" style={{display: 'flex', justifyContent: 'space-between', marginBottom: '3px'}}>
              <span className="cw-k" style={{fontSize: '9px', color: '#8b949e'}}>Amount:</span>
              <span className="cw-v" style={{fontSize: '9px', color: '#e6edf3'}}>0.1 BTC</span>
            </div>
            <div className="cw-row" style={{display: 'flex', justifyContent: 'space-between', marginBottom: '3px'}}>
              <span className="cw-k" style={{fontSize: '9px', color: '#8b949e'}}>Price:</span>
              <span className="cw-v" style={{fontSize: '9px', color: '#e6edf3'}}>$6,742</span>
            </div>
            <div className="cw-btns" style={{display: 'flex', gap: '5px', marginTop: '7px'}}>
              <button className="cw-go" style={{flex: 1, padding: '6px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer', border: '0.5px solid #f85149', background: '#f85149', color: '#fff'}}>Confirm Trade</button>
              <button className="cw-no" style={{flex: 1, padding: '6px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer', border: '0.5px solid #30363d', background: 'transparent', color: '#8b949e'}}>Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// SHOPPING WORKSPACE
function ShoppingWorkspace({ taskMessage }) {
  const products = [
    { name: 'Nike Dri-FIT Shirt', site: 'Amazon', price: '₹1,299', best: true },
    { name: 'Adidas Originals', site: 'Flipkart', price: '₹1,499', best: false },
    { name: 'Puma Essential', site: 'Myntra', price: '₹999', best: false }
  ];
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">🛍️</span><span className="ph-title">Best matches</span></div>
        <div className="panel-body">
          {products.map((p, i) => (
            <div key={i} className={`prod-card ${p.best ? 'best' : ''}`} style={{background: '#0d1117', border: '0.5px solid', borderColor: p.best ? '#3fb950' : '#30363d', borderRadius: '7px', margin: '6px 12px', padding: '9px', cursor: 'pointer'}}>
              <div className="prod-top" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                <div className="prod-img" style={{fontSize: '22px'}}>👕</div>
                <div><div className="prod-name" style={{fontSize: '10px', color: '#c9d1d9', fontWeight: 500}}>{p.name}</div><div className="prod-site" style={{fontSize: '9px', color: '#8b949e'}}>{p.site}</div></div>
                <div className="prod-price" style={{fontSize: '12px', color: '#e6edf3', fontWeight: 500, marginLeft: 'auto'}}>{p.price}</div>
              </div>
              {p.best && <div className="prod-tag tg" style={{fontSize: '8px', marginTop: '4px', color: '#3fb950'}}>✓ Best match</div>}
            </div>
          ))}
          <div className="checkout-block" style={{margin: '6px 12px 10px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '8px', padding: '10px'}}>
            <div className="checkout-row" style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
              <span className="ck-k" style={{fontSize: '9px', color: '#8b949e'}}>Selected:</span>
              <span className="ck-v" style={{fontSize: '9px', color: '#c9d1d9'}}>Nike Dri-FIT Shirt</span>
            </div>
            <div className="checkout-row" style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
              <span className="ck-k" style={{fontSize: '9px', color: '#8b949e'}}>Total:</span>
              <span className="ck-v" style={{fontSize: '9px', color: '#c9d1d9'}}>₹1,299</span>
            </div>
            <button className="order-btn" style={{width: '100%', marginTop: '8px', padding: '7px', background: '#3fb950', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '10px', cursor: 'pointer'}}>Place Order</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// BROWSER FALLBACK WORKSPACE
function BrowserWorkspace({ taskMessage }) {
  const steps = [
    { text: 'Opening browser', done: true },
    { text: 'Navigating to site', done: true },
    { text: 'Filling form', running: true },
    { text: 'Waiting for response', pending: true }
  ];
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header">
          <span className="ph-icon">🌐</span><span className="ph-title">Browser Automation</span>
          <span className="badge ba" style={{marginLeft: 'auto'}}>Fallback mode</span>
        </div>
        <div className="panel-body">
          <div className="browser-bar-2" style={{height: '26px', background: '#0d1117', borderBottom: '0.5px solid #30363d', display: 'flex', alignItems: 'center', padding: '0 8px', gap: '5px'}}>
            <div className="bdots2" style={{display: 'flex', gap: '3px'}}>
              <span style={{width: '6px', height: '6px', borderRadius: '50%', background: '#f85149'}}></span>
              <span style={{width: '6px', height: '6px', borderRadius: '50%', background: '#d29922'}}></span>
              <span style={{width: '6px', height: '6px', borderRadius: '50%', background: '#3fb950'}}></span>
            </div>
            <div className="burl2" style={{flex: 1, background: '#21262d', borderRadius: '3px', padding: '2px 7px', fontSize: '9px', color: '#8b949e', fontFamily: 'monospace'}}>
              https://example.com
            </div>
            <div className="ai-badge2" style={{fontSize: '8px', background: '#7c3aed', color: '#fff', padding: '1px 5px', borderRadius: '3px'}}>AI</div>
          </div>
          <div className="steps-list" style={{padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px'}}>
            {steps.map((s, i) => (
              <div key={i} className="sl-step" style={{display: 'flex', alignItems: 'center', gap: '7px', fontSize: '10px', color: '#8b949e'}}>
                <div className={`sl-dot ${s.done ? 'sl-ok' : s.running ? 'sl-run' : 'sl-td'}`} style={{
                  width: '16px', height: '16px', borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '8px',
                  background: s.done ? '#23863622' : s.running ? '#7c3aed22' : '#21262d',
                  border: `0.5px solid ${s.done ? '#238636' : s.running ? '#7c3aed' : '#30363d'}`,
                  color: s.done ? '#3fb950' : s.running ? '#d2a8ff' : '#484f58'
                }}>
                  {s.done ? '✓' : s.running ? '●' : '○'}
                </div>
                <span style={{color: s.done ? '#3fb950' : s.running ? '#d2a8ff' : '#8b949e'}}>{s.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// VIDEO WORKSPACE
function VideoWorkspace({ taskMessage }) {
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">🎬</span><span className="ph-title">Video Editor</span></div>
        <div className="panel-body">
          <div className="video-screen" style={{background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '6px', padding: '16px', minHeight: '120px', borderBottom: '0.5px solid #30363d'}}>
            <span style={{fontSize: '32px'}}>🎬</span>
            <span style={{fontSize: '10px', color: '#8b949e'}}>product_video.mp4</span>
            <span style={{fontSize: '9px', color: '#3fb950'}}>00:00 / 02:45</span>
          </div>
          <div className="tl-wrap" style={{padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '4px'}}>
            <div className="tl-track" style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <span className="tl-lbl" style={{fontSize: '9px', color: '#484f58', minWidth: '38px'}}>Video</span>
              <div className="tl-clips" style={{display: 'flex', gap: '2px', flex: 1}}>
                <div className="clip clip-v" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#3a1a6e', flex: 2}}>Intro</div>
                <div className="clip clip-v" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#3a1a6e', flex: 3}}>Main</div>
                <div className="clip clip-v" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#3a1a6e', flex: 1}}>End</div>
              </div>
            </div>
            <div className="tl-track" style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <span className="tl-lbl" style={{fontSize: '9px', color: '#484f58', minWidth: '38px'}}>Audio</span>
              <div className="tl-clips" style={{display: 'flex', gap: '2px', flex: 1}}>
                <div className="clip clip-a" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#1a3a1a', flex: 1}}>BG Music</div>
              </div>
            </div>
            <div className="tl-track" style={{display: 'flex', alignItems: 'center', gap: '6px'}}>
              <span className="tl-lbl" style={{fontSize: '9px', color: '#484f58', minWidth: '38px'}}>Text</span>
              <div className="tl-clips" style={{display: 'flex', gap: '2px', flex: 1}}>
                <div className="clip clip-t" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#7c3aed', flex: 1}}>Title</div>
                <div className="clip clip-t" style={{height: '18px', borderRadius: '3px', padding: '0 5px', fontSize: '8px', color: '#fff', display: 'flex', alignItems: 'center', background: '#7c3aed', flex: 1}}>CTA</div>
              </div>
            </div>
          </div>
          <div className="tl-controls" style={{display: 'flex', gap: '6px', justifyContent: 'center', padding: '6px', borderTop: '0.5px solid #30363d'}}>
            <div className="tlc" style={{width: '22px', height: '22px', borderRadius: '50%', background: '#21262d', border: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', cursor: 'pointer', color: '#c9d1d9'}}>⏮</div>
            <div className="tlc" style={{width: '22px', height: '22px', borderRadius: '50%', background: '#7c3aed', border: '0.5px solid #7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', cursor: 'pointer', color: '#fff'}}>▶</div>
            <div className="tlc" style={{width: '22px', height: '22px', borderRadius: '50%', background: '#21262d', border: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', cursor: 'pointer', color: '#c9d1d9'}}>⏭</div>
            <button className="export-btn-v" style={{padding: '4px 10px', background: '#3fb950', border: 'none', borderRadius: '5px', color: '#fff', fontSize: '9px', cursor: 'pointer', marginLeft: '10px'}}>Export</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// SOCIAL WORKSPACE
function SocialWorkspace({ taskMessage }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['Instagram']);
  const platforms = ['Instagram', 'Facebook', 'Twitter', 'LinkedIn'];
  
  const togglePlatform = (p) => {
    setSelectedPlatforms(prev => 
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    );
  };
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">📱</span><span className="ph-title">Post Preview</span></div>
        <div className="panel-body">
          <div className="ig-post" style={{background: '#fff', borderRadius: '8px', border: '0.5px solid #dbdbdb', overflow: 'hidden', margin: '8px 10px'}}>
            <div className="ig-head" style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '7px 9px', borderBottom: '0.5px solid #f0f0f0'}}>
              <div className="ig-av" style={{width: '24px', height: '24px', borderRadius: '50%', background: '#e1306c', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', color: '#fff', fontWeight: 500}}>YO</div>
              <div className="ig-name" style={{fontSize: '10px', color: '#262626', fontWeight: 500}}>your_brand</div>
            </div>
            <div className="ig-img" style={{background: '#1a1a3e', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '4px'}}>
              <span style={{fontSize: '32px'}}>🚀</span>
              <span style={{fontSize: '10px', color: '#fff'}}>Launch Day!</span>
            </div>
            <div className="ig-caption" style={{padding: '7px 9px', fontSize: '9px', color: '#262626', lineHeight: 1.5}}>
              🎉 We're officially live! Check out our new product...
              <span style={{color: '#00376b'}}>#launch #startup #newproduct</span>
            </div>
          </div>
          <div className="c-section" style={{padding: '6px 12px 3px', fontSize: '9px', color: '#484f58', textTransform: 'uppercase'}}>Platforms</div>
          <div className="plat-row" style={{display: 'flex', gap: '5px', flexWrap: 'wrap', padding: '8px 12px'}}>
            {platforms.map(p => (
              <div key={p} className={`plat ${selectedPlatforms.includes(p) ? 'on' : ''}`} 
                onClick={() => togglePlatform(p)}
                style={{padding: '4px 9px', borderRadius: '5px', fontSize: '9px', border: '0.5px solid', cursor: 'pointer', borderColor: selectedPlatforms.includes(p) ? '#7c3aed' : '#30363d', background: selectedPlatforms.includes(p) ? '#7c3aed22' : 'transparent', color: selectedPlatforms.includes(p) ? '#d2a8ff' : '#8b949e'}}>
                {p}
              </div>
            ))}
          </div>
          <div className="sched-time" style={{margin: '0 12px 8px', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '6px', padding: '5px 8px', fontSize: '9px', color: '#c9d1d9'}}>
            📅 Schedule: Now (immediately)
          </div>
          <button className="post-btn" style={{margin: '0 12px 10px', padding: '7px', background: '#e1306c', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '10px', cursor: 'pointer', display: 'block', width: 'calc(100% - 24px)'}}>Post to {selectedPlatforms.length} platform{selectedPlatforms.length > 1 ? 's' : ''}</button>
        </div>
      </div>
    </div>
  );
}

// FLIGHT WORKSPACE
function FlightWorkspace({ taskMessage }) {
  const [selectedSeat, setSelectedSeat] = useState('12A');
  const flights = [
    { airline: 'IndiGo', time: '06:15 → 08:30', dur: '2h 15m', price: '₹3,499', best: true },
    { airline: 'Air India', time: '09:00 → 11:20', dur: '2h 20m', price: '₹4,199', best: false },
    { airline: 'SpiceJet', time: '14:30 → 16:50', dur: '2h 20m', price: '₹2,999', best: false }
  ];
  const rows = [10, 11, 12, 13];
  const cols = ['A', 'B', 'C', 'D', 'E', 'F'];
  const takenSeats = ['10B', '10C', '11A', '11E', '12D', '13B', '13C'];
  
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">✈️</span><span className="ph-title">Flights — Goa Friday</span></div>
        <div className="panel-body">
          {flights.map((f, i) => (
            <div key={i} className={`flight-card ${f.best ? 'best' : ''}`} style={{margin: '6px 12px', background: '#0d1117', border: '0.5px solid', borderColor: f.best ? '#3fb950' : '#30363d', borderRadius: '8px', padding: '9px', cursor: 'pointer'}}>
              <div className="fl-row" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                <div className="fl-airline" style={{fontSize: '10px', color: '#e6edf3', fontWeight: 500, minWidth: '72px'}}>{f.airline}</div>
                <div className="fl-times" style={{fontSize: '10px', color: '#c9d1d9'}}>{f.time}</div>
                <div className="fl-dur" style={{fontSize: '9px', color: '#8b949e', flex: 1}}>{f.dur}</div>
                <div className="fl-price" style={{fontSize: '12px', color: '#e6edf3', fontWeight: 500}}>{f.price}</div>
              </div>
              {f.best && <div style={{fontSize: '8px', marginTop: '4px', color: '#3fb950'}}>✓ Best price</div>}
            </div>
          ))}
        </div>
      </div>
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">💺</span><span className="ph-title">Select Seat</span></div>
        <div className="panel-body">
          <div className="seat-map" style={{padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: '3px'}}>
            {rows.map(row => (
              <div key={row} className="seat-row" style={{display: 'flex', gap: '3px', alignItems: 'center'}}>
                <span className="seat-rn" style={{fontSize: '8px', color: '#484f58', minWidth: '16px'}}>{row}</span>
                {cols.slice(0, 3).map(col => {
                  const seatId = `${row}${col}`;
                  const taken = takenSeats.includes(seatId);
                  const selected = selectedSeat === seatId;
                  return (
                    <div key={seatId} 
                      className={`seat ${taken ? 'taken' : 'free'} ${selected ? 'sel' : ''}`}
                      onClick={() => !taken && setSelectedSeat(seatId)}
                      style={{width: '16px', height: '16px', borderRadius: '3px', border: '0.5px solid', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '7px', cursor: taken ? 'not-allowed' : 'pointer', background: selected ? '#7c3aed' : taken ? '#21262d' : 'transparent', borderColor: selected ? '#7c3aed' : '#30363d', color: selected ? '#fff' : taken ? '#484f58' : '#8b949e'}}>
                      {col}
                    </div>
                  );
                })}
                <div className="seat-gap" style={{width: '12px'}}></div>
                {cols.slice(3).map(col => {
                  const seatId = `${row}${col}`;
                  const taken = takenSeats.includes(seatId);
                  const selected = selectedSeat === seatId;
                  return (
                    <div key={seatId} 
                      className={`seat ${taken ? 'taken' : 'free'} ${selected ? 'sel' : ''}`}
                      onClick={() => !taken && setSelectedSeat(seatId)}
                      style={{width: '16px', height: '16px', borderRadius: '3px', border: '0.5px solid', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '7px', cursor: taken ? 'not-allowed' : 'pointer', background: selected ? '#7c3aed' : taken ? '#21262d' : 'transparent', borderColor: selected ? '#7c3aed' : '#30363d', color: selected ? '#fff' : taken ? '#484f58' : '#8b949e'}}>
                      {col}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div style={{padding: '8px 12px', fontSize: '9px', color: '#8b949e'}}>
            Selected: <span style={{color: '#d2a8ff'}}>{selectedSeat}</span> (Window)
          </div>
          <button style={{margin: '0 12px 10px', padding: '7px', background: '#3fb950', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '10px', cursor: 'pointer', display: 'block', width: 'calc(100% - 24px)'}}>Book Flight — ₹3,499</button>
        </div>
      </div>
    </div>
  );
}

// EMAIL WORKSPACE
function EmailWorkspace({ taskMessage }) {
  return (
    <div className="panels">
      <div className="panel" style={{flex: 1}}>
        <div className="panel-header"><span className="ph-icon">📧</span><span className="ph-title">Compose Email</span></div>
        <div className="panel-body" style={{padding: '12px'}}>
          <div style={{marginBottom: '8px'}}>
            <label style={{fontSize: '9px', color: '#8b949e', display: 'block', marginBottom: '4px'}}>To:</label>
            <input type="text" placeholder="recipient@email.com" style={{width: '100%', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '4px', padding: '6px 8px', fontSize: '10px', color: '#e6edf3', outline: 'none'}} />
          </div>
          <div style={{marginBottom: '8px'}}>
            <label style={{fontSize: '9px', color: '#8b949e', display: 'block', marginBottom: '4px'}}>Subject:</label>
            <input type="text" placeholder="Email subject" style={{width: '100%', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '4px', padding: '6px 8px', fontSize: '10px', color: '#e6edf3', outline: 'none'}} />
          </div>
          <div style={{marginBottom: '8px'}}>
            <label style={{fontSize: '9px', color: '#8b949e', display: 'block', marginBottom: '4px'}}>Message:</label>
            <textarea placeholder="Write your email..." rows={6} style={{width: '100%', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '4px', padding: '6px 8px', fontSize: '10px', color: '#e6edf3', outline: 'none', resize: 'none'}} />
          </div>
          <button style={{width: '100%', padding: '7px', background: '#7c3aed', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '10px', cursor: 'pointer'}}>Send Email</button>
        </div>
      </div>
    </div>
  );
}

// EXAMPLE TASKS
const EXAMPLE_TASKS = [
  { text: 'build a banking app', type: 'code' },
  { text: 'schedule a meeting tomorrow', type: 'meeting' },
  { text: 'buy 0.1 BTC now', type: 'trade' },
  { text: 'book me a shirt for weekend', type: 'shopping' },
  { text: 'fly me to Goa Friday', type: 'flight' },
  { text: 'edit my product video', type: 'video' },
  { text: 'post launch on instagram', type: 'social' },
  { text: 'renew my car insurance', type: 'browser' }
];

export default function TaskAdaptiveWorkspace({ 
  messages, input, setInput, send, loading, AgentSteps, UIComponentRenderer, sessionId,
  // New props for Settings, Integrations, TaskPanel
  showSettings, setShowSettings,
  showIntegrations, setShowIntegrations,
  showTaskPanel, setShowTaskPanel,
  SettingsPanel, IntegrationsPanel, TaskPanelComponent
}) {
  const endRef = useRef(null);
  const [workspaceState, setWorkspaceState] = useState('home'); // home, thinking, active
  const [taskType, setTaskType] = useState(null);
  const [taskMessage, setTaskMessage] = useState('');
  const [thinkingSteps, setThinkingSteps] = useState([]);
  
  // Extract AI-generated code and files from messages
  const generatedCode = extractCodeFromResponse(messages);
  const generatedFiles = extractFilesFromResponse(messages, generatedCode);
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Detect task type from latest user message
  useEffect(() => {
    const lastUserMsg = messages.slice().reverse().find(m => m.role === 'user');
    if (lastUserMsg && loading) {
      const detected = detectTaskType(lastUserMsg.text);
      setTaskType(detected);
      setTaskMessage(lastUserMsg.text);
      setWorkspaceState('thinking');
      
      // Simulate thinking steps
      setThinkingSteps([]);
      const steps = ['Understanding request...', 'Detecting task type...', 'Assembling workspace...'];
      steps.forEach((step, i) => {
        setTimeout(() => {
          setThinkingSteps(prev => [...prev, step]);
          if (i === steps.length - 1) {
            setTimeout(() => setWorkspaceState('active'), 500);
          }
        }, (i + 1) * 400);
      });
    } else if (!loading && messages.length === 0) {
      setWorkspaceState('home');
      setTaskType(null);
    }
  }, [messages, loading]);

  const hasTask = workspaceState === 'active' || (messages.some(m => m.ui_components && m.ui_components.length > 0));
  const activeTask = messages.slice().reverse().find(m => m.ui_components?.length > 0);
  const config = taskType ? TASK_CONFIG[taskType] : null;

  const handleExampleClick = (example) => {
    setInput(example.text);
    setTimeout(() => send(example.text), 100);
  };

  const renderWorkspace = () => {
    switch (taskType) {
      case 'code': return <CodeWorkspace taskMessage={taskMessage} messages={messages} generatedCode={generatedCode} generatedFiles={generatedFiles} />;
      case 'meeting': return <MeetingWorkspace taskMessage={taskMessage} />;
      case 'trade': return <TradeWorkspace taskMessage={taskMessage} />;
      case 'shopping': return <ShoppingWorkspace taskMessage={taskMessage} />;
      case 'flight': return <FlightWorkspace taskMessage={taskMessage} />;
      case 'video': return <VideoWorkspace taskMessage={taskMessage} />;
      case 'social': return <SocialWorkspace taskMessage={taskMessage} />;
      case 'email': return <EmailWorkspace taskMessage={taskMessage} />;
      case 'browser': return <BrowserWorkspace taskMessage={taskMessage} />;
      default: return <BrowserWorkspace taskMessage={taskMessage} />;
    }
  };

  return (
    <div className="app">
      <div className="topbar">
        <div className="logo">S</div>
        <div className="brand">Super Manager</div>
        <div className="online">
          <div className="sdot"></div>
          <span id="onlineLabel">{workspaceState === 'active' ? `Working: ${taskMessage?.slice(0, 30)}...` : 'Waiting for a task...'}</span>
        </div>
        {/* Toolbar buttons */}
        <div style={{display: 'flex', gap: '8px', marginLeft: 'auto'}}>
          <button 
            onClick={() => setShowTaskPanel && setShowTaskPanel(!showTaskPanel)}
            className="toolbar-btn"
            style={{background: showTaskPanel ? '#7c3aed22' : 'transparent', border: '0.5px solid #30363d', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: '#8b949e', fontSize: '10px'}}
            title="Tasks"
          >
            <ListTodo size={14} /> Tasks
          </button>
          <button 
            onClick={() => setShowIntegrations && setShowIntegrations(!showIntegrations)}
            className="toolbar-btn"
            style={{background: showIntegrations ? '#7c3aed22' : 'transparent', border: '0.5px solid #30363d', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: '#8b949e', fontSize: '10px'}}
            title="Integrations"
          >
            <Plug size={14} /> Connect
          </button>
          <button 
            onClick={() => setShowSettings && setShowSettings(!showSettings)}
            className="toolbar-btn"
            style={{background: showSettings ? '#7c3aed22' : 'transparent', border: '0.5px solid #30363d', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: '#8b949e', fontSize: '10px'}}
            title="Settings"
          >
            <Settings size={14} />
          </button>
        </div>
      </div>

      <div className="body">
        {/* CHAT — always left */}
        <div className="chat-col">
          <div className="chat-msgs" id="chatMsgs">
            <div className="ma" id="welcomeMsg">
              <div className="bub">Hey. Tell me what you need done. I'll figure out the rest.</div>
              <div className="mts">Now</div>
            </div>
            
            {messages.map((m, idx) => (
              <div key={idx} className={m.role === 'user' ? 'mu' : 'ma'}>
                <div className="bub">
                    {m.role === 'user' ? (
                       m.text
                    ) : (
                       <ReactMarkdown 
                         remarkPlugins={[remarkGfm]}
                         components={{
                           a: ({node, ...props}) => (
                             <a {...props} target="_blank" rel="noopener noreferrer" />
                           )
                         }}
                       >
                         {m.text || ''}
                       </ReactMarkdown>
                    )}
                </div>
                {m.steps && m.steps.length > 0 && AgentSteps && (
                    <div className="think-pill" style={{marginTop: '4px'}}>
                        <AgentSteps steps={m.steps} />
                    </div>
                )}
                <div className="mts">{new Date(m.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
              </div>
            ))}
            
            {loading && (
              <div className="ma">
                <div className="bub da"><span></span><span></span><span></span></div>
              </div>
            )}
            
            <div ref={endRef} />
          </div>
          
          <div className="chat-input-area" style={{display: 'flex', borderTop: '0.5px solid #30363d', padding: '10px', background: '#0d1117', alignItems: 'center'}}>
            <input 
              type="text" 
              id="chatInput" 
              placeholder="what do you want done?" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') send() }}
              style={{flex: 1, background: '#161b22', border: '0.5px solid #30363d', color: '#c9d1d9', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', outline: 'none'}}
            />
            <button 
              onClick={() => send()}
              disabled={!input.trim() || loading}
              style={{marginLeft: '8px', background: input.trim() ? '#7c3aed' : '#21262d', color: input.trim() ? '#fff' : '#484f58', border: 'none', borderRadius: '8px', padding: '10px 14px', cursor: input.trim() && !loading ? 'pointer' : 'not-allowed', transition: 'all 0.2s', fontWeight: 500}}
            >
              Send
            </button>
          </div>
        </div>

        {/* WORKSPACE AREA */}
        <div className="ws-area">
          {workspaceState === 'home' && !hasTask && !loading ? (
            <div id="state-home" className="home">
              <div className="home-logo">S</div>
              <div>
                <div className="home-title">Nothing running yet.</div>
                <div className="home-sub" style={{marginTop: '5px'}}>Give me any task. A workspace will open automatically — built for exactly that task, with every panel it needs.</div>
              </div>
              <div className="task-examples">
                <div className="ex-label">Click any of these to see how the workspace assembles:</div>
                <div className="ex-row">
                  {EXAMPLE_TASKS.slice(0, 3).map((ex, i) => (
                    <div key={i} className="ex-pill" onClick={() => handleExampleClick(ex)}>{ex.text}</div>
                  ))}
                </div>
                <div className="ex-row">
                  {EXAMPLE_TASKS.slice(3, 6).map((ex, i) => (
                    <div key={i} className="ex-pill" onClick={() => handleExampleClick(ex)}>{ex.text}</div>
                  ))}
                </div>
                <div className="ex-row">
                  {EXAMPLE_TASKS.slice(6).map((ex, i) => (
                    <div key={i} className="ex-pill" onClick={() => handleExampleClick(ex)}>{ex.text}</div>
                  ))}
                </div>
              </div>
            </div>
          ) : workspaceState === 'thinking' || (loading && !hasTask) ? (
             <div id="state-thinking" style={{flex: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '24px'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '10px', width: '100%', maxWidth: '420px'}}>
                  <div style={{width: '22px', height: '22px', borderRadius: '6px', background: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: '#fff'}}>S</div>
                  <div style={{fontSize: '12px', color: '#e6edf3', fontWeight: '500'}}>Processing: {taskType ? TASK_CONFIG[taskType]?.label : 'Task'}...</div>
                </div>
                <div style={{width: '100%', maxWidth: '420px', display: 'flex', flexDirection: 'column', gap: '6px'}}>
                  {thinkingSteps.map((step, i) => (
                    <div key={i} style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 10px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '6px', fontSize: '11px', color: '#8b949e'}}>
                      <span style={{color: '#3fb950'}}>✓</span> {step}
                    </div>
                  ))}
                </div>
                <div style={{width: '100%', maxWidth: '420px'}}>
                  <div style={{fontSize: '9px', color: '#484f58', marginBottom: '6px'}}>Assembling workspace panels:</div>
                  <div style={{display: 'flex', gap: '5px', flexWrap: 'wrap'}}>
                    {config?.badges?.map((b, i) => (
                      <span key={i} className={`badge ${b.cls}`}>{b.text}</span>
                    ))}
                  </div>
                </div>
             </div>
          ) : workspaceState === 'active' || hasTask ? (
            <div id="state-active" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%', background: '#0d1117'}}>
               <div className="ws-header">
                  <span style={{fontSize: '12px'}}>{config?.icon || '⚡'}</span>
                  <span className="wsh-label">{taskMessage || 'Active Task'}</span>
                  {config?.badges?.map((b, i) => (
                    <span key={i} className={`badge ${b.cls}`}>{b.text}</span>
                  ))}
                  <div className="live-ind"><div className="ldot"></div>live</div>
               </div>
               {activeTask && activeTask.ui_components && activeTask.ui_components.length > 0 ? (
                 <div className="panels" style={{flex: 1, display: 'flex', overflow: 'hidden'}}>
                    <div style={{flex: 1, overflowY: 'auto', padding: '20px'}}>
                      {UIComponentRenderer && <UIComponentRenderer components={activeTask.ui_components} sessionId={sessionId} />}
                    </div>
                 </div>
               ) : (
                 renderWorkspace()
               )}
            </div>
          ) : (
            <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b949e'}}>
              Task Completed or Cancelled.
            </div>
          )}
        </div>
        
        {/* Task Panel (Right sidebar) */}
        {showTaskPanel && TaskPanelComponent && (
          <div className="task-panel" style={{width: '220px', borderLeft: '0.5px solid #30363d', background: '#0d1117', display: 'flex', flexDirection: 'column'}}>
            <div style={{padding: '10px 12px', borderBottom: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <span style={{fontSize: '11px', color: '#c9d1d9', fontWeight: 500}}>Active Tasks</span>
              <button onClick={() => setShowTaskPanel(false)} style={{background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer', padding: '2px'}}><X size={14} /></button>
            </div>
            <div style={{flex: 1, overflow: 'auto'}}>
              <TaskPanelComponent />
            </div>
          </div>
        )}
      </div>
      
      {/* Settings Modal */}
      {showSettings && SettingsPanel && (
        <div className="modal-overlay" style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000}}>
          <div style={{background: '#161b22', borderRadius: '12px', border: '0.5px solid #30363d', width: '90%', maxWidth: '600px', maxHeight: '80vh', overflow: 'auto'}}>
            <div style={{padding: '16px', borderBottom: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <span style={{fontSize: '14px', color: '#e6edf3', fontWeight: 600}}>Settings</span>
              <button onClick={() => setShowSettings(false)} style={{background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer'}}><X size={18} /></button>
            </div>
            <div style={{padding: '16px'}}>
              <SettingsPanel onClose={() => setShowSettings(false)} />
            </div>
          </div>
        </div>
      )}
      
      {/* Integrations Modal */}
      {showIntegrations && IntegrationsPanel && (
        <div className="modal-overlay" style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px'}}>
          <div style={{background: '#161b22', borderRadius: '12px', border: '0.5px solid #30363d', width: '90%', maxWidth: '800px', maxHeight: '85vh', display: 'flex', flexDirection: 'column'}}>
            <div style={{padding: '16px', borderBottom: '0.5px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0}}>
              <span style={{fontSize: '14px', color: '#e6edf3', fontWeight: 600}}>Connect Integrations</span>
              <button onClick={() => setShowIntegrations(false)} style={{background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer'}}><X size={18} /></button>
            </div>
            <div style={{flex: 1, overflow: 'auto', padding: '16px'}}>
              <IntegrationsPanel onClose={() => setShowIntegrations(false)} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
