import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, FileText, MessageSquare, Zap } from 'lucide-react';
import MessageBubble from './MessageBubble';
import api from '../services/api';

function ChatInterface({ documents }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [noDocWarning, setNoDocWarning] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    if (documents.length === 0) {
      setNoDocWarning(true);
      setTimeout(() => setNoDocWarning(false), 3000);
      return;
    }

    setNoDocWarning(false);
    const question = input.trim();
    const userMessage = { role: 'user', content: question };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const data = await api('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, conversation_history: messages })
      });

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        warnings: data.security_warnings
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: error.detail || 'Sorry, I encountered an error processing your question.',
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const hasDocuments = documents.length > 0;

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      maxWidth: '860px',
      margin: '0 auto',
      padding: '20px',
      boxSizing: 'border-box'
    }}>
      {/* No-document warning banner */}
      {noDocWarning && (
        <div style={{
          marginBottom: '12px',
          padding: '12px 16px',
          background: '#fef3c7',
          border: '1px solid #fbbf24',
          borderRadius: '8px',
          color: '#92400e',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <FileText size={16} />
          No documents uploaded yet — go to the Documents tab to upload a PDF first.
        </div>
      )}

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '8px 4px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            textAlign: 'center',
            padding: '40px 20px',
            color: '#6b7280'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px',
              boxShadow: '0 8px 20px rgba(139, 92, 246, 0.3)'
            }}>
              <MessageSquare size={32} color="white" />
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
              Smart Document Q&A
            </h2>
            <p style={{ fontSize: '14px', marginBottom: '24px', maxWidth: '380px', lineHeight: '1.6' }}>
              Powered by Gemini 2.0 Flash. Upload a PDF and ask anything about its contents.
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '12px',
              maxWidth: '480px',
              width: '100%'
            }}>
              {[
                { icon: <FileText size={16} />, text: 'Upload PDFs' },
                { icon: <Zap size={16} />, text: 'Instant answers' },
                { icon: <MessageSquare size={16} />, text: 'Follow-up questions' }
              ].map((item, i) => (
                <div key={i} style={{
                  padding: '12px',
                  background: 'white',
                  borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: '#6b7280'
                }}>
                  <span style={{ color: '#8b5cf6' }}>{item.icon}</span>
                  {item.text}
                </div>
              ))}
            </div>
            {!hasDocuments && (
              <p style={{
                marginTop: '20px',
                fontSize: '13px',
                color: '#9ca3af',
                padding: '8px 16px',
                background: '#f9fafb',
                borderRadius: '6px',
                border: '1px dashed #d1d5db'
              }}>
                No documents yet — upload one to get started
              </p>
            )}
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {loading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            alignSelf: 'flex-start',
            maxWidth: '200px'
          }}>
            <Loader size={16} color="#8b5cf6" style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontSize: '13px', color: '#6b7280' }}>Thinking…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} style={{
        background: 'white',
        padding: '16px',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        marginTop: '12px',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={hasDocuments ? 'Ask a question about your documents…' : 'Upload a document to start asking questions'}
            disabled={loading}
            style={{
              flex: 1,
              padding: '11px 14px',
              border: '1.5px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px',
              outline: 'none',
              transition: 'border-color 0.15s',
              background: loading ? '#f9fafb' : 'white',
              color: '#1f2937'
            }}
            onFocus={(e) => e.target.style.borderColor = '#8b5cf6'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: '11px 20px',
              background: loading || !input.trim() ? '#e5e7eb' : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
              color: loading || !input.trim() ? '#9ca3af' : 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: '500',
              fontSize: '14px',
              transition: 'all 0.15s',
              whiteSpace: 'nowrap'
            }}
          >
            <Send size={15} />
            Send
          </button>
        </div>
        {hasDocuments && (
          <p style={{ fontSize: '11px', color: '#9ca3af', marginTop: '8px', marginBottom: 0, paddingLeft: '2px' }}>
            {documents.length} document{documents.length !== 1 ? 's' : ''} loaded
          </p>
        )}
      </form>
    </div>
  );
}

export default ChatInterface;
