import { useState, useEffect } from 'react'
import { MessageCircle, Search, FileQuestion, BookOpen, Zap, ClipboardCheck } from 'lucide-react'
import { api } from './api'
import ChatPanel from './components/ChatPanel'
import SearchPanel from './components/SearchPanel'
import QuizPanel from './components/QuizPanel'
import SummaryPanel from './components/SummaryPanel'
import SlideViewer from './components/SlideViewer'
import ExamPanel from './components/ExamPanel'
import DBStatusPanel from './components/DBStatusPanel'

const TABS = [
  { id: 'chat', label: 'Tutor', icon: MessageCircle },
  { id: 'search', label: 'Search', icon: Search },
  { id: 'quiz', label: 'Quiz', icon: FileQuestion },
  { id: 'exam', label: 'Exam', icon: ClipboardCheck },
  { id: 'summary', label: 'Summary', icon: BookOpen },
  { id: 'slides', label: 'Slides', icon: Zap },
]

export default function App() {
  const [tab, setTab] = useState('chat')
  const [status, setStatus] = useState(null)
  const [lectures, setLectures] = useState(null)

  useEffect(() => {
    api.health().then(setStatus).catch(() => setStatus({ status: 'offline' }))
    api.lectures().then(setLectures).catch(() => {})
  }, [])

  return (
    <div className="h-screen flex flex-col">
      <header className="flex items-center gap-4 px-6 py-3 border-b border-border bg-surface">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-bg font-bold text-sm">N</div>
          <div>
            <h1 className="text-sm font-semibold text-text-bright leading-tight">BRI610 AI Tutor</h1>
            <p className="text-[11px] text-text-dim">Computational Neuroscience · SNU BCS</p>
          </div>
        </div>
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

      <main className="flex-1 overflow-hidden">
        {tab === 'chat' && <ChatPanel lectures={lectures} />}
        {tab === 'search' && <SearchPanel lectures={lectures} />}
        {tab === 'quiz' && <QuizPanel lectures={lectures} />}
        {tab === 'exam' && <ExamPanel lectures={lectures} />}
        {tab === 'summary' && <SummaryPanel lectures={lectures} />}
        {tab === 'slides' && <SlideViewer lectures={lectures} />}
      </main>
    </div>
  )
}
