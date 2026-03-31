const BASE = '/api';

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => get('/health'),
  lectures: () => get('/lectures'),
  search: (query, source = 'all', lecture = null, limit = 8) =>
    post('/search', { query, source, lecture, limit }),
  chat: (message, lecture = null, mode = 'tutor', history = []) =>
    post('/chat', { message, lecture, mode, history }),
  quiz: (topic, lecture = null, num_questions = 5, difficulty = 'medium') =>
    post('/quiz', { topic, lecture, num_questions, difficulty }),
  summary: (lecture, focus = null) =>
    post('/summary', { lecture, focus }),
  slideImage: (lecture, page) => `/images/${lecture}/p${String(page).padStart(2, '0')}.jpg`,
};
