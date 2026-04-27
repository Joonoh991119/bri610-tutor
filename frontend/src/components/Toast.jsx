/**
 * Toast.jsx — In-app notification system (CSS-only animations, no libraries)
 *
 * Three toast types:
 *   xp       — small chip near rating buttons (1.5s)
 *   level_up — full-width banner from top with confetti shimmer (3.5s)
 *   badge    — corner card with badge icon (3s)
 *
 * Usage:
 *   wrap your app in <ToastProvider>
 *   const { push } = useToast()
 *   push({ type: 'xp', xp: 10 })
 *   push({ type: 'level_up', title: '레벨 5!', subtitle: '...' })
 *   push({ type: 'badge', badge: 'streak_3', name: '3일 연속' })
 */
import { createContext, useCallback, useContext, useRef, useState } from 'react'
import {
  Sparkles, Star, Flame, Award, Lightbulb, FunctionSquare,
  Sunrise, Moon
} from 'lucide-react'

// Lucide icon component map (per badge id; no emoji)
const BADGE_ICON_MAP = {
  Award, Flame, Lightbulb, FunctionSquare, Sunrise, Moon,
}

// ── Internal keyframe definitions injected once ──────────────────────────────
const STYLE_ID = 'toast-keyframes'
function injectStyles() {
  if (document.getElementById(STYLE_ID)) return
  const s = document.createElement('style')
  s.id = STYLE_ID
  s.textContent = `
    @keyframes toast-slide-down {
      from { opacity: 0; transform: translateY(-14px) scale(0.97); }
      to   { opacity: 1; transform: translateY(0)    scale(1);     }
    }
    @keyframes toast-fade-out {
      from { opacity: 1; }
      to   { opacity: 0; transform: scale(0.95); }
    }
    @keyframes toast-xp-float {
      0%   { opacity: 0; transform: translateY(0)   scale(0.9); }
      20%  { opacity: 1; transform: translateY(-6px) scale(1.06); }
      80%  { opacity: 1; transform: translateY(-8px) scale(1);   }
      100% { opacity: 0; transform: translateY(-16px) scale(0.9);}
    }
    @keyframes toast-shimmer {
      0%   { background-position: -200% center; }
      100% { background-position:  200% center; }
    }
    @keyframes confetti-spin {
      0%   { transform: rotate(0deg)   scale(1); }
      50%  { transform: rotate(180deg) scale(1.1); }
      100% { transform: rotate(360deg) scale(1); }
    }
    .toast-enter { animation: toast-slide-down 280ms cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
    .toast-exit  { animation: toast-fade-out   240ms ease-in          forwards; }
    .toast-xp    { animation: toast-xp-float   1.5s  ease-out         forwards; }
    .toast-shimmer-bg {
      background: linear-gradient(
        90deg,
        var(--color-accent-soft) 0%,
        color-mix(in oklab, var(--color-accent) 25%, var(--color-accent-soft)) 50%,
        var(--color-accent-soft) 100%
      );
      background-size: 200% auto;
      animation: toast-shimmer 1.8s linear infinite;
    }
  `
  document.head.appendChild(s)
}

// ── Context ───────────────────────────────────────────────────────────────────
const ToastCtx = createContext({ push: () => {} })

let _id = 0
const uid = () => ++_id

export function ToastProvider({ children }) {
  injectStyles()
  const [toasts, setToasts] = useState([])
  const timers = useRef({})

  const dismiss = useCallback((id) => {
    setToasts(t => t.map(x => x.id === id ? { ...x, exiting: true } : x))
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 260)
  }, [])

  const push = useCallback((msg) => {
    const id  = uid()
    const ttl = msg.type === 'xp' ? 1500 : msg.type === 'level_up' ? 3500 : 3000
    setToasts(t => [...t, { ...msg, id, exiting: false }])
    timers.current[id] = setTimeout(() => dismiss(id), ttl)
  }, [dismiss])

  return (
    <ToastCtx.Provider value={{ push }}>
      {children}
      <ToastLayer toasts={toasts} dismiss={dismiss} />
    </ToastCtx.Provider>
  )
}

export function useToast() {
  return useContext(ToastCtx)
}

// ── Rendering layer ───────────────────────────────────────────────────────────
function ToastLayer({ toasts, dismiss }) {
  const xpToasts     = toasts.filter(t => t.type === 'xp')
  const bigToasts    = toasts.filter(t => t.type !== 'xp')

  return (
    <>
      {/* XP chips — fixed bottom-right near rating area */}
      <div
        style={{
          position: 'fixed', bottom: '96px', right: '32px',
          zIndex: 9000, display: 'flex', flexDirection: 'column', gap: '6px',
          alignItems: 'flex-end', pointerEvents: 'none',
        }}
      >
        {xpToasts.map(t => <XpChip key={t.id} t={t} />)}
      </div>

      {/* Banner / badge toasts — top center */}
      <div
        style={{
          position: 'fixed', top: '64px', left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 9100, display: 'flex', flexDirection: 'column', gap: '8px',
          alignItems: 'center', width: 'min(480px, 92vw)',
        }}
      >
        {bigToasts.map(t =>
          t.type === 'level_up'
            ? <LevelUpBanner key={t.id} t={t} dismiss={dismiss} />
            : <BadgeCard key={t.id} t={t} dismiss={dismiss} />
        )}
      </div>
    </>
  )
}

function XpChip({ t }) {
  return (
    <div
      className="toast-xp"
      style={{
        background: 'color-mix(in oklab, var(--color-accent) 18%, var(--color-surface))',
        border: '1px solid color-mix(in oklab, var(--color-accent) 40%, transparent)',
        color: 'var(--color-accent)',
        borderRadius: '999px',
        padding: '4px 12px',
        fontSize: '13px',
        fontWeight: 700,
        letterSpacing: '-0.01em',
        whiteSpace: 'nowrap',
        boxShadow: '0 2px 12px rgba(0,0,0,0.35)',
      }}
    >
      +{t.xp} XP
    </div>
  )
}

function LevelUpBanner({ t, dismiss }) {
  return (
    <div
      className={`toast-shimmer-bg ${t.exiting ? 'toast-exit' : 'toast-enter'}`}
      onClick={() => dismiss(t.id)}
      style={{
        width: '100%',
        borderRadius: '12px',
        border: '1px solid color-mix(in oklab, var(--color-accent) 45%, transparent)',
        padding: '16px 20px',
        cursor: 'pointer',
        boxShadow: '0 4px 24px rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', gap: '14px',
      }}
    >
      {/* Confetti icon */}
      <span style={{ animation: 'confetti-spin 1.2s ease-in-out infinite', display: 'inline-block' }}>
        <Star size={28} style={{ color: 'var(--color-accent)' }} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: 'var(--color-text-bright)', fontWeight: 700, fontSize: '15px',
          letterSpacing: '-0.02em', lineHeight: 1.3,
        }}>
          {t.title}
        </div>
        {t.subtitle && (
          <div style={{ color: 'var(--color-text-dim)', fontSize: '12px', marginTop: '2px' }}>
            {t.subtitle}
          </div>
        )}
      </div>
      <Sparkles size={18} style={{ color: 'var(--color-accent)', opacity: 0.7, flexShrink: 0 }} />
    </div>
  )
}

// Lucide icon name per badge (no emoji — vector + academic palette).
const BADGE_ICON_NAMES = {
  first_card:    'Award',
  streak_3:      'Flame',
  streak_7:      'Flame',
  streak_30:     'Flame',
  concept_mover: 'Lightbulb',
  derive_master: 'FunctionSquare',
  early_bird:    'Sunrise',
  nightowl:      'Moon',
}

function BadgeIcon({ name, size = 22 }) {
  const Cmp = BADGE_ICON_MAP[name] || Award
  return <Cmp size={size} strokeWidth={1.7} />
}

function BadgeCard({ t, dismiss }) {
  const iconName = BADGE_ICON_NAMES[t.badge] || 'Award'
  return (
    <div
      className={t.exiting ? 'toast-exit' : 'toast-enter'}
      onClick={() => dismiss(t.id)}
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: '8px',
        padding: '12px 14px',
        cursor: 'pointer',
        boxShadow: '0 6px 18px rgba(15, 23, 42, 0.12)',
        display: 'flex', alignItems: 'center', gap: '12px',
        width: '100%',
        color: 'var(--color-text)',
      }}
    >
      <span style={{
        color: 'var(--color-accent)',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 32, height: 32, borderRadius: 6,
        background: 'var(--color-accent-soft)',
        flexShrink: 0,
      }}>
        <BadgeIcon name={iconName} size={20} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: 'var(--color-text-dim)', fontSize: '10px', textTransform: 'uppercase',
          letterSpacing: '0.14em', marginBottom: '3px', fontWeight: 600,
        }}>
          획득 — Badge
        </div>
        <div style={{
          color: 'var(--color-text-bright)', fontWeight: 600, fontSize: '13.5px',
          fontFamily: 'var(--font-serif)',
        }}>
          {t.name || t.badge}
        </div>
      </div>
    </div>
  )
}
