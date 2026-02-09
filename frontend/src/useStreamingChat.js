/**
 * useStreamingChat - React hook for real-time streaming AI chat
 * 
 * Uses Server-Sent Events (SSE) to receive tokens as they're generated.
 * Just like ChatGPT - instant responses, token by token!
 */
import { useState, useCallback, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'https://super-manager-api.onrender.com/api';

/**
 * Hook for streaming chat with real-time token updates
 */
export function useStreamingChat() {
  const [messages, setMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
  const [error, setError] = useState(null);
  
  const abortControllerRef = useRef(null);

  /**
   * Send a message and stream the response
   */
  const sendMessage = useCallback(async (message) => {
    if (!message.trim() || isStreaming) return;
    
    setError(null);
    setIsStreaming(true);
    setCurrentResponse('');
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date()
    }]);
    
    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();
    
    try {
      const response = await fetch(`${API_BASE}/stream/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message, 
          session_id: sessionId 
        }),
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) throw new Error('Failed to connect');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let newSessionId = sessionId;
      let hasAction = false;
      let actionType = null;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'token') {
                // Add token to current response immediately!
                fullResponse += data.content;
                setCurrentResponse(fullResponse);
              } else if (data.type === 'done') {
                // Response complete
                newSessionId = data.session_id;
                hasAction = data.has_action;
                actionType = data.action_type;
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
      
      // Add complete assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date(),
        hasAction,
        actionType
      }]);
      
      setSessionId(newSessionId);
      setCurrentResponse('');
      
      if (hasAction) {
        setPendingAction({ type: actionType });
      }
      
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
        setMessages(prev => [...prev, {
          role: 'error',
          content: err.message,
          timestamp: new Date()
        }]);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [sessionId, isStreaming]);

  /**
   * Confirm or cancel pending action with streaming status
   */
  const confirmAction = useCallback(async (confirmed) => {
    if (!sessionId || !pendingAction) return;
    
    setIsStreaming(true);
    setCurrentResponse('');
    
    try {
      const response = await fetch(`${API_BASE}/stream/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, confirmed })
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'status') {
                fullResponse += data.content;
                setCurrentResponse(fullResponse);
              }
            } catch (e) {}
          }
        }
      }
      
      // Add execution result
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date(),
        isExecutionResult: true
      }]);
      
      setCurrentResponse('');
      setPendingAction(null);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId, pendingAction]);

  /**
   * Stop current streaming
   */
  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  /**
   * Clear chat history
   */
  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setPendingAction(null);
    setCurrentResponse('');
    setError(null);
  }, []);

  return {
    messages,
    currentResponse,  // Partial response while streaming
    isStreaming,
    sessionId,
    pendingAction,
    error,
    sendMessage,
    confirmAction,
    stopStreaming,
    clearChat
  };
}

/**
 * Hook for WebSocket-based real-time chat (alternative to SSE)
 */
export function useWebSocketChat() {
  const [messages, setMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  
  const wsRef = useRef(null);
  const sessionIdRef = useRef(null);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback((sessionId = null) => {
    const sid = sessionId || crypto.randomUUID();
    sessionIdRef.current = sid;
    
    const wsUrl = `${API_BASE.replace('http', 'ws')}/stream/ws/${sid}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'token') {
        setCurrentResponse(prev => prev + data.content);
      } else if (data.type === 'status') {
        setCurrentResponse(prev => prev + data.content);
      } else if (data.type === 'done') {
        // Save complete message
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: currentResponse,
          timestamp: new Date(),
          hasAction: data.has_action
        }]);
        setCurrentResponse('');
        setIsStreaming(false);
        
        if (data.has_action) {
          setPendingAction({ type: data.action_type });
        }
      }
    };
    
    wsRef.current.onclose = () => {
      setIsConnected(false);
    };
    
    wsRef.current.onerror = () => {
      setIsConnected(false);
    };
  }, [currentResponse]);

  /**
   * Send message via WebSocket
   */
  const sendMessage = useCallback((message) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      // Retry after connection
      setTimeout(() => sendMessage(message), 500);
      return;
    }
    
    setMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date()
    }]);
    
    setCurrentResponse('');
    setIsStreaming(true);
    
    wsRef.current.send(JSON.stringify({ message }));
  }, [connect]);

  /**
   * Confirm action via WebSocket
   */
  const confirmAction = useCallback((confirmed) => {
    if (!wsRef.current) return;
    
    setCurrentResponse('');
    setIsStreaming(true);
    
    wsRef.current.send(JSON.stringify({ 
      action: confirmed ? 'confirm' : 'cancel',
      confirmed 
    }));
  }, []);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  return {
    messages,
    currentResponse,
    isConnected,
    isStreaming,
    pendingAction,
    connect,
    disconnect,
    sendMessage,
    confirmAction
  };
}

export default useStreamingChat;
