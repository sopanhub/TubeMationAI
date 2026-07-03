'use client';

import { useState, useEffect, useCallback } from 'react';

const getApiUrl = (path) => {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || '';
  const cleanBackend = backend.replace(/\/$/, '');
  return `${cleanBackend}${path}`;
};

export default function SettingsModal({ onClose }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const [formData, setFormData] = useState({
    GEMINI_API_KEY: '',
    GROQ_API_KEY: '',
    YOUTUBE_CLIENT_ID: '',
    YOUTUBE_CLIENT_SECRET: '',
    YOUTUBE_REFRESH_TOKEN: '',
  });

  const [isSet, setIsSet] = useState({});

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(getApiUrl('/api/settings'));
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setIsSet(data.settings || {});
    } catch (e) {
      setError('Failed to load settings: ' + e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);

    // Only send fields that the user typed in
    const updates = {};
    for (const [key, value] of Object.entries(formData)) {
      if (value.trim() !== '') {
        updates[key] = value.trim();
      }
    }

    if (Object.keys(updates).length === 0) {
      setSaving(false);
      onClose(); // Nothing to save
      return;
    }

    try {
      const res = await fetch(getApiUrl('/api/settings'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setSuccessMsg('Settings saved successfully!');
      
      // Update local state to show they are now set, and clear inputs
      const newIsSet = { ...isSet };
      const newFormData = { ...formData };
      for (const key of Object.keys(updates)) {
        newIsSet[key] = true;
        newFormData[key] = '';
      }
      setIsSet(newIsSet);
      setFormData(newFormData);

      setTimeout(() => {
        setSuccessMsg(null);
      }, 3000);
    } catch (e) {
      setError('Failed to save settings: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── Styles ──────────────────────────────────────────────────────────────────
  const overlay = {
    position: 'fixed', inset: 0, zIndex: 1000,
    backgroundColor: 'rgba(0,0,0,0.75)',
    backdropFilter: 'blur(6px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '1rem',
  };
  const modal = {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '16px',
    width: '100%', maxWidth: '600px',
    maxHeight: '85vh',
    display: 'flex', flexDirection: 'column',
    boxShadow: '0 0 40px rgba(0,0,0,0.5)',
    overflow: 'hidden',
  };
  const header = {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '1.25rem 1.5rem',
    borderBottom: '1px solid #334155',
    background: 'linear-gradient(135deg, #1e293b, #0f172a)',
    flexShrink: 0,
  };
  const titleStyle = {
    fontSize: '1.35rem', fontWeight: '800', color: '#f8fafc',
    display: 'flex', alignItems: 'center', gap: '0.5rem',
  };
  const closeBtn = {
    background: 'none', border: '1px solid #334155',
    color: '#94a3b8', borderRadius: '8px',
    padding: '0.4rem 0.8rem', cursor: 'pointer', fontSize: '1rem',
    transition: 'all 0.2s',
  };
  const body = {
    overflowY: 'auto', padding: '1.5rem',
    display: 'flex', flexDirection: 'column', gap: '1.5rem',
  };
  const msgBox = (type) => ({
    padding: '0.75rem 1rem',
    borderRadius: '8px',
    fontSize: '0.9rem',
    backgroundColor: type === 'error' ? '#7f1d1d' : '#064e3b',
    color: type === 'error' ? '#fecaca' : '#a7f3d0',
    border: `1px solid ${type === 'error' ? '#f87171' : '#34d399'}`,
  });
  
  const formGroup = {
    display: 'flex', flexDirection: 'column', gap: '0.5rem'
  };
  const label = {
    fontSize: '0.9rem', fontWeight: '600', color: '#cbd5e1',
    display: 'flex', justifyContent: 'space-between'
  };
  const statusBadge = (set) => ({
    fontSize: '0.75rem', fontWeight: '700',
    padding: '0.15rem 0.5rem', borderRadius: '999px',
    backgroundColor: set ? '#059669' : '#475569',
    color: '#f8fafc',
  });
  const input = {
    width: '100%', padding: '0.75rem 1rem',
    backgroundColor: '#1e293b', border: '1px solid #475569',
    borderRadius: '8px', color: '#f8fafc', fontSize: '0.95rem',
    outline: 'none', transition: 'border-color 0.2s'
  };
  const helpText = {
    fontSize: '0.8rem', color: '#64748b'
  };
  
  const footer = {
    padding: '1.25rem 1.5rem',
    borderTop: '1px solid #334155',
    display: 'flex', justifyContent: 'flex-end', gap: '1rem',
    backgroundColor: '#0f172a'
  };
  const cancelBtn = {
    padding: '0.6rem 1.2rem', backgroundColor: 'transparent',
    color: '#94a3b8', border: '1px solid #475569', borderRadius: '8px',
    fontWeight: '600', cursor: 'pointer', transition: 'all 0.2s',
  };
  const saveBtn = {
    padding: '0.6rem 1.5rem', backgroundColor: '#3b82f6',
    color: 'white', border: 'none', borderRadius: '8px',
    fontWeight: '600', cursor: saving ? 'not-allowed' : 'pointer',
    opacity: saving ? 0.7 : 1, transition: 'all 0.2s',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
  };

  const fields = [
    {
      id: 'GEMINI_API_KEY',
      label: 'Gemini API Key',
      help: 'Required for video analysis. Get one at: aistudio.google.com/app/apikey',
      type: 'password'
    },
    {
      id: 'GROQ_API_KEY',
      label: 'Groq API Key (Optional)',
      help: 'Enables "Magic Edit" voice/caption assistant. Get one at: console.groq.com/keys',
      type: 'password'
    },
    {
      id: 'YOUTUBE_CLIENT_ID',
      label: 'YouTube Client ID (Optional)',
      help: 'Fill this to upload automatic videos on YouTube, or leave blank to upload manually by downloading the video.',
      type: 'text'
    },
    {
      id: 'YOUTUBE_CLIENT_SECRET',
      label: 'YouTube Client Secret (Optional)',
      help: 'Fill this to upload automatic videos on YouTube, or leave blank to upload manually by downloading the video.',
      type: 'password'
    },
    {
      id: 'YOUTUBE_REFRESH_TOKEN',
      label: 'YouTube Refresh Token (Optional)',
      help: 'Fill this to upload automatic videos on YouTube, or leave blank to upload manually by downloading the video.',
      type: 'password'
    }
  ];

  return (
    <div style={overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={modal}>
        {/* Header */}
        <div style={header}>
          <span style={titleStyle}>⚙️ Settings</span>
          <button onClick={onClose} style={closeBtn}>✕ Close</button>
        </div>

        {/* Body */}
        <div style={body}>
          {error && <div style={msgBox('error')}>❌ {error}</div>}
          {successMsg && <div style={msgBox('success')}>✅ {successMsg}</div>}
          
          <p style={{ color: '#94a3b8', fontSize: '0.95rem', margin: 0 }}>
            Configure your API keys and credentials here. They will be saved securely to your local `.env` file.
          </p>

          <form id="settings-form" onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {fields.map(field => (
              <div key={field.id} style={formGroup}>
                <div style={label}>
                  {field.label}
                  <span style={statusBadge(isSet[field.id])}>
                    {isSet[field.id] ? '✓ Set' : 'Not Set'}
                  </span>
                </div>
                <input
                  type={field.type}
                  name={field.id}
                  value={formData[field.id]}
                  onChange={handleChange}
                  placeholder={isSet[field.id] ? '(Leave blank to keep existing value)' : `Enter ${field.label}`}
                  style={input}
                  onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                  onBlur={(e) => e.target.style.borderColor = '#475569'}
                  disabled={loading}
                />
                <div style={helpText}>{field.help}</div>
              </div>
            ))}
          </form>
        </div>
        
        {/* Footer */}
        <div style={footer}>
          <button onClick={onClose} style={cancelBtn} disabled={saving}>Cancel</button>
          <button type="submit" form="settings-form" style={saveBtn} disabled={saving || loading}>
            {saving ? '⏳ Saving...' : '💾 Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
