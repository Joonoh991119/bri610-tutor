import { useState, useEffect, useRef } from 'react'
import { MessageCircle, Search, FileQuestion, BookOpen, Brain, GraduationCap, Timer, Sliders, Activity } from 'lucide-react'
import { api } from './api'
import ChatPanel from './components/ChatPanel'
import CoursePanel from './components/CoursePanel'
import InteractivePanel from './components/InteractivePanel'
import MasteryDashboard from './components/MasteryDashboard'
import SearchPanel from './components/SearchPanel'
import QuizPanel from './components/QuizPanel'
import SummaryPanel from './components/SummaryPanel'
import DBStatusPanel from './components/DBStatusPanel'
import SRSPanel from './components/SRSPanel'
import LecturePanel from './components/LecturePanel'
import PersonaHeader from './components/PersonaHeader'
import PersonaHeaderCompact from './components/PersonaHeaderCompact'
import BottomNav from './components/BottomNav'
import MoreSheet from './components/MoreSheet'
import { ToastProvider } from './components/Toast'

// Minimized navigation: 7 study-essential tabs total. Removed redundancy:
//   - Walkthrough (duplicated by Lecture mode)
//   - Exam (duplicated by 1h Course + Quiz quick mode)
//   - Slides (accessible via bank-card citations + summary refs)
const TABS = [
  { id: 'chat',        label: 'Tutor',   icon: MessageCircle },
  { id: 'course',      label: '1h 코스',  icon: Timer },
  { id: 'mastery',     label: '대시보드', icon: Activity },
  { id: 'srs',         label: '복습',    icon: Brain },
  { id: 'summary',     label: 'Summary', icon: BookOpen },
  { id: 'lecture',     label: '강의',    icon: GraduationCap },
  { id: 'interactive', label: '실험실',  icon: Sliders },
  { id: 'quiz',        label: 'Quiz',    icon: FileQuestion },
  { id: 'search',      label: '검색',    icon: Search },
]

const SECONDARY_IDS = new Set(['lecture', 'interactive', 'quiz', 'search'])

export default function App() {
  const [tab, setTab] = useState('chat')
  const [moreOpen, setMoreOpen] = useState(false)
  const [status, setStatus] = useState(null)
  const [lectures, setLectures] = useState(null)
  const [me, setMe] = useState(null)
  const meIntervalRef = useRef(null)

  useEffect(() => {
    api.health().then(setStatus).catch(() => setStatus({ status: 'offline' }))
    api.lectures().then(setLectures).catch(() => {})

    const fetchMe = () => api.me().then(setMe).catch(() => {})
    fetchMe()
    api.streakTouch().then(setMe).catch(() => {})

    meIntervalRef.current = setInterval(fetchMe, 30_000)
    return () => clearInterval(meIntervalRef.current)
  }, [])

  const goToSrs = () => setTab('srs')
  const refreshMe = () => api.me().then(setMe).catch(() => {})

  return (
    <ToastProvider>
      <div className="h-screen flex flex-col">
        {/* ── Desktop top header (≥ md) ──────────────────────────── */}
        <header className="hidden md:flex items-center gap-4 px-6 py-3 border-b border-border bg-surface">
          <PersonaHeader me={me} onSrsClick={goToSrs} />

          <nav className="flex gap-1 ml-6">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  tab === t.id
                    ? 'bg-accent/15 text-accent'
                    : 'text-text-dim hover:text-text hover:bg-surface-2'
                }`}
              >
                <t.icon size={14} />
                {t.label}
              </button>
            ))}
          </nav>
          <DBStatusPanel status={status} />
        </header>

        {/* ── Mobile compact header (< md) ───────────────────────── */}
        <header className="md:hidden flex items-center gap-3 px-4 py-2.5 border-b border-border bg-surface sticky top-0 z-30">
          <PersonaHeaderCompact me={me} />
          <DBStatusPanel status={status} compact />
        </header>

        <main className="flex-1 overflow-auto md:overflow-hidden">
          {tab === 'chat'        && <ChatPanel lectures={lectures} />}
          {tab === 'course'      && <CoursePanel />}
          {tab === 'mastery'     && <MasteryDashboard onJumpTo={() => setTab('srs')} />}
          {tab === 'srs'         && <SRSPanel onReviewComplete={refreshMe} />}
          {tab === 'summary'     && <SummaryPanel lectures={lectures} />}
          {tab === 'lecture'     && <LecturePanel />}
          {tab === 'interactive' && <InteractivePanel />}
          {tab === 'quiz'        && <QuizPanel lectures={lectures} />}
          {tab === 'search'      && <SearchPanel lectures={lectures} />}
        </main>

        {/* ── Mobile bottom nav (< md) ───────────────────────────── */}
        <BottomNav
          tab={tab}
          onChange={setTab}
          onMoreClick={() => setMoreOpen(true)}
          moreActive={SECONDARY_IDS.has(tab)}
        />

        <MoreSheet
          open={moreOpen}
          tab={tab}
          onChange={setTab}
          onClose={() => setMoreOpen(false)}
        />
      </div>
    </ToastProvider>
  )
}
