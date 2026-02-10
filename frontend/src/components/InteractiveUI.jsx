/**
 * Interactive UI Components
 * Renders buttons, cards, forms, and other interactive elements
 * returned by the AI backend
 */

import React, { useState, useRef } from 'react'
import { 
  Check, X, ExternalLink, Calendar, Clock, CreditCard, 
  Shield, ChevronRight, Loader, Download, RefreshCw, Edit3
} from 'lucide-react'
import './InteractiveUI.css'

/**
 * Button Component - Renders interactive buttons
 */
export const UIButton = ({ button, onAction, loading }) => {
  const styleClasses = {
    primary: 'ui-btn-primary',
    secondary: 'ui-btn-secondary',
    success: 'ui-btn-success',
    danger: 'ui-btn-danger',
    warning: 'ui-btn-warning',
    outline: 'ui-btn-outline',
    ghost: 'ui-btn-ghost'
  }

  const handleClick = () => {
    if (button.url) {
      window.open(button.url, '_blank')
    } else {
      onAction(button.action, button.id, button.metadata || {})
    }
  }

  return (
    <button
      className={`ui-btn ${styleClasses[button.style] || 'ui-btn-primary'}`}
      onClick={handleClick}
      disabled={loading || button.disabled}
    >
      {button.icon && <span className="btn-icon">{button.icon}</span>}
      {button.label}
      {button.loading && <Loader className="spin" size={14} />}
    </button>
  )
}

/**
 * Button Group - Renders a group of buttons
 */
export const ButtonGroup = ({ component, onAction, loading }) => {
  const layoutClass = component.layout === 'grid' 
    ? `btn-grid cols-${component.columns || 2}` 
    : `btn-${component.layout || 'horizontal'}`

  return (
    <div className={`btn-group ${layoutClass}`}>
      {component.buttons?.map((btn, idx) => (
        <UIButton 
          key={btn.id || idx} 
          button={btn} 
          onAction={onAction}
          loading={loading}
        />
      ))}
    </div>
  )
}

/**
 * Card Component - Renders offer/option cards
 */
export const UICard = ({ card, onAction, loading }) => {
  const styleClasses = {
    default: 'ui-card-default',
    elevated: 'ui-card-elevated',
    bordered: 'ui-card-bordered',
    featured: 'ui-card-featured',
    compact: 'ui-card-compact'
  }

  return (
    <div className={`ui-card ${styleClasses[card.style] || 'ui-card-default'}`}>
      {card.image && (
        <div className="card-image">
          <img src={card.image} alt={card.title} />
        </div>
      )}
      
      <div className="card-content">
        {card.badges && card.badges.length > 0 && (
          <div className="card-badges">
            {card.badges.map((badge, idx) => (
              <span 
                key={idx} 
                className={`badge badge-${badge.color || 'blue'}`}
              >
                {badge.text}
              </span>
            ))}
          </div>
        )}
        
        <h3 className="card-title">{card.title}</h3>
        
        {card.description && (
          <p className="card-description">{card.description}</p>
        )}
        
        {card.metadata && (
          <div className="card-metadata">
            {card.metadata.price_per_person && (
              <div className="card-price">
                <span className="price-label">Per person:</span>
                <span className="price-value">₹{card.metadata.price_per_person.toLocaleString()}</span>
              </div>
            )}
            {card.metadata.total_price && (
              <div className="card-total">
                <span className="total-label">Total:</span>
                <span className="total-value">₹{card.metadata.total_price.toLocaleString()}</span>
              </div>
            )}
            {card.metadata.savings > 0 && (
              <div className="card-savings">
                🎉 You save ₹{card.metadata.savings.toLocaleString()}
              </div>
            )}
          </div>
        )}
        
        {card.actions && card.actions.length > 0 && (
          <div className="card-actions">
            {card.actions.map((action, idx) => (
              <UIButton 
                key={action.id || idx}
                button={action}
                onAction={onAction}
                loading={loading}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Card Grid - Renders a grid of cards
 */
export const CardGrid = ({ component, onAction, loading }) => {
  return (
    <div className={`card-grid cols-${component.columns || 2}`}>
      {component.cards?.map((card, idx) => (
        <UICard 
          key={card.id || idx}
          card={card}
          onAction={onAction}
          loading={loading}
        />
      ))}
    </div>
  )
}

/**
 * Confirmation Dialog
 */
export const ConfirmationDialog = ({ component, onAction, loading }) => {
  return (
    <div className="confirmation-dialog">
      <div className="confirmation-actions">
        <button
          className="ui-btn-success"
          onClick={() => onAction('confirm_yes', 'confirm_yes', {})}
          disabled={loading}
        >
          <Check size={16} /> {component.confirm_label || 'Yes, proceed'}
        </button>
        <button
          className="ui-btn-secondary"
          onClick={() => onAction('confirm_no', 'confirm_no', {})}
          disabled={loading}
        >
          <X size={16} /> {component.cancel_label || 'Cancel'}
        </button>
      </div>
    </div>
  )
}

/**
 * Payment Component
 */
export const PaymentComponent = ({ component, onAction, loading }) => {
  return (
    <div className="payment-component">
      <div className="payment-header">
        <CreditCard size={24} />
        <span>Secure Payment</span>
        <Shield size={16} className="shield-icon" />
      </div>
      
      <div className="payment-details">
        <div className="payment-amount">
          <span className="amount-label">Amount:</span>
          <span className="amount-value">₹{component.amount?.toLocaleString()}</span>
        </div>
        <div className="payment-provider">
          via {component.provider || 'Razorpay'}
        </div>
      </div>
      
      {component.expires_at && (
        <div className="payment-expiry">
          <Clock size={14} />
          Expires: {new Date(component.expires_at).toLocaleString()}
        </div>
      )}
      
      <div className="payment-actions">
        {component.buttons?.map((btn, idx) => (
          <a
            key={idx}
            href={btn.url || component.payment_link}
            target="_blank"
            rel="noopener noreferrer"
            className="ui-btn-primary payment-btn"
          >
            <CreditCard size={16} />
            {btn.label || `Pay ₹${component.amount?.toLocaleString()}`}
            <ExternalLink size={14} />
          </a>
        )) || (
          <a
            href={component.payment_link}
            target="_blank"
            rel="noopener noreferrer"
            className="ui-btn-primary payment-btn"
          >
            <CreditCard size={16} />
            Pay ₹{component.amount?.toLocaleString()}
            <ExternalLink size={14} />
          </a>
        )}
      </div>
      
      <div className="payment-security">
        <Shield size={12} />
        <span>256-bit encryption • Secure payment gateway</span>
      </div>
    </div>
  )
}

/**
 * OTP Input Component
 */
export const OTPInput = ({ component, onSubmit, loading }) => {
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const inputRefs = useRef([])

  const handleChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return

    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when complete
    const fullOtp = newOtp.join('')
    if (fullOtp.length === 6 && !fullOtp.includes('')) {
      onSubmit(fullOtp)
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pastedData) {
      const newOtp = pastedData.split('').concat(['', '', '', '', '', '']).slice(0, 6)
      setOtp(newOtp)
      if (pastedData.length === 6) {
        onSubmit(pastedData)
      }
    }
  }

  return (
    <div className="otp-component">
      <div className="otp-header">
        <Shield size={20} />
        <span>Enter Verification Code</span>
      </div>
      
      <p className="otp-sent-to">
        Code sent to {component.destination}
      </p>
      
      <div className="otp-inputs">
        {[0, 1, 2, 3, 4, 5].map((idx) => (
          <input
            key={idx}
            ref={(el) => inputRefs.current[idx] = el}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={otp[idx]}
            onChange={(e) => handleChange(idx, e.target.value)}
            onKeyDown={(e) => handleKeyDown(idx, e)}
            onPaste={handlePaste}
            className="otp-digit"
            disabled={loading}
          />
        ))}
      </div>
      
      {component.expires_at && (
        <p className="otp-expiry">
          <Clock size={12} />
          Expires at {new Date(component.expires_at).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}

/**
 * Date Picker Component
 */
export const DatePicker = ({ component, onSelect, loading }) => {
  const [selectedDate, setSelectedDate] = useState('')

  const handleSubmit = () => {
    if (selectedDate) {
      onSelect(`Selected date: ${selectedDate}`)
    }
  }

  return (
    <div className="date-picker-component">
      <label className="date-label">
        <Calendar size={16} />
        {component.label || 'Select Date'}
      </label>
      <div className="date-input-group">
        <input
          type="date"
          min={component.min_date}
          max={component.max_date}
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          disabled={loading}
        />
        <button 
          className="ui-btn-primary"
          onClick={handleSubmit}
          disabled={!selectedDate || loading}
        >
          Select <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

/**
 * Image Card - For displaying generated images
 */
export const ImageCard = ({ image, onAction, loading }) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const handleDownload = () => {
    if (image.url) {
      const link = document.createElement('a')
      link.href = image.url
      link.download = `logo_${image.id || 'image'}.png`
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  return (
    <div className={`image-card ${imageLoaded ? 'loaded' : ''}`}>
      <div className="image-container">
        {!imageLoaded && !imageError && (
          <div className="image-loading">
            <Loader className="spin" size={24} />
            <span>Loading...</span>
          </div>
        )}
        {imageError ? (
          <div className="image-error">
            <X size={24} />
            <span>Failed to load</span>
          </div>
        ) : (
          <img
            src={image.image_url || image.url}
            alt={image.title || `Image ${image.index}`}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            style={{ display: imageLoaded ? 'block' : 'none' }}
          />
        )}
      </div>
      
      <div className="image-info">
        <h4>{image.title || `Concept ${image.index}`}</h4>
        
        <div className="image-actions">
          <button 
            className="ui-btn ui-btn-primary"
            onClick={() => onAction('select_logo', image.id, { image })}
            disabled={loading}
          >
            <Check size={14} /> Select
          </button>
          <button 
            className="ui-btn ui-btn-outline"
            onClick={handleDownload}
            disabled={loading}
          >
            <Download size={14} /> Download
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Image Gallery - For displaying multiple generated images
 */
export const ImageGallery = ({ component, onAction, loading }) => {
  const images = component.images || []
  const actions = component.actions || []

  return (
    <div className="image-gallery">
      <div className="gallery-grid">
        {images.map((img, idx) => (
          <ImageCard
            key={img.id || idx}
            image={img}
            onAction={onAction}
            loading={loading}
          />
        ))}
      </div>
      
      {actions.length > 0 && (
        <div className="gallery-actions">
          {actions.map((action, idx) => (
            <button
              key={action.id || idx}
              className={`ui-btn ${action.action === 'regenerate_logos' ? 'ui-btn-secondary' : 'ui-btn-outline'}`}
              onClick={() => onAction(action.action, action.id, action.metadata || {})}
              disabled={loading}
            >
              {action.action === 'regenerate_logos' && <RefreshCw size={14} />}
              {action.action === 'edit_prompt' && <Edit3 size={14} />}
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Main UI Component Renderer
 */
export const UIComponentRenderer = ({ component, onAction, onMessage, loading }) => {
  if (!component) return null

  switch (component.type) {
    case 'button_group':
      return <ButtonGroup component={component} onAction={onAction} loading={loading} />
    
    case 'card_grid':
      return <CardGrid component={component} onAction={onAction} loading={loading} />
    
    case 'confirmation':
      return <ConfirmationDialog component={component} onAction={onAction} loading={loading} />
    
    case 'payment':
      return <PaymentComponent component={component} onAction={onAction} loading={loading} />
    
    case 'otp_input':
      return <OTPInput component={component} onSubmit={onMessage} loading={loading} />
    
    case 'date_picker':
      return <DatePicker component={component} onSelect={onMessage} loading={loading} />
    
    case 'image_gallery':
      return <ImageGallery component={component} onAction={onAction} loading={loading} />
    
    case 'image_card':
      return <ImageCard image={component} onAction={onAction} loading={loading} />
    
    default:
      // Try to render buttons if present
      if (component.buttons) {
        return <ButtonGroup component={component} onAction={onAction} loading={loading} />
      }
      // Try to render images if present
      if (component.images) {
        return <ImageGallery component={component} onAction={onAction} loading={loading} />
      }
      return null
  }
}

export default UIComponentRenderer
