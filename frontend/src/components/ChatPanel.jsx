import { useState, useRef, useEffect } from 'react'
import { Send, Search, Layers, Brain, Sparkles, X } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

const STAGES = [
  { text: "Embedding query...", icon: Sparkles },
  { text: "Searching slides & textbooks...", icon: Search, delay: 2000 },
  { text: "Ranking results (RRF)...", icon: Layers, delay: 5000 },
  { text: "Generating answer...", icon: Brain, delay: 7000 },
]

function LoadingIndicator({ stage, elapsed }) {
  const StageIcon = STAGES[stage]?.icon || Sparkles
  return (
    <div className="flex items-center gap-3 text-sm text-text-dim py-2">
      <div className="flex gap-1">
        {STAGES.map((_, i) => (
          <div key={i} className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${
            i <= stage ? 'bg-accent' : 'bg-border'
          }`} />
        ))}
      </div>
      <StageIcon size={14} className="text-accent animate-pulse" />
      <span>{STAGES[stage]?.text}</span>
      <span className="text-[10px] text-text-dim/50 ml-auto">{elapsed}s</span>
    </div>
  )
}

export default function ChatPanel({ lectures }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loadingStage, setLoadingStage] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [lecture, setLecture] = useState(null)
  const [mode, setMode] = useState('auto')
  const [slidePreview, setSlidePreview] = useState(null)
  const endRef = useRef(null)
  const timersRef = useRef([])
  const elapsedRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loadingStage])

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
    if (elapsedRef.current) clearInterval(elapsedRef.current)
    elapsedRef.current = null
  }

  const send = async () => {
    if (!input.trim() || loadingStage !== null) return
    const msg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])

    // Start loading stages
    setLoadingStage(0)
    setElapsed(0)
    elapsedRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    STAGES.forEach((s, i) => {
      if (i > 0 && s.delay) {
        timersRef.current.push(setTimeout(() => setLoadingStage(i), s.delay))
      }
    })

    try {
      const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }))
      const res = await api.chat(msg, lecture, mode, history)
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.answer,
        sources: res.sources, agent: res.agent,
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Error: ${e.message}`,
      }])
    }
    clearTimers()
    setLoadingStage(null)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-3 px-4 py-2 bg-surface-2 border-b border-border text-xs">
        <select
          value={lecture || ''}
          onChange={e => setLecture(e.target.value || null)}
          className="bg-surface border border-border rounded px-2 py-1 text-text-dim"
        >
          <option value="">All Lectures</option>
          {lectures?.lectures?.map(l => (
            <option key={l.id} value={l.id}>{l.id}: {l.title.slice(0, 40)}</option>
          ))}
        </select>
        <div className="flex gap-1">
          {['auto', 'tutor', 'derive', 'exam'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-2 py-1 rounded text-[11px] ${
                mode === m ? 'bg-accent/20 text-accent' : 'text-text-dim hover:bg-surface'
              }`}
            >
              {m === 'auto' ? '🤖 Auto' : m === 'tutor' ? '💬 Tutor' : m === 'derive' ? '📐 Derive' : '📝 Exam'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-20 text-text-dim">
            <div className="text-4xl mb-4">🧠</div>
            <h2 className="text-lg font-semibold text-text-bright mb-2">BRI610 AI Tutor</h2>
            <p className="text-sm max-w-md mx-auto">
              Ask about membrane biophysics, Hodgkin-Huxley model, cable theory, or any lecture topic.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {[
                'Nernst equation 유도해줘',
                'HH model에서 m, n, h gate의 역할은?',
                'Cable theory의 length constant 의미',
                'GHK equation vs Nernst equation 차이',
              ].map(q => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-3 py-1.5 rounded-full bg-surface-2 border border-border text-xs text-text-dim hover:text-accent hover:border-accent/30 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] ${
              m.role === 'user'
                ? 'bg-accent/10 border border-accent/20 rounded-2xl rounded-br-sm px-4 py-2'
                : 'space-y-2'
            }`}>
              {m.role === 'user' ? (
                <p className="text-sm">{m.content}</p>
              ) : (
                <>
                  {m.agent && (
                    <span className="inline-block text-[10px] px-2 py-0.5 rounded bg-surface-2 text-text-dim mb-1">
                      🤖 {m.agent}
                    </span>
                  )}
                  <div className="markdown-body text-sm">
                    <Markdown>{m.content}</Markdown>
                  </div>
                  {m.sources?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {m.sources.map((s, j) => (
                        <button
                          key={j}
                          onClick={() => s.type === 'slide' && setSlidePreview({ lecture: s.lecture, page: s.page })}
                          className={`text-[10px] px-2 py-0.5 rounded-full border ${
                            s.type === 'slide'
                              ? 'border-slide/30 text-slide bg-slide/5 hover:bg-slide/15 cursor-pointer'
                              : 'border-book/30 text-book bg-book/5'
                          }`}
                        >
                          {s.type === 'slide' ? `📑 ${s.lecture} p.${s.page}` : `📖 Ch.${s.chapter} §${s.section}`}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}

        {loadingStage !== null && (
          <LoadingIndicator stage={loadingStage} elapsed={elapsed} />
        )}
        <div ref={endRef} />
      </div>

      {slidePreview && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8" onClick={() => setSlidePreview(null)}>
          <div className="relative max-w-4xl max-h-full" onClick={e => e.stopPropagation()}>
            <button onClick={() => setSlidePreview(null)} className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-surface flex items-center justify-center text-text-dim hover:text-text">
              <X size={16} />
            </button>
            <img
              src={api.slideImage(slidePreview.lecture, slidePreview.page)}
              alt={`${slidePreview.lecture} p${slidePreview.page}`}
              className="rounded-lg shadow-2xl max-h-[80vh] object-contain"
            />
            <p className="text-center text-xs text-text-dim mt-2">{slidePreview.lecture} — Slide {slidePreview.page}</p>
          </div>
        </div>
      )}

      <div className="border-t border-border bg-surface px-4 py-3">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about computational neuroscience..."
            className="flex-1 bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-text placeholder:text-text-dim/50 focus:outline-none focus:border-accent/50"
          />
          <button
            onClick={send}
            disabled={loadingStage !== null || !input.trim()}
            className="px-4 py-2.5 bg-accent text-bg rounded-lg font-medium text-sm hover:bg-accent-dim disabled:opacity-30 transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
