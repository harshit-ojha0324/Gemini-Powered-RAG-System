import { useCallback, useEffect, useRef, useState } from 'react';
import { FileText, Menu, MessageSquare, Plus, Shield } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import SecurityDashboard from './components/SecurityDashboard';
import Sidebar, { ApiStatus } from './components/Sidebar';
import useApiStatus from './hooks/useApiStatus';
import useConversation from './hooks/useConversation';
import useUploads from './hooks/useUploads';
import api from './services/api';
import './App.css';

const VIEWS = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'security', label: 'Security', icon: Shield },
];

const STATS_POLL_MS = 10000;
// Keep in sync with the 860px breakpoint in App.css.
const DOCKED_SIDEBAR_QUERY = '(min-width: 861px)';

function Drawer({ onClose, returnFocusRef, children }) {
  const panelRef = useRef(null);

  useEffect(() => {
    const panel = panelRef.current;
    (panel?.querySelector('[aria-current="page"]') || panel?.querySelector('button'))?.focus();
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    // The drawer only exists on small screens; close it if the window widens.
    const docked = window.matchMedia(DOCKED_SIDEBAR_QUERY);
    const onResize = () => docked.matches && onClose();
    document.addEventListener('keydown', onKeyDown);
    docked.addEventListener('change', onResize);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      docked.removeEventListener('change', onResize);
      // Opening the drawer makes the page behind it inert, which blurs the menu
      // button, so the button is passed in rather than read from activeElement.
      returnFocusRef.current?.focus();
    };
  }, [onClose, returnFocusRef]);

  return (
    <div className="drawer-layer">
      <div className="drawer-backdrop" onClick={onClose} />
      <div className="drawer" ref={panelRef} role="dialog" aria-modal="true" aria-label="Navigation">
        {children}
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState('chat');
  const [documents, setDocuments] = useState([]);
  const [libraryState, setLibraryState] = useState('loading');
  const [stats, setStats] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const fileInput = useRef(null);
  const menuButton = useRef(null);
  const apiStatus = useApiStatus();

  const loadDocuments = useCallback(async () => {
    try {
      const { data } = await api.get('/api/documents');
      const newestFirst = [...data.documents].sort((a, b) =>
        String(b.uploaded_at).localeCompare(String(a.uploaded_at))
      );
      setDocuments(newestFirst);
      setLibraryState('ready');
    } catch {
      setLibraryState((state) => (state === 'ready' ? state : 'error'));
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const { data } = await api.get('/api/stats');
      setStats(data.statistics);
    } catch {
      // Keep the last known counts; the status indicator reports the outage.
    }
  }, []);

  const refreshLibrary = useCallback(() => {
    loadDocuments();
    loadStats();
  }, [loadDocuments, loadStats]);

  // Load once the first health check settles, and again whenever the API comes back.
  useEffect(() => {
    if (apiStatus !== 'checking') refreshLibrary();
  }, [apiStatus, refreshLibrary]);

  useEffect(() => {
    const timer = setInterval(loadStats, STATS_POLL_MS);
    return () => clearInterval(timer);
  }, [loadStats]);

  const { uploads, upload, dismiss } = useUploads(refreshLibrary);
  const conversation = useConversation({ onSettled: loadStats });

  const chooseFiles = useCallback(() => fileInput.current?.click(), []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const navigate = useCallback((id) => {
    setView(id);
    setDrawerOpen(false);
  }, []);

  const sidebarProps = {
    views: VIEWS,
    current: view,
    counts: { documents: documents.length, security: stats?.security_incidents ?? 0 },
    onNavigate: navigate,
    apiStatus,
  };

  return (
    <div className="app">
      <Sidebar {...sidebarProps} className="sidebar-docked" />

      <div className="main" inert={drawerOpen ? '' : undefined}>
        <header className="topbar">
          <button
            type="button"
            className="icon-btn"
            ref={menuButton}
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={18} aria-hidden="true" />
          </button>
          <span className="topbar-title">{VIEWS.find((item) => item.id === view).label}</span>
          {view === 'chat' && conversation.messages.length > 0 && (
            <button type="button" className="icon-btn" onClick={conversation.reset} aria-label="New chat" title="New chat">
              <Plus size={18} aria-hidden="true" />
            </button>
          )}
          <ApiStatus status={apiStatus} compact />
        </header>

        <main className="view">
          {view === 'chat' && (
            <ChatInterface
              documents={documents}
              libraryState={libraryState}
              apiStatus={apiStatus}
              conversation={conversation}
              uploads={uploads}
              onChooseFiles={chooseFiles}
              onDismissUpload={dismiss}
              onNavigate={navigate}
            />
          )}
          {view === 'documents' && (
            <DocumentUpload
              documents={documents}
              libraryState={libraryState}
              uploads={uploads}
              onUploadFiles={upload}
              onChooseFiles={chooseFiles}
              onDismissUpload={dismiss}
              onDocumentsChanged={refreshLibrary}
            />
          )}
          {view === 'security' && <SecurityDashboard stats={stats} onRefreshStats={loadStats} />}
        </main>
      </div>

      {drawerOpen && (
        <Drawer onClose={closeDrawer} returnFocusRef={menuButton}>
          <Sidebar {...sidebarProps} />
        </Drawer>
      )}

      <input
        ref={fileInput}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        hidden
        onChange={(event) => {
          upload(event.target.files);
          event.target.value = '';
        }}
      />
    </div>
  );
}

export default App;
