import React, { useState } from 'react'
import { 
  Mail, 
  Lock, 
  CheckCircle, 
  AlertCircle, 
  Loader,
  Key,
  X
} from 'lucide-react'
import { apiUrl } from '../lib/apiBase'
import './OnboardingWizard.css'

export default function OnboardingWizard({ userId, onComplete, onSkip }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  
  // Form data
  const [email, setEmail] = useState('')
  const [appPassword, setAppPassword] = useState('')
  const [displayName, setDisplayName] = useState('AI Assistant')

  const handleSetup = async () => {
    if (!email || !appPassword) {
      setError('Please enter both email and app password')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(apiUrl('/api/identity/setup'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          email: email,
          app_password: appPassword,
          display_name: displayName
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Setup failed')
      }

      setSuccess(true)
      setTimeout(() => {
        onComplete?.(data)
      }, 2000)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="onboarding-wizard">
      <div className="wizard-header">
        <h1>🤖 AI Identity Setup</h1>
        <button className="skip-btn" onClick={onSkip}>
          Skip for now
        </button>
      </div>

      <div className="wizard-content">
        <div className="wizard-step">
          <h2>Connect Your AI's Gmail Account</h2>
          <p className="step-description">
            Your AI needs a dedicated Gmail account with an <strong>App Password</strong> to act autonomously and send emails on your behalf.
          </p>

          <div className="instruction-card" style={{ padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', marginBottom: '24px' }}>
            <h4 style={{ margin: '0 0 10px 0', display: 'flex', alignItems: 'center', gap: '8px', color: '#e2e8f0' }}>
              <Key size={18} /> How to get an App Password:
            </h4>
            <ol style={{ margin: 0, paddingLeft: '24px', color: '#cbd5e1', lineHeight: '1.6' }}>
              <li>Enable <strong>2-Step Verification</strong> on the Google Account.</li>
              <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'none' }}>Google App Passwords</a>.</li>
              <li>Create a new password (Custom name: "Super Manager AI") and paste the 16-letter code below.</li>
            </ol>
          </div>

          {error && (
            <div className="error-box">
              <AlertCircle size={20} />
              <span>{error}</span>
              <button onClick={() => setError(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}><X size={16} /></button>
            </div>
          )}

          {success ? (
            <div className="success-box" style={{ textAlign: 'center', padding: '30px' }}>
              <CheckCircle size={48} color="#10b981" style={{ margin: '0 auto 15px' }} />
              <h3 style={{ color: '#10b981' }}>AI Identity Connected!</h3>
              <p style={{ color: '#94a3b8' }}>Your AI is now ready to send emails and sign up for services.</p>
            </div>
          ) : (
            <form onSubmit={(e) => { e.preventDefault(); handleSetup(); }}>
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#e2e8f0', marginBottom: '8px' }}>
                  <Mail size={16} /> AI Gmail Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. yourname.assistant@gmail.com"
                  required
                  style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid #475569', borderRadius: '6px', color: 'white', marginBottom: '16px' }}
                />
              </div>

              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#e2e8f0', marginBottom: '8px' }}>
                  <Key size={16} /> App Password
                </label>
                <input
                  type="password"
                  value={appPassword}
                  onChange={(e) => setAppPassword(e.target.value.replace(/\s/g, ''))}
                  placeholder="16-character code"
                  maxLength={19}
                  required
                  style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid #475569', borderRadius: '6px', color: 'white', marginBottom: '8px' }}
                />
                <div style={{ fontSize: '0.85em', color: '#94a3b8', marginBottom: '16px' }}>Spaces are removed automatically.</div>
              </div>

              <div className="form-group">
                <label style={{ display: 'block', color: '#e2e8f0', marginBottom: '8px' }}>AI Display Name (optional)</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="AI Assistant"
                  style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid #475569', borderRadius: '6px', color: 'white', marginBottom: '24px' }}
                />
              </div>

              <button 
                type="submit" 
                className="submit-btn"
                disabled={loading}
                style={{ width: '100%', padding: '14px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
              >
                {loading ? (
                  <><Loader className="spinning" size={20} /> Verifying...</>
                ) : (
                  <><CheckCircle size={20} /> Connect AI Identity</>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
