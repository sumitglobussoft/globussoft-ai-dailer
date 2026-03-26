import React from 'react';

export default function CheckInTab({ fieldOpsData, setFieldOpsData, sites, handlePunchIn, punching, punchStatus }) {
  return (
    <div className="glass-panel" style={{maxWidth: '500px', margin: '0 auto', textAlign: 'center', padding: '3rem 2rem'}}>
      <h2 style={{marginTop: 0}}>Secure Site Check-In</h2>
      <p style={{color: '#94a3b8', marginBottom: '2rem'}}>Verify your GPS location within 500m of the site property.</p>
      
      <div className="form-group" style={{textAlign: 'left'}}>
        <label>Salesperson Name</label>
        <input className="form-input" placeholder="e.g. Rahul Sharma" value={fieldOpsData.agent_name} onChange={e => setFieldOpsData({...fieldOpsData, agent_name: e.target.value})} />
      </div>
      
      <div className="form-group" style={{textAlign: 'left'}}>
        <label>Property Site</label>
        <select className="form-input" value={fieldOpsData.site_id} onChange={e => setFieldOpsData({...fieldOpsData, site_id: e.target.value})}>
          <option value="">-- Select Property --</option>
          {sites.map(site => (
            <option key={site.id} value={site.id}>{site.name}</option>
          ))}
        </select>
      </div>

      <button className="btn-punch" onClick={handlePunchIn} disabled={punching}>
        {punching ? 'Locating GPS 📡...' : '📍 Verify GPS & Punch In'}
      </button>

      {punchStatus && (
        <div className={`punch-result ${punchStatus.punch_status === 'Valid' ? 'valid' : 'invalid'}`}>
          <h3 style={{margin: '0 0 8px 0'}}>{punchStatus.punch_status === 'Valid' ? '✅ Punch Confirmed' : '❌ Out of Bounds'}</h3>
          <p style={{margin: 0}}>You are <strong>{punchStatus.distance_m} meters</strong> away from {punchStatus.site_name}.</p>
        </div>
      )}
    </div>
  );
}
