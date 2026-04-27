import { MessageCircle, Timer, Brain, Activity, MoreHorizontal } from 'lucide-react'

/**
 * One UI / Galaxy bottom navigation.
 *
 * 5 primary tabs (Tutor / 1h Course / Dashboard / SRS / More).
 * The "more" button triggers a bottom sheet for everything else.
 */
const PRIMARY = [
  { id: 'chat',    label: 'Tutor',   icon: MessageCircle },
  { id: 'course',  label: '1h 코스',  icon: Timer },
  { id: 'mastery', label: '대시보드', icon: Activity },
  { id: 'srs',     label: '복습',    icon: Brain },
]

export default function BottomNav({ tab, onChange, onMoreClick, moreActive }) {
  return (
    <nav className="bottom-nav md:hidden" aria-label="Primary navigation">
      {PRIMARY.map(t => {
        const Icon = t.icon
        const isActive = tab === t.id
        return (
          <button
            key={t.id}
            data-active={isActive}
            data-tap
            onClick={() => onChange(t.id)}
            aria-label={t.label}
          >
            <Icon size={22} strokeWidth={isActive ? 2.2 : 1.8} />
            <span>{t.label}</span>
          </button>
        )
      })}
      <button
        data-active={moreActive}
        data-tap
        onClick={onMoreClick}
        aria-label="More tabs"
      >
        <MoreHorizontal size={22} strokeWidth={moreActive ? 2.2 : 1.8} />
        <span>더보기</span>
      </button>
    </nav>
  )
}
