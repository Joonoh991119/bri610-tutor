const BASE = '/api';

// Per-browser user identity. The first time the app loads we mint a deterministic
// numeric user_id derived from a UUID seed (so multiple devices/sessions on the
// SAME browser share state, but different browsers/users are isolated).
function getUserId() {
  if (typeof localStorage === 'undefined') return 1;
  let id = localStorage.getItem('bri610.user_id');
  if (id) return Number(id);
  // Mint a fresh id: small int hashed from a UUID, then call /api/users/ensure
  const seed = (crypto.randomUUID && crypto.randomUUID()) ||
               (Math.random().toString(36).slice(2) + Date.now().toString(36));
  // Simple deterministic hash → 1..1_000_000
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = ((h << 5) - h + seed.charCodeAt(i)) | 0;
  id = String((Math.abs(h) % 999999) + 2);   // avoid id=1 collision with default seed
  localStorage.setItem('bri610.user_id', id);
  localStorage.setItem('bri610.user_seed', seed);
  // Fire-and-forget: backend creates the row if missing
  fetch(`${BASE}/users/ensure?user_id=${id}`, { method: 'POST' }).catch(() => {});
  return Number(id);
}

const USER_ID = getUserId();
export { USER_ID };

function appendUid(path) {
  // Append user_id query param if path doesn't already specify one
  if (path.includes('user_id=')) return path;
  const sep = path.includes('?') ? '&' : '?';
  return `${path}${sep}user_id=${USER_ID}`;
}

async function post(path, body) {
  const res = await fetch(`${BASE}${appendUid(path)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: USER_ID, ...(body || {}) }),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

async function get(path) {
  const res = await fetch(`${BASE}${appendUid(path)}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => get('/health'),
  lectures: () => get('/lectures'),
  dbStats: () => get('/db-stats'),
  search: (query, source = 'all', lecture = null, limit = 8) =>
    post('/search', { query, source, lecture, limit }),
  chat: (message, lecture = null, mode = 'auto', history = []) =>
    post('/chat', { message, lecture, mode, history }),
  quiz: (topic, lecture = null, num_questions = 5, difficulty = 'medium') =>
    post('/quiz', { topic, lecture, num_questions, difficulty }),
  exam: (lecture, duration_min = 60, total_points = 100) =>
    post('/exam', { lecture, duration_min, total_points }),
  summary: (lecture, focus = null) =>
    post('/summary', { lecture, focus }),
  grade: (question, answer, lecture = null) =>
    post('/grade', { question, answer, lecture }),
  cachedSummary: (lecture) => get(`/summaries/${lecture}`),
  generateSummary: (lecture) => post(`/summaries/${lecture}/generate`, {}),
  submitFeedback: (lecture, feedback) =>
    post(`/summaries/${lecture}/feedback`, { feedback }),
  slideImage: (lecture, page) => `/images/${lecture}/p${String(page).padStart(2, '0')}.jpg`,
  // v0.5
  v05Status:    () => get('/v05/status'),
  srsQueue:     (userId = 1, limit = 20) => get(`/srs/queue?user_id=${userId}&limit=${limit}`),
  srsReview:    (cardId, rating) => post('/srs/review', { card_id: cardId, rating }),
  bankNext:     (userId = 1, limit = 10) => get(`/bank/next?user_id=${userId}&limit=${limit}`),
  verify:       (lhs, rhs) => post('/verify', { lhs, rhs }),
  multiLens:    (text, opts = {}) => post('/review/multi-lens', { text, ...opts }),
  personaWrap:  (text, opts = {}) => post('/persona/wrap', { text, ...opts }),
  // v0.5 gamification
  me:           () => get('/me'),
  streakTouch:  (userId = 1) => post('/me/streak/touch', { user_id: userId }),
  masteryGrid:  (userId = 1) => get(`/me/mastery?user_id=${userId}`),
  // v0.5 Walkthrough
  walkthroughList:  () => get('/walkthrough/list'),
  walkthroughStart: (id, userId = 1) => post('/walkthrough/start', { walkthrough_id: id, user_id: userId }),
  walkthroughStep:  (sid, ui, latex = null) => post('/walkthrough/step', { session_id: sid, user_input: ui, latex_attempt: latex }),
  walkthroughState: (sid) => get(`/walkthrough/state/${sid}`),
  // v0.5 Lecture mode
  lectureList:    () => get('/lecture/list'),
  lectureStart:   (lectureId, userId = 1) => post('/lecture/start', { lecture_id: lectureId, user_id: userId }),
  lectureNarrate: (sid, expand = true) => post('/lecture/narrate', { session_id: sid, expand }),
  lectureAdvance: (sid) => post('/lecture/advance', { session_id: sid }),
  lectureSubmit:  (sid, answer) => post('/lecture/submit', { session_id: sid, answer }),
  // v0.7 pre-built bank (course-inheritance: summary + narration + quiz + take-home)
  quizBank:      (lecture) => get(`/quiz/bank/${lecture}`),
  takeHome:      (lecture) => get(`/take-home/${lecture}`),
  courseSlim:    (lecture) => get(`/course/${lecture}`),
  // 1-hour Course
  courseOverview: () => get('/course/overview'),
  courseStart:    (userId = 1) => post(`/course/start?user_id=${userId}`, {}),
  courseNext:     (runId) => get(`/course/next?run_id=${runId}`),
  courseAnswer:   (runId, qid, ans, timeS = 0) =>
    post('/course/answer', { run_id: runId, question_id: qid, user_answer: ans, time_spent_s: timeS }),
  courseRun:      (runId) => get(`/course/run/${runId}`),
};
