/**
 * WalkthroughPanel — BRI610 Walkthrough mode (Group F, v0.5)
 *
 * Visual language matches SRSPanel.jsx exactly:
 *  - Same CSS custom property tokens (var(--color-accent), etc.)
 *  - Same prose typography and badge patterns
 *  - No raw violet/indigo — only semantic tokens
 *
 * Layout:
 *  1. Walkthrough selector (pill-buttons)
 *  2. Progress bar + step counter
 *  3. Current step narration (Markdown + KaTeX)
 *  4. Structured-input gate (3 textareas)
 *  5. Optional LaTeX textarea
 *  6. Submit button + failure counter
 *  7. Move badge + verifier badge + next narration reveal
 */

import { useState, useRef, useEffect } from 'react'
import {
  GraduationCap, Loader2, ChevronRight, RefreshCw,
  CheckCircle, XCircle, MinusCircle, AlertTriangle,
  Sparkles, Eye
} from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

// ── Color tokens (matching SRSPanel) ────────────────────────────

const MOVE_COLORS = {
  analogy:                       'var(--color-type-concept)',
  prerequisite_check:            'var(--color-type-recall)',
  derivation_prompt:             'var(--color-type-proof)',
  counterexample:                'var(--color-rating-again)',
  dimensional_analysis:          'var(--color-type-application)',
  limiting_case:                 'var(--color-secondary)',
  direct_explanation_with_followup: 'var(--color-accent)',
  socratic_exit:                 'var(--color-rating-hard)',
}

const MOVE_LABELS_KO = {
  analogy:                       '유추',
  prerequisite_check:            '선행 개념 점검',
  derivation_prompt:             '유도 촉구',
  counterexample:                '반례',
  dimensional_analysis:          '차원 분석',
  limiting_case:                 '극한 케이스',
  direct_explanation_with_followup: '직접 설명',
  socratic_exit:                 '정답 공개',
}

const LECTURE_LABELS = {
  L3: 'L3 · 이온 채널',
  L5: 'L5 · Hodgkin-Huxley',
  L7: 'L7 · Cable Theory',
}

// ── Sub-components ────────────────────────────────────────────────

function WalkthroughSelector({ walkthroughs, selected, onSelect, disabled }) {
  return (
    <div className="flex flex-wrap gap-2">
      {walkthroughs.map(wt => {
        const isSelected = selected === wt.id
        return (
          <button
            key={wt.id}
            disabled={disabled}
            onClick={() => onSelect(wt.id)}
            className="px-3.5 py-1.5 rounded-full text-[12px] font-semibold transition-all disabled:opacity-50"
            style={{
              background: isSelected
                ? 'var(--color-accent)'
                : 'color-mix(in oklab, var(--color-accent) 10%, transparent)',
              color: isSelected ? 'var(--color-bg)' : 'var(--color-accent)',
              border: `1px solid color-mix(in oklab, var(--color-accent) ${isSelected ? '100' : '30'}%, transparent)`,
            }}
          >
            {wt.title_ko || wt.title}
          </button>
        )
      })}
    </div>
  )
}

function MoveBadge({ move }) {
  if (!move) return null
  const color = MOVE_COLORS[move] || 'var(--color-text-dim)'
  const label = MOVE_LABELS_KO[move] || move
  return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold"
      style={{
        background: `color-mix(in oklab, ${color} 14%, transparent)`,
        color,
        border: `1px solid color-mix(in oklab, ${color} 30%, transparent)`,
      }}
    >
      전략: {label}
    </span>
  )
}

function VerifierBadge({ result }) {
  if (!result) return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold"
      style={{
        background: 'color-mix(in oklab, var(--color-text-dim) 10%, transparent)',
        color: 'var(--color-text-dim)',
      }}
    >
      <MinusCircle size={11} /> 미검증
    </span>
  )

  const { status } = result
  if (status === 'correct' || status === 'equivalent') return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold"
      style={{
        background: 'color-mix(in oklab, var(--color-success) 14%, transparent)',
        color: 'var(--color-success)',
      }}
    >
      <CheckCircle size={11} /> 검증됨
    </span>
  )

  if (status === 'wrong') return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold"
      style={{
        background: 'color-mix(in oklab, var(--color-rating-again) 14%, transparent)',
        color: 'var(--color-rating-again)',
      }}
    >
      <XCircle size={11} /> 오답
    </span>
  )

  return (
    <span
      className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-semibold"
      style={{
        background: 'color-mix(in oklab, var(--color-text-dim) 10%, transparent)',
        color: 'var(--color-text-dim)',
      }}
    >
      <MinusCircle size={11} /> 미검증
    </span>
  )
}

function FailureCounter({ failures, max = 3 }) {
  const dots = Array.from({ length: max }, (_, i) => i < failures)
  return (
    <span
      className="inline-flex items-center gap-1 text-[11px]"
      style={{ color: failures > 0 ? 'var(--color-rating-again)' : 'var(--color-text-dim)' }}
      title={`시도 ${failures}/${max}`}
    >
      시도
      {dots.map((filled, i) => (
        <span
          key={i}
          className="inline-block w-2 h-2 rounded-full"
          style={{
            background: filled ? 'var(--color-rating-again)' : 'var(--color-border)',
            transition: 'background 0.2s',
          }}
        />
      ))}
      {failures}/{max}
    </span>
  )
}

const GATE_FIELDS = [
  { key: 'understood', label: '내가 이해한 바', placeholder: '현재 단계에서 내가 이해하고 있는 내용…' },
  { key: 'tried',      label: '내가 시도한 것', placeholder: '어떻게 접근해 봤는지…' },
  { key: 'stuck',      label: '막힌 부분',       placeholder: '어디서, 왜 막혔는지…' },
]

// ── Main component ─────────────────────────────────────────────────

export default function WalkthroughPanel() {
  const [walkthroughs, setWalkthroughs] = useState([])
  const [loadingList, setLoadingList] = useState(true)
  const [selectedId, setSelectedId] = useState(null)

  // Session state
  const [sessionId, setSessionId] = useState(null)
  const [stepData, setStepData]   = useState(null)   // last /step response
  const [firstStep, setFirstStep] = useState(null)   // from /start

  // Input gate values
  const [gate, setGate] = useState({ understood: '', tried: '', stuck: '' })
  const [latexInput, setLatexInput] = useState('')

  // UI state
  const [submitting, setSubmitting] = useState(false)
  const [starting,   setStarting]   = useState(false)
  const [narration,  setNarration]  = useState('')    // current narration
  const [lastResponse, setLastResponse] = useState(null)
  const [gateError,  setGateError]  = useState(null)
  const [apiError,   setApiError]   = useState(null)

  const bottomRef = useRef(null)

  // Load walkthrough list on mount
  useEffect(() => {
    api.walkthroughList()
      .then(r => {
        const list = r.walkthroughs || []
        setWalkthroughs(list)
        if (list.length > 0) setSelectedId(list[0].id)
      })
      .catch(() => setWalkthroughs([]))
      .finally(() => setLoadingList(false))
  }, [])

  // Scroll to bottom on new narration
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [narration, lastResponse])

  const gateAllFilled = GATE_FIELDS.every(f => gate[f.key].trim().length > 0)

  const needsGate = stepData
    ? (stepData.input_gate?.required?.length > 0)
    : (firstStep?.kind === 'socratic' || firstStep?.kind === 'derive_attempt')

  const currentStep = stepData || firstStep
  const isComplete  = stepData?.is_complete || false
  const failures    = stepData?.mode_lock_failures ?? 0
  const totalSteps  = stepData?.total_steps ?? firstStep?.total_steps ?? 0
  const stepNum     = stepData?.step_num ?? 1
  const acceptsLatex = currentStep?.accepts_latex ?? false
  const progressPct  = totalSteps > 0 ? Math.round((stepNum / totalSteps) * 100) : 0

  async function handleStart(id) {
    setSelectedId(id)
    setStarting(true)
    setSessionId(null)
    setStepData(null)
    setFirstStep(null)
    setNarration('')
    setLastResponse(null)
    setGate({ understood: '', tried: '', stuck: '' })
    setLatexInput('')
    setGateError(null)
    setApiError(null)

    try {
      const r = await api.walkthroughStart(id, 1)
      setSessionId(r.session_id)
      setFirstStep(r.first_step)

      // Immediately fetch initial narration
      const init = await api.walkthroughStep(r.session_id, '', null)
      setStepData(init)
      setNarration(init.narration_md || '')
      setLastResponse(null)
    } catch (e) {
      setApiError(String(e))
    } finally {
      setStarting(false)
    }
  }

  async function handleSubmit() {
    if (!sessionId || submitting) return

    // Build combined user_input from gate fields + free text
    const gateText = GATE_FIELDS
      .map(f => `**${f.label}**: ${gate[f.key].trim()}`)
      .join('\n\n')

    setSubmitting(true)
    setGateError(null)
    setApiError(null)

    try {
      const res = await api.walkthroughStep(
        sessionId,
        gateText,
        latexInput.trim() || null,
      )

      if (res.gate_error) {
        setGateError(res.input_gate?.missing || [])
        return
      }

      setLastResponse(res)
      setNarration(res.narration_md || '')
      setStepData(res)
      // Reset inputs
      setGate({ understood: '', tried: '', stuck: '' })
      setLatexInput('')
    } catch (e) {
      const msg = String(e)
      if (msg.includes('422')) {
        setGateError(['모든 칸을 채워주세요.'])
      } else {
        setApiError(msg)
      }
    } finally {
      setSubmitting(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────

  if (loadingList) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: 'var(--color-text-dim)' }}>
        <Loader2 className="animate-spin mr-2" size={18} /> 워크스루 목록 로딩 중…
      </div>
    )
  }

  if (walkthroughs.length === 0) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: 'var(--color-text-dim)' }}>
        워크스루를 찾을 수 없습니다. 백엔드 서버를 확인하세요.
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg)' }}>

      {/* ── Top bar ── */}
      <div
        className="flex items-center gap-4 px-7 py-2.5 text-[12px] flex-wrap"
        style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}
      >
        <div className="flex items-center gap-1.5 font-semibold" style={{ color: 'var(--color-accent)' }}>
          <GraduationCap size={15} /> 워크스루 (Walkthrough)
        </div>
        {sessionId && (
          <>
            <span style={{ color: 'var(--color-text-dim)' }}>
              단계 <span className="tabular-nums font-semibold" style={{ color: 'var(--color-text-bright)' }}>{stepNum}</span> / {totalSteps}
            </span>
            <FailureCounter failures={failures} max={3} />
          </>
        )}
        <div className="flex-1" />
        {sessionId && (
          <button
            onClick={() => handleStart(selectedId)}
            className="inline-flex items-center gap-1 transition-colors"
            style={{ color: 'var(--color-text-dim)' }}
            onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-text)'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-dim)'}
          >
            <RefreshCw size={12} /> 다시 시작
          </button>
        )}
      </div>

      {/* ── Progress bar ── */}
      {sessionId && (
        <div className="h-[3px]" style={{ background: 'var(--color-surface-2)' }}>
          <div
            className="h-full transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%`, background: 'var(--color-accent)' }}
          />
        </div>
      )}

      {/* ── Scrollable content ── */}
      <div className="flex-1 overflow-y-auto py-8 px-6 flex flex-col items-center gap-6">
        <div className="w-full max-w-3xl flex flex-col gap-5">

          {/* Walkthrough selector */}
          <div
            className="rounded-xl px-6 py-5"
            style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
          >
            <p className="text-[11px] uppercase tracking-[0.18em] mb-3" style={{ color: 'var(--color-text-faint)' }}>
              워크스루 선택
            </p>
            <WalkthroughSelector
              walkthroughs={walkthroughs}
              selected={selectedId}
              onSelect={handleStart}
              disabled={starting || submitting}
            />
          </div>

          {/* Loading spinner while starting */}
          {starting && (
            <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-dim)' }}>
              <Loader2 className="animate-spin" size={16} /> 세션을 시작하는 중…
            </div>
          )}

          {/* Current step narration */}
          {narration && (
            <div
              className="rounded-xl reveal"
              style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', boxShadow: '0 12px 32px -8px rgba(0,0,0,0.35)' }}
            >
              {/* Step meta strip */}
              {currentStep && (
                <div
                  className="flex items-center gap-2.5 px-6 py-3.5 flex-wrap text-[11px]"
                  style={{ borderBottom: '1px solid var(--color-border-soft)' }}
                >
                  <span
                    className="px-2 py-0.5 rounded-full font-semibold tracking-wide uppercase"
                    style={{
                      background: 'color-mix(in oklab, var(--color-type-proof) 14%, transparent)',
                      color: 'var(--color-type-proof)',
                    }}
                  >
                    {currentStep.kind === 'explain' ? '설명' :
                     currentStep.kind === 'socratic' ? '소크라테스' :
                     currentStep.kind === 'derive_attempt' ? '유도 시도' :
                     currentStep.kind === 'checkpoint' ? '체크포인트' :
                     currentStep.kind === 'reveal' ? '정답 공개' : currentStep.kind}
                  </span>
                  {lastResponse?.move_used && <MoveBadge move={lastResponse.move_used} />}
                  {lastResponse?.verifier_result !== undefined && (
                    <VerifierBadge result={lastResponse.verifier_result} />
                  )}
                  {walkthroughs.find(w => w.id === selectedId) && (
                    <span style={{ color: 'var(--color-text-dim)' }}>
                      {LECTURE_LABELS[walkthroughs.find(w => w.id === selectedId)?.lecture] || ''}
                    </span>
                  )}
                </div>
              )}

              {/* Narration body */}
              <div className="px-7 py-7">
                <div className="prose max-w-none" style={{ fontSize: '1rem', lineHeight: 1.82 }}>
                  <Markdown>{narration}</Markdown>
                </div>
              </div>

              {/* Verifier residual (if wrong) */}
              {lastResponse?.verifier_result?.status === 'wrong' && lastResponse.verifier_result.residual_latex && (
                <div
                  className="px-7 py-4 text-[13px]"
                  style={{ borderTop: '1px solid var(--color-border-soft)', color: 'var(--color-rating-again)' }}
                >
                  <span className="font-semibold">SymPy 잔차: </span>
                  <code className="px-1.5 py-0.5 rounded text-[12px]"
                        style={{ background: 'var(--color-surface-2)' }}>
                    {lastResponse.verifier_result.residual_latex}
                  </code>
                </div>
              )}

              {/* Complete banner */}
              {isComplete && (
                <div
                  className="px-7 py-5 flex items-center gap-3 reveal"
                  style={{ borderTop: '1px solid var(--color-border-soft)', background: 'color-mix(in oklab, var(--color-success) 8%, transparent)' }}
                >
                  <Sparkles size={18} style={{ color: 'var(--color-success)' }} />
                  <span className="font-semibold" style={{ color: 'var(--color-success)' }}>
                    워크스루 완료! 다음 주제를 선택하거나 SRS 복습을 이어가세요.
                  </span>
                </div>
              )}
            </div>
          )}

          {/* ── Input section (hidden when complete or no session) ── */}
          {sessionId && !isComplete && narration && (
            <div
              className="rounded-xl"
              style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
            >
              {/* Structured-input gate */}
              {needsGate && (
                <div className="px-6 pt-5 pb-4">
                  <p className="text-[11px] uppercase tracking-[0.18em] mb-3" style={{ color: 'var(--color-text-faint)' }}>
                    답변 전 세 칸을 채워주세요 (Structured Input Gate)
                  </p>
                  <div className="flex flex-col gap-3">
                    {GATE_FIELDS.map(f => (
                      <div key={f.key}>
                        <label
                          className="block text-[12px] font-semibold mb-1"
                          style={{ color: 'var(--color-text-dim)' }}
                        >
                          {f.label}
                        </label>
                        <textarea
                          rows={2}
                          placeholder={f.placeholder}
                          value={gate[f.key]}
                          onChange={e => setGate(g => ({ ...g, [f.key]: e.target.value }))}
                          className="w-full rounded-lg px-3 py-2 text-[13px] resize-none transition-colors"
                          style={{
                            background:  'var(--color-surface-2)',
                            border:      '1px solid var(--color-border)',
                            color:       'var(--color-text)',
                            outline:     'none',
                          }}
                          onFocus={e => e.target.style.borderColor = 'var(--color-accent)'}
                          onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* LaTeX input (if step accepts_latex) */}
              {acceptsLatex && (
                <div
                  className="px-6 pb-4"
                  style={{ borderTop: needsGate ? '1px solid var(--color-border-soft)' : 'none', paddingTop: needsGate ? '1rem' : '1.25rem' }}
                >
                  <label
                    className="block text-[12px] font-semibold mb-1"
                    style={{ color: 'var(--color-type-proof)' }}
                  >
                    LaTeX 답안 <span style={{ color: 'var(--color-text-dim)', fontWeight: 400 }}>($...$ 으로 감싸거나 직접 LHS = RHS 입력)</span>
                  </label>
                  <textarea
                    rows={2}
                    placeholder="예: $\frac{dn}{dt} = \alpha_n(1-n) - \beta_n n$"
                    value={latexInput}
                    onChange={e => setLatexInput(e.target.value)}
                    className="w-full rounded-lg px-3 py-2 text-[13px] font-mono resize-none transition-colors"
                    style={{
                      background:  'var(--color-surface-2)',
                      border:      '1px solid var(--color-border)',
                      color:       'var(--color-text)',
                      outline:     'none',
                    }}
                    onFocus={e => e.target.style.borderColor = 'var(--color-type-proof)'}
                    onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                  />
                </div>
              )}

              {/* Gate error */}
              {gateError && (
                <div
                  className="mx-6 mb-3 px-3 py-2 rounded-lg flex items-start gap-2 text-[12px]"
                  style={{ background: 'color-mix(in oklab, var(--color-rating-again) 10%, transparent)', color: 'var(--color-rating-again)' }}
                >
                  <AlertTriangle size={13} className="shrink-0 mt-0.5" />
                  <span>
                    다음 칸이 비어 있습니다: <strong>{Array.isArray(gateError) ? gateError.join(', ') : gateError}</strong>
                  </span>
                </div>
              )}

              {/* API error */}
              {apiError && (
                <div
                  className="mx-6 mb-3 px-3 py-2 rounded-lg text-[12px]"
                  style={{ background: 'color-mix(in oklab, var(--color-rating-again) 10%, transparent)', color: 'var(--color-rating-again)' }}
                >
                  오류: {apiError}
                </div>
              )}

              {/* Submit */}
              <div
                className="px-6 pb-5"
                style={{ borderTop: '1px solid var(--color-border-soft)', paddingTop: '1rem' }}
              >
                <button
                  onClick={handleSubmit}
                  disabled={submitting || (needsGate && !gateAllFilled)}
                  className="w-full py-2.5 rounded-lg font-semibold text-sm inline-flex items-center justify-center gap-2 transition-all disabled:opacity-40"
                  style={{
                    background: 'var(--color-accent)',
                    color: 'var(--color-bg)',
                  }}
                >
                  {submitting
                    ? <><Loader2 className="animate-spin" size={15} /> 처리 중…</>
                    : <><ChevronRight size={15} /> 제출 및 다음으로</>
                  }
                </button>
                {needsGate && !gateAllFilled && (
                  <p className="text-[11px] text-center mt-2" style={{ color: 'var(--color-text-faint)' }}>
                    세 칸을 모두 채워야 제출할 수 있습니다.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Non-gate steps: direct submit button (explain, checkpoint) */}
          {sessionId && !isComplete && narration && !needsGate && (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="w-full max-w-3xl py-2.5 rounded-lg font-semibold text-sm inline-flex items-center justify-center gap-2 transition-all disabled:opacity-40"
              style={{
                background: 'color-mix(in oklab, var(--color-accent) 14%, transparent)',
                color:      'var(--color-accent)',
                border:     '1px solid color-mix(in oklab, var(--color-accent) 30%, transparent)',
              }}
            >
              {submitting
                ? <><Loader2 className="animate-spin" size={15} /> 처리 중…</>
                : <><Eye size={15} /> 이해했습니다 — 다음 단계</>
              }
            </button>
          )}

          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  )
}
