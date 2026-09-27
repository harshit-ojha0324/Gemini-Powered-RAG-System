import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { FileUp, Loader2, Plus } from 'lucide-react';
import MessageBubble from './MessageBubble';
import UploadList from './UploadList';
import { documentTitle, plural } from '../lib/format';
import { scrollBehavior } from '../lib/motion';
import { API_BASE_URL } from '../services/api';
import './ChatInterface.css';

const MAX_INPUT_HEIGHT = 200;

function EmptyState({ documents, libraryState, apiStatus, uploads, onChooseFiles, onDismissUpload, onAsk }) {
  if (libraryState === 'loading') return null;

  if (!documents.length && (apiStatus === 'offline' || libraryState === 'error')) {
    return (
      <div className="empty">
        <h2 className="empty-title">Can&apos;t reach the API</h2>
        <p className="empty-text">
          Nothing is answering at {API_BASE_URL}. Start the backend with <code>make start</code> and this
          page reconnects on its own.
        </p>
      </div>
    );
  }

  if (!documents.length) {
    return (
      <div className="empty">
        <h2 className="empty-title">Add a PDF to get started</h2>
        <p className="empty-text">
          Upload a document, then ask questions about it. Gemini answers from the passages it finds and
          cites the page each one came from.
        </p>
        <button type="button" className="btn btn-primary" onClick={onChooseFiles}>
          <FileUp size={16} aria-hidden="true" />
          Upload PDF
        </button>
        {uploads.length > 0 && <UploadList uploads={uploads} onDismiss={onDismissUpload} />}
      </div>
    );
  }

  const library = documents.length === 1 ? 'your PDF' : `your ${documents.length} PDFs`;
  const suggestions = [
    `Summarize “${documentTitle(documents[0].filename)}”`,
    'What are the main conclusions?',
    documents.length === 1 ? 'Which methods or data does it rely on?' : 'Where do these documents agree or disagree?',
  ];

  return (
    <div className="empty">
      <h2 className="empty-title">Ask about your documents</h2>
      <p className="empty-text">
        Gemini answers from passages in {library} and cites the page each one came from.
      </p>
      <ul className="suggestions" aria-label="Suggested questions">
        {suggestions.map((suggestion) => (
          <li key={suggestion}>
            <button type="button" className="suggestion" onClick={() => onAsk(suggestion)}>
              {suggestion}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChatInterface({
  documents,
  libraryState,
  apiStatus,
  conversation,
  uploads,
  onChooseFiles,
  onDismissUpload,
  onNavigate,
}) {
  const { messages, pending, ask, reset, retry } = conversation;
  const [draft, setDraft] = useState('');
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const lastQuestionRef = useRef(null);
  const hasDocuments = documents.length > 0;
  let lastQuestionId;
  for (const message of messages) {
    if (message.role === 'user') lastQuestionId = message.id;
  }

  // A new question scrolls to the bottom (where the progress line is); an answer
  // brings its question to the top so reading starts at the beginning.
  useEffect(() => {
    const last = messages[messages.length - 1];
    if (!last) return;
    if (last.role === 'user') {
      const scroller = scrollRef.current;
      scroller?.scrollTo({ top: scroller.scrollHeight, behavior: scrollBehavior() });
    } else {
      lastQuestionRef.current?.scrollIntoView({ block: 'start', behavior: scrollBehavior() });
    }
  }, [messages]);

  useLayoutEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, MAX_INPUT_HEIGHT)}px`;
  }, [draft]);

  const submit = (text) => {
    if (!hasDocuments || pending || !text.trim()) return;
    setDraft('');
    ask(text);
  };

  const askSuggestion = (text) => {
    ask(text);
    inputRef.current?.focus();
  };

  const onKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit(draft);
    }
  };

  const offline = apiStatus === 'offline' || libraryState === 'error';
  const placeholder = !hasDocuments
    ? offline
      ? "Can't reach the API"
      : 'Add a PDF to start asking questions'
    : documents.length === 1
      ? 'Ask about your document'
      : `Ask about your ${documents.length} documents`;

  return (
    <div className="chat">
      <h1 className="visually-hidden">Chat</h1>

      {messages.length > 0 && (
        <button type="button" className="btn btn-secondary btn-sm chat-new" onClick={reset}>
          <Plus size={15} aria-hidden="true" />
          New chat
        </button>
      )}

      <div className="chat-scroll" ref={scrollRef}>
        <div className="chat-column">
          {messages.length === 0 ? (
            <EmptyState
              documents={documents}
              libraryState={libraryState}
              apiStatus={apiStatus}
              uploads={uploads}
              onChooseFiles={onChooseFiles}
              onDismissUpload={onDismissUpload}
              onAsk={askSuggestion}
            />
          ) : (
            <div className="transcript" role="log" aria-live="polite" aria-busy={pending}>
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  anchorRef={message.id === lastQuestionId ? lastQuestionRef : undefined}
                  onRetry={retry}
                  onNavigate={onNavigate}
                />
              ))}
              {pending && (
                <p className="pending" role="status">
                  <Loader2 size={15} className="spin" aria-hidden="true" />
                  Searching {plural(documents.length, 'document')}…
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <form
        className="composer-wrap"
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        <div className="composer" data-disabled={!hasDocuments || undefined}>
          <label htmlFor="question" className="visually-hidden">
            Question
          </label>
          <textarea
            id="question"
            ref={inputRef}
            rows={1}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            disabled={!hasDocuments}
          />
          <button
            type="submit"
            className="btn btn-primary composer-send"
            disabled={!hasDocuments || pending || !draft.trim()}
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInterface;
