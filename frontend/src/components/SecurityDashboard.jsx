import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Eye, Clock } from 'lucide-react';
import api from '../services/api';

function SecurityDashboard() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [logsData, statsData] = await Promise.all([
        api('/api/security/logs?limit=20'),
        api('/api/stats')
      ]);

      setLogs(logsData.logs);
      setStats(statsData.statistics);
      setLoading(false);
    } catch (error) {
      console.error('Error loading security data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Loading security data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '24px', fontSize: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Shield size={28} color="#8b5cf6" />
        Security Dashboard
      </h2>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        <StatCard
          title="Total Incidents"
          value={stats?.security_incidents || 0}
          icon={<AlertTriangle size={24} />}
          color="#ef4444"
        />
        <StatCard
          title="PII Detections"
          value={stats?.pii_detections || 0}
          icon={<Eye size={24} />}
          color="#f59e0b"
        />
        <StatCard
          title="Total Queries"
          value={stats?.total_queries || 0}
          icon={<Clock size={24} />}
          color="#8b5cf6"
        />
        <StatCard
          title="Security Score"
          value={stats ? Math.round(((stats.total_queries - stats.security_incidents) / Math.max(stats.total_queries, 1)) * 100) + '%' : '100%'}
          icon={<Shield size={24} />}
          color="#10b981"
        />
      </div>

      {/* Security Logs */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginBottom: '16px', fontSize: '18px' }}>Recent Security Events</h3>
        
        {logs.length === 0 ? (
          <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px' }}>
            No security events recorded
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                  <th style={{ padding: '12px', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                    Time
                  </th>
                  <th style={{ padding: '12px', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                    Query
                  </th>
                  <th style={{ padding: '12px', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                    Flags
                  </th>
                  <th style={{ padding: '12px', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                    PII
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '12px', fontSize: '13px' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px', maxWidth: '400px' }}>
                      {log.query.length > 100 ? log.query.substring(0, 100) + '...' : log.query}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {log.flags.map((flag, i) => (
                        <span
                          key={i}
                          style={{
                            display: 'inline-block',
                            padding: '4px 8px',
                            background: '#fee2e2',
                            color: '#991b1b',
                            borderRadius: '4px',
                            fontSize: '11px',
                            marginRight: '4px',
                            marginBottom: '4px'
                          }}
                        >
                          {flag}
                        </span>
                      ))}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {log.pii_detected ? (
                        <span style={{
                          display: 'inline-block',
                          width: '20px',
                          height: '20px',
                          background: '#fecaca',
                          borderRadius: '50%',
                          color: '#991b1b',
                          lineHeight: '20px'
                        }}>
                          ⚠
                        </span>
                      ) : (
                        <span style={{ color: '#9ca3af' }}>-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div>
          <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
            {title}
          </p>
          <p style={{ fontSize: '28px', fontWeight: 'bold', color }}>
            {value}
          </p>
        </div>
        <div style={{ color }}>{icon}</div>
      </div>
    </div>
  );
}

export default SecurityDashboard;