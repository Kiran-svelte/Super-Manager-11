/**
 * Modal Component
 * Beautiful glassmorphism modal with animations
 */
import React, { useEffect, useRef, useCallback } from 'react'
import { X } from 'lucide-react'

export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  const modalRef = useRef(null)
  const previousActive = useRef(null)
  
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])
  
  // Focus trap and body scroll lock
  useEffect(() => {
    if (isOpen) {
      previousActive.current = document.activeElement
      document.body.style.overflow = 'hidden'
      modalRef.current?.focus()
    } else {
      document.body.style.overflow = ''
      previousActive.current?.focus()
    }
    
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])
  
  // Handle backdrop click
  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }, [onClose])
  
  if (!isOpen) return null
  
  const sizeClasses = {
    sm: '400px',
    md: '500px',
    lg: '700px',
    xl: '900px',
    full: '95vw'
  }
  
  return (
    <div 
      className="modal-backdrop"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div 
        ref={modalRef}
        className="modal-container"
        style={{ '--modal-width': sizeClasses[size] || sizeClasses.md }}
        tabIndex={-1}
      >
        <div className="modal-header">
          {title && <h2 id="modal-title" className="modal-title">{title}</h2>}
          <button 
            className="modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X />
          </button>
        </div>
        <div className="modal-content">
          {children}
        </div>
      </div>
      
      <style>{`
        .modal-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          z-index: 1000;
          animation: backdrop-fade-in 0.2s ease-out;
        }
        
        @keyframes backdrop-fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        .modal-container {
          width: 100%;
          max-width: var(--modal-width);
          max-height: 90vh;
          background: rgba(15, 23, 42, 0.95);
          backdrop-filter: blur(40px);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 20px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          animation: modal-slide-up 0.3s ease-out;
          box-shadow: 
            0 25px 50px rgba(0, 0, 0, 0.5),
            0 0 0 1px rgba(255, 255, 255, 0.05) inset;
          position: relative;
        }
        
        /* Glass reflection at top */
        .modal-container::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
          );
        }
        
        @keyframes modal-slide-up {
          from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .modal-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #f1f5f9;
          margin: 0;
        }
        
        .modal-close {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(148, 163, 184, 0.2);
          width: 36px;
          height: 36px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #94a3b8;
          transition: all 0.2s;
        }
        
        .modal-close:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #f1f5f9;
          border-color: rgba(148, 163, 184, 0.4);
        }
        
        .modal-close svg {
          width: 18px;
          height: 18px;
        }
        
        .modal-content {
          padding: 24px;
          overflow-y: auto;
          color: #e2e8f0;
        }
        
        /* Custom scrollbar for modal */
        .modal-content::-webkit-scrollbar {
          width: 6px;
        }
        
        .modal-content::-webkit-scrollbar-track {
          background: transparent;
        }
        
        .modal-content::-webkit-scrollbar-thumb {
          background: rgba(148, 163, 184, 0.3);
          border-radius: 3px;
        }
        
        @media (max-width: 640px) {
          .modal-backdrop {
            padding: 0;
            align-items: flex-end;
          }
          
          .modal-container {
            max-width: 100%;
            max-height: 80vh;
            border-radius: 20px 20px 0 0;
            animation: modal-slide-up-mobile 0.3s ease-out;
          }
          
          @keyframes modal-slide-up-mobile {
            from {
              transform: translateY(100%);
            }
            to {
              transform: translateY(0);
            }
          }
        }
      `}</style>
    </div>
  )
}

// Confirm Dialog
export function ConfirmDialog({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = 'Confirm', 
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'primary' // primary, danger
}) {
  const variantStyles = {
    primary: {
      bg: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
      shadow: 'rgba(14, 165, 233, 0.3)'
    },
    danger: {
      bg: 'linear-gradient(135deg, #ef4444, #dc2626)',
      shadow: 'rgba(239, 68, 68, 0.3)'
    }
  }
  
  const style = variantStyles[variant] || variantStyles.primary
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <p style={{ marginBottom: 24, lineHeight: 1.6, color: '#94a3b8' }}>
        {message}
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
        <button 
          onClick={onClose}
          style={{
            padding: '10px 20px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(148, 163, 184, 0.2)',
            borderRadius: 10,
            color: '#94a3b8',
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {cancelText}
        </button>
        <button 
          onClick={() => {
            onConfirm()
            onClose()
          }}
          style={{
            padding: '10px 20px',
            background: style.bg,
            border: 'none',
            borderRadius: 10,
            color: 'white',
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            boxShadow: `0 4px 15px ${style.shadow}`,
            transition: 'all 0.2s'
          }}
        >
          {confirmText}
        </button>
      </div>
    </Modal>
  )
}

export default { Modal, ConfirmDialog }
