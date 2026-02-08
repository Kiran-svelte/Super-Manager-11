import React, { useState, useEffect } from 'react'
import { 
  X, 
  Mail, 
  Key, 
  Save, 
  Loader, 
  CheckCircle, 
  AlertCircle,
  Bot,
  Shield,
  Server,
  Zap
} from 'lucide-react'
import './AISettings.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-11-production.up.railway.app'

/**
 * AI Settings Panel
 * 
 * Allows users to configure:
 * - AI's dedicated email account
 * - OAuth credentials
 * - Service signups
 */
export default function AISettings({ userId, onClose, onSave }) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [activeTab, setActiveTab] = useState('email')
  
  // Email configuration
  const [email, setEmail] = useState('')
  const [appPassword, setAppPassword] = useState('')
  const [displayName, setDisplayName] = useState('AI Assistant')
  
  // Current status
  const [currentIdentity, setCurrentIdentity] = useState(null)
  const [capabilities, setCapabilities] = useState([])
  const [serviceAccounts, setServiceAccounts] = useState([])

  // Load current settings
  useEffect(() => {
    loadSettings()
  }, [userId])

  const loadSettings = async () => {
    setLoading(true)
    try {
      // Get current identity
      const identityRes = await fetch(`${API}/api/identity/status/${userId}`)
      const identityData = await identityRes.json()
      
      if (identityData.has_identity && identityData.identity) {
        setCurrentIdentity(identityData.identity)
        setEmail(identityData.identity.email || '')
        setDisplayName(identityData.identity.display_name || 'AI Assistant')
      }

      // Get service accounts
      const accountsRes = await fetch(`${API}/api/identity/services/${userId}`)
      if (accountsRes.ok) {
        const accountsData = await accountsRes.json()
        setServiceAccounts(accountsData.services || [])
      }

      // Get available capabilities
      const capsRes = await fetch(`${API}/api/identity/task/capabilities`)
      if (capsRes.ok) {
        const capsData = await capsRes.json()
        setCapabilities(capsData.capabilities || [])
      }
      
    } catch (err) {
      console.error('Failed to load settings:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveEmail = async () => {
    if (!email || !appPassword) {
      setError('Please enter both email and app password')
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(null)

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

      setSuccess('Email configured successfully! Your AI can now sign up for services.')
      setCurrentIdentity(data.identity)
      onSave?.(data)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleTestSignup = async (serviceName) => {
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      // First create a plan
      const planRes = await fetch(`${API}/api/identity/task/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_request: `Sign up for ${serviceName} and get API key`
        })
      })

      const planData = await planRes.json()

      if (!planData.success) {
        throw new Error(planData.detail || 'Failed to create plan')
      }

      setSuccess(`Plan created! Task ID: ${planData.task_id}. Check the status in the activity panel.`)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="ai-settings-overlay">
        <div className="ai-settings-panel">
          <div className="settings-loading">
            <Loader className="spin" size={32} />
            <span>Loading settings...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="ai-settings-overlay">
      <div className="ai-settings-panel">
        {/* Header */}
        <div className="settings-header">
          <div className="header-title">
            <Bot size={24} />
            <h2>AI Configuration</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="settings-tabs">
          <button 
            className={`tab ${activeTab === 'email' ? 'active' : ''}`}
            onClick={() => setActiveTab('email')}
          >
            <Mail size={16} />
            Email Identity
          </button>
          <button 
            className={`tab ${activeTab === 'services' ? 'active' : ''}`}
            onClick={() => setActiveTab('services')}
          >
            <Key size={16} />
            Service Accounts
          </button>
          <button 
            className={`tab ${activeTab === 'capabilities' ? 'active' : ''}`}
            onClick={() => setActiveTab('capabilities')}
          >
            <Zap size={16} />
            Capabilities
          </button>
        </div>

        {/* Content */}
        <div className="settings-content">
          {error && (
            <div className="alert error">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
          
          {success && (
            <div className="alert success">
              <CheckCircle size={16} />
              {success}
            </div>
          )}

          {/* Email Tab */}
          {activeTab === 'email' && (
            <div className="tab-content">
              <div className="section-intro">
                <Shield size={20} />
                <p>Give your AI its own Gmail account for autonomous operations. The AI will use this email to sign up for services, receive verification codes, and get API keys.</p>
              </div>

              {currentIdentity && (
                <div className="current-identity">
                  <CheckCircle size={16} color="var(--success)" />
                  <span>Current: <strong>{currentIdentity.email}</strong></span>
                </div>
              )}

              <div className="form-group">
                <label>Gmail Address</label>
                <div className="input-with-icon">
                  <Mail size={16} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your-ai@gmail.com"
                  />
                </div>
                <small>Create a new Gmail account specifically for your AI</small>
              </div>

              <div className="form-group">
                <label>App Password</label>
                <div className="input-with-icon">
                  <Key size={16} />
                  <input
                    type="password"
                    value={appPassword}
                    onChange={(e) => setAppPassword(e.target.value)}
                    placeholder="xxxx xxxx xxxx xxxx"
                  />
                </div>
                <small>
                  <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer">
                    Generate an App Password
                  </a> (requires 2-Step Verification)
                </small>
              </div>

              <div className="form-group">
                <label>Display Name (optional)</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="AI Assistant"
                />
              </div>

              <button 
                className="save-btn"
                onClick={handleSaveEmail}
                disabled={saving}
              >
                {saving ? (
                  <>
                    <Loader className="spin" size={16} />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    Save Email Configuration
                  </>
                )}
              </button>
            </div>
          )}

          {/* Services Tab */}
          {activeTab === 'services' && (
            <div className="tab-content">
              <div className="section-intro">
                <Server size={20} />
                <p>Your AI can autonomously sign up for these services and manage API keys.</p>
              </div>

              <div className="services-list">
                {serviceAccounts.length > 0 ? (
                  serviceAccounts.map((account, i) => (
                    <div key={i} className="service-item">
                      <div className="service-info">
                        <strong>{account.service_name}</strong>
                        <span className="service-email">{account.email}</span>
                      </div>
                      <div className="service-status">
                        {account.api_key ? (
                          <span className="badge success">
                            <CheckCircle size={12} />
                            API Key Active
                          </span>
                        ) : (
                          <span className="badge pending">Pending</span>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">
                    <p>No service accounts yet. Your AI will create them as needed.</p>
                  </div>
                )}
              </div>

              <div className="quick-signup">
                <h4>Quick Signup</h4>
                <p>Test autonomous signup for a service:</p>
                <div className="signup-buttons">
                  {['groq', 'together', 'huggingface', 'openrouter'].map(service => (
                    <button 
                      key={service}
                      className="signup-btn"
                      onClick={() => handleTestSignup(service)}
                      disabled={saving}
                    >
                      {service}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Capabilities Tab */}
          {activeTab === 'capabilities' && (
            <div className="tab-content">
              <div className="section-intro">
                <Zap size={20} />
                <p>These are the capabilities your AI can provide. It will automatically find and sign up for the right services.</p>
              </div>

              <div className="capabilities-list">
                {capabilities.map((cap, i) => (
                  <div key={i} className="capability-item">
                    <div className="cap-header">
                      <strong>{cap.name.replace(/_/g, ' ')}</strong>
                    </div>
                    <p className="cap-desc">{cap.description}</p>
                    <div className="cap-providers">
                      {cap.providers?.map((p, j) => (
                        <span key={j} className={`provider-badge ${p.free_tier ? 'free' : ''}`}>
                          {p.name}
                          {p.free_tier && ' (free)'}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
