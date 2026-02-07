/**
 * Animated Background Component
 * Floating particles, gradient orbs, and parallax effects
 */
import React, { useEffect, useRef, useMemo } from 'react'

// =============================================================================
// Floating Particles Background
// =============================================================================

export function ParticlesBackground({ count = 50 }) {
  const particles = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      size: Math.random() * 4 + 1,
      x: Math.random() * 100,
      y: Math.random() * 100,
      duration: Math.random() * 20 + 10,
      delay: Math.random() * 10,
      opacity: Math.random() * 0.5 + 0.1
    }))
  }, [count])

  return (
    <div className="particles-container">
      {particles.map(p => (
        <div
          key={p.id}
          className="particle"
          style={{
            '--size': `${p.size}px`,
            '--x': `${p.x}%`,
            '--y': `${p.y}%`,
            '--duration': `${p.duration}s`,
            '--delay': `${p.delay}s`,
            '--opacity': p.opacity
          }}
        />
      ))}
      <style>{`
        .particles-container {
          position: fixed;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
          z-index: -1;
        }
        
        .particle {
          position: absolute;
          width: var(--size);
          height: var(--size);
          left: var(--x);
          top: var(--y);
          background: radial-gradient(circle, rgba(56, 189, 248, var(--opacity)), transparent);
          border-radius: 50%;
          animation: float-particle var(--duration) ease-in-out infinite;
          animation-delay: var(--delay);
        }
        
        @keyframes float-particle {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: var(--opacity);
          }
          50% {
            transform: translate(calc(var(--size) * 10), calc(var(--size) * -15)) scale(1.5);
            opacity: calc(var(--opacity) * 0.5);
          }
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Gradient Orbs Background
// =============================================================================

export function GradientOrbs() {
  return (
    <div className="gradient-orbs">
      <div className="orb orb-1"></div>
      <div className="orb orb-2"></div>
      <div className="orb orb-3"></div>
      <style>{`
        .gradient-orbs {
          position: fixed;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
          z-index: -1;
        }
        
        .orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.4;
          animation: orb-float 20s ease-in-out infinite;
        }
        
        .orb-1 {
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, rgba(14, 165, 233, 0.6), transparent 70%);
          top: -200px;
          right: -200px;
          animation-delay: 0s;
        }
        
        .orb-2 {
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(217, 70, 239, 0.5), transparent 70%);
          bottom: -150px;
          left: -150px;
          animation-delay: -5s;
        }
        
        .orb-3 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(16, 185, 129, 0.4), transparent 70%);
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          animation-delay: -10s;
        }
        
        @keyframes orb-float {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          25% {
            transform: translate(30px, -30px) scale(1.1);
          }
          50% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          75% {
            transform: translate(-30px, -20px) scale(1.05);
          }
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Mouse Follower / Spotlight Effect
// =============================================================================

export function MouseSpotlight() {
  const spotlightRef = useRef(null)
  
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (spotlightRef.current) {
        spotlightRef.current.style.setProperty('--mouse-x', `${e.clientX}px`)
        spotlightRef.current.style.setProperty('--mouse-y', `${e.clientY}px`)
      }
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])
  
  return (
    <div ref={spotlightRef} className="mouse-spotlight">
      <style>{`
        .mouse-spotlight {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 0;
          background: radial-gradient(
            600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
            rgba(14, 165, 233, 0.06),
            transparent 40%
          );
          transition: background 0.3s ease;
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Grid Pattern Background
// =============================================================================

export function GridPattern() {
  return (
    <div className="grid-pattern">
      <style>{`
        .grid-pattern {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: -2;
          background-image: 
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
          background-size: 50px 50px;
          mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
          -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Animated Border Component
// =============================================================================

export function AnimatedBorder({ children, className = '' }) {
  return (
    <div className={`animated-border-wrapper ${className}`}>
      <div className="animated-border-content">
        {children}
      </div>
      <style>{`
        .animated-border-wrapper {
          position: relative;
          padding: 2px;
          border-radius: 16px;
          background: linear-gradient(
            90deg,
            #0ea5e9,
            #d946ef,
            #10b981,
            #0ea5e9
          );
          background-size: 300% 100%;
          animation: border-gradient 4s linear infinite;
        }
        
        .animated-border-content {
          background: rgba(15, 23, 42, 0.95);
          border-radius: 14px;
          height: 100%;
        }
        
        @keyframes border-gradient {
          0% { background-position: 0% 50%; }
          100% { background-position: 300% 50%; }
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Glow Card Component
// =============================================================================

export function GlowCard({ children, className = '', glowColor = 'primary' }) {
  const colors = {
    primary: 'rgba(14, 165, 233, 0.3)',
    accent: 'rgba(217, 70, 239, 0.3)',
    success: 'rgba(16, 185, 129, 0.3)'
  }
  
  return (
    <div 
      className={`glow-card ${className}`}
      style={{ '--glow-color': colors[glowColor] || colors.primary }}
    >
      {children}
      <style>{`
        .glow-card {
          position: relative;
          background: rgba(15, 23, 42, 0.8);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 16px;
          overflow: hidden;
          transition: all 0.3s ease;
        }
        
        .glow-card::before {
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
        
        .glow-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 40px var(--glow-color);
          border-color: rgba(148, 163, 184, 0.4);
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Ripple Button Component
// =============================================================================

export function RippleButton({ children, onClick, className = '', ...props }) {
  const buttonRef = useRef(null)
  
  const handleClick = (e) => {
    const button = buttonRef.current
    if (!button) return
    
    const rect = button.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    const ripple = document.createElement('span')
    ripple.className = 'ripple'
    ripple.style.left = `${x}px`
    ripple.style.top = `${y}px`
    
    button.appendChild(ripple)
    
    setTimeout(() => ripple.remove(), 600)
    
    onClick?.(e)
  }
  
  return (
    <button 
      ref={buttonRef}
      className={`ripple-button ${className}`}
      onClick={handleClick}
      {...props}
    >
      {children}
      <style>{`
        .ripple-button {
          position: relative;
          overflow: hidden;
        }
        
        .ripple-button .ripple {
          position: absolute;
          width: 10px;
          height: 10px;
          background: rgba(255, 255, 255, 0.4);
          border-radius: 50%;
          transform: translate(-50%, -50%) scale(0);
          animation: ripple-effect 0.6s ease-out;
          pointer-events: none;
        }
        
        @keyframes ripple-effect {
          to {
            transform: translate(-50%, -50%) scale(20);
            opacity: 0;
          }
        }
      `}</style>
    </button>
  )
}

// =============================================================================
// Skeleton Loader Component
// =============================================================================

export function Skeleton({ width = '100%', height = '20px', borderRadius = '8px' }) {
  return (
    <div 
      className="skeleton"
      style={{ width, height, borderRadius }}
    >
      <style>{`
        .skeleton {
          background: linear-gradient(
            90deg,
            rgba(30, 41, 59, 0.6) 25%,
            rgba(51, 65, 85, 0.4) 50%,
            rgba(30, 41, 59, 0.6) 75%
          );
          background-size: 200% 100%;
          animation: skeleton-shimmer 1.5s infinite;
        }
        
        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  )
}

// =============================================================================
// Pulse Indicator Component
// =============================================================================

export function PulseIndicator({ color = 'success', size = 8 }) {
  const colors = {
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6'
  }
  
  return (
    <span 
      className="pulse-indicator"
      style={{ 
        '--color': colors[color] || colors.success,
        '--size': `${size}px`
      }}
    >
      <style>{`
        .pulse-indicator {
          display: inline-block;
          width: var(--size);
          height: var(--size);
          background: var(--color);
          border-radius: 50%;
          position: relative;
        }
        
        .pulse-indicator::after {
          content: '';
          position: absolute;
          inset: 0;
          background: var(--color);
          border-radius: 50%;
          animation: pulse-ring 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        
        @keyframes pulse-ring {
          75%, 100% {
            transform: scale(2.5);
            opacity: 0;
          }
        }
      `}</style>
    </span>
  )
}

// =============================================================================
// Animated Counter Component
// =============================================================================

export function AnimatedCounter({ value, duration = 1000 }) {
  const [displayValue, setDisplayValue] = React.useState(0)
  
  useEffect(() => {
    let startTime = null
    const startValue = displayValue
    const endValue = value
    
    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(startValue + (endValue - startValue) * eased)
      
      setDisplayValue(current)
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    
    requestAnimationFrame(animate)
  }, [value, duration])
  
  return <span className="animated-counter">{displayValue.toLocaleString()}</span>
}

export default { 
  ParticlesBackground, 
  GradientOrbs, 
  MouseSpotlight, 
  GridPattern,
  AnimatedBorder,
  GlowCard,
  RippleButton,
  Skeleton,
  PulseIndicator,
  AnimatedCounter
}
