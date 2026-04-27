import { useEffect, useState, useRef } from 'react'
import {
  GraduationCap, BookOpen, ChevronRight, Loader2,
  RotateCcw, CheckCircle, HelpCircle, Layers,
} from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

// ── Step-kind color mapping (no violet/indigo) ────────────────────────────
const KIND_COLOR = {
  expose:          'var(--color-type-recall)',       // deep blue
  derive:          'var(--color-type-proof)',         // maroon
  intuition_check: 'var(--color-type-application)',  // sienna
  connect:         'var(--color-type-concept)',       // forest green
}

const KIND_LABEL = {
  expose:          '설명',
  derive:          '유도',
  intuition_check: '직관 확인',
  connect:         '연결',
}

const KIND_ICON = {
  expose:          BookOpen,
  derive:          Layers,
  intuition_check: HelpCircle,
  connect:         CheckCircle,
}

// ── Slide ref badge ───────────────────────────────────────────────────────
function SlideRefBadge({ ref: r }) {
  if (!r) return null
  const text = typeof r === 'string' ? r : `Slide ${r}`
  return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-medium"
      style={{
        background: 'color-mix(in oklab, var(--color-slide) 12%, transparent)',
        color: 'var(--color-slide)',
      }}
    >
      <BookOpen size={10} /> {text}
    </span>
  )
}

// ── Kind badge (styled like TypeBadge in SRSPanel) ────────────────────────
function KindBadge({ kind }) {
  const c = KIND_COLOR[kind] || 'var(--color-text-dim)'
  const label = KIND_LABEL[kind] || kind
  const Icon = KIND_ICON[kind] || BookOpen
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded-full font-semibold tracking-wide"
      style={{
        background: `color-mix(in oklab, ${c} 14%, transparent)`,
        color: c,
      }}
    >
      <Icon size={11} /> {label}
    </span>
  )
}

// ── PHASE 1: Plan selector ────────────────────────────────────────────────
function PlanSelector({ onStart }) {
  const [plans, setPlans] = useState(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(null) // lecture_id being started

  useEffect(() => {
    api.lectureList()
      .then(r => setPlans(r.plans || []))
      .catch(() => setPlans([]))
      .finally(() => setLoading(false))
  }, [])

  const handleStart = async (plan) => {
    if (starting) return
    setStarting(plan.id)
    try {
      const session = await api.lectureStart(plan.id)
      onStart(session)
    } catch (e) {
      console.error('lectureStart failed', e)
      setStarting(null)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: 'var(--color-text-dim)' }}>
        <Loader2 className="animate-spin mr-2" size={18} /> 강의 목록 불러오는 중...
      </div>
    )
  }

  if (!plans || plans.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 px-8 text-center">
        <GraduationCap size={32} style={{ color: 'var(--color-text-faint)' }} />
        <p style={{ color: 'var(--color-text-dim)' }}>강의 계획이 없습니다. 백엔드에서 seed를 실행해 주세요.</p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto py-10 px-6 flex flex-col items-center">
      <div className="w-full max-w-3xl">
        {/* Section heading */}
        <div className="mb-8">
          <p className="text-[11px] uppercase tracking-[0.18em] mb-1.5"
             style={{ color: 'var(--color-text-faint)' }}>강의 모드</p>
          <h2 className="text-xl font-semibold leading-snug"
              style={{ color: 'var(--color-text-bright)', fontFamily: 'var(--font-serif)' }}>
            강의를 선택하세요
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-dim)' }}>
            각 강의는 단계별 내레이션과 직관 확인으로 구성됩니다.
          </p>
        </div>

        {/* Plan cards */}
        <div className="flex flex-col gap-3">
          {plans.map(plan => (
            <button
              key={plan.id}
              onClick={() => handleStart(plan)}
              disabled={!!starting}
              className="text-left rounded-xl px-6 py-5 pop transition-all disabled:opacity-60 group"
              style={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                boxShadow: '0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 16px -6px rgba(0,0,0,0.12)',
              }}
              onMouseEnter={e => {
                if (!starting) e.currentTarget.style.borderColor = 'var(--color-accent)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--color-border)'
              }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-base leading-snug mb-1"
                     style={{ color: 'var(--color-text-bright)', fontFamily: 'var(--font-serif)' }}>
                    {plan.title_ko}
                  </p>
                  <p className="text-sm leading-relaxed"
                     style={{ color: 'var(--color-text-dim)' }}>
                    {plan.objective}
                  </p>
                </div>
                <div className="flex-shrink-0 flex flex-col items-end gap-2 pt-0.5">
                  <span className="text-[11px] font-medium tabular-nums"
                        style={{ color: 'var(--color-text-faint)' }}>
                    {plan.num_steps}단계
                  </span>
                  {starting === plan.id
                    ? <Loader2 size={16} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
                    : <ChevronRight size={16}
                        style={{ color: 'var(--color-text-faint)' }}
                        className="group-hover:translate-x-0.5 transition-transform" />
                  }
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── PHASE 2: Lecture in progress ──────────────────────────────────────────
function LectureInProgress({ session, onExit }) {
  // session = { session_id, lecture_id, title_ko, objective, total_steps, first_step }
  const [step, setStep] = useState(null)        // current narrated step
  const [loading, setLoading] = useState(true)  // fetching narration
  const [advancing, setAdvancing] = useState(false)
  const [answer, setAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [submitMsg, setSubmitMsg] = useState('')
  const [isComplete, setIsComplete] = useState(false)
  const bodyRef = useRef(null)

  // On mount, narrate the first step (session.first_step carries step_num=1)
  useEffect(() => {
    narrate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Scroll to top of body whenever step changes
  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = 0
  }, [step?.step_id])

  const narrate = async () => {
    setLoading(true)
    try {
      const r = await api.lectureNarrate(session.session_id)
      if (r.is_complete) {
        setIsComplete(true)
      } else {
        setStep(r)
        setAnswer('')
        setSubmitted(false)
        setSubmitMsg('')
      }
    } catch (e) {
      console.error('lectureNarrate failed', e)
    } finally {
      setLoading(false)
    }
  }

  const handleAdvance = async () => {
    if (advancing) return
    setAdvancing(true)
    try {
      await api.lectureAdvance(session.session_id)
      await narrate()
    } catch (e) {
      console.error('lectureAdvance failed', e)
    } finally {
      setAdvancing(false)
    }
  }

  const handleSubmit = async () => {
    if (!answer.trim() || advancing) return
    setAdvancing(true)
    try {
      await api.lectureSubmit(session.session_id, answer.trim())
      setSubmitted(true)
      setSubmitMsg('기록됨')
      // Brief feedback, then advance
      setTimeout(async () => {
        await api.lectureAdvance(session.session_id)
        await narrate()
        setAdvancing(false)
      }, 900)
    } catch (e) {
      console.error('lectureSubmit failed', e)
      setAdvancing(false)
    }
  }

  if (isComplete) {
    return <CompleteBanner title_ko={session.title_ko} onRestart={onExit} />
  }

  const stepNum  = step?.step_num  ?? 1
  const total    = session.total_steps ?? step?.total_steps ?? 1
  const progress = Math.min(100, Math.round(((stepNum - 1) / total) * 100))
  const kind     = step?.kind
  const kindColor = KIND_COLOR[kind] || 'var(--color-text-dim)'

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg)' }}>

      {/* Top status bar */}
      <div
        className="flex items-center gap-4 px-7 py-2.5 text-[12px] flex-wrap"
        style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}
      >
        <div className="flex items-center gap-1.5 font-semibold" style={{ color: 'var(--color-accent)' }}>
          <GraduationCap size={15} />
          <span className="max-w-[220px] truncate" title={session.title_ko}>
            {session.title_ko}
          </span>
        </div>
        <span style={{ color: 'var(--color-text-dim)' }}>
          단계{' '}
          <span className="tabular-nums font-semibold" style={{ color: 'var(--color-text-bright)' }}>
            {stepNum}
          </span>
          {' / '}
          {total}
        </span>
        {kind && <KindBadge kind={kind} />}
        <div className="flex-1" />
        <button
          onClick={onExit}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[12px] font-medium transition-colors"
          style={{
            color: 'var(--color-error)',
            border: '1px solid color-mix(in oklab, var(--color-error) 28%, transparent)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'color-mix(in oklab, var(--color-error) 10%, transparent)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <RotateCcw size={12} /> 강의 종료
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-[3px]" style={{ background: 'var(--color-surface-2)' }}>
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%`, background: 'var(--color-accent)' }}
        />
      </div>

      {/* Body */}
      <div ref={bodyRef} className="flex-1 overflow-y-auto py-10 px-6 flex flex-col items-center">
        {loading ? (
          <div className="flex items-center gap-2 mt-24" style={{ color: 'var(--color-text-dim)' }}>
            <Loader2 className="animate-spin" size={18} /> 내레이션 생성 중...
          </div>
        ) : step ? (
          <div
            key={step.step_id}
            className="w-full max-w-3xl rounded-xl pop"
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: '0 1px 0 rgba(255,255,255,0.02) inset, 0 12px 32px -8px rgba(0,0,0,0.15)',
            }}
          >
            {/* Meta strip */}
            <div
              className="flex items-center gap-2.5 px-7 py-3.5 flex-wrap"
              style={{ borderBottom: '1px solid var(--color-border-soft)' }}
            >
              <KindBadge kind={step.kind} />
              {step.title_ko && (
                <span
                  className="text-[12px] font-medium"
                  style={{ color: 'var(--color-text-dim)' }}
                >
                  {step.title_ko}
                </span>
              )}
              <div className="flex-1" />
              {/* Slide refs */}
              {Array.isArray(step.slide_refs) && step.slide_refs.map((r, i) => (
                <SlideRefBadge key={i} ref={r} />
              ))}
            </div>

            {/* Instruction */}
            {step.instruction_md && (
              <div
                className="px-7 pt-5 pb-2"
                style={{ borderBottom: '1px solid var(--color-border-soft)' }}
              >
                <p
                  className="text-[11px] uppercase tracking-[0.18em] mb-2"
                  style={{ color: 'var(--color-text-faint)' }}
                >
                  학습 목표
                </p>
                <div className="text-sm" style={{ color: 'var(--color-text-dim)' }}>
                  <Markdown>{step.instruction_md}</Markdown>
                </div>
              </div>
            )}

            {/* Slide images — inline visual context for this step */}
            {Array.isArray(step.slide_images) && step.slide_images.length > 0 && (
              <div
                className="px-7 pt-5 pb-3"
                style={{ borderBottom: '1px solid var(--color-border-soft)' }}
              >
                <p
                  className="text-[11px] uppercase tracking-[0.18em] mb-3"
                  style={{ color: 'var(--color-text-faint)' }}
                >
                  관련 슬라이드 ({step.slide_images.length})
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {step.slide_images.map((si, i) => (
                    <a
                      key={i}
                      href={si.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg overflow-hidden border border-border-soft hover:border-accent transition-colors"
                      title={si.ref}
                    >
                      <img
                        src={si.url}
                        alt={si.ref}
                        loading="lazy"
                        style={{ width: '100%', display: 'block', background: 'var(--color-surface-2)' }}
                      />
                      <div
                        className="text-[10px] py-1 text-center"
                        style={{ color: 'var(--color-text-dim)', background: 'var(--color-surface)' }}
                      >
                        {si.ref}
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Narration */}
            <div className="px-7 py-7">
              <p
                className="text-[11px] uppercase tracking-[0.18em] mb-4"
                style={{ color: 'var(--color-text-faint)' }}
              >
                내레이션
              </p>
              <div
                className="prose max-w-none reveal"
                style={{ fontSize: '1.02rem', lineHeight: 1.8 }}
              >
                <Markdown>{step.narration_md}</Markdown>
              </div>
            </div>

            {/* Intuition check input */}
            {kind === 'intuition_check' && step.micro_question && (
              <div
                className="px-7 pb-2 pt-5 reveal"
                style={{ borderTop: '1px solid var(--color-border-soft)' }}
              >
                {/* Question callout */}
                <div
                  className="rounded-lg px-5 py-4 mb-4"
                  style={{
                    background: `color-mix(in oklab, ${kindColor} 8%, transparent)`,
                    border: `1px solid color-mix(in oklab, ${kindColor} 22%, transparent)`,
                  }}
                >
                  <p
                    className="text-[11px] uppercase tracking-[0.18em] mb-2 font-semibold"
                    style={{ color: kindColor }}
                  >
                    직관 확인 질문
                  </p>
                  <div className="prose max-w-none" style={{ fontSize: '0.97rem' }}>
                    <Markdown>{step.micro_question}</Markdown>
                  </div>
                </div>

                {submitted ? (
                  <div
                    className="py-3 text-center text-sm font-semibold rounded-lg reveal"
                    style={{
                      background: 'color-mix(in oklab, var(--color-success) 10%, transparent)',
                      color: 'var(--color-success)',
                      border: '1px solid color-mix(in oklab, var(--color-success) 28%, transparent)',
                    }}
                  >
                    {submitMsg}
                  </div>
                ) : (
                  <div className="flex flex-col gap-2.5">
                    <textarea
                      value={answer}
                      onChange={e => setAnswer(e.target.value)}
                      rows={4}
                      placeholder="자유롭게 답변을 작성하세요..."
                      className="w-full rounded-lg px-4 py-3 text-sm resize-none outline-none transition-colors"
                      style={{
                        background: 'var(--color-bg)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text)',
                        fontFamily: 'var(--font-serif)',
                        lineHeight: 1.7,
                      }}
                      onFocus={e => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
                      onBlur={e => (e.currentTarget.style.borderColor = 'var(--color-border)')}
                      disabled={advancing}
                    />
                    <button
                      onClick={handleSubmit}
                      disabled={!answer.trim() || advancing}
                      className="self-end px-5 py-2 rounded-lg text-sm font-semibold inline-flex items-center gap-2 transition-all disabled:opacity-50"
                      style={{
                        background: kindColor,
                        color: '#fff',
                      }}
                    >
                      {advancing
                        ? <><Loader2 size={14} className="animate-spin" /> 제출 중...</>
                        : <>답변 제출 <ChevronRight size={14} /></>
                      }
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Action button for non-intuition_check steps */}
            {kind !== 'intuition_check' && (
              <div
                className="px-7 pb-7 pt-5"
                style={{ borderTop: '1px solid var(--color-border-soft)' }}
              >
                <button
                  onClick={handleAdvance}
                  disabled={advancing}
                  className="w-full py-3 rounded-lg font-medium text-sm inline-flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  style={{
                    background: 'color-mix(in oklab, var(--color-accent) 14%, transparent)',
                    color: 'var(--color-accent)',
                    border: '1px solid color-mix(in oklab, var(--color-accent) 30%, transparent)',
                  }}
                  onMouseEnter={e => {
                    if (!advancing)
                      e.currentTarget.style.background = 'color-mix(in oklab, var(--color-accent) 22%, transparent)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'color-mix(in oklab, var(--color-accent) 14%, transparent)'
                  }}
                >
                  {advancing
                    ? <><Loader2 size={14} className="animate-spin" /> 다음 단계 준비 중...</>
                    : <>이해했습니다 — 다음 단계로 <ChevronRight size={14} /></>
                  }
                </button>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}

// ── PHASE 3: Complete ─────────────────────────────────────────────────────
function CompleteBanner({ title_ko, onRestart }) {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-6 px-8 text-center">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center pop"
        style={{ background: 'color-mix(in oklab, var(--color-success) 14%, transparent)' }}
      >
        <GraduationCap size={30} style={{ color: 'var(--color-success)' }} />
      </div>
      <div className="reveal">
        <p
          className="text-xl font-semibold mb-2"
          style={{ color: 'var(--color-text-bright)', fontFamily: 'var(--font-serif)' }}
        >
          강의 완료
        </p>
        <p className="text-sm max-w-md leading-relaxed" style={{ color: 'var(--color-text-dim)' }}>
          <span style={{ color: 'var(--color-accent)', fontStyle: 'italic' }}>{title_ko}</span> 강의를 마쳤습니다.
          다음에 도전할 lecture 를 선택하세요.
        </p>
      </div>
      <button
        onClick={onRestart}
        className="px-5 py-2 rounded-lg text-sm font-semibold inline-flex items-center gap-2 transition-all"
        style={{
          background: 'var(--color-accent)',
          color: '#fff',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-accent-dim)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'var(--color-accent)')}
      >
        <RotateCcw size={14} /> 강의 목록으로 돌아가기
      </button>
    </div>
  )
}

// ── Root component ────────────────────────────────────────────────────────
export default function LecturePanel() {
  // phase: 'select' | 'lecture'
  const [phase, setPhase] = useState('select')
  const [session, setSession] = useState(null)

  const handleStart = (sess) => {
    setSession(sess)
    setPhase('lecture')
  }

  const handleExit = () => {
    setSession(null)
    setPhase('select')
  }

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg)' }}>
      {phase === 'select' && (
        <PlanSelector onStart={handleStart} />
      )}
      {phase === 'lecture' && session && (
        <LectureInProgress session={session} onExit={handleExit} />
      )}
    </div>
  )
}
