import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../api'

export default function SlideViewer({ lectures }) {
  const lectureList = lectures?.lectures ?? []
  const firstLecture = lectureList[0]?.id ?? 'L3'
  const [lecture, setLecture] = useState(firstLecture)
  const [page, setPage] = useState(1)
  const pageMap = useMemo(() => {
    const m = {}
    for (const l of lectureList) m[l.id] = l.slides ?? 1
    return m
  }, [lectureList])
  const maxPage = pageMap[lecture] || 1

  const go = (delta) => {
    const next = page + delta
    if (next >= 1 && next <= maxPage) setPage(next)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center gap-3 px-4 py-2 bg-surface-2 border-b border-border">
        <select
          value={lecture}
          onChange={e => { setLecture(e.target.value); setPage(1); }}
          className="bg-surface border border-border rounded px-2 py-1.5 text-xs text-text-dim"
        >
          {lectures?.lectures?.map(l => (
            <option key={l.id} value={l.id}>{l.id}: {l.title.slice(0, 50)}</option>
          ))}
        </select>
        <div className="flex items-center gap-1">
          <button onClick={() => go(-1)} disabled={page <= 1} className="p-1 rounded hover:bg-surface disabled:opacity-30">
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs text-text-dim w-20 text-center">{page} / {maxPage}</span>
          <button onClick={() => go(1)} disabled={page >= maxPage} className="p-1 rounded hover:bg-surface disabled:opacity-30">
            <ChevronRight size={16} />
          </button>
        </div>
        <input
          type="range"
          min={1}
          max={maxPage}
          value={page}
          onChange={e => setPage(Number(e.target.value))}
          className="flex-1 max-w-xs accent-accent"
        />
      </div>

      {/* Slide image */}
      <div className="flex-1 flex items-center justify-center p-4 bg-bg overflow-hidden">
        <img
          src={api.slideImage(lecture, page)}
          alt={`${lecture} slide ${page}`}
          className="max-h-full max-w-full object-contain rounded-lg shadow-lg"
        />
      </div>

      {/* Thumbnail strip */}
      <div className="flex gap-1 px-4 py-2 bg-surface-2 border-t border-border overflow-x-auto">
        {Array.from({ length: Math.min(maxPage, 20) }, (_, i) => {
          const p = Math.max(1, Math.round((i / 19) * (maxPage - 1)) + 1)
          return (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`shrink-0 w-12 h-8 rounded border text-[9px] ${
                page === p ? 'border-accent text-accent' : 'border-border text-text-dim hover:border-text-dim'
              }`}
            >
              {p}
            </button>
          )
        })}
      </div>
    </div>
  )
}
