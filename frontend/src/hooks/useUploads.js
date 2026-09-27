import { useCallback, useRef, useState } from 'react';
import api, { getErrorMessage } from '../services/api';
import { plural } from '../lib/format';

const DONE_VISIBLE_MS = 6000;

const isPdf = (file) => file.type === 'application/pdf' || /\.pdf$/i.test(file.name);

/**
 * Uploads PDFs one at a time and tracks each file's progress. Lives in App so
 * uploads keep going while the user moves between views.
 */
export default function useUploads(onUploaded) {
  const [uploads, setUploads] = useState([]);
  const nextId = useRef(0);
  const queue = useRef(Promise.resolve());

  const update = useCallback((id, patch) => {
    setUploads((list) => list.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }, []);

  const dismiss = useCallback((id) => {
    setUploads((list) => list.filter((item) => item.id !== id));
  }, []);

  const upload = useCallback(
    (fileList) => {
      const files = Array.from(fileList || []);
      if (!files.length) return;

      const entries = files.map((file) => ({ id: (nextId.current += 1), file, accepted: isPdf(file) }));
      setUploads((list) => [
        ...list,
        ...entries.map(({ id, file, accepted }) => ({
          id,
          name: file.name,
          status: accepted ? 'queued' : 'error',
          message: accepted ? 'Waiting…' : 'Only PDF files can be added.',
        })),
      ]);

      for (const entry of entries.filter((item) => item.accepted)) {
        queue.current = queue.current.then(async () => {
          update(entry.id, { status: 'uploading', message: 'Uploading and indexing…' });
          try {
            const form = new FormData();
            form.append('file', entry.file);
            const { data } = await api.post('/api/upload', form);
            update(entry.id, { status: 'done', message: `Indexed ${plural(data.chunks, 'passage')}` });
            setTimeout(() => dismiss(entry.id), DONE_VISIBLE_MS);
          } catch (error) {
            update(entry.id, { status: 'error', message: getErrorMessage(error, 'Upload failed.') });
          }
          // Refresh even after a failure: the backend may have stored the file anyway.
          onUploaded?.();
        });
      }
    },
    [dismiss, onUploaded, update]
  );

  return { uploads, upload, dismiss };
}
