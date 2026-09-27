import { useRef, useState } from 'react';
import { FileText, FileUp, Trash2 } from 'lucide-react';
import UploadList from './UploadList';
import api, { API_BASE_URL, getErrorMessage } from '../services/api';
import { formatBytes, formatDate } from '../lib/format';
import './DocumentUpload.css';

function DocumentUpload({
  documents,
  libraryState,
  uploads,
  onUploadFiles,
  onChooseFiles,
  onDismissUpload,
  onDocumentsChanged,
}) {
  const [dragActive, setDragActive] = useState(false);
  const dragDepth = useRef(0);
  const libraryHeading = useRef(null);
  const [confirming, setConfirming] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [refocus, setRefocus] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  // Count enter/leave pairs so moving over child elements doesn't flicker the highlight.
  const onDragEnter = (event) => {
    event.preventDefault();
    dragDepth.current += 1;
    setDragActive(true);
  };
  const onDragLeave = () => {
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragActive(false);
  };
  const onDrop = (event) => {
    event.preventDefault();
    dragDepth.current = 0;
    setDragActive(false);
    onUploadFiles(event.dataTransfer.files);
  };

  const cancelDelete = (filename) => {
    setConfirming(null);
    setRefocus(filename);
  };

  const deleteDocument = async (filename) => {
    setDeleting(filename);
    setDeleteError(null);
    try {
      await api.delete(`/api/documents/${encodeURIComponent(filename)}`);
      onDocumentsChanged();
      // The row (and the focused button in it) is about to disappear.
      libraryHeading.current?.focus();
    } catch (error) {
      setDeleteError(`Couldn't delete ${filename}. ${getErrorMessage(error, '')}`.trim());
    } finally {
      setDeleting(null);
      setConfirming(null);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>Documents</h1>
        <p>
          PDFs you add are split into passages and indexed for search. Answers cite the pages those
          passages came from.
        </p>
      </header>

      <div
        className={`dropzone${dragActive ? ' is-active' : ''}`}
        onDragEnter={onDragEnter}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <FileUp size={22} className="dropzone-icon" aria-hidden="true" />
        <div className="dropzone-text">
          <p className="dropzone-title">{dragActive ? 'Drop to upload' : 'Drop PDFs here'}</p>
          <p className="dropzone-hint">PDF files only. Each one is indexed as soon as it uploads.</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={onChooseFiles}>
          Choose files
        </button>
      </div>

      {uploads.length > 0 && <UploadList uploads={uploads} onDismiss={onDismissUpload} />}

      <section className="library" aria-labelledby="library-title">
        <h2 className="section-title" id="library-title" ref={libraryHeading} tabIndex={-1}>
          Library
          {libraryState === 'ready' && <span className="count">{documents.length}</span>}
        </h2>

        {deleteError && (
          <p className="library-error" role="alert">
            {deleteError}
          </p>
        )}

        {libraryState === 'error' && !documents.length ? (
          <p className="empty-inline">Can&apos;t load documents. Nothing is answering at {API_BASE_URL}.</p>
        ) : libraryState === 'ready' && !documents.length ? (
          <p className="empty-inline">No documents yet. Files you add above appear here once they&apos;re indexed.</p>
        ) : (
          documents.length > 0 && (
            <table className="table doc-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col" className="num">
                    Size
                  </th>
                  <th scope="col" className="doc-added">
                    Added
                  </th>
                  <th scope="col">
                    <span className="visually-hidden">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) =>
                  confirming === doc.filename ? (
                    // The confirmation takes over the whole row so the columns don't shift.
                    <tr key={doc.filename} className="confirm-row">
                      <td colSpan={4}>
                        <div className="confirm">
                          <p className="confirm-text">
                            Delete <strong>{doc.filename}</strong>? Its passages are removed from search too.
                          </p>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => cancelDelete(doc.filename)}
                            autoFocus
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            onClick={() => deleteDocument(doc.filename)}
                            disabled={deleting === doc.filename}
                          >
                            {deleting === doc.filename ? 'Deleting…' : 'Delete'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    <tr key={doc.filename}>
                      <td className="doc-name-cell">
                        <div className="doc-name">
                          <FileText size={16} aria-hidden="true" />
                          <span title={doc.filename}>{doc.filename}</span>
                        </div>
                      </td>
                      <td className="num doc-size">{formatBytes(doc.size)}</td>
                      <td className="doc-added">{formatDate(doc.uploaded_at)}</td>
                      <td className="doc-actions">
                        <button
                          type="button"
                          className="icon-btn"
                          aria-label={`Delete ${doc.filename}`}
                          title="Delete"
                          onClick={() => setConfirming(doc.filename)}
                          autoFocus={refocus === doc.filename}
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          )
        )}
      </section>
    </div>
  );
}

export default DocumentUpload;
