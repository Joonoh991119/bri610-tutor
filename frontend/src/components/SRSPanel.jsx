import { useEffect, useMemo, useState } from 'react'
import { Brain, RefreshCw, Loader2, BookOpen, Sparkles, ChevronRight, Eye, Info } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'
import { useToast } from './Toast'

// 4-button SRS rating row. Colors map to semantic tokens defined in index.css
// (no violet/indigo — see palette comments).
const RATINGS = [
  { value: 1, label: 'Again', hint: '못함',  varColor: 'var(--color-rating-again)' },
  { value: 2, label: 'Hard',  hint: '어려움', varColor: 'var(--color-rating-hard)' },
  { value: 3, label: 'Good',  hint: '괜찮음', varColor: 'var(--color-rating-good)' },
  { value: 4, label: 'Easy',  hint: '쉬움',  varColor: 'var(--color-rating-easy)' },
]

const TYPE_TOKEN = {
  recall:      'var(--color-type-recall)',
  concept:     'var(--color-type-concept)',
  application: 'var(--color-type-application)',
  proof:       'var(--color-type-proof)',
}

const TYPE_LABEL = {
  recall:      '암기',
  concept:     '개념',
  application: '응용',
  proof:       '증명',
}

function CitationBadge({ c }) {
  if (!c) return null
  const text = c.kind === 'slide'
    ? `Slide ${c.lecture}${c.page ? ` p.${c.page}` : ''}`
    : c.kind === 'textbook'
      ? `${(c.book || '').replace(/_/g, ' & ')} Ch.${c.ch}${c.page ? ` p.${c.page}` : ''}`
      : c.kind || 'source'
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded-full font-medium"
      style={{
        background: 'color-mix(in oklab, var(--color-book) 12%, transparent)',
        color:      'var(--color-book)',
      }}
    >
      <BookOpen size={11} /> {text}
    </span>
  )
}

function TypeBadge({ type }) {
  const c = TYPE_TOKEN[type] || 'var(--color-text-dim)'
  return (
    <span
      className="text-[11px] px-2 py-0.5 rounded-full font-semibold tracking-wide"
      style={{
        background: `color-mix(in oklab, ${c} 14%, transparent)`,
        color:      c,
      }}
    >
      {TYPE_LABEL[type] || type}
    </span>
  )
}

function DifficultyDots({ d }) {
  return (
    <span className="inline-flex items-center gap-0.5" title={`난이도 ${d}/5`}>
      {[1, 2, 3, 4, 5].map(i => (
        <span
          key={i}
          className="block w-1.5 h-1.5 rounded-full"
          style={{
            background: i <= d ? 'var(--color-accent)' : 'var(--color-border)',
          }}
        />
      ))}
    </span>
  )
}

export default function SRSPanel({ onReviewComplete }) {
  const { push: pushToast } = useToast()
  const [queue, setQueue] = useState([])
  const [idx, setIdx] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [stats, setStats] = useState({ reviewed: 0, again: 0, easy: 0 })
  const [personaIntro, setPersonaIntro] = useState('')
  const [adaptive, setAdaptive] = useState(null) // { mode, topReasons }

  const card = queue[idx]
  const total = queue.length
  const remaining = total - idx
  const progressPct = total > 0 ? Math.min(100, Math.round((idx / total) * 100)) : 0

  const refresh = async () => {
    setLoading(true)
    try {
      const r = await api.srsQueue(1, 30)
      setQueue(r.queue || [])
      setIdx(0)
      setRevealed(false)
      // Capture adaptive metadata if present
      if (r.mode === 'adaptive' || (r.queue && r.queue[0]?.reasons)) {
        const firstReasons = r.queue?.[0]?.reasons || []
        setAdaptive({
          mode: r.mode || 'adaptive',
          topReasons: firstReasons.slice(0, 3),
        })
      } else {
        setAdaptive(null)
      }
    } catch (e) {
      setQueue([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  // One-shot persona session opener.
  useEffect(() => {
    if (!queue.length || personaIntro) return
    const topics = Array.from(new Set(queue.slice(0, 5).map(c => c.topic))).join(', ')
    api.personaWrap(
      `오늘 ${total}개 카드 복습 시작. 주제: ${topics}.`,
      { last_topic: queue[0]?.topic, streak_days: 0, user_display_name: '준오' }
    )
      .then(r => setPersonaIntro((r.text || '').trim()))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queue.length])

  const submit = async (rating) => {
    if (!card || submitting) return
    setSubmitting(true)
    try {
      const result = await api.srsReview(card.card_id, rating)

      // ── Toast triggers (additive — layout unchanged) ──
      const g = result?.gamification
      if (g) {
        if (g.xp_gained > 0) pushToast({ type: 'xp', xp: g.xp_gained })
        if (g.level_up)      pushToast({ type: 'level_up', title: g.level_up.title, subtitle: g.level_up.subtitle })
        if (g.badges_awarded?.length) {
          g.badges_awarded.forEach(badge =>
            pushToast({ type: 'badge', badge, name: badge.replace(/_/g, ' ') })
          )
        }
      }
      if (onReviewComplete) onReviewComplete()

      setStats(s => ({
        reviewed: s.reviewed + 1,
        again:    s.again + (rating === 1 ? 1 : 0),
        easy:     s.easy + (rating === 4 ? 1 : 0),
      }))
      setRevealed(false)
      if (idx + 1 < queue.length) setIdx(idx + 1)
      else await refresh()
    } catch (e) {
      console.error('srsReview failed', e)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && !queue.length) {
    return (
      <div className="h-full flex items-center justify-center text-text-dim">
        <Loader2 className="animate-spin mr-2" size={18} /> Loading SRS queue…
      </div>
    )
  }

  if (!queue.length) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 px-8 text-center">
        <div className="w-14 h-14 rounded-full flex items-center justify-center"
             style={{ background: 'color-mix(in oklab, var(--color-accent) 14%, transparent)' }}>
          <Brain size={26} style={{ color: 'var(--color-accent)' }} />
        </div>
        <p className="text-base font-medium" style={{ color: 'var(--color-text-bright)' }}>오늘 복습할 카드가 없습니다</p>
        <p className="text-sm max-w-md" style={{ color: 'var(--color-text-dim)' }}>
          서버에서 <code className="px-1.5 py-0.5 rounded text-[12px]"
                       style={{ background: 'var(--color-surface-2)', color: 'var(--color-accent)' }}>
            python scripts/seed_bank_demo.py
          </code> 를 실행해 12개 시드 카드를 등록해 주세요.
        </p>
        <button
          onClick={refresh}
          className="px-4 py-1.5 rounded-md text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
          style={{ background: 'var(--color-accent)', color: 'var(--color-bg)' }}
        >
          <RefreshCw size={12} /> 다시 확인
        </button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg)' }}>
      {/* Top status bar */}
      <div className="flex items-center gap-4 px-7 py-2.5 text-[12px]"
           style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center gap-1.5 font-semibold"
             style={{ color: 'var(--color-accent)' }}>
          <Brain size={15} /> 복습 (FSRS-6)
        </div>
        <span style={{ color: 'var(--color-text-dim)' }}>
          남은 <span className="tabular-nums font-semibold" style={{ color: 'var(--color-text-bright)' }}>{remaining}</span> / {total}
        </span>
        <span style={{ color: 'var(--color-text-dim)' }}>
          완료 <span className="tabular-nums font-semibold" style={{ color: 'var(--color-success)' }}>{stats.reviewed}</span>
        </span>
        <span style={{ color: 'var(--color-text-dim)' }}>
          다시 <span className="tabular-nums font-semibold" style={{ color: 'var(--color-rating-again)' }}>{stats.again}</span>
        </span>
        <span style={{ color: 'var(--color-text-dim)' }}>
          쉬움 <span className="tabular-nums font-semibold" style={{ color: 'var(--color-rating-easy)' }}>{stats.easy}</span>
        </span>
        <div className="flex-1" />
        {/* Adaptive selection indicator */}
        {adaptive && (
          <span
            className="inline-flex items-center gap-1.5 relative group cursor-default"
            style={{ color: 'var(--color-info)' }}
          >
            <Info size={12} />
            <span className="text-[11px] font-medium">Adaptive selection</span>
            {/* Tooltip with reasons */}
            {adaptive.topReasons.length > 0 && (
              <span
                className="absolute right-0 top-full mt-1.5 z-50 hidden group-hover:flex flex-col gap-1 rounded-lg px-3 py-2.5 text-[11px] leading-relaxed whitespace-nowrap shadow-lg"
                style={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-dim)',
                  minWidth: '220px',
                }}
              >
                <span className="font-semibold mb-0.5" style={{ color: 'var(--color-text-bright)' }}>
                  선택 근거 (top 3)
                </span>
                {adaptive.topReasons.map((r, i) => (
                  <span key={i} className="flex items-start gap-1.5">
                    <span style={{ color: 'var(--color-info)' }}>·</span>
                    {typeof r === 'string' ? r : JSON.stringify(r)}
                  </span>
                ))}
              </span>
            )}
          </span>
        )}
        <button
          onClick={refresh}
          className="inline-flex items-center gap-1 transition-colors"
          style={{ color: 'var(--color-text-dim)' }}
          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-text)'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-dim)'}
        >
          <RefreshCw size={12} /> 새로 고침
        </button>
      </div>

      {/* Slim progress */}
      <div className="h-[3px]" style={{ background: 'var(--color-surface-2)' }}>
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{ width: `${progressPct}%`, background: 'var(--color-accent)' }}
        />
      </div>

      {/* Persona opener */}
      {personaIntro && (
        <div
          className="px-7 py-2.5 text-[13px] flex items-start gap-2.5 reveal"
          style={{
            background: 'var(--color-accent-soft)',
            borderBottom: '1px solid var(--color-border-soft)',
            color: 'var(--color-text)',
          }}
        >
          <Sparkles size={14} style={{ color: 'var(--color-accent)' }} className="shrink-0 mt-0.5" />
          <span className="leading-relaxed">{personaIntro}</span>
        </div>
      )}

      {/* Card stage */}
      <div className="flex-1 overflow-y-auto py-10 px-6 flex flex-col items-center">
        <div
          key={card.card_id}
          className="w-full max-w-3xl rounded-xl pop"
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            boxShadow: '0 1px 0 rgba(255,255,255,0.02) inset, 0 12px 32px -8px rgba(0,0,0,0.4)',
          }}
        >
          {/* Card meta strip */}
          <div className="flex items-center gap-2.5 px-7 py-3.5 flex-wrap"
               style={{ borderBottom: '1px solid var(--color-border-soft)' }}>
            <TypeBadge type={card.card_type} />
            <span className="text-[11px] font-medium tracking-wider uppercase"
                  style={{ color: 'var(--color-text-dim)' }}>
              {card.topic === 'HH' ? 'Hodgkin–Huxley' : card.topic === 'cable' ? 'Cable Theory' : card.topic}
            </span>
            <DifficultyDots d={card.difficulty} />
            <span className="text-[11px] px-1.5 py-0.5 rounded font-medium"
                  style={{
                    background: 'var(--color-surface-2)',
                    color:      'var(--color-text-dim)',
                  }}>
              {card.bloom}
            </span>
            <div className="flex-1" />
            <CitationBadge c={card.source_citation} />
          </div>

          {/* Prompt */}
          <div className="px-7 py-7">
            <p className="text-[11px] uppercase tracking-[0.18em] mb-3"
               style={{ color: 'var(--color-text-faint)' }}>문제</p>
            <div className="prose max-w-none"
                 style={{ fontSize: '1.02rem', lineHeight: 1.78 }}>
              <Markdown>{card.prompt_md}</Markdown>
            </div>
          </div>

          {/* Reveal */}
          {!revealed ? (
            <div className="px-7 pb-7">
              <button
                onClick={() => setRevealed(true)}
                className="w-full py-3 rounded-lg font-medium text-sm inline-flex items-center justify-center gap-2 transition-all"
                style={{
                  background: 'color-mix(in oklab, var(--color-accent) 14%, transparent)',
                  color: 'var(--color-accent)',
                  border: '1px solid color-mix(in oklab, var(--color-accent) 30%, transparent)',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'color-mix(in oklab, var(--color-accent) 22%, transparent)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'color-mix(in oklab, var(--color-accent) 14%, transparent)'}
              >
                <Eye size={15} /> 정답 보기
              </button>
            </div>
          ) : (
            <div className="reveal">
              <div className="px-7 pt-6 pb-2"
                   style={{ borderTop: '1px solid var(--color-border-soft)' }}>
                <p className="text-[11px] uppercase tracking-[0.18em] mb-3"
                   style={{ color: 'var(--color-success)' }}>정답</p>
                <div className="prose max-w-none"
                     style={{ fontSize: '1rem', lineHeight: 1.78 }}>
                  <Markdown>{card.answer_md}</Markdown>
                </div>
              </div>

              {card.rationale_md && (
                <div className="px-7 pt-5 pb-2"
                     style={{ borderTop: '1px solid var(--color-border-soft)' }}>
                  <p className="text-[11px] uppercase tracking-[0.18em] mb-3"
                     style={{ color: 'var(--color-secondary)' }}>해설</p>
                  <div className="prose max-w-none"
                       style={{ fontSize: '0.93rem', lineHeight: 1.74, color: 'var(--color-text-dim)' }}>
                    <Markdown>{card.rationale_md}</Markdown>
                  </div>
                </div>
              )}

              {/* Rating row */}
              <div className="px-7 pt-6 pb-7"
                   style={{ borderTop: '1px solid var(--color-border-soft)' }}>
                <div className="grid grid-cols-4 gap-2.5">
                  {RATINGS.map(r => (
                    <button
                      key={r.value}
                      onClick={() => submit(r.value)}
                      disabled={submitting}
                      className="py-3 px-3 rounded-lg text-[13px] font-semibold flex flex-col items-center gap-0.5 transition-all disabled:opacity-50"
                      style={{
                        background: 'transparent',
                        color: r.varColor,
                        border: `1px solid color-mix(in oklab, ${r.varColor} 38%, transparent)`,
                      }}
                      onMouseEnter={(e) => {
                        if (!submitting)
                          e.currentTarget.style.background = `color-mix(in oklab, ${r.varColor} 14%, transparent)`
                      }}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      title={`${r.label} — ${r.value}`}
                    >
                      <span>{r.label}</span>
                      <span className="text-[11px] opacity-75">{r.hint}</span>
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-center mt-3.5 leading-relaxed"
                   style={{ color: 'var(--color-text-faint)' }}>
                  FSRS-6이 다음 복습 일자를 자동으로 결정합니다 ·  Again→즉시 재시도, Easy→길게 연기
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
