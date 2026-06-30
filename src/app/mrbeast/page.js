'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

export default function MrBeastDashboard() {
  const [url, setUrl] = useState('');
  const [gameplayUrl, setGameplayUrl] = useState('');
  const [status, setStatus] = useState('Idle');
  const [logs, setLogs] = useState([]);
  const [videoGenerated, setVideoGenerated] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [quality, setQuality] = useState('high');
  const [videoSize, setVideoSize] = useState(null);
  const [generatedClips, setGeneratedClips] = useState([]);
  
  const [videoKey, setVideoKey] = useState(Date.now());
  const videoRef = useRef(null);

  const s = {
    page: { minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', padding: '2rem', fontFamily: 'system-ui, sans-serif' },
    nav: { display: 'flex', alignItems: 'center', marginBottom: '2rem' },
    backBtn: { color: '#60a5fa', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold' },
    header: { textAlign: 'center', marginBottom: '3rem' },
    title: { fontSize: '2.5rem', fontWeight: '800', marginBottom: '0.5rem', background: 'linear-gradient(to right, #60a5fa, #34d399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    subtitle: { color: '#94a3b8' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', maxWidth: '1400px', margin: '0 auto' },
    card: { backgroundColor: '#1e293b', borderRadius: '12px', padding: '1.5rem', border: '1px solid #334155' },
    cardTitle: { fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1.5rem', borderBottom: '1px solid #334155', paddingBottom: '0.75rem' },
    label: { display: 'block', marginBottom: '0.5rem', color: '#cbd5e1', fontWeight: '600' },
    input: { width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #475569', backgroundColor: '#0f172a', color: 'white', marginBottom: '1.5rem', fontSize: '1rem' },
    btn: { width: '100%', padding: '1rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', transition: 'background-color 0.2s', marginTop: '1rem' },
    btnDisabled: { backgroundColor: '#475569', cursor: 'not-allowed' },
    logBox: { backgroundColor: '#020617', padding: '1rem', borderRadius: '8px', border: '1px solid #334155', height: '300px', overflowY: 'auto', fontFamily: 'monospace', fontSize: '0.85rem', color: '#a5b4fc', display: 'flex', flexDirection: 'column', gap: '0.25rem' },
    videoWrapper: { width: '100%', maxWidth: '360px', margin: '0 auto', aspectRatio: '9/16', backgroundColor: 'black', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' },
    statusPill: { display: 'inline-block', padding: '0.25rem 0.75rem', backgroundColor: '#334155', borderRadius: '9999px', fontSize: '0.875rem', marginBottom: '1rem' }
  };

  const addLog = (msg) => setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  useEffect(() => {
    if (videoGenerated && videoRef.current) {
      videoRef.current.load();
    }
  }, [videoGenerated, videoKey]);

  const handleRunAutomation = async () => {
    if (!url.trim()) {
      alert('Paste a main video URL first.');
      return;
    }

    setLoading(true);
    setVideoGenerated(false);
    setVideoSize(null);
    setGeneratedClips([]);
    setLogs([]);
    setStatus('Initializing MrBeast Pipeline…');
    addLog(`Target: ${url.trim()}`);

    try {
      const response = await fetch('/api/generate-mrbeast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), gameplayUrl: gameplayUrl.trim(), quality }),
      });

      if (!response.ok) {
        let errorMsg = 'Unknown error';
        try {
          const errData = await response.json();
          errorMsg = errData.error || response.statusText;
        } catch (e) { }
        addLog('❌ Error: ' + errorMsg);
        setStatus('❌ Generation Failed.');
        setLoading(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); 

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.type === 'log') {
              const msg = parsed.message.trim();
              addLog(msg);
              if (msg.includes('FINAL_FILE_SIZE:')) {
                const size = msg.split('FINAL_FILE_SIZE:')[1].trim();
                setVideoSize(size);
              }
              // Parse individual clip completions
              const clipMatch = msg.match(/Clip (\d+) saved: (mrbeast_clip_\d+\.mp4)/);
              if (clipMatch) {
                const clipNum = parseInt(clipMatch[1]);
                const clipFile = clipMatch[2];
                setGeneratedClips(prev => {
                  const next = [...prev];
                  next[clipNum - 1] = { num: clipNum, file: clipFile, ts: Date.now() };
                  return next;
                });
                setVideoGenerated(true);
              }
              if (msg.includes('Tracking face')) setStatus('Tracking face coordinates…');
              else if (msg.includes('Whisper')) setStatus('Generating word-level captions…');
              else if (msg.includes('Mutating')) setStatus('Applying audio/visual mutations…');
              else if (msg.includes('Writing final')) setStatus('Rendering final dual-screen short…');
            } else if (parsed.type === 'success') {
              setStatus('✅ Short generated successfully!');
              setVideoGenerated(true);
              setVideoKey(Date.now());
            } else if (parsed.type === 'error') {
              addLog('❌ Error: ' + parsed.message);
              setStatus('❌ Generation Failed.');
            }
          } catch (e) { }
        }
      }
    } catch (err) {
      addLog('❌ Network Error: ' + err.message);
      setStatus('❌ Generation Failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <Link href="/" style={s.backBtn}>
          <span>← Back to Menu</span>
        </Link>
      </nav>

      <div style={s.header}>
        <h1 style={s.title}>MrBeast / Streamer Shorts Generator</h1>
        <p style={s.subtitle}>Advanced face tracking, Whisper captions, dual-screen gameplay, and Content ID evasion.</p>
      </div>

      <div style={s.grid}>
        {/* Left Col: Config & Logs */}
        <div>
          <div style={s.card}>
            <h2 style={s.cardTitle}>⚙️ Generation Settings</h2>
            
            <label style={s.label}>Main Video URL (Streamer / Vlog)</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              style={s.input}
              disabled={loading}
            />

            <label style={s.label}>Gameplay URL (Optional - Bottom Screen)</label>
            <input
              type="text"
              value={gameplayUrl}
              onChange={(e) => setGameplayUrl(e.target.value)}
              placeholder="Leave blank for full-screen mode (no split screen)"
              style={s.input}
              disabled={loading}
            />

            <label style={s.label}>Target Quality</label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              style={s.input}
              disabled={loading}
            >
              <option value="low">Low (480p, 30fps, Fast render)</option>
              <option value="medium">Medium (720p, 30fps, Balanced)</option>
              <option value="high">High (1080p, 60fps, Max Quality)</option>
            </select>

            <button
              onClick={handleRunAutomation}
              disabled={loading}
              style={{ ...s.btn, ...(loading ? s.btnDisabled : {}) }}
            >
              {loading && !videoGenerated
                ? 'Processing Pipeline...'
                : 'Generate Viral Short'}
            </button>
          </div>

          <div style={{ ...s.card, marginTop: '2rem' }}>
            <h2 style={s.cardTitle}>🖥️ Terminal Output</h2>
            <div style={s.statusPill}>Status: {status}</div>
            <div style={s.logBox}>
              {logs.map((log, i) => (
                <div key={i}>{log}</div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Output Clips (appear one by one as each renders) */}
        <div style={s.card}>
          <h2 style={s.cardTitle}>
            📱 Generated Clips {videoSize && <span style={{ color: '#34d399', fontSize: '1rem', float: 'right' }}>Clip 1 size: {videoSize}</span>}
          </h2>
          {!videoGenerated && !loading && (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '4rem 0' }}>
              5 Short clips will appear here as each one finishes.
            </div>
          )}
          {loading && generatedClips.filter(Boolean).length === 0 && (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '4rem 0' }}>
              Gemini is analyzing your video...<br/><br/>
              <em>Clips will appear here one-by-one as they finish rendering.</em>
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {generatedClips.filter(Boolean).map((clip) => (
              <div key={clip.num}>
                <p style={{ color: '#60a5fa', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  Clip #{clip.num} — ready!
                </p>
                <div style={{ width: '100%', maxWidth: '280px', margin: '0 auto', aspectRatio: '9/16', backgroundColor: 'black', borderRadius: '8px', overflow: 'hidden' }}>
                  <video
                    controls
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  >
                    <source src={`/output/${clip.file}?t=${clip.ts}`} type="video/mp4" />
                  </video>
                </div>
                <a
                  href={`/output/${clip.file}`}
                  download={clip.file}
                  style={{ display: 'block', textAlign: 'center', marginTop: '0.5rem', color: '#34d399', fontWeight: 'bold', textDecoration: 'none' }}
                >
                  Download Clip #{clip.num}
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
