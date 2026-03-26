import React from 'react';

export default function AnalyticsTab({ analyticsData }) {
  return (
    <div className="analytics-container">
      <div className="wa-header" style={{borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '2rem'}}>
        <h3><span style={{color: '#f59e0b'}}>Executive</span> Data Analytics</h3>
        <p>7-Day trailing performance. Real-time insights derived from CRM pipelines.</p>
      </div>
      
      <div style={{display: 'flex', gap: '2rem', padding: '0 24px'}}>
        <div className="glass-panel" style={{flex: 1}}>
          <h4 style={{marginTop: 0, color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px'}}>Call Volume vs. Deals Closed</h4>
          
          <div className="chart-wrapper">
            {analyticsData.map((stat, i) => {
              const maxCalls = Math.max(...analyticsData.map(d => d.calls)) || 100;
              const callHeight = Math.max(5, (stat.calls / maxCalls) * 100);
              const closedHeight = Math.max(2, (stat.closed / maxCalls) * 100 * 5);

              return (
                <div className="bar-group" key={i}>
                  <div className="bar calls-bar" style={{height: `${callHeight}%`}}>
                    <div className="tooltip">{stat.calls} Calls</div>
                  </div>
                  <div className="bar closed-bar" style={{height: `${closedHeight}%`}}>
                    <div className="tooltip">{stat.closed} Closed</div>
                  </div>
                  <div className="bar-label">
                    {stat.day}<br/>
                    <span style={{fontSize: '0.7rem', color: '#64748b'}}>{stat.date}</span>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '1rem'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem'}}><div style={{width: '12px', height: '12px', background: 'var(--primary)', borderRadius: '2px'}}></div> Total Calls</div>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem'}}><div style={{width: '12px', height: '12px', background: '#22c55e', borderRadius: '2px'}}></div> Won Deals</div>
          </div>
        </div>
      </div>
    </div>
  );
}
