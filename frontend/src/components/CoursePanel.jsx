import { useState, useEffect, useRef } from 'react'
import { Play, Clock, Target, ChevronRight, CheckCircle2, XCircle, Trophy, RotateCcw, BookOpen, GraduationCap, FileQuestion, ClipboardList, Star, Zap } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

/**
 * StudyGuide — compact, per-lecture inheritance card (summary + lecture +
 * quiz + take-home). Implements user mandate v0.7:
 *   "코스에 서머리와 강의와 퀴즈를 상속시켜서 컴팩트한 학습 가이드"
 *
 * Each row queries /api/course/{lecture} for narration / quiz / take-home
 * counts and offers one-click navigation to the corresponding tab.
 */
function LectureRow({ lecture, onOpenCore }) {
  const [data, setData] = useState(null)
  useEffect(() => {
    api.courseSlim(lecture).then(setData).catch(() => setData({}))
  }, [lecture])

  const goTo = (tab, lec) => {
    try { localStorage.setItem(`bri610.${tab}.lecture`, lec) } catch {}
    window.location.hash = tab
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-3 mb-2">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-text-bright">{lecture}</span>
        <span className="text-[10px] text-text-dim" style={{ fontVariantNumeric: 'tabular-nums' }}>
          요약 {data ? Math.round((data.summary?.length || 0) / 1000) : '-'}k자 ·
          나레이션 {data?.narration_steps ?? '-'}단계 ·
          퀴즈 {data?.quiz_n ?? '-'}문항 ·
          논술 {data?.take_home_n ?? '-'}문항
        </span>
      </div>
      <div className="grid grid-cols-6 gap-1.5">
        <button onClick={() => onOpenCore(lecture)} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-accent/10 text-accent hover:bg-accent/20 transition-colors">
          <Star size={14} /> 핵심
        </button>
        <button onClick={() => goTo('summary', lecture)} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-surface-2 hover:bg-accent/10 hover:text-accent transition-colors">
          <BookOpen size={14} /> 서머리
        </button>
        <button onClick={() => goTo('lecture', lecture)} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-surface-2 hover:bg-accent/10 hover:text-accent transition-colors">
          <GraduationCap size={14} /> 강의
        </button>
        <button onClick={() => goTo('quiz', lecture)} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-surface-2 hover:bg-accent/10 hover:text-accent transition-colors">
          <FileQuestion size={14} /> 퀴즈
        </button>
        <button onClick={() => onOpenCore(lecture, 'recall')} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-surface-2 hover:bg-accent/10 hover:text-accent transition-colors">
          <Zap size={14} /> 암기
        </button>
        <button onClick={() => goTo('quiz', lecture)} className="flex flex-col items-center gap-1 px-2 py-2 rounded text-[11px] bg-surface-2 hover:bg-accent/10 hover:text-accent transition-colors">
          <ClipboardList size={14} /> 논술
        </button>
      </div>
    </div>
  )
}

// ─── Core summary modal: 1-page exam-ready + must-memorize + recall quiz ──

function CoreSummaryModal({ lecture, view, onClose }) {
  const [core, setCore] = useState(null)
  const [recall, setRecall] = useState(null)
  const [tab, setTab] = useState(view || 'core') // 'core' | 'recall'
  const [answers, setAnswers] = useState({})
  const [revealed, setRevealed] = useState({})

  useEffect(() => {
    api.coreSummary(lecture).then(setCore).catch(() => setCore({ error: true }))
    api.recallQuiz(lecture).then(setRecall).catch(() => setRecall({ items: [] }))
  }, [lecture])

  if (!core) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-bg rounded-xl border border-border max-w-3xl w-full max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-bg border-b border-border p-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-text-bright">{lecture} 핵심</h2>
            <p className="text-xs text-text-dim mt-0.5">{core.title}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="inline-flex rounded border border-border overflow-hidden">
              <button onClick={() => setTab('core')} className={`px-3 py-1.5 text-xs ${tab === 'core' ? 'bg-accent text-bg' : 'bg-surface-2'}`}>핵심요약</button>
              <button onClick={() => setTab('recall')} className={`px-3 py-1.5 text-xs border-l border-border ${tab === 'recall' ? 'bg-accent text-bg' : 'bg-surface-2'}`}>암기 퀴즈</button>
            </div>
            <button onClick={onClose} className="text-text-dim hover:text-text">✕</button>
          </div>
        </div>

        <div className="p-5">
          {tab === 'core' && (
            <>
              <blockquote className="border-l-2 border-accent pl-3 mb-4 text-sm italic text-text-bright">
                {core.one_line}
              </blockquote>
              <div className="markdown-body text-sm mb-5"><Markdown>{core.summary_md}</Markdown></div>
              <h3 className="text-sm font-semibold text-text-bright mb-2 mt-4 flex items-center gap-2">
                <Star size={14} className="text-accent" /> 필수 암기 ({(core.must_memorize || []).length})
              </h3>
              <ol className="space-y-1.5 text-xs list-decimal list-inside">
                {(core.must_memorize || []).map((m, i) => (
                  <li key={i} className="text-text">
                    <span className="font-medium markdown-body inline"><Markdown>{m.fact}</Markdown></span>
                    {m.hint && <span className="text-text-dim"> — {m.hint}</span>}
                    {m.slide_ref && <span className="text-[10px] text-text-dim ml-1">[{m.slide_ref}]</span>}
                  </li>
                ))}
              </ol>
            </>
          )}

          {tab === 'recall' && recall && (
            <div className="space-y-4">
              {(recall.items || []).map(q => {
                const v = answers[q.id]
                const reveal = revealed[q.id]
                const ok = reveal && (q.accept_patterns || []).some(p => {
                  try { return new RegExp(p).test(v || '') } catch { return false }
                })
                return (
                  <div key={q.id} className="rounded-lg border border-border-soft p-3">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] uppercase text-text-dim">recall · D{q.difficulty}</span>
                      <span className="text-[10px] text-text-dim italic">#{q.fact_tag}</span>
                      {q.slide_ref && <span className="text-[10px] text-text-dim ml-auto">[{q.slide_ref}]</span>}
                    </div>
                    <div className="markdown-body text-sm mb-2"><Markdown>{q.prompt}</Markdown></div>
                    <input
                      value={v || ''}
                      onChange={e => !reveal && setAnswers(p => ({ ...p, [q.id]: e.target.value }))}
                      disabled={reveal}
                      placeholder="답 입력..."
                      className={`w-full bg-surface-2 border rounded px-3 py-2 text-sm focus:outline-none ${reveal ? (ok ? 'border-success' : 'border-error') : 'border-border focus:border-accent/50'}`}
                    />
                    <div className="mt-2 flex items-center gap-2">
                      {!reveal ? (
                        <button onClick={() => setRevealed(p => ({ ...p, [q.id]: true }))} className="text-xs text-accent hover:underline">정답 확인</button>
                      ) : (
                        <span className={`text-xs ${ok ? 'text-success' : 'text-error'}`}>
                          {ok ? '✓ 정답' : '✗ 정답: '}{!ok && q.answer}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
              {(recall.items || []).length === 0 && (
                <p className="text-text-dim text-sm text-center py-8">{lecture} recall 항목이 아직 없습니다.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StudyGuide() {
  const lectures = ['L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']
  const [coreOpen, setCoreOpen] = useState(null) // {lecture, view}

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-text-bright mb-2 flex items-center gap-2">
        <BookOpen size={14} /> 강의별 학습 가이드 (핵심 · 서머리 · 강의 · 퀴즈 · 암기 · 논술)
      </h3>
      {lectures.map(l => (
        <LectureRow key={l} lecture={l} onOpenCore={(lec, view) => setCoreOpen({ lecture: lec, view: view || 'core' })} />
      ))}
      {coreOpen && (
        <CoreSummaryModal
          lecture={coreOpen.lecture}
          view={coreOpen.view}
          onClose={() => setCoreOpen(null)}
        />
      )}
    </div>
  )
}

/**
 * 1-hour compact L2~L8 course panel.
 *
 * Three states:
 *   1. lobby     — overview cards, "시작" button, time estimate
 *   2. question  — render prompt, accept answer, submit
 *   3. feedback  — show correctness + canonical answer + rationale, advance
 *   4. done      — final score + retry
 */
export default function CoursePanel() {
  const [stage, setStage] = useState('loading')   // loading | lobby | question | feedback | done
  const [overview, setOverview] = useState(null)
  const [runId, setRunId] = useState(null)
  const [progress, setProgress] = useState({ index: 0, total: 28, correct: 0, attempted: 0 })
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [error, setError] = useState(null)
  const startTimeRef = useRef(null)

  // ── Load overview ─────────────────────────────────────────────
  useEffect(() => {
    api.courseOverview()
      .then(d => { setOverview(d); setStage('lobby') })
      .catch(e => { setError(String(e)); setStage('lobby') })
  }, [])

  // ── Begin / resume run ────────────────────────────────────────
  const begin = async () => {
    try {
      const r = await api.courseStart()
      setRunId(r.run_id)
      setProgress(p => ({ ...p, index: r.current_index, correct: r.correct, attempted: r.attempted }))
      const next = await api.courseNext(r.run_id)
      if (next.done) { setStage('done') } else {
        setQuestion(next.question)
        setProgress(p => ({ ...p, index: next.index, total: next.total }))
        startTimeRef.current = Date.now()
        setStage('question')
      }
    } catch (e) { setError(String(e)) }
  }

  // ── Submit answer ─────────────────────────────────────────────
  const submit = async () => {
    if (!answer.trim()) return
    const elapsed = startTimeRef.current ? Math.round((Date.now() - startTimeRef.current) / 1000) : 0
    try {
      const fb = await api.courseAnswer(runId, question.id, answer, elapsed)
      setFeedback(fb)
      setProgress(p => ({ ...p, index: fb.current_index, correct: fb.correct_count, attempted: fb.total_attempted }))
      setStage('feedback')
    } catch (e) { setError(String(e)) }
  }

  const advance = async () => {
    setAnswer(''); setFeedback(null)
    try {
      const next = await api.courseNext(runId)
      if (next.done) {
        setStage('done')
      } else {
        setQuestion(next.question)
        setProgress(p => ({ ...p, index: next.index, total: next.total }))
        startTimeRef.current = Date.now()
        setStage('question')
      }
    } catch (e) { setError(String(e)) }
  }

  const restart = () => {
    setStage('loading'); setRunId(null); setQuestion(null); setFeedback(null); setAnswer('')
    api.courseOverview().then(d => { setOverview(d); setStage('lobby') }).catch(() => setStage('lobby'))
  }

  // ──────────────────────────────────────────────────────────────
  // Lobby
  // ──────────────────────────────────────────────────────────────
  if (stage === 'loading') {
    return <div className="p-6 text-text-dim text-sm">코스 정보 불러오는 중…</div>
  }

  if (stage === 'lobby') {
    if (!overview || (overview.total_questions ?? 0) === 0) {
      return (
        <div className="p-6 max-w-3xl mx-auto">
          <StudyGuide />
          <h2 className="text-xl font-bold mb-2 text-text-bright">1시간 컴팩트 코스 (L2 ~ L8)</h2>
          <p className="text-text-dim text-sm mb-4">
            아직 문항이 준비되지 않았어요. Opus 출제자 에이전트가 28문항을 작성 중이에요. 잠시 후 다시 확인해주세요.
          </p>
          <button
            onClick={() => api.courseOverview().then(d => setOverview(d)).catch(() => {})}
            className="px-4 py-2 rounded-lg bg-surface-2 text-text border border-border hover:bg-surface-3 text-sm"
          >
            새로고침
          </button>
        </div>
      )
    }
    const totalMin = Math.round(overview.total_time_s / 60)
    const targetMin = Math.round(overview.target_time_s / 60)

    return (
      <div className="p-6 max-w-3xl mx-auto">
        {/* v0.7 — 강의별 학습 가이드 (summary + lecture + quiz + take-home inheritance) */}
        <StudyGuide />

        <div className="mb-6">
          <h2 className="text-xl font-bold mb-2 text-text-bright">1시간 컴팩트 코스</h2>
          <p className="text-text-dim text-sm">
            L2 ~ L8 의 핵심을 60 분 안에 압축. 출제 비율 70% 필수지식 + 30% 응용. 슬라이드 지식만으로 풀이.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="p-4 rounded-xl bg-surface border border-border-soft">
            <div className="flex items-center gap-2 mb-1 text-text-dim text-xs">
              <Target size={14} /> 문항 수
            </div>
            <div className="text-2xl font-bold text-accent" style={{fontVariantNumeric:'tabular-nums'}}>
              {overview.total_questions}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-surface border border-border-soft">
            <div className="flex items-center gap-2 mb-1 text-text-dim text-xs">
              <Clock size={14} /> 예상 시간
            </div>
            <div className="text-2xl font-bold text-secondary" style={{fontVariantNumeric:'tabular-nums'}}>
              {totalMin}<span className="text-sm text-text-dim font-normal"> /{targetMin} 분</span>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-surface border border-border-soft">
            <div className="text-text-dim text-xs mb-1">출제 비율</div>
            <div className="text-base font-semibold text-text">
              필수 70% · 응용 30%
            </div>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-semibold text-text-bright mb-2">강의별 구성</h3>
          <div className="space-y-1.5">
            {overview.lectures.map(l => (
              <div key={l.lecture}
                   className="flex items-center justify-between px-3 py-2 rounded-lg bg-surface border border-border-soft text-sm">
                <span className="font-medium text-text-bright">{l.lecture}</span>
                <span className="text-text-dim text-xs" style={{fontVariantNumeric:'tabular-nums'}}>
                  필수 {l.mandatory} · 응용 {l.applied} · {Math.round((l.time_s||0)/60)} 분
                </span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={begin}
          data-tap
          className="w-full md:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-accent text-[var(--color-bg)] font-semibold text-sm hover:bg-accent-dim transition-colors"
        >
          <Play size={16} /> 코스 시작
        </button>
        {error && <div className="mt-3 text-error text-xs">{error}</div>}
      </div>
    )
  }

  // ──────────────────────────────────────────────────────────────
  // Question
  // ──────────────────────────────────────────────────────────────
  if (stage === 'question' && question) {
    return (
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <ProgressBar progress={progress} />
        <div className="mb-2 flex items-center gap-2 text-xs">
          <span className={`px-2 py-0.5 rounded-full font-medium ${
            question.kind === 'mandatory'
              ? 'bg-accent-soft text-accent'
              : 'bg-[color-mix(in_oklab,var(--color-warning)_18%,transparent)] text-warning'
          }`}>
            {question.kind === 'mandatory' ? '필수' : '응용'}
          </span>
          <span className="text-text-dim">{question.lecture} · 슬라이드 p.{question.slide_page}</span>
        </div>

        <div className="prose mb-4">
          <Markdown>{question.prompt_md}</Markdown>
        </div>

        <textarea
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          rows={6}
          placeholder="답변을 작성하세요. 한국어 + 수식($..$) 모두 가능."
          className="w-full p-3 rounded-lg border border-border bg-surface text-text resize-y focus:outline-none focus:border-accent"
        />

        <div className="mt-3 flex gap-2">
          <button
            onClick={submit}
            data-tap
            disabled={!answer.trim()}
            className="px-5 py-2.5 rounded-lg bg-accent text-[var(--color-bg)] font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            제출
          </button>
          <button
            onClick={() => { setAnswer(''); submit() }}
            data-tap
            className="px-3 py-2.5 rounded-lg bg-surface-2 text-text-dim text-sm border border-border-soft"
          >
            모르겠음 (스킵)
          </button>
        </div>
      </div>
    )
  }

  // ──────────────────────────────────────────────────────────────
  // Feedback
  // ──────────────────────────────────────────────────────────────
  if (stage === 'feedback' && feedback) {
    return (
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <ProgressBar progress={progress} />
        <div className={`mb-4 p-4 rounded-xl border-l-4 ${
          feedback.correct
            ? 'bg-[color-mix(in_oklab,var(--color-success)_10%,transparent)] border-success'
            : 'bg-[color-mix(in_oklab,var(--color-error)_8%,transparent)] border-error'
        }`}>
          <div className="flex items-center gap-2 font-semibold mb-1">
            {feedback.correct
              ? <><CheckCircle2 size={18} className="text-success" /><span className="text-success">정답!</span></>
              : <><XCircle size={18} className="text-error" /><span className="text-error">아쉬워요 — 모범 답안 확인</span></>}
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-xs font-semibold text-text-dim mb-1.5 uppercase tracking-wider">모범 답안</h4>
          <div className="prose p-4 rounded-lg bg-surface border border-border-soft">
            <Markdown>{feedback.canonical_answer_md}</Markdown>
          </div>
        </div>

        <div className="mb-6">
          <h4 className="text-xs font-semibold text-text-dim mb-1.5 uppercase tracking-wider">해설</h4>
          <div className="prose p-3 rounded-lg bg-surface-2 text-sm">
            <Markdown>{feedback.rationale_md}</Markdown>
          </div>
          <div className="text-xs text-text-faint mt-2">슬라이드 p.{feedback.slide_page}</div>
        </div>

        <button
          onClick={advance}
          data-tap
          className="w-full md:w-auto flex items-center justify-center gap-1.5 px-5 py-3 rounded-xl bg-accent text-[var(--color-bg)] font-semibold text-sm"
        >
          다음 문항 <ChevronRight size={16} />
        </button>
      </div>
    )
  }

  // ──────────────────────────────────────────────────────────────
  // Done
  // ──────────────────────────────────────────────────────────────
  if (stage === 'done') {
    const acc = progress.attempted > 0 ? Math.round((progress.correct / progress.attempted) * 100) : 0
    return (
      <div className="p-6 max-w-2xl mx-auto text-center">
        <Trophy size={48} className="text-accent mx-auto mb-3" />
        <h2 className="text-2xl font-bold mb-2 text-text-bright">코스 완료!</h2>
        <p className="text-text-dim text-sm mb-6">
          L2 ~ L8 핵심 28 문항을 끝냈어요.
        </p>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Stat label="정답률" value={`${acc}%`} color="var(--color-accent)" />
          <Stat label="정답 / 시도" value={`${progress.correct}/${progress.attempted}`} color="var(--color-secondary)" />
          <Stat label="다음 추천" value={acc < 70 ? '복습 모드' : 'SRS' } color="var(--color-text)" />
        </div>
        <button onClick={restart}
                data-tap
                className="px-5 py-2.5 rounded-lg bg-surface-2 border border-border-soft text-text font-medium text-sm flex items-center gap-2 mx-auto">
          <RotateCcw size={14} /> 다시 시작
        </button>
      </div>
    )
  }

  return <div className="p-6 text-text-dim text-sm">대기 중…</div>
}

// ── Helpers ────────────────────────────────────────────────────
function ProgressBar({ progress }) {
  const pct = progress.total > 0 ? (progress.index / progress.total) * 100 : 0
  return (
    <div className="mb-4">
      <div className="flex justify-between text-[11px] text-text-dim mb-1.5" style={{fontVariantNumeric:'tabular-nums'}}>
        <span>{progress.index} / {progress.total}</span>
        <span>정답 {progress.correct}/{progress.attempted}</span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
        <div className="h-full bg-accent transition-all duration-300" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function Stat({ label, value, color }) {
  return (
    <div className="p-4 rounded-xl bg-surface border border-border-soft">
      <div className="text-xs text-text-dim mb-1">{label}</div>
      <div className="text-xl font-bold" style={{ color, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
    </div>
  )
}
