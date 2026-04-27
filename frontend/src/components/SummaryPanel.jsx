import { useState, useEffect } from 'react'
import { BookOpen, Loader2, RefreshCw, MessageSquare, Check } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

function timeAgo(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function SummaryPanel({ lectures }) {
  // Initial lecture: read from localStorage so cross-summary hyperlinks land
  // on the correct lecture (set by Markdown.jsx when user clicks #summary?lecture=Lx)
  const initialLecture = (() => {
    try {
      const stored = localStorage.getItem('bri610.summary.lecture')
      if (stored && /^L[2-8]$/.test(stored)) return stored
    } catch {}
    return 'L2'
  })()
  const [lecture, setLecture] = useState(initialLecture)

  // Listen for hashchange to update lecture when a cross-link is clicked while already on #summary
  useEffect(() => {
    const onHash = () => {
      try {
        const stored = localStorage.getItem('bri610.summary.lecture')
        if (stored && /^L[2-8]$/.test(stored) && stored !== lecture) {
          setLecture(stored)
        }
      } catch {}
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [lecture])
  const [focus, setFocus] = useState('')
  const [cached, setCached] = useState(null)
  const [liveResult, setLiveResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingType, setLoadingType] = useState(null) // 'cache' | 'live' | 'generate'
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackSaved, setFeedbackSaved] = useState(false)

  // Load cached summary on lecture change
  useEffect(() => {
    setCached(null)
    setLiveResult(null)
    setFeedbackOpen(false)
    setFeedbackText('')
    setFeedbackSaved(false)
    setLoadingType('cache')
    api.cachedSummary(lecture)
      .then(data => {
        setCached(data)
        if (data.feedback) setFeedbackText(data.feedback)
      })
      .catch(() => setCached(null))
      .finally(() => setLoadingType(null))
  }, [lecture])

  const generateAndCache = async () => {
    setLoading(true)
    setLoadingType('generate')
    try {
      const data = await api.generateSummary(lecture)
      setCached(data)
    } catch (e) {
      setLiveResult({ error: e.message })
    }
    setLoading(false)
    setLoadingType(null)
  }

  const searchWithFocus = async () => {
    if (!focus.trim()) return
    setLoading(true)
    setLoadingType('live')
    try {
      const res = await api.summary(lecture, focus)
      setLiveResult(res)
    } catch (e) {
      setLiveResult({ error: e.message })
    }
    setLoading(false)
    setLoadingType(null)
  }

  const submitFeedback = async () => {
    try {
      await api.submitFeedback(lecture, feedbackText)
      setFeedbackSaved(true)
      setTimeout(() => setFeedbackSaved(false), 3000)
    } catch (e) {
      alert('Failed to save feedback: ' + e.message)
    }
  }

  const result = liveResult || cached
  const isCached = !liveResult && cached

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto">
      {/* Controls */}
      <div className="bg-surface rounded-xl border border-border p-4 mb-6">
        <h2 className="text-sm font-semibold text-text-bright mb-3 flex items-center gap-2">
          <BookOpen size={16} className="text-accent" /> Lecture Summary
        </h2>
        <div className="flex gap-2 mb-2">
          <select value={lecture} onChange={e => setLecture(e.target.value)} className="bg-surface-2 border border-border rounded px-3 py-2 text-sm">
            {lectures?.lectures?.map(l => (
              <option key={l.id} value={l.id}>{l.id}: {l.title.slice(0, 45)}</option>
            ))}
          </select>
          {!cached && loadingType !== 'cache' && (
            <button
              onClick={generateAndCache}
              disabled={loading}
              className="px-4 py-2 bg-accent text-bg rounded text-sm font-medium flex items-center gap-1.5"
            >
              {loadingType === 'generate' ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Generate & Cache
            </button>
          )}
        </div>
        <div className="flex gap-2">
          <input
            value={focus}
            onChange={e => setFocus(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && searchWithFocus()}
            placeholder="Focus topic (e.g. 'cable equation derivation')..."
            className="flex-1 bg-surface-2 border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent/50"
          />
          <button
            onClick={searchWithFocus}
            disabled={loading || !focus.trim()}
            className="px-4 py-2 bg-surface-2 border border-border rounded text-sm text-text-dim hover:text-accent disabled:opacity-30"
          >
            {loadingType === 'live' ? <Loader2 size={14} className="animate-spin" /> : 'Focus Search'}
          </button>
        </div>
      </div>

      {/* Loading */}
      {loadingType === 'cache' && (
        <div className="flex items-center justify-center py-12 text-text-dim text-sm">
          <Loader2 size={16} className="animate-spin mr-2" /> Loading cached summary...
        </div>
      )}
      {loadingType === 'generate' && (
        <div className="flex items-center justify-center py-12 text-text-dim text-sm">
          <Loader2 size={16} className="animate-spin mr-2" /> Generating summary with Qwen (30-60s)...
        </div>
      )}

      {/* Error */}
      {result?.error && <p className="text-error text-sm mb-4">Error: {result.error}</p>}

      {/* Summary display */}
      {(result?.summary) && !loading && (
        <div className="bg-surface rounded-xl border border-border p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs px-2 py-0.5 rounded bg-accent/10 text-accent">{lecture}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
              isCached ? 'bg-success/10 text-success' : 'bg-slide/10 text-slide'
            }`}>
              {isCached ? 'Cached' : 'Live'}
            </span>
            {isCached && cached.generated_at && (
              <span className="text-[10px] text-text-dim">generated {timeAgo(cached.generated_at)}</span>
            )}
            {cached && (
              <button
                onClick={generateAndCache}
                className="ml-auto text-[10px] text-text-dim hover:text-accent flex items-center gap-1"
                title="Regenerate summary"
              >
                <RefreshCw size={10} /> Regenerate
              </button>
            )}
          </div>

          <div className="markdown-body text-sm">
            <Markdown>{result.summary}</Markdown>
          </div>

          {/* Feedback section */}
          {isCached && (
            <div className="mt-6 border-t border-border pt-4">
              <button
                onClick={() => setFeedbackOpen(!feedbackOpen)}
                className="flex items-center gap-1.5 text-xs text-text-dim hover:text-accent"
              >
                <MessageSquare size={12} />
                {cached.feedback ? 'View / Edit Feedback' : 'Suggest Correction'}
              </button>

              {feedbackOpen && (
                <div className="mt-3 space-y-2">
                  <textarea
                    value={feedbackText}
                    onChange={e => setFeedbackText(e.target.value)}
                    placeholder="Note corrections, missing info, or emphasis changes..."
                    rows={3}
                    className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-text placeholder:text-text-dim/50 focus:outline-none focus:border-accent/50 resize-none"
                  />
                  <div className="flex items-center gap-2">
                    <button
                      onClick={submitFeedback}
                      disabled={!feedbackText.trim()}
                      className="px-3 py-1.5 bg-accent text-bg rounded text-xs font-medium disabled:opacity-30"
                    >
                      Save Feedback
                    </button>
                    {feedbackSaved && (
                      <span className="text-success text-xs flex items-center gap-1">
                        <Check size={12} /> Saved
                      </span>
                    )}
                    {cached.feedback_at && (
                      <span className="text-[10px] text-text-dim ml-auto">
                        last updated {timeAgo(cached.feedback_at)}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* No cached, no result, not loading */}
      {!result && !loading && loadingType !== 'cache' && (
        <div className="text-center py-12 text-text-dim text-sm">
          <BookOpen size={32} className="mx-auto mb-3 opacity-30" />
          <p>No cached summary for {lecture}.</p>
          <p className="mt-1">Click <strong>Generate & Cache</strong> to create one.</p>
        </div>
      )}
    </div>
  )
}
