import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { api } from '../api'

export default function SearchPanel({ lectures }) {
  const [query, setQuery] = useState('')
  const [source, setSource] = useState('all')
  const [lecture, setLecture] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState(null)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await api.search(query, source, lecture, 12)
      setResults(res)
    } catch (e) {
      setResults([])
    }
    setLoading(false)
  }

  return (
    <div className="h-full flex">
      {/* Results list */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-surface-2">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder="Search slides & textbook..."
            className="flex-1 bg-surface border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent/50"
          />
          <select value={source} onChange={e => setSource(e.target.value)} className="bg-surface border border-border rounded px-2 py-2 text-xs text-text-dim">
            <option value="all">All</option>
            <option value="slides">Slides only</option>
            <option value="textbook">Textbook only</option>
          </select>
          <select value={lecture || ''} onChange={e => setLecture(e.target.value || null)} className="bg-surface border border-border rounded px-2 py-2 text-xs text-text-dim">
            <option value="">All lectures</option>
            {lectures?.lectures?.map(l => <option key={l.id} value={l.id}>{l.id}</option>)}
          </select>
          <button onClick={search} disabled={loading} className="px-3 py-2 bg-accent rounded text-bg text-sm">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {results.map((r, i) => (
            <button
              key={i}
              onClick={() => setPreview(r)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                preview === r ? 'border-accent/40 bg-accent/5' : 'border-border bg-surface hover:bg-surface-2'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  r.source === 'slide' ? 'bg-slide/10 text-slide' : 'bg-book/10 text-book'
                }`}>
                  {r.source === 'slide' ? `📑 ${r.lecture} p${r.page}` : `📖 Ch.${r.chapter}`}
                </span>
                <span className="text-[10px] text-text-dim">score: {r.score}</span>
              </div>
              <p className="text-xs text-text-dim line-clamp-2">
                {r.source === 'slide' ? r.title : `${r.section_title} (pp.${r.pages})`}
              </p>
            </button>
          ))}
          {results.length === 0 && !loading && (
            <p className="text-center text-text-dim text-sm mt-10">Search to find relevant content</p>
          )}
        </div>
      </div>

      {/* Preview pane */}
      <div className="w-[45%] border-l border-border bg-surface overflow-y-auto p-4">
        {preview ? (
          <div>
            <div className="mb-3">
              <span className={`text-xs px-2 py-0.5 rounded ${
                preview.source === 'slide' ? 'bg-slide/10 text-slide' : 'bg-book/10 text-book'
              }`}>
                {preview.source === 'slide' ? `${preview.lecture} Slide ${preview.page}` : `Dayan & Abbott Ch.${preview.chapter} §${preview.section}`}
              </span>
            </div>
            {preview.source === 'slide' && (
              <img
                src={api.slideImage(preview.lecture, preview.page)}
                alt="slide"
                className="rounded-lg mb-3 w-full"
              />
            )}
            <h3 className="text-sm font-semibold text-text-bright mb-2">
              {preview.source === 'slide' ? preview.title : preview.section_title}
            </h3>
            <pre className="text-xs text-text-dim whitespace-pre-wrap leading-relaxed font-sans">
              {preview.content}
            </pre>
          </div>
        ) : (
          <p className="text-center text-text-dim text-sm mt-20">Select a result to preview</p>
        )}
      </div>
    </div>
  )
}
