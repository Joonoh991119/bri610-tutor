import { useState, useEffect, useRef } from 'react'
import { Database, ChevronDown } from 'lucide-react'
import { api } from '../api'

export default function DBStatusPanel({ status, compact = false }) {
  const [open, setOpen] = useState(false)
  const [stats, setStats] = useState(null)
  const ref = useRef(null)

  useEffect(() => {
    if (open && !stats) {
      api.dbStats().then(setStats).catch(() => {})
    }
  }, [open])

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const modelName = status?.chat_model?.split('/')[1]?.split(':')[0] || '?'

  return (
    <div className={`relative ${compact ? '' : 'ml-auto'}`} ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 ${compact ? 'px-2 py-1.5' : 'px-2 py-1'} rounded hover:bg-surface-2 transition-colors`}
        aria-label="Backend status"
      >
        <span className={`w-2 h-2 rounded-full ${status?.status === 'ok' ? 'bg-success' : 'bg-error'}`} />
        {!compact && (
          <span className="text-[11px] text-text-dim">
            {status?.status === 'ok'
              ? `${modelName} · ${status.db?.embedded || 0} vectors`
              : 'Backend offline'}
          </span>
        )}
        <ChevronDown size={10} className={`text-text-dim transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && status?.status === 'ok' && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-surface border border-border rounded-lg shadow-xl z-50 p-4 text-xs">
          <div className="flex items-center gap-2 mb-3 text-text-bright font-medium">
            <Database size={14} className="text-accent" />
            Database Status
          </div>

          {/* Slides */}
          <div className="mb-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider mb-1">Slides</div>
            <table className="w-full">
              <thead>
                <tr className="text-text-dim">
                  <th className="text-left font-normal pb-1">Lecture</th>
                  <th className="text-right font-normal pb-1">Slides</th>
                  <th className="text-right font-normal pb-1">Embedded</th>
                </tr>
              </thead>
              <tbody>
                {stats?.slides?.map(s => (
                  <tr key={s.lecture} className="border-t border-border/50">
                    <td className="py-0.5 text-text">{s.lecture}</td>
                    <td className="py-0.5 text-right">{s.total}</td>
                    <td className="py-0.5 text-right">
                      <span className={s.embedded === s.total ? 'text-success' : 'text-error'}>
                        {s.embedded}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Textbooks */}
          <div className="mb-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider mb-1">Textbooks</div>
            <table className="w-full">
              <thead>
                <tr className="text-text-dim">
                  <th className="text-left font-normal pb-1">Book</th>
                  <th className="text-right font-normal pb-1">Pages</th>
                  <th className="text-right font-normal pb-1">Text</th>
                  <th className="text-right font-normal pb-1">Image</th>
                </tr>
              </thead>
              <tbody>
                {stats?.textbooks?.map(b => (
                  <tr key={b.book} className="border-t border-border/50">
                    <td className="py-0.5 text-text">{b.book.replace('_', ' ').slice(0, 18)}</td>
                    <td className="py-0.5 text-right">{b.total}</td>
                    <td className="py-0.5 text-right">
                      <span className={b.text_emb === b.total ? 'text-success' : 'text-error'}>
                        {b.text_emb}
                      </span>
                    </td>
                    <td className="py-0.5 text-right text-text-dim">{b.img_emb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Model info */}
          <div className="border-t border-border pt-2 space-y-1 text-text-dim">
            <div>Chat: <span className="text-text">{status.chat_model}</span></div>
            <div>Embed: <span className="text-text">{status.embed_model}</span></div>
            <div>Retrieval: <span className="text-text">{status.retrieval}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}
