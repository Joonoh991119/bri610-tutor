import { useState } from 'react'
import { BookOpen, Loader2 } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

export default function SummaryPanel({ lectures }) {
  const [lecture, setLecture] = useState('L3')
  const [focus, setFocus] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const res = await api.summary(lecture, focus || null)
      setResult(res)
    } catch (e) {
      setResult({ error: e.message })
    }
    setLoading(false)
  }

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto">
      <div className="bg-surface rounded-xl border border-border p-4 mb-6">
        <h2 className="text-sm font-semibold text-text-bright mb-3 flex items-center gap-2">
          <BookOpen size={16} className="text-accent" /> Exam Summary Generator
        </h2>
        <div className="flex gap-2">
          <select value={lecture} onChange={e => setLecture(e.target.value)} className="bg-surface-2 border border-border rounded px-3 py-2 text-sm">
            {lectures?.lectures?.map(l => (
              <option key={l.id} value={l.id}>{l.id}: {l.title.slice(0, 45)}</option>
            ))}
          </select>
          <input
            value={focus}
            onChange={e => setFocus(e.target.value)}
            placeholder="Focus topic (optional)..."
            className="flex-1 bg-surface-2 border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent/50"
          />
          <button onClick={generate} disabled={loading} className="px-4 py-2 bg-accent text-bg rounded text-sm font-medium">
            {loading ? <Loader2 size={14} className="animate-spin" /> : 'Summarize'}
          </button>
        </div>
      </div>

      {result?.error && <p className="text-error text-sm">Error: {result.error}</p>}

      {result?.summary && (
        <div className="bg-surface rounded-xl border border-border p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs px-2 py-0.5 rounded bg-accent/10 text-accent">{result.lecture}</span>
            <span className="text-xs text-text-dim">{result.title} · {result.slide_count} slides · {result.textbook_refs} textbook refs</span>
          </div>
          <div className="markdown-body text-sm">
            <Markdown>{result.summary}</Markdown>
          </div>
        </div>
      )}
    </div>
  )
}
