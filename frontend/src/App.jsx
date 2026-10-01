import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import SecurityDashboard from './components/SecurityDashboard';
import { FileText, Shield, Upload, Menu, X, MessageSquare } from 'lucide-react';
import api from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    loadDocuments();
    loadStats();
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await api('/api/documents');
      setDocuments(data.documents);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api('/api/stats');
      setStats(data.statistics);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleDocumentUpload = () => {
    loadDocuments();
    loadStats();
  };

  const navItems = [
    { id: 'chat', label: 'Chat', icon: <MessageSquare size={17} /> },
    { id: 'upload', label: 'Documents', icon: <Upload size={17} />, badge: documents.length || null },
    { id: 'security', label: 'Security', icon: <Shield size={17} />, badge: stats?.security_incidents || null },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif', background: '#f8fafc' }}>

      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? '240px' : '0',
        background: 'linear-gradient(180deg, #1e1b4b 0%, #0f0d2e 100%)',
        color: 'white',
        transition: 'width 0.25s ease',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0
      }}>
        {/* Logo */}
        <div style={{ padding: '24px 20px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <FileText size={20} color="white" />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: '700', letterSpacing: '-0.3px' }}>Doc Q&A</div>
              <div style={{ fontSize: '10px', opacity: 0.5, marginTop: '1px' }}>Powered by Gemini</div>
            </div>
          </div>

          {/* Nav */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: activeTab === item.id ? 'rgba(139,92,246,0.25)' : 'transparent',
                  border: activeTab === item.id ? '1px solid rgba(139,92,246,0.4)' : '1px solid transparent',
                  borderRadius: '8px',
                  color: activeTab === item.id ? '#c4b5fd' : 'rgba(255,255,255,0.6)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '13px',
                  fontWeight: activeTab === item.id ? '600' : '400',
                  transition: 'all 0.15s'
                }}
              >
                {item.icon}
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge > 0 && (
                  <span style={{
                    background: activeTab === item.id ? '#8b5cf6' : 'rgba(255,255,255,0.15)',
                    borderRadius: '10px',
                    padding: '1px 7px',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Stats */}
        {stats && (
          <div style={{ marginTop: 'auto', padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
            <div style={{ fontSize: '10px', fontWeight: '600', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.8px', marginBottom: '10px', textTransform: 'uppercase' }}>
              Overview
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {[
                { label: 'Documents', value: stats.total_documents },
                { label: 'Queries', value: stats.total_queries },
                { label: 'Security events', value: stats.security_incidents },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                  <span style={{ color: 'rgba(255,255,255,0.45)' }}>{label}</span>
                  <span style={{ color: 'rgba(255,255,255,0.85)', fontWeight: '600' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <header style={{
          background: 'white',
          padding: '0 20px',
          height: '52px',
          boxShadow: '0 1px 0 #e5e7eb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0
        }}>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '6px', borderRadius: '6px', color: '#6b7280', display: 'flex' }}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {documents.length > 0 && (
              <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                {documents.length} doc{documents.length !== 1 ? 's' : ''} loaded
              </span>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '7px', height: '7px', background: '#22c55e', borderRadius: '50%' }} />
              <span style={{ fontSize: '12px', color: '#6b7280' }}>API connected</span>
            </div>
          </div>
        </header>

        {/* Content */}
        <main style={{ flex: 1, overflow: 'auto' }}>
          {activeTab === 'chat' && <ChatInterface documents={documents} />}
          {activeTab === 'security' && <SecurityDashboard />}
          {activeTab === 'upload' && (
            <DocumentUpload
              onUploadSuccess={handleDocumentUpload}
              documents={documents}
              onDeleteSuccess={handleDocumentUpload}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
