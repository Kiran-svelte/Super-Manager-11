import { useState } from 'react';
import useActionRecorder from '../hooks/useActionRecorder';

/**
 * TeachingMode - Recording UI Component
 * Shows recording indicator, action log, and done button.
 */
export default function TeachingMode({ sessionId, apiUrl, onWorkflowSaved, onCancel }) {
  const { isRecording, actions, startRecording, stopRecording, actionCount } = useActionRecorder();
  const [saving, setSaving] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [result, setResult] = useState(null);

  const handleStart = () => {
    startRecording();
  };

  const handleStop = async () => {
    const recorded = stopRecording();
    setSaving(true);

    try {
      const resp = await fetch(`${apiUrl}/api/teach/record`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          task_description: taskName || 'Recorded workflow',
          actions: recorded,
        }),
      });

      const data = await resp.json();
      setResult(data);

      if (data.status === 'saved' && onWorkflowSaved) {
        onWorkflowSaved(data);
      }
    } catch (err) {
      setResult({ status: 'error', message: err.message });
    } finally {
      setSaving(false);
    }
  };

  if (result) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        border: `1px solid ${result.status === 'saved' ? '#4ecca3' : '#e94560'}`,
        borderRadius: '12px',
        padding: '20px',
        margin: '12px 0',
        color: '#eee',
      }}>
        {result.status === 'saved' ? (
          <>
            <h3 style={{ color: '#4ecca3', margin: '0 0 8px' }}>Workflow Saved</h3>
            <p>Name: <strong>{result.workflow_name}</strong></p>
            <p>Steps: {result.steps_count}</p>
            {result.parameters?.length > 0 && (
              <p>Parameters: {result.parameters.join(', ')}</p>
            )}
            <p style={{ color: '#aaa', fontSize: '13px' }}>
              You can now use this workflow by asking: "Run {result.workflow_name}"
            </p>
          </>
        ) : (
          <>
            <h3 style={{ color: '#e94560', margin: '0 0 8px' }}>Recording Failed</h3>
            <p>{result.message}</p>
          </>
        )}
        <button
          onClick={onCancel}
          style={{
            marginTop: '10px',
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #555',
            background: 'transparent',
            color: '#aaa',
            cursor: 'pointer',
          }}
        >
          Close
        </button>
      </div>
    );
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      border: `1px solid ${isRecording ? '#e94560' : '#4ecca3'}`,
      borderRadius: '12px',
      padding: '20px',
      margin: '12px 0',
      color: '#eee',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        {isRecording && (
          <span style={{
            width: '12px', height: '12px', borderRadius: '50%',
            background: '#e94560',
            animation: 'pulse 1s infinite',
          }} />
        )}
        <h3 style={{ margin: 0 }}>
          {isRecording ? 'Recording...' : 'Teaching Mode'}
        </h3>
      </div>

      {!isRecording && (
        <>
          <p style={{ color: '#aaa', marginBottom: '12px' }}>
            Name the task you want to teach, then click Start to begin recording your actions.
          </p>
          <input
            type="text"
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
            placeholder="e.g., Book a hotel on MakeMyTrip"
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid #333',
              background: 'rgba(255,255,255,0.05)',
              color: '#eee',
              marginBottom: '12px',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleStart}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: 'none',
                background: '#4ecca3',
                color: '#000',
                cursor: 'pointer',
                fontWeight: 'bold',
              }}
            >
              Start Recording
            </button>
            <button
              onClick={onCancel}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#aaa',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </>
      )}

      {isRecording && (
        <>
          <div style={{
            background: 'rgba(0,0,0,0.3)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '12px',
            maxHeight: '200px',
            overflowY: 'auto',
          }}>
            <div style={{ fontSize: '13px', color: '#aaa', marginBottom: '6px' }}>
              Actions captured: {actionCount}
            </div>
            {actions.slice(-5).map((a, i) => (
              <div key={i} style={{
                fontSize: '12px',
                color: '#7ec8e3',
                padding: '2px 0',
                fontFamily: 'monospace',
              }}>
                {a.type}: {a.selector || a.url || a.value || ''}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleStop}
              disabled={saving || actionCount < 2}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: 'none',
                background: actionCount >= 2 ? '#e94560' : '#333',
                color: actionCount >= 2 ? '#fff' : '#666',
                cursor: actionCount >= 2 ? 'pointer' : 'not-allowed',
                fontWeight: 'bold',
              }}
            >
              {saving ? 'Saving...' : 'Done Recording'}
            </button>
            <button
              onClick={onCancel}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#aaa',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
