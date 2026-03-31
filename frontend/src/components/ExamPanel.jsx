import { useState } from 'react'
import { ClipboardCheck, Loader2, Send } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

export default function ExamPanel({ lectures }) {
  const [lecture, setLecture] = useState('L3')
  const [duration, setDuration] = useState(60)
  const [exam, setExam] = useState(null)
  const [loading, setLoading] = useState(false)

  // Grading state
  const [gradeQ, setGradeQ] = useState('')
  const [gradeA, setGradeA] = useState('')
  const [gradeResult, setGradeResult] = useState(null)
  const [grading, setGrading] = useState(false)

  const generateExam = async () => {
    setLoading(true)
    setExam(null)
    try {
      const res = await api.exam(lecture, duration)
      setExam(res)
    } catch (e) {
      setExam({ error: e.message })
    }
    setLoading(false)
  }

  const gradeAnswer = async () => {
    if (!gradeQ.trim() || !gradeA.trim()) return
    setGrading(true)
    setGradeResult(null)
    try {
      const res = await api.grade(gradeQ, gradeA, lecture)
      setGradeResult(res)
    } catch (e) {
      setGradeResult({ error: e.message })
    }
    setGrading(false)
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto space-y-6">
      {/* Exam Generator */}
      <div className="bg-surface rounded-xl border border-border p-4">
        <h2 className="text-sm font-semibold text-text-bright mb-3 flex items-center gap-2">
          <ClipboardCheck size={16} className="text-accent" /> Mock Exam Generator
        </h2>
        <div className="flex gap-2 items-end">
          <div>
            <label className="text-[10px] text-text-dim block mb-1">Lecture</label>
            <select value={lecture} onChange={e => setLecture(e.target.value)}
              className="bg-surface-2 border border-border rounded px-3 py-2 text-sm">
              {lectures?.lectures?.map(l => (
                <option key={l.id} value={l.id}>{l.id}: {l.title?.slice(0, 40)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-text-dim block mb-1">Duration (min)</label>
            <input type="number" value={duration} onChange={e => setDuration(Number(e.target.value))}
              min={30} max={180} className="w-20 bg-surface-2 border border-border rounded px-2 py-2 text-sm text-center" />
          </div>
          <button onClick={generateExam} disabled={loading}
            className="px-4 py-2 bg-accent text-bg rounded text-sm font-medium">
            {loading ? <Loader2 size={14} className="animate-spin" /> : 'Generate Exam'}
          </button>
        </div>
      </div>

      {/* Exam Content */}
      {exam?.error && <p className="text-error text-sm">Error: {exam.error}</p>}
      {exam?.exam && (
        <div className="bg-surface rounded-xl border border-border p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs px-2 py-0.5 rounded bg-accent/10 text-accent">{exam.lecture}</span>
            <span className="text-xs text-text-dim">Mock Exam</span>
          </div>
          <div className="markdown-body text-sm">
            <Markdown>{exam.exam}</Markdown>
          </div>
          {exam.sources?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-border">
              {exam.sources.map((s, i) => (
                <span key={i} className={`text-[10px] px-2 py-0.5 rounded-full border ${
                  s.type === 'slide' ? 'border-slide/30 text-slide bg-slide/5' : 'border-book/30 text-book bg-book/5'
                }`}>
                  {s.type === 'slide' ? `📑 ${s.lecture} p.${s.page}` : `📖 Ch.${s.chapter}`}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Answer Grading */}
      <div className="bg-surface rounded-xl border border-border p-4">
        <h2 className="text-sm font-semibold text-text-bright mb-3">Grade My Answer</h2>
        <div className="space-y-2">
          <div>
            <label className="text-[10px] text-text-dim block mb-1">Question</label>
            <textarea value={gradeQ} onChange={e => setGradeQ(e.target.value)}
              rows={2} placeholder="Paste or type the exam question..."
              className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-sm resize-none focus:outline-none focus:border-accent/50" />
          </div>
          <div>
            <label className="text-[10px] text-text-dim block mb-1">Your Answer</label>
            <textarea value={gradeA} onChange={e => setGradeA(e.target.value)}
              rows={4} placeholder="Type your answer here..."
              className="w-full bg-surface-2 border border-border rounded px-3 py-2 text-sm resize-none focus:outline-none focus:border-accent/50" />
          </div>
          <button onClick={gradeAnswer} disabled={grading || !gradeQ.trim() || !gradeA.trim()}
            className="flex items-center gap-1.5 px-4 py-2 bg-accent text-bg rounded text-sm font-medium disabled:opacity-30">
            {grading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Grade
          </button>
        </div>
      </div>

      {/* Grade Result */}
      {gradeResult?.error && <p className="text-error text-sm">Error: {gradeResult.error}</p>}
      {gradeResult?.grade && (
        <div className="bg-surface rounded-xl border border-border p-6">
          <h3 className="text-sm font-semibold text-text-bright mb-2">Feedback</h3>
          <div className="markdown-body text-sm">
            <Markdown>{gradeResult.grade}</Markdown>
          </div>
        </div>
      )}
    </div>
  )
}
