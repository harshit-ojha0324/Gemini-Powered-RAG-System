import { createContext, memo, useContext, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AlertCircle, AlertTriangle, Check, ChevronRight, Copy, FileText, RotateCcw, ShieldAlert } from 'lucide-react';
import rehypeEvidence from '../lib/evidence';
import { describeWarnings } from '../lib/security';
import { scrollBehavior } from '../lib/motion';
import './MessageBubble.css';

// Lets the citation chips inside the rendered markdown reach the answer's
// source list without remounting the markdown on every click.
const EvidenceContext = createContext({ activePage: null, showPage: () => {} });

function Cite(props) {
  const { activePage, showPage } = useContext(EvidenceContext);
  const page = props['data-page'];
  if (props['data-linked'] !== 'true') {
    return <span className="cite cite-unlinked">{props.children}</span>;
  }
  return (
    <button
      type="button"
      className="cite"
      aria-pressed={activePage === page}
      aria-label={`Show the passage from page ${page}`}
      onClick={() => showPage(page)}
    >
      {props.children}
    </button>
  );
}

function Redaction() {
  return <span className="redaction" role="img" aria-label="Redacted" />;
}

function Link({ href, children }) {
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  );
}

const MARKDOWN_COMPONENTS = { cite: Cite, redaction: Redaction, a: Link };

// The backend cuts passages at 200 characters and always appends "...".
// Show an ellipsis only when the passage doesn't already end a sentence.
function cleanExcerpt(text = '') {
  const passage = text.replace(/\s+/g, ' ').trim().replace(/\.\.\.$/, '').trimEnd();
  return /[.!?]$/.test(passage) ? passage : `${passage}…`;
}

function pageLabel(page) {
  return /^\d+$/.test(String(page)) ? `p. ${page}` : '';
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard access can be refused (e.g. outside a secure context); nothing to do.
    }
  };
  return (
    <button type="button" className="btn btn-ghost btn-sm" onClick={copy}>
      {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function Sources({ sources, activePage, open, onToggle, listRef }) {
  const groups = useMemo(() => {
    const byDocument = new Map();
    for (const source of sources) {
      const name = source.source || 'Unknown document';
      if (!byDocument.has(name)) byDocument.set(name, []);
      byDocument.get(name).push(source);
    }
    for (const list of byDocument.values()) {
      list.sort((a, b) => (Number(a.page) || 0) - (Number(b.page) || 0));
    }
    return [...byDocument.entries()];
  }, [sources]);

  return (
    <details className="sources" open={open} onToggle={(event) => onToggle(event.currentTarget.open)} ref={listRef}>
      <summary>
        <ChevronRight size={14} className="sources-chevron" aria-hidden="true" />
        Sources
        <span className="sources-count">{sources.length}</span>
      </summary>
      {groups.map(([name, items]) => (
        <div className="source-group" key={name}>
          <p className="source-doc">
            <FileText size={13} aria-hidden="true" />
            <span>{name}</span>
          </p>
          <ul className="source-list">
            {items.map((source, index) => (
              <li
                key={index}
                className={`source${activePage === String(source.page) ? ' is-active' : ''}`}
                data-page={source.page}
              >
                <span className="source-page">{pageLabel(source.page)}</span>
                <p className="source-text">
                  <span className="source-quote">{cleanExcerpt(source.content)}</span>
                </p>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </details>
  );
}

function Answer({ message }) {
  const sources = message.sources || [];
  const [activePage, setActivePage] = useState(null);
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const sourcesRef = useRef(null);
  const notices = useMemo(() => describeWarnings(message.warnings), [message.warnings]);
  const pages = useMemo(() => [...new Set(sources.map((source) => String(source.page)))], [sources]);

  const showPage = (page) => {
    const next = activePage === page ? null : page;
    setActivePage(next);
    if (!next) return;
    setSourcesOpen(true);
    requestAnimationFrame(() => {
      sourcesRef.current
        ?.querySelector(`.source[data-page="${CSS.escape(page)}"]`)
        ?.scrollIntoView({ block: 'nearest', behavior: scrollBehavior() });
    });
  };

  // Parse the markdown once per answer; chip state flows through context.
  const body = useMemo(
    () => (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeEvidence, { pages }]]}
        components={MARKDOWN_COMPONENTS}
        skipHtml
      >
        {message.content}
      </ReactMarkdown>
    ),
    [message.content, pages]
  );

  return (
    <article className="answer">
      {notices.map((notice, index) => (
        <p key={index} className={`notice notice-${notice.kind}`}>
          {notice.kind === 'redacted' ? (
            <span className="redaction notice-bar" aria-hidden="true" />
          ) : (
            <AlertTriangle size={14} aria-hidden="true" />
          )}
          <span>{notice.text}</span>
        </p>
      ))}

      <EvidenceContext.Provider value={{ activePage, showPage }}>
        <div className="answer-body">{body}</div>
      </EvidenceContext.Provider>

      {sources.length > 0 && (
        <Sources
          sources={sources}
          activePage={activePage}
          open={sourcesOpen}
          onToggle={setSourcesOpen}
          listRef={sourcesRef}
        />
      )}

      <div className="answer-actions">
        <CopyButton text={message.content} />
      </div>
    </article>
  );
}

function BlockedReply({ onNavigate }) {
  return (
    <div className="reply-callout reply-blocked">
      <ShieldAlert size={18} aria-hidden="true" />
      <div>
        <p className="callout-title">Blocked by the security filter</p>
        <p>
          This question matched an injection pattern (SQL, script, or instructions aimed at the
          assistant), so it was never sent to Gemini. Rephrase it as a plain question about your
          documents.
        </p>
        <button type="button" className="link-btn" onClick={() => onNavigate('security')}>
          View security log
        </button>
      </div>
    </div>
  );
}

function FailedReply({ message, onRetry }) {
  return (
    <div className="reply-callout reply-failed">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <p className="callout-title">Couldn&apos;t get an answer</p>
        <p>{message.content}</p>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => onRetry(message.id)}>
          <RotateCcw size={14} aria-hidden="true" />
          Try again
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ message, anchorRef, onRetry, onNavigate }) {
  if (message.role === 'user') {
    return (
      <h2 className="question" ref={anchorRef}>
        {message.content}
      </h2>
    );
  }
  if (message.status === 'blocked') return <BlockedReply onNavigate={onNavigate} />;
  if (message.status === 'error') return <FailedReply message={message} onRetry={onRetry} />;
  return <Answer message={message} />;
}

export default memo(MessageBubble);
