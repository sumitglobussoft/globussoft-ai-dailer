import React from 'react';

export default function LogsTab({ API_URL, authToken }) {
  return (
    <div style={{padding: '1rem'}}>
      <div className="wa-header" style={{borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div><h3><span style={{color: '#3b82f6'}}>📋 Live</span> Server Logs</h3>
        <p style={{margin: 0}}>Real-time server events — LLM responses, TTS, errors, and more.</p></div>
        <button className="btn-call" style={{borderColor: '#ef4444', color: '#ef4444', padding: '4px 16px', fontSize: '0.8rem'}} onClick={() => { const el = document.getElementById('live-log-area'); if (el) el.innerHTML = ''; }}>🗑️ Clear</button>
      </div>
      <div id="live-log-area" ref={el => {
        if (!el || el.dataset.connected) return;
        el.dataset.connected = '1';
        const es = new EventSource(`${API_URL}/live-logs?token=${authToken}`);
        es.onmessage = (ev) => {
          const line = document.createElement('div');
          line.textContent = ev.data;
          line.style.padding = '3px 12px';
          line.style.fontFamily = '"JetBrains Mono", "Fira Code", monospace';
          line.style.fontSize = '0.78rem';
          line.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
          if (ev.data.includes('ERROR')) { line.style.color = '#f87171'; line.style.background = 'rgba(239,68,68,0.06)'; }
          else if (ev.data.includes('WARNING')) { line.style.color = '#fbbf24'; }
          else if (ev.data.includes('[LLM]') || ev.data.includes('[TTS') || ev.data.includes('[STT]')) { line.style.color = '#67e8f9'; }
          else if (ev.data.includes('GREETING') || ev.data.includes('RECORDING')) { line.style.color = '#a78bfa'; }
          else { line.style.color = '#94a3b8'; }
          el.appendChild(line);
          if (el.children.length > 500) el.removeChild(el.firstChild);
          el.scrollTop = el.scrollHeight;
        };
        el._es = es;
      }} style={{
        background: 'rgba(2, 6, 23, 0.8)', border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: '8px', height: '70vh', overflowY: 'auto', overflowX: 'hidden'
      }} />
    </div>
  );
}
