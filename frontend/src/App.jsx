import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Send, Loader, CheckCircle, XCircle, Clock, Check, X, MapPin, Hotel, Activity, Utensils } from 'lucide-react'
import './App.css'
import './App_ai.css'

const API_BASE = import.meta.env.VITE_API_URL || 'https://super-manager-api.onrender.com/api'

function App() {
  const [message, setMessage] = useState('')
  const [conversation, setConversation] = useState([])
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState([])
  const [plugins, setPlugins] = useState([])
  const [pendingConfirmation, setPendingConfirmation] = useState(null)
  const [pendingSelection, setPendingSelection] = useState(null)
  const [selectedOptions, setSelectedOptions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)

  useEffect(() => {
    loadTasks()
    loadPlugins()
  }, [])

  const loadTasks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/tasks/?user_id=default`)
      setTasks(response.data)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const loadPlugins = async () => {
    try {
      const response = await axios.get(`${API_BASE}/plugins/`)
      setPlugins(response.data.plugins || [])
    } catch (error) {
      console.error('Failed to load plugins:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!message.trim() || loading) return

    const userMessage = message.trim()
    setMessage('')
    setLoading(true)

    // Add user message to conversation
    const newUserMessage = {
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }
    setConversation(prev => [...prev, newUserMessage])

    try {
      const response = await axios.post(`${API_BASE}/agent/process`, {
        message: userMessage,
        user_id: 'default',
        session_id: currentSessionId
      })

      handleAgentResponse(response.data)
      loadTasks()
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || 'Failed to process request',
        timestamp: new Date()
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleAgentResponse = (data) => {
    if (data.session_id) {
      setCurrentSessionId(data.session_id)
    }

    // Check if selection is required
    if (data.requires_selection) {
      const selectionMessage = {
        type: 'selection',
        content: data.response,
        session_id: data.session_id,
        options: data.options || [],
        stage_type: data.stage_type,
        intent: data.intent,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, selectionMessage])
      setPendingSelection(selectionMessage)
      setSelectedOptions([])
    }
    // Check if confirmation is required
    else if (data.requires_confirmation) {
      const confirmationMessage = {
        type: 'confirmation',
        content: data.response,
        session_id: data.session_id,
        pending_actions: data.pending_actions,
        intent: data.intent,
        plan: data.plan,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, confirmationMessage])
      setPendingConfirmation(confirmationMessage)
    }
    // Regular response
    else {
      const agentResponse = {
        type: 'agent',
        content: data.response,
        intent: data.intent,
        plan: data.plan,
        result: data.result,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, agentResponse])
    }
  }

  const handleOptionToggle = (optionId) => {
    if (!pendingSelection) return

    // Check if this is a multiple choice stage
    const isMultipleChoice = pendingSelection.stage_type === 'activities_selection' ||
      pendingSelection.stage_type === 'dining_selection'

    if (isMultipleChoice) {
      // Toggle selection
      setSelectedOptions(prev =>
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      )
    } else {
      // Single selection - submit immediately
      handleOptionSelect(optionId)
    }
  }

  const handleOptionSelect = async (optionId) => {
    if (!pendingSelection) return

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/agent/select`, {
        session_id: pendingSelection.session_id,
        selection: optionId
      })

      // Add user's selection to conversation
      const selectedOption = pendingSelection.options.find(opt => opt.id === optionId)
      const userSelection = {
        type: 'user',
        content: `Selected: ${selectedOption?.name || optionId}`,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, userSelection])

      setPendingSelection(null)
      setSelectedOptions([])

      // Handle the response
      if (response.data.status === 'next_stage') {
        // Show next stage
        const nextStageMessage = {
          type: 'selection',
          content: response.data.response,
          session_id: response.data.session_id,
          options: response.data.options || [],
          stage_type: response.data.stage_type,
          timestamp: new Date()
        }
        setConversation(prev => [...prev, nextStageMessage])
        setPendingSelection(nextStageMessage)
      } else if (response.data.status === 'ready_for_confirmation') {
        // Show final confirmation
        const confirmationMessage = {
          type: 'confirmation',
          content: response.data.response,
          session_id: response.data.session_id,
          pending_actions: response.data.pending_actions,
          timestamp: new Date()
        }
        setConversation(prev => [...prev, confirmationMessage])
        setPendingConfirmation(confirmationMessage)
      }
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || 'Failed to process selection',
        timestamp: new Date()
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleMultipleSelectionSubmit = async () => {
    if (!pendingSelection || selectedOptions.length === 0) return

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/agent/select`, {
        session_id: pendingSelection.session_id,
        selections: selectedOptions
      })

      // Add user's selections to conversation
      const selectedNames = selectedOptions.map(id => {
        const opt = pendingSelection.options.find(o => o.id === id)
        return opt?.name || id
      }).join(', ')

      const userSelection = {
        type: 'user',
        content: `Selected: ${selectedNames}`,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, userSelection])

      setPendingSelection(null)
      setSelectedOptions([])

      // Handle the response
      if (response.data.status === 'next_stage') {
        const nextStageMessage = {
          type: 'selection',
          content: response.data.response,
          session_id: response.data.session_id,
          options: response.data.options || [],
          stage_type: response.data.stage_type,
          timestamp: new Date()
        }
        setConversation(prev => [...prev, nextStageMessage])
        setPendingSelection(nextStageMessage)
      } else if (response.data.status === 'ready_for_confirmation') {
        const confirmationMessage = {
          type: 'confirmation',
          content: response.data.response,
          session_id: response.data.session_id,
          pending_actions: response.data.pending_actions,
          timestamp: new Date()
        }
        setConversation(prev => [...prev, confirmationMessage])
        setPendingConfirmation(confirmationMessage)
      }
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || 'Failed to process selection',
        timestamp: new Date()
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmation = async (approve) => {
    if (!pendingConfirmation) return

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/agent/confirm`, {
        session_id: pendingConfirmation.session_id,
        action: approve ? 'approve_all' : 'reject_all'
      })

      const resultMessage = {
        type: 'agent',
        content: response.data.message,
        results: response.data.results,
        timestamp: new Date()
      }

      setConversation(prev => [...prev, resultMessage])
      setPendingConfirmation(null)
      loadTasks()
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || 'Failed to process confirmation',
        timestamp: new Date()
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="icon completed" />
      case 'failed':
        return <XCircle className="icon failed" />
      case 'in_progress':
        return <Loader className="icon spinning" />
      default:
        return <Clock className="icon pending" />
    }
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Super Manager</h1>
          <p className="subtitle">AI Agent System - Intent to Action</p>
        </header>

        {/* AI Status Bar */}
        {loading && (
          <div className="ai-status-bar">
            <div className="ai-status-content">
              <span className="ai-icon">✨</span>
              <span className="ai-text">Using AI to generate response...</span>
            </div>
          </div>
        )}

        {/* Error Bar (if needed) */}
        {conversation.length > 0 && conversation[conversation.length - 1].type === 'error' && (
          <div className="ai-status-bar error">
            <div className="ai-status-content">
              <span className="ai-icon">⚠️</span>
              <span className="ai-text">AI CALL ERROR</span>
            </div>
          </div>
        )}

        <div className="main-content">
          <div className="chat-section">
            <div className="chat-container">
              {conversation.length === 0 && (
                <div className="welcome-message">
                  <h2>Welcome to Super Manager</h2>
                  <p>I'm your AI agent that can help you with:</p>
                  <ul>
                    <li>🎂 Birthday party planning with destination selection</li>
                    <li>✈️ Travel planning with accommodation & activities</li>
                    <li>📅 Meeting scheduling with Zoom & emails</li>
                    <li>🍽️ Restaurant bookings</li>
                    <li>📞 Phone calls to resorts, bakeries, etc.</li>
                  </ul>
                  <p className="example">Try: "I need to enjoy my birthday this weekend"</p>
                </div>
              )}

              {conversation.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  <div className="message-content">
                    <div className="message-text">{msg.content}</div>

                    {/* Selection Options */}
                    {msg.type === 'selection' && msg.options && msg.options.length > 0 && (
                      <div className="selection-options">
                        <div className="options-grid">
                          {msg.options.map((option) => {
                            const isMultipleChoice = msg.stage_type === 'activities_selection' || msg.stage_type === 'dining_selection'
                            const isSelected = selectedOptions.includes(option.id)

                            return (
                              <button
                                key={option.id}
                                onClick={() => isMultipleChoice ? handleOptionToggle(option.id) : handleOptionSelect(option.id)}
                                className={`option-card ${isSelected ? 'selected' : ''}`}
                                disabled={loading || pendingSelection?.session_id !== msg.session_id}
                              >
                                <div className="option-icon">
                                  {msg.stage_type === 'clarification' || msg.stage_type === 'destination_selection' ? <MapPin size={24} /> :
                                    msg.stage_type === 'accommodation_selection' ? <Hotel size={24} /> :
                                      msg.stage_type === 'activities_selection' ? <Activity size={24} /> :
                                        <Utensils size={24} />}
                                </div>
                                <div className="option-name">{option.name}</div>
                                {option.description && (
                                  <div className="option-description">{option.description}</div>
                                )}
                                {option.price && (
                                  <div className="option-price">{option.price}</div>
                                )}
                                {option.rating && (
                                  <div className="option-rating">{option.rating}</div>
                                )}
                                {option.duration && (
                                  <div className="option-duration">{option.duration}</div>
                                )}
                                {isMultipleChoice && isSelected && (
                                  <div className="option-check">✓</div>
                                )}
                              </button>
                            )
                          })}
                        </div>
                        {(msg.stage_type === 'activities_selection' || msg.stage_type === 'dining_selection') &&
                          pendingSelection?.session_id === msg.session_id && (
                            <div className="multiple-choice-actions">
                              <button
                                onClick={handleMultipleSelectionSubmit}
                                className="continue-button"
                                disabled={loading || selectedOptions.length === 0}
                              >
                                Continue ({selectedOptions.length} selected)
                              </button>
                            </div>
                          )}
                      </div>
                    )}

                    {/* Confirmation Actions */}
                    {msg.type === 'confirmation' && msg.pending_actions && (
                      <div className="confirmation-actions">
                        <h4>Actions to be performed:</h4>
                        <ul className="action-list">
                          {msg.pending_actions.map((action, i) => (
                            <li key={action.id} className="action-item">
                              <span className="action-number">{i + 1}.</span>
                              <span className="action-description">{action.description}</span>
                            </li>
                          ))}
                        </ul>

                        {pendingConfirmation && pendingConfirmation.session_id === msg.session_id && (
                          <div className="confirmation-buttons">
                            <button
                              onClick={() => handleConfirmation(true)}
                              className="confirm-button approve"
                              disabled={loading}
                            >
                              <Check size={18} />
                              Yes, proceed
                            </button>
                            <button
                              onClick={() => handleConfirmation(false)}
                              className="confirm-button reject"
                              disabled={loading}
                            >
                              <X size={18} />
                              No, cancel
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Execution Results */}
                    {msg.results && (
                      <div className="execution-results">
                        <h4>Execution Results:</h4>
                        {msg.results.map((result, i) => (
                          <div key={i} className="result-item">
                            {getStatusIcon(result.status)}
                            <div className="result-details">
                              <div className="result-action">{result.action}</div>
                              <div className="result-message">{result.result}</div>
                              {result.details && (
                                <div className="result-extra">
                                  {result.details.join_url && (
                                    <a href={result.details.join_url} target="_blank" rel="noopener noreferrer">
                                      Join Meeting
                                    </a>
                                  )}
                                  {result.details.booking_reference && (
                                    <div>Booking: {result.details.booking_reference}</div>
                                  )}
                                  {result.details.order_number && (
                                    <div>Order: {result.details.order_number}</div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message agent">
                  <div className="message-content">
                    <Loader className="icon spinning" />
                    <span>Processing...</span>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="input-form">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Tell me what you need..."
                className="message-input"
                disabled={loading}
              />
              <button
                type="submit"
                className="send-button"
                disabled={loading || !message.trim()}
              >
                <Send size={20} />
              </button>
            </form>
          </div>

          <div className="sidebar">
            <div className="sidebar-section">
              <h3>Recent Tasks</h3>
              <div className="tasks-list">
                {tasks.slice(0, 5).map((task) => (
                  <div key={task.id} className="task-item">
                    <div className="task-header">
                      {getStatusIcon(task.status)}
                      <span className="task-intent">{task.intent}</span>
                    </div>
                    <div className="task-status">{task.status}</div>
                  </div>
                ))}
                {tasks.length === 0 && (
                  <p className="empty-state">No tasks yet</p>
                )}
              </div>
            </div>

            <div className="sidebar-section">
              <h3>Available Plugins</h3>
              <div className="plugins-list">
                {plugins.map((plugin) => (
                  <div key={plugin.name} className="plugin-item">
                    <div className="plugin-name">{plugin.name}</div>
                    <div className="plugin-capabilities">
                      {plugin.capabilities.slice(0, 3).join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
