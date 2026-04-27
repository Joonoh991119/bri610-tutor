import { useState, useEffect } from 'react'
import { FileQuestion, Loader2, Check, X, RotateCcw, BookOpen } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

/**
 * QuizPanel — pre-built bank surface (v0.7).
 *
 * Layout: lecture selector → fetched bank items (MCQ + short-answer) →
 * per-item answer + reveal + rationale flow. No live LLM call required.
 *
 * Take-home items (derivation/essay) are surfaced in a separate "더보기" tab.
 */
export default function QuizPanel({ lectures }) {
  const initialLecture = (() => {
    try { const s = localStorage.getItem('bri610.quiz.lecture'); if (s && /^L[2-8]$/.test(s)) return s } catch {}
    return 'L3'
  })()
  const [lecture, setLecture] = useState(initialLecture)
  const [tab, setTab] = useState('quiz') // 'quiz' | 'take_home'
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [answers, setAnswers] = useState({}) // { itemId: chosenKey | typedText }
  const [revealed, setRevealed] = useState({}) // { itemId: true }

  // Persist lecture
  useEffect(() => {
    try { localStorage.setItem('bri610.quiz.lecture', lecture) } catch {}
  }, [lecture])

  useEffect(() => {
    setItems([]); setAnswers({}); setRevealed({}); setError(null); setLoading(true)
    const fetcher = tab === 'take_home' ? api.takeHome : api.quizBank
    fetcher(lecture)
      .then(d => setItems(d.items || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [lecture, tab])

  const totalQuiz = tab === 'quiz' ? items.length : 0
  const correctCount = Object.entries(answers).reduce((acc, [id, ans]) => {
    const it = items.find(i => String(i.id) === String(id))
    if (!it || tab !== 'quiz' || !revealed[id]) return acc
    if (it.kind === 'mcq' && ans === it.correct_key) return acc + 1
    if (it.kind === 'short_answer') {
      const patterns = it.accept_patterns || []
      if (patterns.some(p => { try { return new RegExp(p).test(ans || '') } catch { return false } })) return acc + 1
    }
    return acc
  }, 0)

  const score = totalQuiz > 0 ? `${correctCount} / ${Object.keys(revealed).length}` : null
  const allRevealed = items.length > 0 && items.every(i => revealed[i.id])

  const reset = () => { setAnswers({}); setRevealed({}) }

  return (
    <div className="h-full overflow-y-auto p-6 pb-32 max-w-4xl mx-auto">
      {/* Controls */}
      <div className="bg-surface rounded-xl border border-border p-4 mb-6">
        <h2 className="text-sm font-semibold text-text-bright mb-3 flex items-center gap-2">
          <FileQuestion size={16} className="text-accent" /> Pre-built Bank
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <select value={lecture} onChange={e => setLecture(e.target.value)} className="bg-surface-2 border border-border rounded px-3 py-2 text-sm">
            {lectures?.lectures?.map(l => (
              <option key={l.id} value={l.id}>{l.id}: {l.title.slice(0, 40)}</option>
            ))}
          </select>
          <div className="inline-flex rounded border border-border overflow-hidden">
            <button onClick={() => setTab('quiz')} className={`px-3 py-2 text-xs ${tab === 'quiz' ? 'bg-accent text-bg' : 'bg-surface-2 text-text-dim'}`}>
              Quiz <span className="opacity-70">(MCQ + 단답)</span>
            </button>
            <button onClick={() => setTab('take_home')} className={`px-3 py-2 text-xs border-l border-border ${tab === 'take_home' ? 'bg-accent text-bg' : 'bg-surface-2 text-text-dim'}`}>
              Take-home <span className="opacity-70">(논술 + 유도)</span>
            </button>
          </div>
          {tab === 'quiz' && score !== null && (
            <span className="ml-auto text-xs text-text-dim">
              점수: <span className="text-success font-medium">{score}</span>
              <button onClick={reset} title="초기화" className="ml-2 text-text-dim hover:text-accent inline-flex items-center"><RotateCcw size={12} /></button>
            </span>
          )}
        </div>
      </div>

      {/* Loading / error */}
      {loading && (
        <div className="flex items-center justify-center py-12 text-text-dim text-sm">
          <Loader2 size={16} className="animate-spin mr-2" /> Loading bank...
        </div>
      )}
      {error && <p className="text-error text-sm">Error: {error}</p>}

      {/* Empty bank */}
      {!loading && !error && items.length === 0 && (
        <div className="text-center py-12 text-text-dim text-sm">
          <FileQuestion size={32} className="mx-auto mb-3 opacity-30" />
          <p>{lecture} 의 {tab === 'quiz' ? 'quiz' : 'take-home'} 뱅크가 비어있습니다.</p>
        </div>
      )}

      {/* Quiz items (MCQ + short-answer) */}
      {!loading && tab === 'quiz' && items.map((q, i) => (
        <QuizCard
          key={q.id}
          item={q}
          index={i}
          chosen={answers[q.id]}
          onChoose={v => setAnswers(p => ({ ...p, [q.id]: v }))}
          revealed={!!revealed[q.id]}
          onReveal={() => setRevealed(p => ({ ...p, [q.id]: true }))}
        />
      ))}

      {/* Take-home items */}
      {!loading && tab === 'take_home' && items.map((t, i) => (
        <TakeHomeCard
          key={t.id}
          item={t}
          index={i}
          revealed={!!revealed[t.id]}
          onReveal={() => setRevealed(p => ({ ...p, [t.id]: true }))}
        />
      ))}
    </div>
  )
}

// ─── Quiz card (MCQ + short-answer) ────────────────────────────────

function QuizCard({ item, index, chosen, onChoose, revealed, onReveal }) {
  const isMCQ = item.kind === 'mcq'
  const isCorrect = revealed && (
    isMCQ ? chosen === item.correct_key
          : (item.accept_patterns || []).some(p => { try { return new RegExp(p).test(chosen || '') } catch { return false } })
  )

  return (
    <div className="bg-surface rounded-xl border border-border p-5 mb-4">
      <div className="flex items-start gap-3 mb-3">
        <span className="text-xs font-bold text-accent bg-accent/10 rounded-full w-7 h-7 flex items-center justify-center shrink-0 mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[10px] uppercase tracking-wide text-text-dim">{isMCQ ? 'MCQ' : '단답'}</span>
            <span className="text-[10px] text-text-dim">난이도 {item.difficulty}/5</span>
            {item.bloom && <span className="text-[10px] text-text-dim">{item.bloom}</span>}
            {item.topic_tag && <span className="text-[10px] text-text-dim italic">#{item.topic_tag}</span>}
            {item.slide_ref && <span className="text-[10px] text-text-dim ml-auto">{item.slide_ref}</span>}
          </div>
          <div className="markdown-body text-sm text-text-bright"><Markdown>{item.prompt_md}</Markdown></div>
        </div>
      </div>

      {/* MCQ options */}
      {isMCQ && (
        <div className="space-y-1.5 mb-3 ml-10">
          {(item.choices || []).map(opt => {
            const sel = chosen === opt.key
            const isThisCorrect = revealed && opt.key === item.correct_key
            const isThisWrong = revealed && sel && opt.key !== item.correct_key
            return (
              <button
                key={opt.key}
                onClick={() => !revealed && onChoose(opt.key)}
                disabled={revealed}
                className={`w-full text-left px-3 py-2 rounded text-sm border transition-colors flex items-start gap-2 ${
                  isThisCorrect ? 'border-success bg-success/10 text-success' :
                  isThisWrong  ? 'border-error bg-error/10 text-error' :
                  sel          ? 'border-accent bg-accent/10' :
                                 'border-border hover:border-border/80'
                }`}
              >
                <span className="text-xs font-bold mt-0.5">{opt.key}.</span>
                <div className="flex-1 markdown-body text-sm"><Markdown>{opt.text}</Markdown></div>
                {isThisCorrect && <Check size={14} className="text-success" />}
                {isThisWrong && <X size={14} className="text-error" />}
              </button>
            )
          })}
        </div>
      )}

      {/* Short answer */}
      {!isMCQ && (
        <div className="ml-10 mb-3">
          <input
            value={chosen || ''}
            onChange={e => !revealed && onChoose(e.target.value)}
            disabled={revealed}
            placeholder="단답을 입력하세요..."
            className={`w-full bg-surface-2 border rounded px-3 py-2 text-sm focus:outline-none ${
              revealed ? (isCorrect ? 'border-success' : 'border-error') : 'border-border focus:border-accent/50'
            }`}
          />
        </div>
      )}

      {/* Reveal / rationale */}
      <div className="ml-10 flex items-center gap-3">
        {!revealed ? (
          <button onClick={onReveal} className="text-xs text-accent hover:underline">정답 확인</button>
        ) : (
          <span className={`text-xs font-medium ${isCorrect ? 'text-success' : 'text-error'}`}>
            {isCorrect ? '정답!' : '오답'}
            {!isMCQ && ` · 정답: ${item.correct_text}`}
            {isMCQ && ` · 정답: ${item.correct_key}`}
          </span>
        )}
      </div>

      {revealed && (
        <div className="ml-10 mt-3 p-3 bg-surface-2 rounded-lg text-xs">
          <div className="flex items-center gap-2 mb-1.5">
            <BookOpen size={12} className="text-accent" />
            <span className="text-text-dim font-medium">해설</span>
          </div>
          <div className="markdown-body text-xs text-text"><Markdown>{item.rationale_md}</Markdown></div>
        </div>
      )}
    </div>
  )
}

// ─── Take-home card (derivation + essay) ───────────────────────────

function TakeHomeCard({ item, index, revealed, onReveal }) {
  return (
    <div className="bg-surface rounded-xl border border-border p-5 mb-4">
      <div className="flex items-start gap-3 mb-3">
        <span className="text-xs font-bold text-accent bg-accent/10 rounded-full w-7 h-7 flex items-center justify-center shrink-0 mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-[10px] uppercase tracking-wide text-text-dim">{item.kind}</span>
            <span className="text-[10px] text-text-dim">{item.max_points}점</span>
            <span className="text-[10px] text-text-dim">{item.expected_time_min}분</span>
            {item.topic_tag && <span className="text-[10px] text-text-dim italic">#{item.topic_tag}</span>}
            {item.slide_ref && <span className="text-[10px] text-text-dim ml-auto">{item.slide_ref}</span>}
          </div>
          <div className="markdown-body text-sm text-text-bright"><Markdown>{item.prompt_md}</Markdown></div>
        </div>
      </div>

      <div className="ml-10 flex items-center gap-3">
        {!revealed ? (
          <button onClick={onReveal} className="text-xs text-accent hover:underline">모범답안 + 채점기준 펼치기</button>
        ) : (
          <span className="text-xs text-text-dim">— 본인 답안 작성 후 비교</span>
        )}
      </div>

      {revealed && (
        <>
          <div className="ml-10 mt-3 p-3 bg-surface-2 rounded-lg text-xs">
            <div className="text-text-dim font-medium mb-1.5">모범답안</div>
            <div className="markdown-body text-xs text-text"><Markdown>{item.model_answer_md}</Markdown></div>
          </div>
          <div className="ml-10 mt-2 p-3 bg-surface-2 rounded-lg text-xs">
            <div className="text-text-dim font-medium mb-1.5">채점 기준</div>
            <div className="markdown-body text-xs text-text"><Markdown>{item.rubric_md}</Markdown></div>
          </div>
        </>
      )}
    </div>
  )
}
