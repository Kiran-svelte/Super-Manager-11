import React, { useState, useEffect, useCallback } from 'react'
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader, 
  ChevronRight,
  Bell,
  X,
  RefreshCw
} from 'lucide-react'
import './TaskPanel.css'

const API = import.meta.env.VITE_API_URL || 'https://super-manager-11-production.up.railway.app'

/**
 * TaskPanel - Shows real-time task progress
 * 
 * Features:
 * - List of active tasks with progress bars
 * - Substep breakdown for each task
 * - Real-time updates via polling (WebSocket can be added)
 * - Notifications
 */
export default function TaskPanel({ userEmail = 'default@user.com', refreshTrigger = 0 }) {
  const [tasks, setTasks] = useState([])
  const [notifications, setNotifications] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  // Fetch tasks
  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v2/tasks?user_email=${userEmail}`)
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
        setLastUpdate(new Date())
      }
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    }
  }, [userEmail])

  // Refresh when refreshTrigger changes (task confirmed)
  useEffect(() => {
    if (refreshTrigger > 0) {
      fetchTasks()
      fetchNotifications()
    }
  }, [refreshTrigger])

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v2/tasks/notifications?user_email=${userEmail}&unread_only=true`)
      if (res.ok) {
        const data = await res.json()
        setNotifications(data)
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    }
  }, [userEmail])

  // Initial load and polling
  useEffect(() => {
    fetchTasks()
    fetchNotifications()

    // Poll every 10 seconds
    const interval = setInterval(() => {
      fetchTasks()
      fetchNotifications()
    }, 10000)

    return () => clearInterval(interval)
  }, [fetchTasks, fetchNotifications])

  // Mark notification as read
  const dismissNotification = async (notificationId) => {
    try {
      await fetch(`${API}/api/v2/tasks/notifications/${notificationId}/read`, {
        method: 'PUT'
      })
      setNotifications(prev => prev.filter(n => n.id !== notificationId))
    } catch (err) {
      console.error('Failed to dismiss notification:', err)
    }
  }

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="icon-completed" />
      case 'in_progress':
        return <Loader className="icon-progress spinning" />
      case 'waiting_input':
        return <AlertCircle className="icon-waiting" />
      case 'failed':
        return <X className="icon-failed" />
      default:
        return <Clock className="icon-pending" />
    }
  }

  // Get progress bar color
  const getProgressColor = (percent) => {
    if (percent === 100) return '#10b981' // green
    if (percent >= 50) return '#3b82f6'   // blue
    if (percent >= 25) return '#f59e0b'   // amber
    return '#6b7280'                       // gray
  }

  // Format time
  const formatTime = (isoString) => {
    if (!isoString) return ''
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="task-panel">
      {/* Header */}
      <div className="task-panel-header">
        <h2>Tasks</h2>
        <div className="header-actions">
          <button 
            className="refresh-btn" 
            onClick={() => { fetchTasks(); fetchNotifications(); }}
            title="Refresh"
          >
            <RefreshCw size={16} />
          </button>
          <div className="notification-badge">
            <Bell size={16} />
            {notifications.length > 0 && (
              <span className="badge">{notifications.length}</span>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="notifications">
          {notifications.slice(0, 3).map(notif => (
            <div key={notif.id} className="notification-item">
              <div className="notif-content">
                <strong>{notif.title}</strong>
                <p>{notif.body}</p>
              </div>
              <button 
                className="notif-dismiss"
                onClick={() => dismissNotification(notif.id)}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Task List */}
      <div className="task-list">
        {tasks.length === 0 ? (
          <div className="no-tasks">
            <Clock size={32} className="no-tasks-icon" />
            <p>No active tasks</p>
            <span>Tasks will appear here when you ask me to do something</span>
          </div>
        ) : (
          tasks.map(task => (
            <div 
              key={task.id} 
              className={`task-card ${selectedTask?.id === task.id ? 'selected' : ''}`}
              onClick={() => setSelectedTask(selectedTask?.id === task.id ? null : task)}
            >
              {/* Task Header */}
              <div className="task-header">
                {getStatusIcon(task.status)}
                <div className="task-info">
                  <h3>{task.title}</h3>
                  <span className="task-type">{task.task_type}</span>
                </div>
                <ChevronRight 
                  className={`expand-icon ${selectedTask?.id === task.id ? 'expanded' : ''}`} 
                />
              </div>

              {/* Progress Bar */}
              <div className="progress-container">
                <div 
                  className="progress-bar"
                  style={{ 
                    width: `${task.progress_percent}%`,
                    backgroundColor: getProgressColor(task.progress_percent)
                  }}
                />
                <span className="progress-text">{task.progress_percent}%</span>
              </div>

              {/* ETA */}
              {task.estimated_completion && (
                <div className="task-eta">
                  <Clock size={12} />
                  <span>ETA: {formatTime(task.estimated_completion)}</span>
                </div>
              )}

              {/* Expanded Substeps */}
              {selectedTask?.id === task.id && (
                <div className="substeps">
                  {(task.substeps || []).map((step, idx) => (
                    <div key={step.id || idx} className={`substep ${step.status}`}>
                      <div className="substep-indicator">
                        {step.status === 'completed' ? (
                          <CheckCircle size={14} className="step-completed" />
                        ) : step.status === 'in_progress' ? (
                          <Loader size={14} className="step-progress spinning" />
                        ) : step.status === 'waiting' ? (
                          <Clock size={14} className="step-waiting" />
                        ) : (
                          <div className="step-dot" />
                        )}
                      </div>
                      <div className="substep-info">
                        <span className="substep-title">{step.title}</span>
                        {step.scheduled_at && step.status === 'pending' && (
                          <span className="substep-time">
                            <Clock size={10} />
                            {formatTime(step.scheduled_at)}
                          </span>
                        )}
                        {step.error_message && (
                          <span className="substep-error">{step.error_message}</span>
                        )}
                      </div>
                      <span className="substep-weight">{step.progress_weight}%</span>
                    </div>
                  ))}
                </div>
              )}

              {/* User Input Required */}
              {task.needs_user_input && (
                <div className="user-input-required">
                  <AlertCircle size={14} />
                  <span>{task.input_prompt || 'Your input is needed'}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <div className="last-update">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
