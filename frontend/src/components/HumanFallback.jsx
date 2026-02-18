import { useState } from 'react';

/**
 * HumanFallback - Manual Steps Panel
 * Shown when the agent can't complete a task automatically
 * (CAPTCHA, login required, anti-bot, etc.)
 */
export default function HumanFallback({ data, onComplete, onDismiss }) {
  const [completed, setCompleted] = useState(new Set());

  if (!data || !data.context) return null;

  const { reason, task_description, completed_steps, remaining_steps, prefilled_data, current_url } = data.context;

  const reasonLabels = {
    captcha_detected: 'CAPTCHA Detected',
    login_required: 'Login Required',
    anti_bot: 'Anti-Bot Protection',
    complex_form: 'Complex Form',
    two_factor: '2FA Required',
    automation_blocked: 'Automation Blocked',
  };

  const toggleStep = (index) => {
    const next = new Set(completed);
    if (next.has(index)) next.delete(index);
    else next.add(index);
    setCompleted(next);
  };

  const allDone = remaining_steps && remaining_steps.length > 0 && completed.size >= remaining_steps.length;

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      border: '1px solid #e94560',
      borderRadius: '12px',
      padding: '20px',
      margin: '12px 0',
      color: '#eee',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <span style={{ fontSize: '20px' }}>&#9888;</span>
        <h3 style={{ margin: 0, color: '#e94560' }}>
          Manual Action Required: {reasonLabels[reason] || reason}
        </h3>
      </div>

      {task_description && (
        <p style={{ color: '#aaa', marginBottom: '12px' }}>
          Task: {task_description}
        </p>
      )}

      {completed_steps && completed_steps.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          <h4 style={{ margin: '0 0 6px', color: '#4ecca3' }}>Completed by agent:</h4>
          {completed_steps.map((step, i) => (
            <div key={i} style={{ color: '#4ecca3', padding: '4px 0', opacity: 0.7 }}>
              &#10003; {step}
            </div>
          ))}
        </div>
      )}

      {remaining_steps && remaining_steps.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ margin: '0 0 6px', color: '#f0c040' }}>Please complete these steps:</h4>
          {remaining_steps.map((step, i) => (
            <div
              key={i}
              onClick={() => toggleStep(i)}
              style={{
                padding: '8px 12px',
                margin: '4px 0',
                background: completed.has(i) ? 'rgba(78, 204, 163, 0.2)' : 'rgba(255,255,255,0.05)',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'background 0.2s',
              }}
            >
              <span style={{
                width: '20px', height: '20px', borderRadius: '4px',
                border: completed.has(i) ? '2px solid #4ecca3' : '2px solid #555',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '12px', color: '#4ecca3',
              }}>
                {completed.has(i) ? '\u2713' : ''}
              </span>
              <span style={{ textDecoration: completed.has(i) ? 'line-through' : 'none', opacity: completed.has(i) ? 0.6 : 1 }}>
                {i + 1}. {step}
              </span>
            </div>
          ))}
        </div>
      )}

      {prefilled_data && Object.keys(prefilled_data).length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ margin: '0 0 6px', color: '#7ec8e3' }}>Pre-filled data:</h4>
          {Object.entries(prefilled_data).map(([key, value]) => (
            <div key={key} style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', margin: '2px 0', fontSize: '13px' }}>
              <strong>{key}:</strong> {value}
            </div>
          ))}
        </div>
      )}

      {current_url && (
        <div style={{ marginBottom: '16px' }}>
          <a href={current_url} target="_blank" rel="noopener noreferrer" style={{ color: '#7ec8e3', fontSize: '13px' }}>
            Open page: {current_url}
          </a>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={onComplete}
          disabled={!allDone}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: allDone ? '#4ecca3' : '#333',
            color: allDone ? '#000' : '#666',
            cursor: allDone ? 'pointer' : 'not-allowed',
            fontWeight: 'bold',
          }}
        >
          I've completed these steps
        </button>
        <button
          onClick={onDismiss}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: '1px solid #555',
            background: 'transparent',
            color: '#aaa',
            cursor: 'pointer',
          }}
        >
          Skip / Cancel
        </button>
      </div>
    </div>
  );
}
