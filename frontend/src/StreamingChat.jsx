/**
 * StreamingChat - Real-time AI Chat Component
 * 
 * Shows AI responses token-by-token as they're generated.
 * Just like ChatGPT!
 */
import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Check, X, Loader, Sparkles, Zap } from 'lucide-react';
import { useStreamingChat } from './useStreamingChat';
import './StreamingChat.css';

function StreamingChat() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  
  const {
    messages,
    currentResponse,
    isStreaming,
    pendingAction,
    error,
    sendMessage,
    confirmAction,
    stopStreaming,
    clearChat
  } = useStreamingChat();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isStreaming) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="streaming-chat">
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <Sparkles className="header-icon" />
          <h1>Super Manager AI</h1>
        </div>
        <button onClick={clearChat} className="clear-btn">
          Clear Chat
        </button>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && !currentResponse && (
          <div className="welcome-message">
            <Zap size={48} className="welcome-icon" />
            <h2>What can I help you with?</h2>
            <p>I can schedule meetings, send emails, set reminders, help with payments, and much more!</p>
            <div className="example-prompts">
              <button onClick={() => setInput("Schedule a meeting tomorrow at 2pm")}>
                Schedule a meeting
              </button>
              <button onClick={() => setInput("Send an email to john@test.com")}>
                Send an email
              </button>
              <button onClick={() => setInput("Remind me to call mom at 5pm")}>
                Set a reminder
              </button>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="user-bubble">
                {msg.content}
              </div>
            ) : msg.role === 'error' ? (
              <div className="error-bubble">
                ⚠️ {msg.content}
              </div>
            ) : (
              <div className="assistant-bubble">
                <div className="ai-avatar">AI</div>
                <div className="bubble-content">
                  {msg.content}
                  
                  {/* Show action buttons if this message has a pending action */}
                  {msg.hasAction && idx === messages.length - 1 && pendingAction && (
                    <div className="action-buttons">
                      <button 
                        className="confirm-btn"
                        onClick={() => confirmAction(true)}
                        disabled={isStreaming}
                      >
                        <Check size={16} /> Confirm
                      </button>
                      <button 
                        className="cancel-btn"
                        onClick={() => confirmAction(false)}
                        disabled={isStreaming}
                      >
                        <X size={16} /> Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Currently streaming response */}
        {currentResponse && (
          <div className="message assistant streaming">
            <div className="assistant-bubble">
              <div className="ai-avatar">
                <Loader className="spinning" size={16} />
              </div>
              <div className="bubble-content">
                {currentResponse}
                <span className="cursor">▊</span>
              </div>
            </div>
          </div>
        )}

        {/* Streaming indicator */}
        {isStreaming && !currentResponse && (
          <div className="message assistant">
            <div className="assistant-bubble">
              <div className="ai-avatar">AI</div>
              <div className="bubble-content thinking">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            rows={1}
            disabled={isStreaming}
          />
          
          {isStreaming ? (
            <button type="button" onClick={stopStreaming} className="stop-btn">
              <Square size={18} />
            </button>
          ) : (
            <button type="submit" disabled={!input.trim()} className="send-btn">
              <Send size={18} />
            </button>
          )}
        </div>
        
        <p className="input-hint">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}

export default StreamingChat;
