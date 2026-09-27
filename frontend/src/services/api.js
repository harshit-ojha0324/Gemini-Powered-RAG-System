import axios from 'axios';

// Set VITE_API_URL when the backend isn't on localhost:8000.
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// No default Content-Type: axios sends JSON for plain objects and multipart for
// FormData on its own. Forcing 'application/json' here made axios serialize
// PDF uploads as the JSON string {"file":{}}, which the backend rejects.
const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.message);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * A readable message for a failed request. FastAPI sends `detail` as a string
 * for HTTPException and as a list of `{ msg }` objects for validation errors.
 */
export function getErrorMessage(error, fallback = 'Something went wrong.') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => (typeof item === 'string' ? item : item?.msg)).filter(Boolean);
    if (messages.length) return messages.join('; ');
  }
  if (error?.request && !error?.response) {
    return `Can't reach the API at ${API_BASE_URL}. Check that the backend is running.`;
  }
  return fallback;
}

export default api;
