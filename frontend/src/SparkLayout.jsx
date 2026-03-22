import React, { useState } from "react";
import "./SparkLayout.css";

export default function SparkLayout() {
  const [activeMode, setActiveMode] = useState("code"); 

  return (
    <>
      {/* Ported HTML */}
      <div className="app">
  <div className="topbar">
    <div className="topbar-left">
      <div className="logo">S</div>
      <div>
        <div className="title">Super Manager</div>
        <div className="subtitle">Agentic AI workspace</div>
      </div>
    </div>
    <div className="mode-tabs">
      <div className="mode-tab active"  id="tab-code">Code IDE</div>
      <div className="mode-tab"  id="tab-meeting">Meeting</div>
      <div className="mode-tab"  id="tab-chat">Chat only</div>
    </div>
    <div ><div className="status-dot"></div><span >Online</span></div>
  </div>

  <div className="main">
    {/* CHAT PANEL */}
    <div className="chat-panel">
      <div className="chat-messages" id="chatMessages">
        <div className="msg user">
          <div className="msg-bubble">create a banking app named manti bank with all security, create backend, frontend, everything</div>
          <div className="msg-meta">07:13 pm</div>
        </div>
        <div className="msg agent">
          <div className="agent-icon">S</div>
          <div className="thinking-pill"><div className="dot-anim"><span></span><span></span><span></span></div> Planning 12 steps...</div>
          <div className="msg-meta">07:13 pm</div>
        </div>
        <div className="msg agent">
          <div className="msg-bubble">I've planned the Manti Bank project structure. Opening the IDE workspace now — you can watch files being created in real time.</div>
          <div className="workspace-launch" id="wsLaunchBtn" >
            <span >&#9654;</span> View IDE workspace ↗
          </div>
          <div className="msg-meta">07:14 pm</div>
        </div>
        <div className="msg user">
          <div className="msg-bubble">yes</div>
          <div className="msg-meta">07:14 pm</div>
        </div>
        <div className="msg agent">
          <div className="msg-bubble">Creating files... <span >12/15 complete</span>. Running npm install in terminal.</div>
          <div className="msg-meta">07:15 pm</div>
        </div>
      </div>
      <div className="chat-input-bar">
        <input type="text" placeholder="Type your message..." />
      </div>
    </div>

    {/* WORKSPACE: CODE IDE */}
    <div className="workspace" id="ws-code">
      <div className="workspace-header">
        <div className="workspace-title">
          <span >&#9632;</span> MantiBank /
          <span className="ws-badge">IDE mode</span>
        </div>
        <div >
          <span className="ws-badge green">15 files created</span>
          <span className="ws-badge amber">npm installing...</span>
        </div>
      </div>
      <div className="ide-layout">
        <div className="file-tree">
          <div className="tree-section">MantiBank</div>
          <div className="tree-item folder" >&#128193; backend/</div>
          <div className="tree-item active"  id="f-server">&#128196; server.js</div>
          <div className="tree-item"  id="f-config">&#128196; config.js</div>
          <div className="tree-item"  id="f-routes">&#128196; routes.js</div>
          <div className="tree-item"  id="f-models">&#128196; models.js</div>
          <div className="tree-item"  id="f-middleware">&#128196; middleware.js</div>
          <div className="tree-item folder">&#128193; frontend/</div>
          <div className="tree-item new-file" >&#128196; App.js</div>
          <div className="tree-item new-file" >&#128193; components/</div>
          <div className="tree-item new-file" >&#128193; redux/</div>
          <div className="tree-item new-file" >&#128196; index.js</div>
          <div className="tree-section" >Config</div>
          <div className="tree-item">&#128196; package.json</div>
          <div className="tree-item">&#128196; .env.example</div>
        </div>
        <div className="code-area">
          <div className="tab-bar">
            <div className="code-tab active" id="tab-server">server.js</div>
            <div className="code-tab" id="tab-middleware" >middleware.js</div>
            <div className="code-tab" >models.js</div>
          </div>
          <div className="code-editor" id="editor-server">
            <div className="line"><span className="ln">1</span><span className="cm">// MantiBank — Express server with JWT auth</span></div>
            <div className="line"><span className="ln">2</span><span><span className="kw">const</span> <span className="nm">express</span> = <span className="fn">require</span>(<span className="str">'express'</span>);</span></div>
            <div className="line"><span className="ln">3</span><span><span className="kw">const</span> <span className="nm">helmet</span> = <span className="fn">require</span>(<span className="str">'helmet'</span>);</span></div>
            <div className="line"><span className="ln">4</span><span><span className="kw">const</span> <span className="nm">cors</span> = <span className="fn">require</span>(<span className="str">'cors'</span>);</span></div>
            <div className="line"><span className="ln">5</span><span><span className="kw">const</span> <span className="nm">rateLimit</span> = <span className="fn">require</span>(<span className="str">'express-rate-limit'</span>);</span></div>
            <div className="line"><span className="ln">6</span><span></span></div>
            <div className="line"><span className="ln">7</span><span><span className="kw">const</span> <span className="nm">app</span> = <span className="fn">express</span>();</span></div>
            <div className="line"><span className="ln">8</span><span><span className="nm">app</span>.<span className="fn">use</span>(<span className="fn">helmet</span>());</span></div>
            <div className="line"><span className="ln">9</span><span><span className="nm">app</span>.<span className="fn">use</span>(<span className="fn">cors</span>(&#123; <span className="nm">origin</span>: process.env.<span className="nm">ALLOWED_ORIGINS</span> &#125;));</span></div>
            <div className="line"><span className="ln">10</span><span></span></div>
            <div className="line"><span className="ln">11</span><span><span className="kw">const</span> <span className="nm">limiter</span> = <span className="fn">rateLimit</span>(&#123; <span className="nm">windowMs</span>: <span className="str">15 * 60 * 1000</span>, <span className="nm">max</span>: <span className="str">100</span> &#125;);</span></div>
            <div className="line"><span className="ln">12</span><span><span className="nm">app</span>.<span className="fn">use</span>(<span className="str">'/api/'</span>, <span className="nm">limiter</span>);</span></div>
            <div className="line"><span className="ln">13</span><span></span></div>
            <div className="line"><span className="ln">14</span><span><span className="nm">app</span>.<span className="fn">use</span>(<span className="fn">require</span>(<span className="str">'./routes'</span>));</span></div>
            <div className="line"><span className="ln">15</span><span></span></div>
            <div className="line"><span className="ln">16</span><span><span className="nm">app</span>.<span className="fn">listen</span>(<span className="str">3001</span>, () =&gt; console.<span className="fn">log</span>(<span className="str">'MantiBank server running'</span>));</span></div>
          </div>
          <div className="code-editor hidden" id="editor-middleware">
            <div className="line"><span className="ln">1</span><span className="cm">// JWT + bcrypt auth middleware</span></div>
            <div className="line"><span className="ln">2</span><span><span className="kw">const</span> <span className="nm">jwt</span> = <span className="fn">require</span>(<span className="str">'jsonwebtoken'</span>);</span></div>
            <div className="line"><span className="ln">3</span><span><span className="kw">const</span> <span className="nm">bcrypt</span> = <span className="fn">require</span>(<span className="str">'bcryptjs'</span>);</span></div>
            <div className="line"><span className="ln">4</span><span></span></div>
            <div className="line"><span className="ln">5</span><span><span className="kw">const</span> <span className="fn">authenticate</span> = (<span className="nm">req</span>, <span className="nm">res</span>, <span className="nm">next</span>) =&gt; &#123;</span></div>
            <div className="line"><span className="ln">6</span><span>&nbsp;&nbsp;<span className="kw">const</span> <span className="nm">token</span> = req.headers.<span className="nm">authorization</span>?.<span className="fn">split</span>(<span className="str">' '</span>)[<span className="str">1</span>];</span></div>
            <div className="line"><span className="ln">7</span><span>&nbsp;&nbsp;<span className="kw">if</span> (!<span className="nm">token</span>) <span className="kw">return</span> res.<span className="fn">status</span>(<span className="str">401</span>).<span className="fn">json</span>(&#123; <span className="nm">error</span>: <span className="str">'Unauthorized'</span> &#125;);</span></div>
            <div className="line"><span className="ln">8</span><span>&nbsp;&nbsp;<span className="kw">try</span> &#123; req.user = jwt.<span className="fn">verify</span>(<span className="nm">token</span>, process.env.<span className="nm">JWT_SECRET</span>); <span className="fn">next</span>(); &#125;</span></div>
            <div className="line"><span className="ln">9</span><span>&nbsp;&nbsp;<span className="kw">catch</span> &#123; res.<span className="fn">status</span>(<span className="str">403</span>).<span className="fn">json</span>(&#123; <span className="nm">error</span>: <span className="str">'Invalid token'</span> &#125;); &#125;</span></div>
            <div className="line"><span className="ln">10</span><span>&#125;;</span></div>
          </div>
          <div className="terminal">
            <div className="term-line"><span className="term-prompt">$ </span><span className="term-cmd">mkdir -p MantiBank/backend MantiBank/frontend</span></div>
            <div className="term-line"><span className="term-ok">✔ Directories created</span></div>
            <div className="term-line"><span className="term-prompt">$ </span><span className="term-cmd">cd MantiBank && npm init -y && npm install express helmet cors bcryptjs jsonwebtoken</span></div>
            <div className="term-line"><span className="term-out">added 187 packages from 231 contributors</span></div>
            <div className="term-line"><span className="term-ok">✔ Dependencies installed</span></div>
            <div className="term-line"><span className="term-prompt">$ </span><span className="term-cmd">node server.js</span></div>
            <div className="term-line"><span className="term-ok">✔ MantiBank server running on port 3001</span></div>
            <div className="term-line"><span className="term-prompt">$ </span><span className="term-cursor"></span></div>
          </div>
        </div>
      </div>
    </div>

    {/* WORKSPACE: MEETING */}
    <div className="workspace hidden" id="ws-meeting">
      <div className="workspace-header">
        <div className="workspace-title">
          <span >&#9632;</span> Schedule meeting &nbsp;
          <span className="ws-badge">Meeting mode</span>
        </div>
        <span className="ws-badge green">Jitsi ready</span>
      </div>
      <div className="meeting-workspace">
        <div className="meeting-card">
          <h3>Available time slots — tomorrow</h3>
          <div className="time-slots">
            <div className="slot taken">9:00 AM</div>
            <div className="slot selected">10:00 AM</div>
            <div className="slot">11:00 AM</div>
            <div className="slot">2:00 PM</div>
            <div className="slot taken">3:00 PM</div>
            <div className="slot">4:00 PM</div>
          </div>
        </div>
        <div className="meeting-card">
          <h3>Attendees</h3>
          <div className="attendees">
            <div className="attendee"><div className="av a">YO</div><div className="attendee-info"><div className="attendee-name">You (organizer)</div><div className="attendee-status">&#9679; Available</div></div></div>
            <div className="attendee"><div className="av b">RK</div><div className="attendee-info"><div className="attendee-name">Raj Kumar</div><div className="attendee-status">Checking calendar...</div></div></div>
            <div className="attendee"><div className="av c">+</div><div className="attendee-info"><div className="attendee-name" >Add attendee</div></div></div>
          </div>
        </div>
        <div className="meeting-card">
          <h3>Platform</h3>
          <div >
            <div className="slot selected" >Jitsi (free)</div>
            <div className="slot" >Zoom</div>
            <div className="slot" >Google Meet</div>
          </div>
          <button className="confirm-btn">Confirm &amp; send invites</button>
        </div>
      </div>
    </div>

    {/* WORKSPACE: CHAT ONLY */}
    <div className="workspace hidden" id="ws-chat">
      <div className="workspace-header">
        <div className="workspace-title"><span>Chat-only mode</span><span className="ws-badge">No workspace</span></div>
      </div>
      <div >
        <div >&#128172;</div>
        <div >Chat-only mode — no adaptive workspace</div>
        <div >This is what Super Manager currently does: dumps everything into chat text. Switch to Code IDE or Meeting to see the difference.</div>
        <div >
          import os<br />
          project_name = 'MantiBank'<br />
          structure = &#123;'backend': ['server.js'...]'&#125;<br />
          <span ># ← This is the current problem.</span><br />
          <span ># Raw code in chat = bad UX</span>
        </div>
      </div>
    </div>

    {/* TASK PANEL */}
    <div className="task-panel">
      <div className="task-panel-header">
        <span>Tasks</span>
        <span >&#9679; live</span>
      </div>
      <div className="task-list">
        <div className="task-item expanded">
          <div className="task-name"><span className="ic-ok">&#10003;</span> Build Manti Bank app</div>
          <div className="task-type">CODE_WORKSPACE</div>
          <div className="progress-bar"><div className="progress-fill p-green" ></div></div>
          <div className="task-steps">
            <div className="step"><div className="step-dot done">&#10003;</div><span>Plan project structure</span></div>
            <div className="step"><div className="step-dot done">&#10003;</div><span>Create backend files</span></div>
            <div className="step"><div className="step-dot done">&#10003;</div><span>Create frontend scaffold</span></div>
            <div className="step"><div className="step-dot running">&#9632;</div><span>npm install dependencies</span></div>
            <div className="step"><div className="step-dot todo"></div><span>Run &amp; verify server</span></div>
          </div>
        </div>
        <div className="task-item">
          <div className="task-name"><span className="ic-ok">&#10003;</span> Schedule meeting</div>
          <div className="task-type">MEETING_WORKSPACE</div>
          <div className="progress-bar"><div className="progress-fill p-blue" ></div></div>
        </div>
        <div className="task-item">
          <div className="task-name"><span className="ic-ok">&#10003;</span> Deploy app</div>
          <div className="task-type">DEPLOY_WORKFLOW</div>
          <div className="progress-bar"><div className="progress-fill p-green" ></div></div>
        </div>
        <div className="task-item">
          <div className="task-name"><span className="ic-x">&#10005;</span> Schedule for tomorrow</div>
          <div className="task-type">CHAT_WORKFLOW</div>
          <div className="progress-bar"><div className="progress-fill p-amber" ></div></div>
        </div>
      </div>
    </div>
  </div>
</div>
    </>
  );
}
