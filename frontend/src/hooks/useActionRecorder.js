import { useState, useCallback, useRef } from 'react';

/**
 * useActionRecorder - Hook for recording user browser actions
 * Used by Teaching Mode to capture user demonstrations.
 * Records clicks, inputs, navigations, and form submissions.
 */
export default function useActionRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [actions, setActions] = useState([]);
  const actionsRef = useRef([]);
  const listenersRef = useRef([]);

  const addAction = useCallback((action) => {
    const entry = {
      ...action,
      timestamp: Date.now(),
    };
    actionsRef.current = [...actionsRef.current, entry];
    setActions([...actionsRef.current]);
  }, []);

  const startRecording = useCallback(() => {
    actionsRef.current = [];
    setActions([]);
    setIsRecording(true);

    // Click handler
    const clickHandler = (e) => {
      const target = e.target;
      const selector = getCssSelector(target);
      addAction({
        type: 'click',
        selector,
        tagName: target.tagName,
        text: target.textContent?.slice(0, 50) || '',
      });
    };

    // Input handler
    const inputHandler = (e) => {
      const target = e.target;
      if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return;
      const selector = getCssSelector(target);
      addAction({
        type: target.tagName === 'SELECT' ? 'select' : 'input',
        selector,
        value: target.value,
        inputType: target.type || '',
      });
    };

    // Submit handler
    const submitHandler = (e) => {
      const form = e.target;
      const selector = getCssSelector(form);
      addAction({
        type: 'submit',
        selector,
        url: window.location.href,
      });
    };

    // Navigation handler (popstate)
    const navHandler = () => {
      addAction({
        type: 'navigate',
        url: window.location.href,
      });
    };

    document.addEventListener('click', clickHandler, true);
    document.addEventListener('change', inputHandler, true);
    document.addEventListener('submit', submitHandler, true);
    window.addEventListener('popstate', navHandler);

    listenersRef.current = [
      { el: document, event: 'click', handler: clickHandler, capture: true },
      { el: document, event: 'change', handler: inputHandler, capture: true },
      { el: document, event: 'submit', handler: submitHandler, capture: true },
      { el: window, event: 'popstate', handler: navHandler },
    ];

    // Record initial page
    addAction({
      type: 'pageload',
      url: window.location.href,
    });
  }, [addAction]);

  const stopRecording = useCallback(() => {
    setIsRecording(false);

    // Remove all listeners
    listenersRef.current.forEach(({ el, event, handler, capture }) => {
      el.removeEventListener(event, handler, capture || false);
    });
    listenersRef.current = [];

    return actionsRef.current;
  }, []);

  const clearRecording = useCallback(() => {
    actionsRef.current = [];
    setActions([]);
  }, []);

  return {
    isRecording,
    actions,
    startRecording,
    stopRecording,
    clearRecording,
    actionCount: actions.length,
  };
}

/**
 * Generate a CSS selector for a DOM element.
 * Tries ID, then data attributes, then tag+class path.
 */
function getCssSelector(element) {
  if (!element || element === document.body) return 'body';

  // ID selector
  if (element.id) {
    return `#${element.id}`;
  }

  // Name attribute (forms)
  if (element.name) {
    return `[name="${element.name}"]`;
  }

  // Data-testid
  if (element.dataset?.testid) {
    return `[data-testid="${element.dataset.testid}"]`;
  }

  // Build path
  const parts = [];
  let current = element;
  while (current && current !== document.body) {
    let part = current.tagName.toLowerCase();

    if (current.id) {
      parts.unshift(`#${current.id}`);
      break;
    }

    // Add class if available
    if (current.className && typeof current.className === 'string') {
      const classes = current.className.trim().split(/\s+/).slice(0, 2);
      if (classes.length > 0 && classes[0]) {
        part += `.${classes.join('.')}`;
      }
    }

    // Add nth-child for disambiguation
    const parent = current.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
      if (siblings.length > 1) {
        const index = siblings.indexOf(current) + 1;
        part += `:nth-child(${index})`;
      }
    }

    parts.unshift(part);
    current = current.parentElement;
  }

  return parts.join(' > ') || element.tagName.toLowerCase();
}
