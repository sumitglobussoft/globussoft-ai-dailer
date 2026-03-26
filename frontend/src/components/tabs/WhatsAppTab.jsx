import React from 'react';

export default function WhatsAppTab({ whatsappLogs }) {
  return (
    <div className="whatsapp-container">
      <div className="wa-header">
        <h3><span style={{color: '#25D366'}}>WhatsApp</span> Outbound Automated Logs</h3>
        <p>Monitors triggered property e-brochures and automated conversational nudges.</p>
      </div>
      <div className="wa-chat-window">
        {whatsappLogs.length === 0 ? (
          <div className="wa-empty">No WhatsApp triggers sent yet. Change a Lead Status to "Warm" in CRM!</div>
        ) : whatsappLogs.map(log => (
          <div key={log.id} className="wa-message-row">
            <div className="wa-message-bubble">
              <div className="wa-message-recipient">To: {log.first_name} {log.last_name} ({log.phone})</div>
              <div className="wa-message-body">{log.message}</div>
              <div className="wa-message-meta">
                <span className="wa-pill">{log.msg_type} Trigger</span>
                <span className="wa-time">{new Date(log.sent_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                <span className="wa-ticks">✓✓</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
