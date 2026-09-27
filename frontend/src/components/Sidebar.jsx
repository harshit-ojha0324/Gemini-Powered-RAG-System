import Logo from './Logo';
import { API_BASE_URL } from '../services/api';

const STATUS_TEXT = {
  checking: 'Checking API',
  online: 'API connected',
  offline: "Can't reach API",
};

const apiHost = (() => {
  try {
    return new URL(API_BASE_URL).host;
  } catch {
    return API_BASE_URL;
  }
})();

export function ApiStatus({ status, compact = false }) {
  if (compact) {
    return (
      <span className="status-dot" data-state={status} role="img" aria-label={STATUS_TEXT[status]} title={STATUS_TEXT[status]} />
    );
  }
  return (
    <div className="status" role="status">
      <span className="status-dot" data-state={status} aria-hidden="true" />
      <span>{STATUS_TEXT[status]}</span>
      <span className="status-host">{apiHost}</span>
    </div>
  );
}

function Sidebar({ views, current, counts, onNavigate, apiStatus, className = '' }) {
  return (
    <aside className={`sidebar ${className}`}>
      <div className="brand">
        <Logo size={26} />
        <span>Doc Q&amp;A</span>
      </div>

      <nav className="nav" aria-label="Main">
        {views.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className="nav-item"
            aria-current={current === id ? 'page' : undefined}
            onClick={() => onNavigate(id)}
          >
            <Icon size={16} aria-hidden="true" />
            <span>{label}</span>
            {counts[id] > 0 && <span className="nav-count">{counts[id]}</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <ApiStatus status={apiStatus} />
      </div>
    </aside>
  );
}

export default Sidebar;
