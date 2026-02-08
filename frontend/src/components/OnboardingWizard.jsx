import React, { useState, useEffect } from 'react'
import { 
  Mail, 
  Lock, 
  CheckCircle, 
  AlertCircle, 
  Loader,
  ChevronRight,
  ExternalLink,
  Shield,
  Key,
  Info,
  X
} from 'lucide-react'
import './OnboardingWizard.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-11-production.up.railway.app'

/**
 * AI Identity Onboarding Wizard
 * 
 * Guides users through setting up an email for their AI:
 * 1. Create a new Gmail account
 * 2. Enable 2-Step Verification
 * 3. Create an App Password
 * 4. Connect it to Super Manager
 */
export default function OnboardingWizard({ userId, onComplete, onSkip }) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  
  // Form data
  const [email, setEmail] = useState('')
  const [appPassword, setAppPassword] = useState('')
  const [displayName, setDisplayName] = useState('AI Assistant')

  const totalSteps = 4

  const handleSetup = async () => {
    if (!email || !appPassword) {
      setError('Please enter both email and app password')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API}/api/identity/setup`, {
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

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="wizard-step">
            <div className="step-icon">
              <Mail size={48} />
            </div>
            <h2>Create an Email for Your AI</h2>
            <p className="step-description">
              Your AI needs its own Gmail account to send emails, sign up for services, 
              and act as your digital assistant.
            </p>
            
            <div className="instruction-card">
              <h3>Why a separate email?</h3>
              <ul>
                <li>🔐 <strong>Security:</strong> Your personal email stays private</li>
                <li>🤖 <strong>Autonomy:</strong> AI can sign up for services autonomously</li>
                <li>📧 <strong>Organization:</strong> Keep AI activities separate</li>
                <li>🔑 <strong>API Access:</strong> AI can get its own API keys</li>
              </ul>
            </div>

            <a 
              href="https://accounts.google.com/signup" 
              target="_blank" 
              rel="noopener noreferrer"
              className="external-link-btn"
            >
              Create Gmail Account <ExternalLink size={16} />
            </a>

            <p className="hint">
              💡 Tip: Use a name like "yourname.ai.assistant@gmail.com"
            </p>
          </div>
        )

      case 2:
        return (
          <div className="wizard-step">
            <div className="step-icon">
              <Shield size={48} />
            </div>
            <h2>Enable 2-Step Verification</h2>
            <p className="step-description">
              This is required to create an App Password (which we'll use next).
            </p>

            <div className="instruction-card">
              <h3>Steps:</h3>
              <ol>
                <li>Go to your Google Account settings</li>
                <li>Click <strong>Security</strong> in the left menu</li>
                <li>Under "Signing in to Google", click <strong>2-Step Verification</strong></li>
                <li>Follow the setup wizard (use your phone)</li>
                <li>Complete the verification</li>
              </ol>
            </div>

            <a 
              href="https://myaccount.google.com/security" 
              target="_blank" 
              rel="noopener noreferrer"
              className="external-link-btn"
            >
              Open Google Security Settings <ExternalLink size={16} />
            </a>

            <div className="warning-box">
              <AlertCircle size={20} />
              <span>Make sure you're signed into the new AI email, not your personal account!</span>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="wizard-step">
            <div className="step-icon">
              <Key size={48} />
            </div>
            <h2>Create an App Password</h2>
            <p className="step-description">
              App Passwords let the AI access Gmail without using your regular password.
            </p>

            <div className="instruction-card">
              <h3>Steps:</h3>
              <ol>
                <li>Go to App Passwords page (link below)</li>
                <li>Select app: <strong>Mail</strong></li>
                <li>Select device: <strong>Other (Custom name)</strong></li>
                <li>Enter name: <strong>Super Manager AI</strong></li>
                <li>Click <strong>Generate</strong></li>
                <li>Copy the 16-character password shown</li>
              </ol>
            </div>

            <a 
              href="https://myaccount.google.com/apppasswords" 
              target="_blank" 
              rel="noopener noreferrer"
              className="external-link-btn"
            >
              Create App Password <ExternalLink size={16} />
            </a>

            <div className="info-box">
              <Info size={20} />
              <span>The password looks like: <code>xxxx xxxx xxxx xxxx</code></span>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="wizard-step">
            <div className="step-icon success">
              <Lock size={48} />
            </div>
            <h2>Connect Your AI</h2>
            <p className="step-description">
              Enter the Gmail address and App Password to give your AI its identity.
            </p>

            {error && (
              <div className="error-box">
                <AlertCircle size={20} />
                <span>{error}</span>
                <button onClick={() => setError(null)}><X size={16} /></button>
              </div>
            )}

            {success ? (
              <div className="success-box">
                <CheckCircle size={48} />
                <h3>AI Identity Created!</h3>
                <p>Your AI can now send emails, sign up for services, and act autonomously.</p>
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); handleSetup(); }}>
                <div className="form-group">
                  <label>
                    <Mail size={16} /> AI Gmail Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ai.assistant@gmail.com"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    <Key size={16} /> App Password
                  </label>
                  <input
                    type="password"
                    value={appPassword}
                    onChange={(e) => setAppPassword(e.target.value.replace(/\s/g, ''))}
                    placeholder="xxxxxxxxxxxxxxxx"
                    maxLength={16}
                    required
                  />
                  <span className="hint">Paste the 16-character app password (spaces are removed automatically)</span>
                </div>

                <div className="form-group">
                  <label>
                    AI Display Name (optional)
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="AI Assistant"
                  />
                </div>

                <button 
                  type="submit" 
                  className="submit-btn"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader className="spinning" size={20} />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircle size={20} />
                      Connect AI Identity
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        )

      default:
        return null
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

      {/* Progress bar */}
      <div className="progress-bar">
        {[1, 2, 3, 4].map((s) => (
          <div 
            key={s}
            className={`progress-step ${step >= s ? 'active' : ''} ${step === s ? 'current' : ''}`}
            onClick={() => s < step && setStep(s)}
          >
            <div className="step-number">{s}</div>
            <span className="step-label">
              {s === 1 && 'Create Email'}
              {s === 2 && 'Enable 2FA'}
              {s === 3 && 'App Password'}
              {s === 4 && 'Connect'}
            </span>
          </div>
        ))}
      </div>

      {/* Step content */}
      <div className="wizard-content">
        {renderStep()}
      </div>

      {/* Navigation */}
      <div className="wizard-nav">
        {step > 1 && (
          <button 
            className="nav-btn prev"
            onClick={() => setStep(step - 1)}
          >
            Back
          </button>
        )}
        
        {step < totalSteps && (
          <button 
            className="nav-btn next"
            onClick={() => setStep(step + 1)}
          >
            Next <ChevronRight size={16} />
          </button>
        )}
      </div>
    </div>
  )
}
