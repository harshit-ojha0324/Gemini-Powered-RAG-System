import React, { useState } from 'react';
import { User, Bot, AlertTriangle, ChevronDown, ChevronUp, FileText } from 'lucide-react';

function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      alignItems: 'flex-start',
      justifyContent: isUser ? 'flex-end' : 'flex-start'
    }}>
      {!isUser && (
        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 2px 6px rgba(139,92,246,0.3)'
        }}>
          <Bot size={18} color="white" />
        </div>
      )}

      <div style={{
        maxWidth: '72%',
        background: isUser
          ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
          : message.error ? '#fff1f2' : 'white',
        color: isUser ? 'white' : message.error ? '#be123c' : '#1f2937',
        padding: '12px 16px',
        borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        border: message.error ? '1px solid #fecdd3' : 'none'
      }}>
        <p style={{ lineHeight: '1.65', margin: 0, fontSize: '14px', whiteSpace: 'pre-wrap' }}>
          {message.content}
        </p>

        {/* Security Warnings */}
        {message.warnings && message.warnings.length > 0 && (
          <div style={{
            marginTop: '10px',
            padding: '8px 12px',
            background: 'rgba(251,191,36,0.15)',
            borderLeft: '3px solid #fbbf24',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '6px',
            fontSize: '12px',
            color: '#92400e'
          }}>
            <AlertTriangle size={13} style={{ marginTop: '1px', flexShrink: 0 }} />
            <span>{message.warnings.join(' · ')}</span>
          </div>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div style={{ marginTop: '10px' }}>
            <button
              onClick={() => setShowSources(!showSources)}
              style={{
                background: 'rgba(139,92,246,0.08)',
                border: 'none',
                color: '#7c3aed',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                padding: '4px 8px',
                borderRadius: '4px',
                fontWeight: '500'
              }}
            >
              {showSources ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
            </button>

            {showSources && (
              <div style={{
                marginTop: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {message.sources.map((source, idx) => (
                  <div key={idx} style={{
                    padding: '8px 10px',
                    background: 'rgba(0,0,0,0.03)',
                    borderRadius: '6px',
                    borderLeft: '2px solid #8b5cf6',
                    fontSize: '12px'
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      marginBottom: '4px',
                      fontWeight: '600',
                      color: '#4b5563'
                    }}>
                      <FileText size={11} />
                      {source.source} · Page {source.page}
                    </div>
                    <p style={{ margin: 0, color: '#6b7280', lineHeight: '1.5' }}>
                      {source.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '10px',
          background: '#e9d5ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <User size={18} color="#7c3aed" />
        </div>
      )}
    </div>
  );
}

export default MessageBubble;
