import React, { useState, useEffect, useRef } from 'react';

export default function KnowledgeBase({ apiUrl }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const fileInputRef = useRef(null);

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${apiUrl}/knowledge`);
      const data = await res.json();
      setFiles(data);
    } catch(e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setStatusMsg('Vectorizing and Embedding PDF using Gemini 004...');
    try {
      const res = await fetch(`${apiUrl}/knowledge/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        setStatusMsg(`✅ Successfully processed ${data.chunks_added} semantic chunks!`);
        fetchFiles();
        if (fileInputRef.current) fileInputRef.current.value = "";
      } else {
        setStatusMsg(`❌ Error: ${data.message || data.detail}`);
      }
    } catch (e) {
      setStatusMsg(`❌ Upload failed: ${e.message}`);
    }
    setUploading(false);
  };

  return (
    <div className="glass-panel" style={{padding: '2rem'}}>
      <h2 style={{marginTop: 0, marginBottom: '0.5rem', color: '#f8fafc'}}>🧠 RAG Knowledge Base</h2>
      <p style={{color: '#94a3b8', marginBottom: '2rem'}}>Upload company PDFs, product sheets, and manuals. The AI will instantly read these during live calls to answer highly technical questions exactly, eliminating hallucinations.</p>
      
      <div style={{display: 'flex', gap: '2rem', flexWrap: 'wrap'}}>
        <div style={{flex: '1 1 300px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '1.5rem'}}>
          <h3 style={{marginTop: 0, color: '#e2e8f0'}}>Upload Document</h3>
          <form onSubmit={handleUpload} style={{display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem'}}>
            <input 
              type="file" 
              accept=".pdf" 
              ref={fileInputRef} 
              className="form-input" 
              style={{background: 'rgba(0,0,0,0.3)', color: '#94a3b8', padding: '10px'}}
              required
            />
            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? 'Processing Vector Embeddings...' : '☁️ Upload & Embed PDF'}
            </button>
            {statusMsg && <p style={{fontSize: '0.9rem', color: statusMsg.includes('❌') ? '#ef4444' : '#4ade80'}}>{statusMsg}</p>}
          </form>
        </div>

        <div style={{flex: '2 1 400px'}}>
          <h3 style={{marginTop: 0, color: '#e2e8f0'}}>Active Vector Memory</h3>
          <div style={{background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '1rem', minHeight: '200px'}}>
            {files.length === 0 ? (
              <p style={{color: '#64748b', textAlign: 'center', marginTop: '3rem'}}>No documents in the vector database yet.</p>
            ) : (
              <ul style={{listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px'}}>
                {files.map((f, i) => (
                  <li key={i} style={{display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8'}}>
                    <span style={{fontSize: '1.2rem'}}>📄</span>
                    <span style={{color: '#cbd5e1', fontWeight: 500}}>{f.filename}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
