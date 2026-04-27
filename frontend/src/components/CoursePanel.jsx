import { useState, useEffect, useRef } from 'react'
import { Play, Clock, Target, ChevronRight, CheckCircle2, XCircle, Trophy, RotateCcw } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

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
