import { useState } from 'react';
import vault from '../utils/secureVault';

/**
 * SecureInput - Encrypted Input Overlay
 * Shows when the agent requests sensitive data.
 * Data is encrypted client-side and never sent to the backend in plaintext.
 */
export default function SecureInput({ field, label, onSubmit, onCancel }) {
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    if (!value.trim()) return;
    setSaving(true);

    try {
      await vault.initialize();
      await vault.store(field, value);
      setSaved(true);

      if (onSubmit) {
        onSubmit({ field, stored: true });
      }
    } catch (err) {
      console.error('Vault store error:', err);
    } finally {
      setSaving(false);
    }
  };

  if (saved) {
    return (
      <div style={{
        background: 'rgba(78, 204, 163, 0.1)',
        border: '1px solid #4ecca3',
        borderRadius: '10px',
        padding: '14px 18px',
        margin: '8px 0',
        color: '#4ecca3',
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span>&#128274;</span>
        <span>{label || field} securely stored (encrypted)</span>
      </div>
    );
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      border: '1px solid #f0c040',
      borderRadius: '12px',
      padding: '18px',
      margin: '8px 0',
      color: '#eee',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <span style={{ fontSize: '18px' }}>&#128274;</span>
        <h4 style={{ margin: 0, color: '#f0c040' }}>Secure Input Required</h4>
      </div>

      <p style={{ color: '#aaa', fontSize: '13px', margin: '0 0 12px' }}>
        This data will be encrypted and stored locally. It will NOT be sent to the server.
      </p>

      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: '#bbb' }}>
        {label || field}:
      </label>
      <input
        type={field === 'password' ? 'password' : 'text'}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={`Enter ${label || field}...`}
        autoComplete="off"
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
        onKeyDown={(e) => e.key === 'Enter' && handleSave()}
      />

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleSave}
          disabled={!value.trim() || saving}
          style={{
            padding: '8px 18px',
            borderRadius: '8px',
            border: 'none',
            background: value.trim() ? '#4ecca3' : '#333',
            color: value.trim() ? '#000' : '#666',
            cursor: value.trim() ? 'pointer' : 'not-allowed',
            fontWeight: 'bold',
          }}
        >
          {saving ? 'Encrypting...' : 'Save Securely'}
        </button>
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: '1px solid #555',
              background: 'transparent',
              color: '#aaa',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
