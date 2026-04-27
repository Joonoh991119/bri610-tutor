/**
 * PersonaHeader.jsx — Persona avatar + gamification stats bar.
 *
 * Replaces the plain "N" brand block in App.jsx header.
 * Receives `me` (from /api/me) and `onSrsClick` callback.
 *
 * Visual structure (no emoji — Lucide vector icons only):
 *   [ Avatar bubble ] [ Name + greeting ] [ Flame streak | Lv N | XP bar | reviewed/due ] [ MasteryStrip ]
 *
 * Streak tier colors (light scientific palette):
 *   0–2 days → muted info blue
 *   3–6     → moss-teal secondary
 *   7+      → primary journal blue (active)
 */
import { Flame } from 'lucide-react'
import MasteryStrip from './MasteryStrip'

// Avatar color by streak tier — uses CSS variables where possible
function avatarColor(streakDays) {
  if (streakDays >= 7) return 'var(--color-accent)'         // active journal blue
  if (streakDays >= 3) return 'var(--color-secondary)'      // moss-teal secondary
  return 'var(--color-text-dim)'                             // calm neutral
}

function avatarGlow(streakDays) {
  if (streakDays >= 7) return '0 0 0 3px color-mix(in oklab, var(--color-accent) 20%, transparent)'
  if (streakDays >= 3) return '0 0 0 2px color-mix(in oklab, var(--color-secondary) 18%, transparent)'
  return 'none'
}

// Greeting line pulled from last_topic or fallback
function greeting(me) {
  if (!me) return '오늘도 한 페이지씩!'
  const topic = me.last_topic
  if (topic) return `${topic} 이어서 갈까요?`
  if (me.streak_days >= 7)  return `${me.streak_days}일 연속! 오늘도 기세를 이어요.`
  if (me.streak_days >= 3)  return `${me.streak_days}일째 꾸준히 — 잘하고 있어요.`
  return '오늘도 한 페이지씩!'
}

export default function PersonaHeader({ me, onSrsClick }) {
  const streak     = me?.streak_days  ?? 0
  const level      = me?.level        ?? 1
  const xpProg     = me?.xp_progress  ?? { xp_current_level: 0, xp_next_level: 100, pct: 0 }
  const reviewed   = me?.today_reviewed ?? 0
  const due        = me?.due_count      ?? 0
  const aColor     = avatarColor(streak)
  const aGlow      = avatarGlow(streak)
  const greetText  = greeting(me)

  return (
    <div
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '0',          // outer padding from header
        minWidth: 0, flexWrap: 'nowrap',
      }}
    >
      {/* ── Avatar bubble ─────────────────────────────────────────── */}
      <div
        style={{
          width: '36px', height: '36px', borderRadius: '10px', flexShrink: 0,
          background: `color-mix(in oklab, ${aColor} 20%, var(--color-surface-2))`,
          border: `1.5px solid color-mix(in oklab, ${aColor} 55%, transparent)`,
          boxShadow: aGlow,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: '15px', lineHeight: 1,
          color: aColor,
          transition: 'box-shadow 0.8s ease, border-color 0.8s ease, background 0.8s ease',
          userSelect: 'none',
        }}
      >
        뉴
      </div>

      {/* ── Name + greeting ───────────────────────────────────────── */}
      <div style={{ minWidth: 0 }}>
        <div style={{
          fontSize: '13px', fontWeight: 700,
          color: 'var(--color-text-bright)', lineHeight: 1.2,
          letterSpacing: '-0.015em',
        }}>
          뉴런쌤
        </div>
        <div style={{
          fontSize: '10.5px', color: 'var(--color-text-dim)',
          lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          maxWidth: '180px',
        }}>
          {greetText}
        </div>
      </div>

      {/* ── Divider ───────────────────────────────────────────────── */}
      <div style={{
        width: '1px', height: '28px', flexShrink: 0,
        background: 'var(--color-border-soft)',
        marginLeft: '4px', marginRight: '4px',
      }} />

      {/* ── Compact stats: streak + due-today only (XP/level/MasteryStrip moved to /mastery dashboard) ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '4px',
          fontSize: '12px', fontWeight: 600,
          color: streak >= 3 ? 'var(--color-accent)' : 'var(--color-text-dim)',
        }}>
          <Flame size={13} strokeWidth={1.8} />
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>{streak}</span>
          <span style={{ fontSize: '10.5px', fontWeight: 400, color: 'var(--color-text-faint)' }}>일</span>
        </div>

        <button onClick={onSrsClick} style={{
          fontSize: '11px', color: 'var(--color-text-dim)',
          display: 'flex', alignItems: 'center', gap: '3px',
          fontVariantNumeric: 'tabular-nums',
          background: 'transparent', border: 0, cursor: 'pointer', padding: 0,
        }}>
          <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{reviewed}</span>
          <span style={{ opacity: 0.5 }}>/</span>
          <span>{due + reviewed}</span>
          <span style={{ opacity: 0.5, fontSize: '10px', marginLeft: '1px' }}>카드</span>
        </button>
      </div>
    </div>
  )
}
