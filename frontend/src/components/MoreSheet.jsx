import { useEffect } from 'react'
import { Search, FileQuestion, GraduationCap, BookOpen, Sliders, X } from 'lucide-react'

// Mobile More-sheet — secondary tabs only (primary is in BottomNav)
const SECONDARY = [
  { id: 'summary',     label: 'Summary', icon: BookOpen },
  { id: 'lecture',     label: '강의',    icon: GraduationCap },
  { id: 'interactive', label: '실험실',  icon: Sliders },
  { id: 'quiz',        label: 'Quiz',    icon: FileQuestion },
  { id: 'search',      label: '검색',    icon: Search },
]

/**
 * Bottom sheet drawer for overflow tabs (Galaxy / One UI pattern).
 * Tap a tile → switches tab + closes sheet. Tap backdrop → closes.
 */
export default function MoreSheet({ open, tab, onChange, onClose }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <>
      <div className="sheet-backdrop" onClick={onClose} />
      <div className="sheet" role="dialog" aria-label="More tabs">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{
            fontSize: 16, fontWeight: 700, color: 'var(--color-text-bright)',
            margin: 0, letterSpacing: '-0.01em',
          }}>
            모든 탭
          </h3>
          <button
            onClick={onClose}
            data-tap
            style={{
              border: 0, background: 'var(--color-surface-2)',
              borderRadius: 10, padding: 8, cursor: 'pointer',
              color: 'var(--color-text-dim)',
            }}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 10,
        }}>
          {SECONDARY.map(t => {
            const Icon = t.icon
            const isActive = tab === t.id
            return (
              <button
                key={t.id}
                data-tap
                onClick={() => { onChange(t.id); onClose() }}
                style={{
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  gap: 6,
                  padding: '16px 8px',
                  background: isActive ? 'var(--color-accent-soft)' : 'var(--color-surface-2)',
                  border: `1px solid ${isActive ? 'var(--color-accent)' : 'var(--color-border-soft)'}`,
                  borderRadius: 14,
                  color: isActive ? 'var(--color-accent)' : 'var(--color-text)',
                  fontSize: 12.5,
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  minHeight: 76,
                  transition: 'background 140ms ease',
                }}
              >
                <Icon size={22} strokeWidth={isActive ? 2.2 : 1.8} />
                <span>{t.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </>
  )
}
