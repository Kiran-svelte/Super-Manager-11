/**
 * Super Manager - Custom React Hooks
 * ===================================
 * 
 * Collection of custom hooks for the Super Manager frontend.
 */

import { useState, useCallback, useRef, useEffect } from 'react';

// =============================================================================
// useChat Hook
// =============================================================================

/**
 * Hook for managing chat state and API communication
 */
export function useChat(options = {}) {
  const {
    apiUrl = import.meta.env.VITE_API_URL || 'https://backend-production-a98d.up.railway.app',
    onError = null,
    maxRetries = 3,
  } = options;

  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  
  const abortControllerRef = useRef(null);

  // Send message to API
  const sendMessage = useCallback(async (content) => {
    if (!content?.trim()) {
      return null;
    }

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    let retries = 0;
    
    while (retries < maxRetries) {
      try {
        const response = await fetch(`${apiUrl}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: content.trim(),
            conversation_id: conversationId,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `HTTP ${response.status}`);
        }

        const data = await response.json();
        
        // Update conversation ID
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }

        // Add assistant message
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || data.message || 'No response',
          timestamp: new Date().toISOString(),
          metadata: data.metadata,
          actions: data.actions,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoading(false);
        
        return assistantMessage;

      } catch (err) {
        if (err.name === 'AbortError') {
          setIsLoading(false);
          return null;
        }

        retries++;
        
        if (retries >= maxRetries) {
          const errorMessage = err.message || 'Failed to send message';
          setError(errorMessage);
          setIsLoading(false);
          
          if (onError) {
            onError(err);
          }
          
          return null;
        }

        // Wait before retry (exponential backoff)
        await new Promise(r => setTimeout(r, Math.pow(2, retries) * 1000));
      }
    }

    setIsLoading(false);
    return null;
  }, [apiUrl, conversationId, maxRetries, onError]);

  // Clear chat history
  const clearChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  // Cancel pending request
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsLoading(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    messages,
    isLoading,
    error,
    conversationId,
    sendMessage,
    clearChat,
    cancel,
    setMessages,
  };
}

// =============================================================================
// useLocalStorage Hook
// =============================================================================

/**
 * Hook for persisting state in localStorage
 */
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

// =============================================================================
// useDebounce Hook
// =============================================================================

/**
 * Hook for debouncing values
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// =============================================================================
// useOnClickOutside Hook
// =============================================================================

/**
 * Hook for detecting clicks outside an element
 */
export function useOnClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}

// =============================================================================
// useKeyPress Hook
// =============================================================================

/**
 * Hook for detecting key presses
 */
export function useKeyPress(targetKey) {
  const [keyPressed, setKeyPressed] = useState(false);

  useEffect(() => {
    const downHandler = ({ key }) => {
      if (key === targetKey) {
        setKeyPressed(true);
      }
    };

    const upHandler = ({ key }) => {
      if (key === targetKey) {
        setKeyPressed(false);
      }
    };

    window.addEventListener('keydown', downHandler);
    window.addEventListener('keyup', upHandler);

    return () => {
      window.removeEventListener('keydown', downHandler);
      window.removeEventListener('keyup', upHandler);
    };
  }, [targetKey]);

  return keyPressed;
}

// =============================================================================
// useMediaQuery Hook
// =============================================================================

/**
 * Hook for responsive design
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (event) => setMatches(event.matches);

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else {
      // Legacy
      mediaQuery.addListener(handler);
    }

    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handler);
      } else {
        mediaQuery.removeListener(handler);
      }
    };
  }, [query]);

  return matches;
}

// =============================================================================
// useScrollToBottom Hook
// =============================================================================

/**
 * Hook for auto-scrolling to bottom of container
 */
export function useScrollToBottom(dependency) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [dependency]);

  return ref;
}

// =============================================================================
// useTheme Hook
// =============================================================================

/**
 * Hook for managing theme (light/dark)
 */
export function useTheme() {
  const [theme, setTheme] = useLocalStorage('theme', 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }, [setTheme]);

  return { theme, setTheme, toggleTheme };
}

// =============================================================================
// useFetch Hook
// =============================================================================

/**
 * Generic hook for data fetching
 */
export function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { 
    immediate = true,
    transform = (d) => d,
  } = options;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const result = await response.json();
      setData(transform(result));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [url, transform]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [fetchData, immediate]);

  return { data, loading, error, refetch: fetchData };
}

export default {
  useChat,
  useLocalStorage,
  useDebounce,
  useOnClickOutside,
  useKeyPress,
  useMediaQuery,
  useScrollToBottom,
  useTheme,
  useFetch,
};
