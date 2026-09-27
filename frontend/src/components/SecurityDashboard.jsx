import { useEffect, useState } from 'react';
import api, { API_BASE_URL } from '../services/api';
import { formatDateTime, formatRelativeTime } from '../lib/format';
import { eventOutcome, flagLabel, outcomeLabel, splitRedactions } from '../lib/security';
import './SecurityDashboard.css';

const POLL_MS = 5000;

function RedactedText({ text }) {
  return splitRedactions(text).map((part, index) =>
    part.redacted ? (
      <span key={index} className="redaction" role="img" aria-label="Redacted" />
    ) : (
      <span key={index}>{part.text}</span>
    )
  );
}

function Figure({ label, value }) {
  return (
    <div className="figure">
      <dt>{label}</dt>
      <dd>{value ?? '–'}</dd>
    </div>
  );
}

function SecurityDashboard({ stats, onRefreshStats }) {
  const [events, setEvents] = useState([]);
  const [state, setState] = useState('loading');
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      onRefreshStats();
      try {
        const { data } = await api.get('/api/security/logs', { params: { limit: 50 } });
        if (cancelled) return;
        setEvents(data.logs || []);
        setState('ready');
      } catch {
        if (!cancelled) setState((current) => (current === 'ready' ? current : 'error'));
      }
      if (!cancelled) setNow(Date.now());
    };

    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [onRefreshStats]);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Security</h1>
        <p>
          Every question is screened before it reaches Gemini. Injection attempts are blocked, and personal
          data such as email addresses and phone numbers is redacted.
        </p>
      </header>

      <dl className="figures">
        <Figure label="Questions asked" value={stats?.total_queries} />
        <Figure label="Flagged events" value={stats?.security_incidents} />
        <Figure label="PII redactions" value={stats?.pii_detections} />
      </dl>
      <p className="figures-note">Counts since the API last started. The event log below is kept on disk.</p>

      <section className="events" aria-labelledby="events-title">
        <h2 className="section-title" id="events-title">
          Event log
          {state === 'ready' && <span className="count">{events.length}</span>}
        </h2>

        {state === 'error' && (
          <p className="empty-inline">
            Can&apos;t load the event log. Nothing is answering at {API_BASE_URL}; this page retries every few
            seconds.
          </p>
        )}

        {state === 'ready' && !events.length && (
          <p className="empty-inline">
            No flagged questions yet. Questions that trip the injection filter or contain personal data are
            recorded here.
          </p>
        )}

        {state === 'ready' && events.length > 0 && (
          <table className="table event-table">
            <thead>
              <tr>
                <th scope="col">When</th>
                <th scope="col">Question</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, index) => {
                const outcome = eventOutcome(event);
                return (
                  <tr key={`${event.timestamp}-${index}`}>
                    <td className="event-when">
                      <time dateTime={event.timestamp} title={formatDateTime(event.timestamp)}>
                        {formatRelativeTime(event.timestamp, now)}
                      </time>
                    </td>
                    <td className="event-question">
                      <div className="event-question-text">
                        <RedactedText text={event.query} />
                      </div>
                    </td>
                    <td className="event-result">
                      <span className={`tag tag-${outcome}`}>{outcomeLabel(outcome)}</span>
                      <span className="event-flags">{(event.flags || []).map(flagLabel).join(', ')}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

export default SecurityDashboard;
