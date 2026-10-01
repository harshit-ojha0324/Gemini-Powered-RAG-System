import React, { useState } from 'react';
import { Upload, File, Trash2, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import api from '../services/api';

function DocumentUpload({ onUploadSuccess, documents, onDeleteSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [deletingFile, setDeletingFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
  };

  const handleFileInput = (e) => {
    if (e.target.files?.[0]) handleUpload(e.target.files[0]);
    e.target.value = '';
  };

  const handleUpload = async (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus({ type: 'error', message: 'Only PDF files are allowed.' });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const data = await api('/api/upload', { method: 'POST', body: formData });
      setUploadStatus({
        type: 'success',
        message: `"${file.name}" uploaded — ${data.chunks} chunks indexed`
      });
      onUploadSuccess();
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.detail || 'Upload failed. Please try again.'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete "${filename}"?`)) return;
    setDeletingFile(filename);
    try {
      await api(`/api/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      setUploadStatus({ type: 'success', message: `"${filename}" deleted.` });
      onDeleteSuccess();
    } catch {
      setUploadStatus({ type: 'error', message: `Failed to delete "${filename}".` });
    } finally {
      setDeletingFile(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const formatDate = (isoString) => {
    try {
      return new Date(isoString).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return '—';
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '820px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#111827', marginBottom: '4px' }}>Documents</h2>
      <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '24px' }}>
        Upload PDFs to make them available for Q&A.
      </p>

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#8b5cf6' : '#d1d5db'}`,
          borderRadius: '12px',
          padding: '40px 24px',
          textAlign: 'center',
          background: dragActive ? '#f5f3ff' : uploading ? '#fafafa' : 'white',
          marginBottom: '20px',
          transition: 'all 0.2s',
          cursor: uploading ? 'default' : 'pointer'
        }}
        onClick={() => !uploading && document.getElementById('file-input').click()}
      >
        <div style={{
          width: '52px',
          height: '52px',
          background: dragActive ? '#ede9fe' : '#f3f4f6',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 14px'
        }}>
          <Upload size={24} color={dragActive ? '#8b5cf6' : '#9ca3af'} />
        </div>
        <p style={{ fontSize: '15px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
          {uploading ? 'Uploading…' : 'Drop a PDF here'}
        </p>
        <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '16px' }}>
          {uploading ? 'Processing your document' : 'or click to browse'}
        </p>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          disabled={uploading}
          style={{ display: 'none' }}
          id="file-input"
        />
        <button
          disabled={uploading}
          onClick={(e) => { e.stopPropagation(); document.getElementById('file-input').click(); }}
          style={{
            padding: '9px 22px',
            background: uploading ? '#e5e7eb' : 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
            color: uploading ? '#9ca3af' : 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: uploading ? 'not-allowed' : 'pointer',
            fontWeight: '500',
            fontSize: '13px'
          }}
        >
          {uploading ? 'Processing…' : 'Select PDF'}
        </button>
      </div>

      {/* Status */}
      {uploadStatus && (
        <div style={{
          padding: '11px 14px',
          background: uploadStatus.type === 'success' ? '#f0fdf4' : '#fef2f2',
          color: uploadStatus.type === 'success' ? '#166534' : '#991b1b',
          border: `1px solid ${uploadStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px'
        }}>
          {uploadStatus.type === 'success'
            ? <CheckCircle size={16} />
            : <AlertCircle size={16} />}
          {uploadStatus.message}
        </div>
      )}

      {/* Document list */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#374151' }}>
            Uploaded documents
          </h3>
          <span style={{ fontSize: '12px', color: '#9ca3af' }}>{documents.length} file{documents.length !== 1 ? 's' : ''}</span>
        </div>

        {documents.length === 0 ? (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            background: 'white',
            borderRadius: '10px',
            border: '1px dashed #e5e7eb',
            color: '#9ca3af',
            fontSize: '13px'
          }}>
            <FileText size={32} color="#d1d5db" style={{ margin: '0 auto 10px' }} />
            No documents yet
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {documents.map((doc, index) => (
              <div
                key={index}
                style={{
                  background: 'white',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  border: '1px solid #f3f4f6',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                  transition: 'box-shadow 0.15s'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
                  <div style={{
                    width: '38px',
                    height: '38px',
                    background: '#f5f3ff',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <File size={18} color="#8b5cf6" />
                  </div>
                  <div style={{ overflow: 'hidden' }}>
                    <p style={{
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#111827',
                      marginBottom: '2px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '480px'
                    }}>
                      {doc.filename}
                    </p>
                    <p style={{ fontSize: '11px', color: '#9ca3af' }}>
                      {formatFileSize(doc.size)} · {formatDate(doc.uploaded_at)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.filename)}
                  disabled={deletingFile === doc.filename}
                  title="Delete document"
                  style={{
                    padding: '7px',
                    background: 'transparent',
                    border: '1px solid #fee2e2',
                    borderRadius: '7px',
                    cursor: deletingFile === doc.filename ? 'not-allowed' : 'pointer',
                    color: deletingFile === doc.filename ? '#fca5a5' : '#ef4444',
                    display: 'flex',
                    flexShrink: 0,
                    transition: 'all 0.15s'
                  }}
                  onMouseEnter={(e) => { if (deletingFile !== doc.filename) e.currentTarget.style.background = '#fef2f2'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentUpload;
