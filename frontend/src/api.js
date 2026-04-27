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
  // 1-hour Course
  courseOverview: () => get('/course/overview'),
  courseStart:    (userId = 1) => post(`/course/start?user_id=${userId}`, {}),
  courseNext:     (runId) => get(`/course/next?run_id=${runId}`),
  courseAnswer:   (runId, qid, ans, timeS = 0) =>
    post('/course/answer', { run_id: runId, question_id: qid, user_answer: ans, time_spent_s: timeS }),
  courseRun:      (runId) => get(`/course/run/${runId}`),
};
