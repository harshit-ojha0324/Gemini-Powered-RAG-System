// The backend sends naive ISO timestamps with microseconds; trim to milliseconds
// so every browser parses them (as local time, which is where the API runs).
export function parseDate(value) {
  if (!value) return null;
  const date = new Date(String(value).replace(/(\.\d{3})\d+/, '$1'));
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return '–';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(value) {
  const date = parseDate(value);
  if (!date) return '–';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(value) {
  const date = parseDate(value);
  if (!date) return '';
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' });
}

const relative = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });

export function formatRelativeTime(value, now = Date.now()) {
  const date = parseDate(value);
  if (!date) return '–';
  const seconds = Math.round((date.getTime() - now) / 1000);
  const abs = Math.abs(seconds);
  if (abs < 45) return 'Just now';
  if (abs < 3600) return relative.format(Math.round(seconds / 60), 'minute');
  if (abs < 86400) return relative.format(Math.round(seconds / 3600), 'hour');
  if (abs < 7 * 86400) return relative.format(Math.round(seconds / 86400), 'day');
  return formatDate(value);
}

export function plural(count, one, many = `${one}s`) {
  return `${count} ${count === 1 ? one : many}`;
}

/** "attention-is-all-you-need.pdf" -> "Attention is all you need" */
export function documentTitle(filename) {
  const base = filename
    .replace(/\.pdf$/i, '')
    .replace(/[-_]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return base ? base.charAt(0).toUpperCase() + base.slice(1) : filename;
}
