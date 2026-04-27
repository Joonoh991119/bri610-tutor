import { Flame } from 'lucide-react'

/**
 * Compact persona header for narrow Galaxy-class screens.
 *
 * Layout: [Avatar] [Name + greeting] · [streak chip] [Lv chip]
 * No mastery strip, no XP bar, no due ratio — those move into SRS tab.
 */
function avatarColor(streakDays) {
  if (streakDays >= 7) return 'var(--color-accent)'
  if (streakDays >= 3) return 'var(--color-secondary)'
  return 'var(--color-text-dim)'
}

function greeting(me) {
  if (!me) return '오늘도 한 페이지씩!'
  if (me.last_topic) return `${me.last_topic} 이어서 갈까요?`
  if (me.streak_days >= 7) return `${me.streak_days}일 연속! 기세 유지.`
  if (me.streak_days >= 3) return `${me.streak_days}일째 — 잘하고 있어요.`
  return '오늘도 한 페이지씩!'
}

export default function PersonaHeaderCompact({ me }) {
  const streak = me?.streak_days ?? 0
  const level  = me?.level ?? 1
  const aColor = avatarColor(streak)
  const greetText = greeting(me)

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      width: '100%', minWidth: 0,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 11, flexShrink: 0,
        background: `color-mix(in oklab, ${aColor} 20%, var(--color-surface-2))`,
        border: `1.5px solid color-mix(in oklab, ${aColor} 55%, transparent)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: 14, color: aColor, userSelect: 'none',
      }}>
        뉴
      </div>

      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{
          fontSize: 14, fontWeight: 700, color: 'var(--color-text-bright)',
          lineHeight: 1.2, letterSpacing: '-0.01em',
        }}>
          뉴런쌤
        </div>
        <div style={{
          fontSize: 11, color: 'var(--color-text-dim)', lineHeight: 1.25,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {greetText}
        </div>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '4px 10px',
        background: 'var(--color-surface-2)',
        borderRadius: 999,
        fontSize: 11.5, fontVariantNumeric: 'tabular-nums',
        color: streak >= 3 ? 'var(--color-accent)' : 'var(--color-text-dim)',
        fontWeight: 600,
      }}>
        <Flame size={12} strokeWidth={1.8} />
        {streak}
      </div>

      <div style={{
        padding: '4px 8px',
        background: 'var(--color-surface-2)',
        borderRadius: 999,
        fontSize: 11.5, fontWeight: 700,
        color: 'var(--color-secondary)',
        fontVariantNumeric: 'tabular-nums',
      }}>
        Lv{level}
      </div>
    </div>
  )
}
