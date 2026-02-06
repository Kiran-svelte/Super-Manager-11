import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader, Zap, Brain, Send, Calendar, Bell, CreditCard, Search } from 'lucide-react';
import './Loading3D.css';

/**
 * 3D Loading Animation Component
 * Shows different loading states based on what the AI is doing
 */

// Main 3D Cube Animation
export const Cube3D = () => (
  <div className="cube-3d">
    <div className="face front"></div>
    <div className="face back"></div>
    <div className="face right"></div>
    <div className="face left"></div>
    <div className="face top"></div>
    <div className="face bottom"></div>
  </div>
);

// Orbiting Particles
export const OrbitAnimation = () => (
  <div className="orbit-container">
    <div className="orbit">
      <div className="orbit-particle p1"></div>
      <div className="orbit-particle p2"></div>
    </div>
    <div className="orbit">
      <div className="orbit-particle p3"></div>
    </div>
  </div>
);

// Neural Network Animation
export const NeuralAnimation = () => (
  <div className="neural-container">
    <svg className="neural-lines" viewBox="0 0 120 80">
      {/* Layer 1 to Layer 2 */}
      <line x1="6" y1="16" x2="42" y2="8" />
      <line x1="6" y1="16" x2="42" y2="32" />
      <line x1="6" y1="16" x2="42" y2="56" />
      <line x1="6" y1="48" x2="42" y2="8" />
      <line x1="6" y1="48" x2="42" y2="32" />
      <line x1="6" y1="48" x2="42" y2="56" />
      {/* Layer 2 to Layer 3 */}
      <line x1="42" y1="8" x2="84" y2="20" />
      <line x1="42" y1="8" x2="84" y2="44" />
      <line x1="42" y1="32" x2="84" y2="20" />
      <line x1="42" y1="32" x2="84" y2="44" />
      <line x1="42" y1="56" x2="84" y2="20" />
      <line x1="42" y1="56" x2="84" y2="44" />
      {/* Layer 3 to Output */}
      <line x1="84" y1="20" x2="114" y2="32" />
      <line x1="84" y1="44" x2="114" y2="32" />
    </svg>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
    <div className="neuron"></div>
  </div>
);

// AI Thinking Indicator
export const AIThinking = ({ message }) => (
  <div className="ai-thinking">
    <div className="ai-avatar">
      <Brain size={18} />
    </div>
    <div className="ai-thinking-content">
      <span className="ai-name">AI Processing</span>
      <div className="thinking-animation">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
);

// Loading dots
export const LoadingDots = () => (
  <div className="loading-dots">
    <div className="dot"></div>
    <div className="dot"></div>
    <div className="dot"></div>
    <div className="dot"></div>
  </div>
);

// Task type icon
const getTaskIcon = (taskType) => {
  switch (taskType) {
    case 'email':
    case 'communication':
      return <Send size={14} />;
    case 'meeting':
    case 'scheduling':
      return <Calendar size={14} />;
    case 'reminder':
      return <Bell size={14} />;
    case 'payment':
      return <CreditCard size={14} />;
    case 'search':
      return <Search size={14} />;
    default:
      return <Zap size={14} />;
  }
};

// Execution Steps Display
export const ExecutionSteps = ({ steps, currentStep }) => (
  <div className="execution-steps">
    {steps.map((step, index) => (
      <div key={index} className="step">
        <div className={`step-icon ${
          index < currentStep ? 'done' : 
          index === currentStep ? 'active' : 'pending'
        }`}>
          {index < currentStep ? (
            <CheckCircle size={16} />
          ) : index === currentStep ? (
            <Loader size={16} className="animate-spin" />
          ) : (
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#4b5563' }} />
          )}
        </div>
        <span className={`step-text ${index === currentStep ? 'active' : ''}`}>
          {step}
        </span>
      </div>
    ))}
  </div>
);

// Success Animation
export const SuccessAnimation = () => (
  <div className="success-animation">
    <CheckCircle size={30} />
  </div>
);

// Error Animation
export const ErrorAnimation = () => (
  <div className="error-animation">
    <XCircle size={30} />
  </div>
);

// Main Loading Component - shows different animations based on state
export const Loading3D = ({ 
  state = 'thinking', // thinking, executing, success, error
  taskType = null,
  message = null,
  steps = [],
  currentStep = 0
}) => {
  const [loadingText, setLoadingText] = useState('');
  
  // Cycle through loading messages
  const thinkingMessages = [
    'Understanding your request...',
    'Planning the best approach...',
    'Analyzing requirements...',
    'Processing with AI...'
  ];
  
  const executingMessages = {
    communication: [
      'Composing message...',
      'Connecting to service...',
      'Sending your message...'
    ],
    scheduling: [
      'Creating meeting...',
      'Generating meeting link...',
      'Sending invitations...'
    ],
    reminder: [
      'Setting up reminder...',
      'Scheduling notification...',
      'Configuring delivery method...'
    ],
    payment: [
      'Generating payment details...',
      'Creating UPI request...',
      'Preparing transaction...'
    ],
    search: [
      'Searching the web...',
      'Gathering information...',
      'Analyzing results...'
    ],
    default: [
      'Executing task...',
      'Processing request...',
      'Almost there...'
    ]
  };

  useEffect(() => {
    if (state === 'thinking') {
      let idx = 0;
      const interval = setInterval(() => {
        setLoadingText(thinkingMessages[idx % thinkingMessages.length]);
        idx++;
      }, 2000);
      setLoadingText(thinkingMessages[0]);
      return () => clearInterval(interval);
    } else if (state === 'executing') {
      const messages = executingMessages[taskType] || executingMessages.default;
      let idx = 0;
      const interval = setInterval(() => {
        setLoadingText(messages[idx % messages.length]);
        idx++;
      }, 1500);
      setLoadingText(messages[0]);
      return () => clearInterval(interval);
    }
  }, [state, taskType]);

  return (
    <div className="loading-3d-container">
      {/* Success State */}
      {state === 'success' && (
        <>
          <SuccessAnimation />
          <div className="loading-text" style={{ color: '#10b981' }}>
            <span>{message || 'Task completed successfully!'}</span>
          </div>
        </>
      )}

      {/* Error State */}
      {state === 'error' && (
        <>
          <ErrorAnimation />
          <div className="loading-text" style={{ color: '#ef4444' }}>
            <span>{message || 'Something went wrong'}</span>
          </div>
        </>
      )}

      {/* Thinking State - Neural Network */}
      {state === 'thinking' && (
        <>
          <NeuralAnimation />
          <div className="loading-text">
            <span>{loadingText}</span>
          </div>
          <LoadingDots />
        </>
      )}

      {/* Executing State - 3D Cube */}
      {state === 'executing' && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Cube3D />
            {taskType && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                color: '#a78bfa',
                fontSize: '0.9rem'
              }}>
                {getTaskIcon(taskType)}
                <span style={{ textTransform: 'capitalize' }}>{taskType}</span>
              </div>
            )}
          </div>
          <div className="loading-text">
            <span>{message || loadingText}</span>
          </div>
          {steps.length > 0 && (
            <ExecutionSteps steps={steps} currentStep={currentStep} />
          )}
        </>
      )}
    </div>
  );
};

export default Loading3D;
