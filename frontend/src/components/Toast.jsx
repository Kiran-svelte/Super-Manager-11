/**
 * Toast Notification Component
 * Beautiful slide-in notifications with auto-dismiss
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'

// Toast Context
const ToastContext = createContext(null)

// Toast Types with Icons and Colors
const toastConfig = {
  success: {
    icon: CheckCircle,
    color: '#10b981',
    bgColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: 'rgba(16, 185, 129, 0.3)'
  },
  error: {
    icon: XCircle,
    color: '#ef4444',
    bgColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: 'rgba(239, 68, 68, 0.3)'
  },
  warning: {
    icon: AlertCircle,
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: 'rgba(245, 158, 11, 0.3)'
  },
  info: {
    icon: Info,
    color: '#3b82f6',
    bgColor: 'rgba(59, 130, 246, 0.15)',
    borderColor: 'rgba(59, 130, 246, 0.3)'
  }
}

// Single Toast Component
function Toast({ id, type, message, onDismiss }) {
  const config = toastConfig[type] || toastConfig.info
  const Icon = config.icon
  
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), 5000)
    return () => clearTimeout(timer)
  }, [id, onDismiss])
  
  return (
    <div 
      className="toast"
      style={{
        '--toast-color': config.color,
        '--toast-bg': config.bgColor,
        '--toast-border': config.borderColor
      }}
    >
      <div className="toast-icon">
        <Icon />
      </div>
      <span className="toast-message">{message}</span>
      <button className="toast-close" onClick={() => onDismiss(id)}>
        <X />
      </button>
    </div>
  )
}

// Toast Container
function ToastContainer({ toasts, dismiss }) {
  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <Toast 
          key={toast.id} 
          {...toast} 
          onDismiss={dismiss}
        />
      ))}
      <style>{`
        .toast-container {
          position: fixed;
          top: 20px;
          right: 20px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          z-index: 9999;
          pointer-events: none;
        }
        
        .toast {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: var(--toast-bg);
          backdrop-filter: blur(20px);
          border: 1px solid var(--toast-border);
          border-radius: 12px;
          color: var(--toast-color);
          pointer-events: auto;
          animation: toast-slide-in 0.3s ease-out;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
          max-width: 400px;
        }
        
        .toast-icon {
          flex-shrink: 0;
        }
        
        .toast-icon svg {
          width: 20px;
          height: 20px;
        }
        
        .toast-message {
          flex: 1;
          font-size: 14px;
          color: #f1f5f9;
          line-height: 1.4;
        }
        
        .toast-close {
          flex-shrink: 0;
          background: none;
          border: none;
          padding: 4px;
          cursor: pointer;
          color: #94a3b8;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 6px;
          transition: all 0.2s;
        }
        
        .toast-close:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #f1f5f9;
        }
        
        .toast-close svg {
          width: 16px;
          height: 16px;
        }
        
        @keyframes toast-slide-in {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @media (max-width: 480px) {
          .toast-container {
            left: 20px;
            right: 20px;
          }
          
          .toast {
            max-width: none;
          }
        }
      `}</style>
    </div>
  )
}

// Toast Provider
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  
  const addToast = useCallback((type, message) => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, type, message }])
    return id
  }, [])
  
  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])
  
  const toast = {
    success: (message) => addToast('success', message),
    error: (message) => addToast('error', message),
    warning: (message) => addToast('warning', message),
    info: (message) => addToast('info', message),
    dismiss
  }
  
  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  )
}

// Hook to use toast
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export default { ToastProvider, useToast }
