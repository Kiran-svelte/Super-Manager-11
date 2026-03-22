import os

with open('frontend/src/TaskAdaptiveWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write('''import React, { useEffect, useRef } from "react";
import "./TaskWorkspace.css";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function TaskAdaptiveWorkspace({ messages, input, setInput, send, loading, AgentSteps, UIComponentRenderer, sessionId }) {
  const endRef = useRef(null);
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const hasTask = messages.some(m => m.ui_components && m.ui_components.length > 0);
  const activeTask = messages.slice().reverse().find(m => m.ui_components?.length > 0);

  return (
    <div className="app">
      <div className="topbar">
        <div className="logo">S</div>
        <div className="brand">Super Manager</div>
        <div className="online"><div className="sdot"></div><span id="onlineLabel">Waiting for a task...</span></div>
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
                       <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text || ''}</ReactMarkdown>
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
          {!hasTask && !loading ? (
            <div id="state-home" className="home" style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
              <div className="home-logo" style={{fontSize: '48px', color: '#30363d', marginBottom: '20px'}}>S</div>
              <div>
                <div className="home-title" style={{fontSize: '24px', fontWeight: 600, color: '#c9d1d9', textAlign: 'center'}}>Nothing running yet.</div>
                <div className="home-sub" style={{marginTop: '10px', color: '#8b949e', textAlign: 'center', maxWidth: '400px'}}>Give me any task. A workspace will open automatically — built for exactly that task, with every panel it needs.</div>
              </div>
            </div>
          ) : loading && !hasTask ? (
             <div id="state-thinking" style={{flex: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '24px'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '10px', width: '100%', maxWidth: '420px'}}>
                  <div style={{width: '22px', height: '22px', borderRadius: '6px', background: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: '#fff'}}>S</div>
                  <div style={{fontSize: '12px', color: '#e6edf3', fontWeight: '500'}} id="thinkLabel">Thinking...</div>
                </div>
             </div>
          ) : activeTask && activeTask.ui_components && activeTask.ui_components.length > 0 ? (
            <div id="state-active" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%', background: '#0d1117'}}>
               <div className="ws-header" style={{padding: '12px 16px', borderBottom: '1px solid #30363d', background: '#161b22', display: 'flex', alignItems: 'center', gap: '10px'}}>
                  <span style={{fontSize: '14px'}}>⚡</span>
                  <span className="wsh-label" style={{color: '#c9d1d9', fontSize: '13px', fontWeight: 500}}>Active Task Workspace</span>
                  <div className="live-ind" style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#3fb950'}}><div className="ldot" style={{width: '6px', height: '6px', borderRadius: '50%', background: '#3fb950', animation: 'pulse 2s infinite'}}></div>Live preview</div>
               </div>
               <div className="panels" style={{flex: 1, display: 'flex', overflow: 'hidden'}}>
                  <div style={{flex: 1, overflowY: 'auto', padding: '20px'}}>
                    {UIComponentRenderer && <UIComponentRenderer components={activeTask.ui_components} sessionId={sessionId} />}
                  </div>
               </div>
            </div>
          ) : (
            <div style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b949e'}}>
              Task Completed or Cancelled.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
''')
    
print("Saved TaskAdaptiveWorkspace.jsx")
