import React, { useState, useEffect } from "react";
import "./TaskWorkspace.css";

export default function TaskAdaptiveWorkspace() {
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
      </div>
      <div className="chat-input-area">
        <input type="text" id="chatInput" placeholder="what do you want done?" />
      </div>
    </div>

    {/* WORKSPACE AREA */}
    <div className="ws-area">

      {/* HOME STATE — blank until task given */}
      <div id="state-home" className="home">
        <div className="home-logo">S</div>
        <div>
          <div className="home-title">Nothing running yet.</div>
          <div className="home-sub" style={{marginTop: '5px'}}>Give me any task. A workspace will open automatically — built for exactly that task, with every panel it needs.</div>
        </div>
        <div className="task-examples">
          <div className="ex-label">Click any of these to see how the workspace assembles:</div>
          <div className="ex-row">
            <div className="ex-pill" onClick={() => {}} // "runTask('code')">build a banking app</div>
            <div className="ex-pill" onClick={() => {}} // "runTask('meeting')">schedule a meeting tomorrow</div>
            <div className="ex-pill" onClick={() => {}} // "runTask('trade')">buy 0.1 BTC now</div>
          </div>
          <div className="ex-row">
            <div className="ex-pill" onClick={() => {}} // "runTask('shirt')">book me a shirt for weekend</div>
            <div className="ex-pill" onClick={() => {}} // "runTask('flight')">fly me to Goa Friday</div>
            <div className="ex-pill" onClick={() => {}} // "runTask('video')">edit my product video</div>
          </div>
          <div className="ex-row">
            <div className="ex-pill" onClick={() => {}} // "runTask('social')">post launch on instagram</div>
            <div className="ex-pill" onClick={() => {}} // "runTask('unknown')">renew my car insurance</div>
          </div>
        </div>
      </div>

      {/* THINKING STATE — shown briefly */}
      <div id="state-thinking" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '24px'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '10px', width: '100%', maxWidth: '420px'}}>
          <div style={{width: '22px', height: '22px', borderRadius: '6px', background: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: '#fff'}}>S</div>
          <div style={{fontSize: '12px', color: '#e6edf3', fontWeight: '500'}} id="thinkLabel">...</div>
        </div>
        <div style={{width: '100%', maxWidth: '420px', display: 'flex', flexDirection: 'column', gap: '6px'}} id="thinkSteps"></div>
        <div style={{width: '100%', maxWidth: '420px'}}>
          <div style={{fontSize: '9px', color: '#484f58', marginBottom: '6px'}}>Assembling workspace panels:</div>
          <div style={{display: 'flex', gap: '5px', flexWrap: 'wrap'}} id="thinkBlocks"></div>
        </div>
      </div>

      {/* WORKSPACE STATES */}
      {/* CODE IDE */}
      <div id="state-code" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128196;</span>
          <span className="wsh-label">build a banking app — MantiBank /</span>
          <span className="badge bp">IDE</span><span className="badge bg">15 files</span><span className="badge ba">npm installing</span>
          <div className="live-ind"><div className="ldot"></div>live preview</div>
        </div>
        <div className="panels">
          {/* Panel 1: File tree */}
          <div className="panel" style={{width: '140px'}}>
            <div className="panel-header"><span className="ph-icon">&#128193;</span><span className="ph-title">Files</span></div>
            <div className="panel-body">
              <div className="ftree-folder">&#128193; backend/</div>
              <div className="ftree-item on">&#128196; server.js</div>
              <div className="ftree-item">&#128196; middleware.js</div>
              <div className="ftree-item">&#128196; routes.js</div>
              <div className="ftree-item">&#128196; models.js</div>
              <div className="ftree-folder">&#128193; frontend/</div>
              <div className="ftree-item" style={{color: '#3fb950'}}>&#128196; App.js</div>
              <div className="ftree-item" style={{color: '#3fb950'}}>&#128193; components/</div>
              <div className="ftree-item">&#128196; package.json</div>
            </div>
          </div>
          {/* Panel 2: Editor + Terminal */}
          <div className="panel" style={{flex: '1', minWidth: '0'}}>
            <div className="panel-header"><span className="ph-icon">&#9998;</span><span className="ph-title">server.js</span><span className="badge bp" style={{fontSize: '8px'}}>active</span></div>
            <div className="panel-body" style={{display: 'flex', flexDirection: 'column'}}>
              <div className="code-editor" style={{flex: '1'}}>
<pre style={{margin: '0'}}><span className="cm">// MantiBank — secure Express server</span>
<span className="kw">const</span> <span className="nm">express</span> = <span className="fn">require</span>(<span className="str">'express'</span>);
<span className="kw">const</span> <span className="nm">helmet</span>  = <span className="fn">require</span>(<span className="str">'helmet'</span>);
<span className="kw">const</span> <span className="nm">cors</span>    = <span className="fn">require</span>(<span className="str">'cors'</span>);
<span className="kw">const</span> <span className="nm">app</span> = <span className="fn">express</span>();
<span className="nm">app</span>.<span className="fn">use</span>(<span className="fn">helmet</span>());
<span className="nm">app</span>.<span className="fn">use</span>(<span className="fn">cors</span>({ <span className="nm">origin</span>: process.env.<span className="nm">ORIGINS</span> }));
<span className="nm">app</span>.<span className="fn">listen</span>(<span className="str">3001</span>);</pre>
              </div>
              <div className="term" style={{borderTop: '0.5px solid #30363d', flexShrink: '0'}}>
                <div><span className="tok">✔ npm install done</span></div>
                <div><span className="tp2">$ </span><span className="tc">node server.js</span></div>
                <div><span className="tok">✔ MantiBank running :3001</span></div>
                <div><span className="tp2">$ </span><span className="tcur"></span></div>
              </div>
            </div>
          </div>
          {/* Panel 3: Live preview */}
          <div className="panel" style={{flex: '1', minWidth: '0'}}>
            <div className="panel-header">
              <span className="ph-icon">&#128452;</span><span className="ph-title">Live preview — localhost:3000</span>
              <div style={{display: 'flex', alignItems: 'center', gap: '3px'}}><div className="ldot"></div><span style={{fontSize: '8px', color: '#3fb950'}}>running</span></div>
            </div>
            <div className="panel-body">
              <div className="bank-preview">
                <div className="bnav"><div className="blogo"><div className="bico">M</div>Manti Bank</div><div style={{display: 'flex', gap: '7px', fontSize: '9px', color: '#a0a8c8'}}><span>Home</span><span>Transfer</span><span>History</span></div></div>
                <div className="bbody">
                  <div className="balcard"><div className="ballbl">Total balance</div><div className="balamt">&#8377;2,45,830</div><div style={{fontSize: '8px', color: '#a0a8c8'}}>MANTI •••• 4821</div></div>
                  <div className="qarow"><div className="qa">&#128197; Pay</div><div className="qa">&#128260; Send</div><div className="qa">&#128179; Deposit</div><div className="qa">&#128200; Invest</div></div>
                  <div className="txn-list">
                    <div className="txn-h">Transactions</div>
                    <div className="txn"><div className="txn-av" style={{background: '#e8f0fe'}}>&#127968;</div><div><div className="txn-name">Amazon</div><div className="txn-date">Today</div></div><div className="txn-amt neg">-&#8377;1,299</div></div>
                    <div className="txn"><div className="txn-av" style={{background: '#e8f5e9'}}>&#128176;</div><div><div className="txn-name">Salary</div><div className="txn-date">Mar 22</div></div><div className="txn-amt pos">+&#8377;75,000</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* MEETING */}
      <div id="state-meeting" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128222;</span>
          <span className="wsh-label">schedule a meeting tomorrow</span>
          <span className="badge bp">Meeting</span><span className="badge bb">Jitsi ready</span>
          <div className="live-ind"><div className="ldot"></div>calendar synced</div>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128197;</span><span className="ph-title">Time slots — tomorrow</span></div>
            <div className="panel-body">
              <div className="slot-grid">
                <div className="slot gone">9:00 AM</div><div className="slot sel">10:00 AM</div><div className="slot">11:00 AM</div>
                <div className="slot">2:00 PM</div><div className="slot gone">3:00 PM</div><div className="slot">4:00 PM</div>
              </div>
              <div className="divider"></div>
              <div className="c-section">Attendees</div>
              <div className="attendee"><div className="att-av" style={{background: '#7c3aed44', color: '#d2a8ff'}}>YO</div><div><div className="att-name">You</div><div className="att-st">&#9679; Available</div></div></div>
              <div className="attendee"><div className="att-av" style={{background: '#1f6feb44', color: '#58a6ff'}}>RK</div><div><div className="att-name">Raj Kumar</div><div className="att-st">Checking...</div></div></div>
              <div className="c-section" style={{marginTop: '6px'}}>Platform</div>
              <div style={{display: 'flex', gap: '5px', padding: '6px 12px'}}>
                <div className="slot sel" style={{flex: '1'}}>Jitsi</div><div className="slot" style={{flex: '1'}}>Zoom</div><div className="slot" style={{flex: '1'}}>Meet</div>
              </div>
              <button className="cfm-btn">Confirm &amp; send invites</button>
            </div>
          </div>
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128250;</span><span className="ph-title">Live meeting preview</span><div style={{display: 'flex', alignItems: 'center', gap: '3px', marginLeft: 'auto'}}><div className="ldot"></div><span style={{fontSize: '8px', color: '#3fb950'}}>Jitsi</span></div></div>
            <div className="panel-body">
              <div className="cam-grid">
                <div className="cam"><div className="cam-live">LIVE</div><span style={{fontSize: '18px'}}>&#128100;</span><div className="cam-name">You</div></div>
                <div className="cam"><span style={{fontSize: '18px'}}>&#128100;</span><div className="cam-name">Raj Kumar</div></div>
              </div>
              <div className="meet-controls"><div className="mc">&#127897;</div><div className="mc">&#127916;</div><div className="mc" style={{background: '#3fb950', borderColor: '#3fb950'}}>&#128222;</div><div className="mc red">&#9660;</div></div>
              <div className="divider"></div>
              <div className="c-section">Recording &amp; sharing</div>
              <div style={{display: 'flex', gap: '5px', padding: '6px 12px', flexWrap: 'wrap'}}>
                <div className="slot sel" style={{fontSize: '9px'}}>&#128250; Record</div>
                <div className="slot sel" style={{fontSize: '9px'}}>&#128203; Transcript</div>
                <div className="slot" style={{fontSize: '9px'}}>&#128229; Auto-email</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* TRADE */}
      <div id="state-trade" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128200;</span>
          <span className="wsh-label">buy 0.1 BTC now</span>
          <span className="badge br">High risk</span><span className="badge bp">Confirm needed</span>
          <div className="live-ind"><div className="ldot"></div>live price</div>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128200;</span><span className="ph-title">BTC/USDT live</span></div>
            <div className="panel-body">
              <div className="chart-bars" id="btcBars"></div>
              <div className="price-big">$67,420</div>
              <div className="price-chg">+2.4% today</div>
              <div className="divider"></div>
              <div className="order-row"><div className="order-side buy-side">BUY</div><div className="order-side sell-side">SELL</div></div>
              <div className="c-pad">
                <div className="c-field"><div className="c-label">Pair</div><div className="c-val">BTC / USDT</div></div>
                <div className="c-field"><div className="c-label">Type</div><div className="c-val">Market</div></div>
                <div className="c-field"><div className="c-label">Amount</div><div className="c-val">0.1 BTC</div></div>
                <div className="c-field"><div className="c-label">Est. cost</div><div className="c-val r">$6,742</div></div>
                <div className="c-field"><div className="c-label">Balance</div><div className="c-val g">$9,100 ✓</div></div>
              </div>
            </div>
          </div>
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#9888;</span><span className="ph-title">Confirm before executing</span></div>
            <div className="panel-body">
              <div style={{padding: '10px 12px'}}>
                <div style={{fontSize: '10px', color: '#8b949e', lineHeight: '1.6', marginBottom: '10px'}}>This is a real money action. I won't do it until you say yes. Check the details below carefully.</div>
              </div>
              <div className="confirm-wrap">
                <div className="cw-title">&#9888; Irreversible — needs approval</div>
                <div className="cw-row"><div className="cw-k">You send</div><div className="cw-v" style={{color: '#f85149'}}>$6,742 USDT</div></div>
                <div className="cw-row"><div className="cw-k">You get</div><div className="cw-v" style={{color: '#3fb950'}}>0.1 BTC</div></div>
                <div className="cw-row"><div className="cw-k">Fee</div><div className="cw-v">$6.74</div></div>
                <div className="cw-row"><div className="cw-k">Exchange</div><div className="cw-v">Binance spot</div></div>
                <div className="cw-btns"><div className="cw-btn cw-no">Cancel</div><div className="cw-btn cw-go">Yes, execute</div></div>
              </div>
              <div style={{padding: '8px 12px', fontSize: '9px', color: '#484f58', lineHeight: '1.6'}}>I had no pre-built "Binance workspace". These two panels — price data + confirm — are what this specific task needed. A different task gets entirely different panels.</div>
            </div>
          </div>
        </div>
      </div>

      {/* SHIRT */}
      <div id="state-shirt" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128248;</span>
          <span className="wsh-label">book me a shirt for weekend</span>
          <span className="badge bg">Low risk</span><span className="badge bp">Size M from memory</span>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128722;</span><span className="ph-title">Results — 3 sites searched</span></div>
            <div className="panel-body">
              <div style={{padding: '6px 12px 3px', fontSize: '9px', color: '#7c3aed'}}>&#128161; I remembered: size M, minimal style — pre-filtered</div>
              <div className="prod-card best">
                <div className="prod-top"><div className="prod-img">&#128248;</div><div><div className="prod-name">Roadster oversized white</div><div className="prod-site">Myntra</div></div><div className="prod-price">&#8377;899</div></div>
                <div className="prod-tag tg">&#10003; Best match + M in stock + Friday delivery</div>
              </div>
              <div className="prod-card">
                <div className="prod-top"><div className="prod-img">&#128248;</div><div><div className="prod-name">H&amp;M slim navy</div><div className="prod-site">HM.com</div></div><div className="prod-price">&#8377;1,299</div></div>
                <div className="prod-tag ta">Slightly formal</div>
              </div>
              <div className="prod-card">
                <div className="prod-top"><div className="prod-img">&#128248;</div><div><div className="prod-name">SNITCH linen cream</div><div className="prod-site">Ajio</div></div><div className="prod-price">&#8377;749</div></div>
                <div className="prod-tag tb">Cheapest option</div>
              </div>
            </div>
          </div>
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128203;</span><span className="ph-title">Checkout</span></div>
            <div className="panel-body">
              <div className="checkout-block">
                <div className="checkout-row"><div className="ck-k">Item</div><div className="ck-v">Roadster oversized white, M</div></div>
                <div className="checkout-row"><div className="ck-k">Deliver to</div><div className="ck-v">Saved home address</div></div>
                <div className="checkout-row"><div className="ck-k">By</div><div className="ck-v" style={{color: '#3fb950'}}>Friday — before weekend ✓</div></div>
                <div className="checkout-row"><div className="ck-k">Pay via</div><div className="ck-v">UPI (last used)</div></div>
                <div className="checkout-row"><div className="ck-k">Total</div><div className="ck-v" style={{fontSize: '12px', fontWeight: '500', color: '#e6edf3'}}>&#8377;899</div></div>
                <button className="order-btn">Order now</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FLIGHT */}
      <div id="state-flight" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#9992;</span>
          <span className="wsh-label">fly me to Goa Friday</span>
          <span className="badge ba">Medium risk</span><span className="badge bp">Window seat from memory</span>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#9992;</span><span className="ph-title">BLR → GOA · Fri Mar 27</span></div>
            <div className="panel-body">
              <div style={{padding: '6px 12px 3px', fontSize: '9px', color: '#7c3aed'}}>&#128161; Searched IndiGo, Air India, SpiceJet</div>
              <div className="flight-card best">
                <div className="fl-row"><div className="fl-airline">IndiGo 6E-502</div><div className="fl-times">8:45 → 10:05</div><div className="fl-dur">1h 20m</div><div className="fl-price">&#8377;4,299</div></div>
                <div style={{fontSize: '8px', color: '#3fb950', marginTop: '3px'}}>&#10003; Best price · non-stop</div>
              </div>
              <div className="flight-card">
                <div className="fl-row"><div className="fl-airline">Air India AI-834</div><div className="fl-times">9:10 → 10:30</div><div className="fl-dur">1h 20m</div><div className="fl-price">&#8377;5,100</div></div>
              </div>
              <div className="divider"></div>
              <div className="c-section">Booking summary</div>
              <div style={{padding: '6px 12px 10px'}}>
                <div className="c-field"><div className="c-label">Flight</div><div className="c-val">IndiGo 6E-502</div></div>
                <div className="c-field"><div className="c-label">Seat</div><div className="c-val g">22A window ✓ (remembered)</div></div>
                <div className="c-field"><div className="c-label">Total</div><div className="c-val a">&#8377;4,299</div></div>
                <div style={{display: 'flex', gap: '5px', marginTop: '7px'}}>
                  <button style={{flex: '1', padding: '6px', background: '#7c3aed', border: 'none', borderRadius: '6px', color: '#fff', fontSize: '10px', cursor: 'pointer', fontFamily: 'var(--font-sans)'}}>Confirm &amp; book</button>
                  <button style={{padding: '6px 10px', background: 'transparent', border: '0.5px solid #30363d', borderRadius: '6px', color: '#8b949e', fontSize: '10px', cursor: 'pointer', fontFamily: 'var(--font-sans)'}}>Change</button>
                </div>
              </div>
            </div>
          </div>
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128186;</span><span className="ph-title">Seat map — IndiGo 6E-502</span></div>
            <div className="panel-body">
              <div style={{padding: '6px 12px 3px', fontSize: '9px', color: '#7c3aed'}}>&#128161; Pre-selected window seat (your preference)</div>
              <div className="seat-map" id="seatMap"></div>
            </div>
          </div>
        </div>
      </div>

      {/* VIDEO */}
      <div id="state-video" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#127916;</span>
          <span className="wsh-label">edit my product video</span>
          <span className="badge bp">Video mode</span><span className="badge ba">AI editing</span>
          <div className="live-ind"><div className="ldot"></div>preview live</div>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1.2'}}>
            <div className="panel-header"><span className="ph-icon">&#9654;</span><span className="ph-title">Preview</span><div style={{display: 'flex', alignItems: 'center', gap: '3px', marginLeft: 'auto'}}><div className="ldot"></div><span style={{fontSize: '8px', color: '#3fb950'}}>00:12 / 01:45</span></div></div>
            <div className="panel-body" style={{display: 'flex', flexDirection: 'column'}}>
              <div className="video-screen" style={{flex: '1'}}>
                <span style={{fontSize: '28px'}}>&#127775;</span>
                <span style={{fontSize: '11px', color: '#a0a8c8'}}>Super Manager — Product Showcase</span>
                <div style={{background: '#7c3aed', color: '#fff', fontSize: '8px', padding: '2px 6px', borderRadius: '4px', marginTop: '4px'}}>&#10024; AI editing</div>
              </div>
              <div className="tl-wrap" style={{borderTop: '0.5px solid #30363d'}}>
                <div className="tl-track"><div className="tl-lbl">Video</div><div className="tl-clips"><div className="clip clip-v" style={{width: '70px'}}>Intro</div><div style={{width: '8px', height: '18px', background: '#1a3a6e', borderRadius: '2px'}}></div><div className="clip clip-v" style={{width: '55px'}}>Demo</div><div style={{width: '8px', height: '18px', background: '#1a3a6e', borderRadius: '2px'}}></div><div className="clip clip-v" style={{width: '45px'}}>CTA</div></div></div>
                <div className="tl-track"><div className="tl-lbl">Audio</div><div className="tl-clips"><div className="clip clip-a" style={{width: '190px'}}>Lo-fi background</div></div></div>
                <div className="tl-track"><div className="tl-lbl">Captions</div><div className="tl-clips"><div className="clip clip-t" style={{width: '80px'}}>AI captions</div><div className="clip clip-t" style={{width: '55px', marginLeft: '3px'}}>Subtitles</div></div></div>
              </div>
              <div className="tl-controls">
                <div className="tlc">&#9194;</div><div className="tlc">&#9654;</div><div className="tlc">&#9193;</div>
                <button className="export-btn-v" style={{marginLeft: '6px'}}>Export &amp; upload</button>
              </div>
            </div>
          </div>
          <div className="panel" style={{width: '160px'}}>
            <div className="panel-header"><span className="ph-icon">&#128260;</span><span className="ph-title">AI tools</span></div>
            <div className="panel-body">
              <div className="c-section">Applied</div>
              <div style={{display: 'flex', flexDirection: 'column', gap: '4px', padding: '6px 12px'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#3fb950'}}><span>&#10003;</span>Remove silence</div>
                <div style={{display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#3fb950'}}><span>&#10003;</span>AI captions</div>
                <div style={{display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10px', color: '#3fb950'}}><span>&#10003;</span>Music added</div>
              </div>
              <div className="c-section">Add</div>
              <div style={{display: 'flex', flexDirection: 'column', gap: '4px', padding: '6px 12px'}}>
                <div style={{padding: '4px 7px', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '5px', fontSize: '9px', color: '#8b949e', cursor: 'pointer'}}>Intro animation</div>
                <div style={{padding: '4px 7px', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '5px', fontSize: '9px', color: '#8b949e', cursor: 'pointer'}}>Logo watermark</div>
                <div style={{padding: '4px 7px', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '5px', fontSize: '9px', color: '#8b949e', cursor: 'pointer'}}>CTA overlay</div>
              </div>
              <div className="c-section">Post to</div>
              <div className="plat-row" style={{padding: '6px 12px'}}>
                <div className="plat on">Instagram</div><div className="plat">YouTube</div><div className="plat">TikTok</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SOCIAL */}
      <div id="state-social" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128247;</span>
          <span className="wsh-label">post launch on instagram</span>
          <span className="badge bp">Social</span><span className="badge bg">AI drafted post</span>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128247;</span><span className="ph-title">Post preview</span></div>
            <div className="panel-body">
              <div className="ig-post">
                <div className="ig-head"><div className="ig-av">SM</div><div className="ig-name">supermanager.ai</div></div>
                <div className="ig-img"><span style={{fontSize: '28px'}}>&#127775;</span><span style={{fontSize: '10px', color: '#fff', fontWeight: '500'}}>Super Manager 3.0</span><span style={{fontSize: '9px', color: '#ddd'}}>AI that actually does things</span></div>
                <div className="ig-caption">&#127775; Introducing Super Manager 3.0 — AI that doesn't tell you what to do, it does it for you.<br /><span style={{color: '#003569'}}>#AI #ProductLaunch #AgenticAI</span></div>
              </div>
              <div style={{padding: '0 10px 4px', fontSize: '9px', color: '#484f58'}}>Edit caption:</div>
              <div style={{margin: '0 10px 8px', background: '#21262d', border: '0.5px solid #30363d', borderRadius: '6px', padding: '6px 8px', fontSize: '9px', color: '#c9d1d9', lineHeight: '1.6'}}>&#127775; Introducing Super Manager 3.0...</div>
            </div>
          </div>
          <div className="panel" style={{width: '170px'}}>
            <div className="panel-header"><span className="ph-icon">&#128228;</span><span className="ph-title">Publish settings</span></div>
            <div className="panel-body">
              <div className="c-section">Post to</div>
              <div className="plat-row">
                <div className="plat on">Instagram</div><div className="plat on">Facebook</div><div className="plat">Twitter</div><div className="plat">LinkedIn</div>
              </div>
              <div className="divider"></div>
              <div className="c-section">Schedule</div>
              <div className="sched-time">Tomorrow 9:00 AM (AI pick)</div>
              <div className="divider"></div>
              <div className="c-section">Auto-actions</div>
              <div style={{display: 'flex', flexDirection: 'column', gap: '4px', padding: '6px 12px'}}>
                <div className="plat on" style={{display: 'block'}}>&#10003; Auto-reply DMs</div>
                <div className="plat on" style={{display: 'block'}}>&#10003; Boost after 1hr</div>
                <div className="plat" style={{display: 'block'}}>Add to story</div>
              </div>
              <button className="post-btn" style={{margin: '6px 12px 10px', width: 'calc(100% - 24px)'}}>Post now</button>
            </div>
          </div>
        </div>
      </div>

      {/* UNKNOWN / BROWSER FALLBACK */}
      <div id="state-unknown" className="hidden" style={{flex: '1', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        <div className="ws-header">
          <span style={{fontSize: '12px'}}>&#128269;</span>
          <span className="wsh-label">renew my car insurance</span>
          <span className="badge bb">No API — browser mode</span><span className="badge ba">AI navigating</span>
        </div>
        <div className="panels">
          <div className="panel" style={{flex: '1'}}>
            <div className="panel-header"><span className="ph-icon">&#128269;</span><span className="ph-title">What I'm doing</span></div>
            <div className="panel-body">
              <div style={{padding: '8px 12px', fontSize: '10px', color: '#d29922', background: '#bb800911', borderBottom: '0.5px solid #bb800944', lineHeight: '1.6'}}>No direct API for this. I'm opening your insurer's site and doing it myself. You just watch.</div>
              <div className="steps-list">
                <div className="sl-step"><div className="sl-dot sl-ok">&#10003;</div>Found insurer: Tata AIG (from your email)</div>
                <div className="sl-step"><div className="sl-dot sl-ok">&#10003;</div>Opened tataaig.com, logged in</div>
                <div className="sl-step"><div className="sl-dot sl-run">&#9632;</div>Navigating to renewal page...</div>
                <div className="sl-step"><div className="sl-dot sl-td"></div>Fill vehicle details</div>
                <div className="sl-step"><div className="sl-dot sl-td"></div>Show you quote — confirm before paying</div>
              </div>
              <div className="divider"></div>
              <div className="c-section">From your memory</div>
              <div style={{padding: '6px 12px', display: 'flex', flexDirection: 'column', gap: '3px'}}>
                <div className="c-field"><div className="c-label">Policy</div><div className="c-val">TTA-2024-MH-99201</div></div>
                <div className="c-field"><div className="c-label">Vehicle</div><div className="c-val">MH12 AB 1234</div></div>
                <div className="c-field"><div className="c-label">Insurer</div><div className="c-val">Tata AIG</div></div>
              </div>
            </div>
          </div>
          <div className="panel" style={{flex: '1.2'}}>
            <div className="panel-header"><span className="ph-icon">&#127760;</span><span className="ph-title">Browser — live view</span><div className="ai-badge2" style={{marginLeft: 'auto'}}>AI cursor active</div></div>
            <div className="panel-body">
              <div className="browser-bar-2">
                <div className="bdots2"><span className="bd-r"></span><span className="bd-y"></span><span className="bd-g"></span></div>
                <div className="burl2">tataaig.com/renew-policy</div>
              </div>
              <div className="browser-body">
                <div className="bf-row"><div className="bf-lbl">Policy no.</div><div className="bf-in act">TTA-2024-MH-99201 &#9646;</div></div>
                <div className="bf-row"><div className="bf-lbl">Reg. no.</div><div className="bf-in">MH12 AB 1234</div></div>
                <div className="bf-row"><div className="bf-lbl">Mobile</div><div className="bf-in">+91 98XXXXXXXX</div></div>
                <div className="bf-row" style={{justifyContent: 'flex-end', marginTop: '4px'}}><button className="bf-btn">Continue</button></div>
                <div style={{marginTop: '10px', fontSize: '9px', color: '#484f58', lineHeight: '1.6', padding: '7px 9px', background: '#161b22', border: '0.5px solid #30363d', borderRadius: '6px'}}>After renewal, I'll save the new policy number and remind you 30 days before next year's expiry — automatically.</div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    {/* TASK PANEL */}
    <div className="task-panel" id="taskPanel" style={{display: 'none'}}>
      <div className="tp-head"><span>Tasks</span><span style={{color: '#3fb950', fontSize: '9px'}}>&#9679; live</span></div>
      <div className="task-list" id="taskList"></div>
    </div>

  </div>
</div>
  );
}
