/**
 * MasteryStrip.jsx — 4-cell per-type mastery strip for PersonaHeader.
 *
 * Cells: recall / concept / application / proof
 * Each cell shows:
 *   - type label + color token
 *   - fill bar: ratio of cards rated good+ today vs total due for that type
 *     (falls back to today_correct / today_reviewed proportionally if per-type data absent)
 *
 * Click sends user to the SRS tab.
 * ~80 LOC as required.
 */
import { BookOpen, Lightbulb, Wrench, FlaskConical } from 'lucide-react'

const TYPES = [
  { key: 'recall',      label: '암기', icon: BookOpen,     color: 'var(--color-type-recall)'      },
  { key: 'concept',     label: '개념', icon: Lightbulb,    color: 'var(--color-type-concept)'     },
  { key: 'application', label: '응용', icon: Wrench,       color: 'var(--color-type-application)' },
  { key: 'proof',       label: '증명', icon: FlaskConical, color: 'var(--color-type-proof)'       },
]

/**
 * `me` — result from /api/me; contains today_reviewed, today_correct, due_count.
 * `mastery` — optional {recall: {done, total}, concept: ..., ...} from a future endpoint.
 * `onSrsClick` — callback to switch to SRS tab.
 */
export default function MasteryStrip({ me, mastery, onSrsClick }) {
  // Derive per-type fill ratio.
  // If mastery data provided, use it; otherwise distribute evenly from totals.
  const total    = me?.today_reviewed  ?? 0
  const correct  = me?.today_correct   ?? 0
  const dueCount = me?.due_count       ?? 0

  function fillFor(key) {
    if (mastery && mastery[key]) {
      const { done, total: tot } = mastery[key]
      return tot > 0 ? Math.min(1, done / tot) : 0
    }
    // Fallback: spread correct evenly across 4 types
    const share = correct / 4
    const denominator = (total / 4) + (dueCount / 4)
    return denominator > 0 ? Math.min(1, share / denominator) : 0
  }

  return (
    <div
      style={{ display: 'flex', gap: '6px', alignItems: 'stretch' }}
      title="이번 주 유형별 마스터리 — 클릭해서 복습 탭으로"
    >
      {TYPES.map(({ key, label, icon: Icon, color }) => {
        const fill = fillFor(key)
        return (
          <button
            key={key}
            onClick={onSrsClick}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              gap: '3px', padding: '5px 8px', borderRadius: '7px', cursor: 'pointer',
              background: `color-mix(in oklab, ${color} 9%, var(--color-surface-2))`,
              border: `1px solid color-mix(in oklab, ${color} 22%, transparent)`,
              transition: 'border-color 0.2s, background 0.2s',
              minWidth: '48px',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background =
                `color-mix(in oklab, ${color} 17%, var(--color-surface-2))`
              e.currentTarget.style.borderColor =
                `color-mix(in oklab, ${color} 40%, transparent)`
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background =
                `color-mix(in oklab, ${color} 9%, var(--color-surface-2))`
              e.currentTarget.style.borderColor =
                `color-mix(in oklab, ${color} 22%, transparent)`
            }}
          >
            <Icon size={11} style={{ color, opacity: 0.9 }} />
            <span style={{ fontSize: '10px', color, fontWeight: 600, lineHeight: 1 }}>
              {label}
            </span>
            {/* Fill bar */}
            <div style={{
              width: '100%', height: '3px', borderRadius: '2px',
              background: `color-mix(in oklab, ${color} 18%, transparent)`,
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${Math.round(fill * 100)}%`,
                background: color,
                borderRadius: '2px',
                transition: 'width 0.6s ease-out',
              }} />
            </div>
          </button>
        )
      })}
    </div>
  )
}
