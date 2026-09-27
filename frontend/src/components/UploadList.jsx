import { AlertCircle, CheckCircle2, Clock, Loader2, X } from 'lucide-react';
import './UploadList.css';

function UploadIcon({ status }) {
  if (status === 'done') return <CheckCircle2 size={16} className="upload-icon" aria-hidden="true" />;
  if (status === 'error') return <AlertCircle size={16} className="upload-icon" aria-hidden="true" />;
  if (status === 'queued') return <Clock size={16} className="upload-icon" aria-hidden="true" />;
  return <Loader2 size={16} className="upload-icon spin" aria-hidden="true" />;
}

function UploadList({ uploads, onDismiss }) {
  return (
    <ul className="upload-list" aria-live="polite">
      {uploads.map((upload) => (
        <li key={upload.id} className="upload" data-status={upload.status}>
          <UploadIcon status={upload.status} />
          <span className="upload-name" title={upload.name}>
            {upload.name}
          </span>
          <span className="upload-message">{upload.message}</span>
          {upload.status === 'error' && (
            <button
              type="button"
              className="icon-btn icon-btn-sm upload-dismiss"
              aria-label={`Dismiss ${upload.name}`}
              onClick={() => onDismiss(upload.id)}
            >
              <X size={14} aria-hidden="true" />
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}

export default UploadList;
