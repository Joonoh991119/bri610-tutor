import { useState } from 'react'
import { FileQuestion, Loader2, Check, X } from 'lucide-react'
import { api } from '../api'
import Markdown from './Markdown'

export default function QuizPanel({ lectures }) {
  const [topic, setTopic] = useState('')
  const [lecture, setLecture] = useState(null)
  const [difficulty, setDifficulty] = useState('medium')
  const [numQ, setNumQ] = useState(5)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [revealed, setRevealed] = useState({})
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setQuiz(null)
    setAnswers({})
    setRevealed({})
    try {
      const res = await api.quiz(topic, lecture, numQ, difficulty)
      setQuiz(res)
    } catch (e) {
      setQuiz({ error: e.message })
    }
    setLoading(false)
  }

  const questions = quiz?.questions || []

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto">
      {/* Generator */}
      <div className="bg-surface rounded-xl border border-border p-4 mb-6">
        <h2 className="text-sm font-semibold text-text-bright mb-3 flex items-center gap-2">
          <FileQuestion size={16} className="text-accent" /> Generate Quiz
        </h2>
        <div className="flex flex-wrap gap-2">
          <input
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && generate()}
            placeholder="Topic (e.g., Nernst equation, HH model)..."
            className="flex-1 min-w-[200px] bg-surface-2 border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent/50"
          />
          <select value={lecture || ''} onChange={e => setLecture(e.target.value || null)} className="bg-surface-2 border border-border rounded px-2 py-2 text-xs">
            <option value="">All</option>
            {lectures?.lectures?.map(l => <option key={l.id} value={l.id}>{l.id}</option>)}
          </select>
          <select value={difficulty} onChange={e => setDifficulty(e.target.value)} className="bg-surface-2 border border-border rounded px-2 py-2 text-xs">
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <input type="number" value={numQ} onChange={e => setNumQ(Number(e.target.value))} min={1} max={10} className="w-16 bg-surface-2 border border-border rounded px-2 py-2 text-xs text-center" />
          <button onClick={generate} disabled={loading} className="px-4 py-2 bg-accent text-bg rounded text-sm font-medium">
            {loading ? <Loader2 size={14} className="animate-spin" /> : 'Generate'}
          </button>
        </div>
      </div>

      {/* Questions */}
      {quiz?.error && <p className="text-error text-sm">Error: {quiz.error}</p>}
      {quiz?.raw_response && <pre className="text-xs text-text-dim whitespace-pre-wrap bg-surface p-4 rounded">{quiz.raw_response}</pre>}

      <div className="space-y-4">
        {questions.map((q, i) => (
          <div key={i} className="bg-surface rounded-xl border border-border p-4">
            <div className="flex items-start gap-3">
              <span className="text-xs font-bold text-accent bg-accent/10 rounded-full w-6 h-6 flex items-center justify-center shrink-0 mt-0.5">
                {q.id || i + 1}
              </span>
              <div className="flex-1">
                <p className="text-sm text-text-bright mb-2">{q.question}</p>

                {q.type === 'multiple_choice' && q.options && (
                  <div className="space-y-1.5 mb-3">
                    {q.options.map((opt, j) => (
                      <button
                        key={j}
                        onClick={() => setAnswers(p => ({ ...p, [i]: opt }))}
                        className={`w-full text-left px-3 py-1.5 rounded text-xs border transition-colors ${
                          answers[i] === opt
                            ? revealed[i]
                              ? opt.startsWith(q.answer?.[0]) ? 'border-success bg-success/10 text-success' : 'border-error bg-error/10 text-error'
                              : 'border-accent bg-accent/10 text-accent'
                            : 'border-border hover:border-border/80'
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {!revealed[i] && (
                    <button
                      onClick={() => setRevealed(p => ({ ...p, [i]: true }))}
                      className="text-[11px] text-accent hover:underline"
                    >
                      Show answer
                    </button>
                  )}
                  {q.source && <span className="text-[10px] text-text-dim">{q.source}</span>}
                </div>

                {revealed[i] && (
                  <div className="mt-2 p-3 bg-surface-2 rounded-lg text-xs">
                    <p className="text-success font-medium mb-1">Answer: {q.answer}</p>
                    {q.explanation && <div className="text-text-dim"><Markdown>{q.explanation}</Markdown></div>}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
