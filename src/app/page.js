'use client';

import Link from 'next/link';

export default function Home() {
  const s = {
    page: { minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', padding: '4rem 2rem', fontFamily: 'system-ui, sans-serif' },
    container: { maxWidth: '1000px', margin: '0 auto', textAlign: 'center' },
    title: { fontSize: '3rem', fontWeight: '800', marginBottom: '1rem', background: 'linear-gradient(to right, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    subtitle: { fontSize: '1.25rem', color: '#94a3b8', marginBottom: '4rem' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' },
    card: { backgroundColor: '#1e293b', borderRadius: '16px', padding: '2rem', textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', transition: 'transform 0.2s, boxShadow 0.2s', border: '1px solid #334155' },
    icon: { fontSize: '4rem', marginBottom: '1.5rem' },
    cardTitle: { fontSize: '1.5rem', fontWeight: '700', marginBottom: '1rem' },
    cardDesc: { color: '#94a3b8', lineHeight: '1.6' }
  };

  return (
    <div style={s.page}>
      <div style={s.container}>
        <h1 style={s.title}>Video Automation Studio</h1>
        <p style={s.subtitle}>Select a generation pipeline to create viral Shorts automatically.</p>
        
        <div style={s.grid}>
          <Link href="/minecraft" style={s.card} className="hover-card">
            <div style={s.icon}>⛏️</div>
            <h2 style={s.cardTitle}>Minecraft Shaders</h2>
            <p style={s.cardDesc}>AI-driven Minecraft shader comparisons. Automatically clips before/after moments and generates dynamic voiceovers.</p>
          </Link>
          
          <Link href="/mrbeast" style={s.card} className="hover-card">
            <div style={s.icon}>🎬</div>
            <h2 style={s.cardTitle}>MrBeast & Streamers</h2>
            <p style={s.cardDesc}>Advanced face tracking, split-screen gameplay, animated Impact captions, and audio masking for viral streamer clips.</p>
          </Link>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        .hover-card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); border-color: #475569; }
      `}} />
    </div>
  );
}
