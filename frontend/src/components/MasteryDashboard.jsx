import { useState, useEffect } from 'react'
import { Activity, Target, TrendingUp } from 'lucide-react'
import { api } from '../api'

/**
 * Mastery dashboard — topic × Bloom heatmap + recommended next session.
 *
 * Pulls from /api/me/mastery (new endpoint) which returns aggregate FSRS+
 * accuracy stats per (topic, bloom) cell. Shows where the learner is strong/
 * weak; recommends a targeted session.
 */
const TOPICS = ['HH', 'cable', 'Nernst', 'membrane_eq', 'L4_synapses', 'L7_models', 'L8_codes', 'neural_codes', 'model_types', 'foundations']
const BLOOMS = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate']

export default function MasteryDashboard({ onJumpTo }) {
  const [grid, setGrid] = useState({})
  const [recommendations, setRec] = useState([])
  const [loading, setLoading] = useState(true)
  const [overall, setOverall] = useState(null)

  useEffect(() => {
    api.masteryGrid()
      .then(d => {
        setGrid(d.grid || {})
        setRec(d.recommendations || [])
        setOverall(d.overall)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const cellColor = (m) => {
    if (m == null) return 'var(--color-surface-3)'
    if (m >= 0.85) return '#228833'           // Tol green — mastered
    if (m >= 0.70) return '#66CCEE'           // Tol cyan — solid
    if (m >= 0.50) return '#CCBB44'           // Tol yellow — wobbly
    if (m >= 0.30) return '#EE6677'           // Tol red — needs work
    return '#dee2e7'                          // very faint — untouched
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="mb-4 flex items-center gap-2">
        <Activity size={18} className="text-accent" />
        <h2 className="text-xl font-bold text-text-bright">숙련도 대시보드</h2>
      </div>
      <p className="text-sm text-text-dim mb-4">
        주제 × Bloom 단계별 숙련도 지도. 빨간 칸은 보강 필요, 초록은 마스터.
      </p>

      {loading && <div className="text-text-dim">불러오는 중…</div>}

      {!loading && overall && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Stat label="전체 평균 숙련도" value={`${Math.round(overall.mean * 100)}%`} color="#4477AA" />
          <Stat label="복습 카드" value={overall.due_count} color="#CCBB44" sub="due" />
          <Stat label="오늘 학습" value={overall.today_reviewed} color="#228833" sub="cards" />
        </div>
      )}

      {!loading && (
        <div className="overflow-x-auto -mx-4 md:-mx-0">
          <table className="border-collapse mx-auto" style={{ fontSize: 12 }}>
            <thead>
              <tr>
                <th className="p-2"></th>
                {BLOOMS.map(b => (
                  <th key={b} className="p-2 text-left text-text-dim font-medium">{b}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TOPICS.map(t => {
                const row = grid[t] || {}
                return (
                  <tr key={t} className="hover:bg-surface-2">
                    <td className="p-2 text-text-dim font-medium pr-3 whitespace-nowrap">{t}</td>
                    {BLOOMS.map(b => {
                      const cell = row[b]
                      const m = cell?.mastery
                      const n = cell?.n
                      return (
                        <td key={b} className="p-1">
                          <button
                            onClick={() => cell && onJumpTo?.(t, b)}
                            disabled={!cell}
                            className="w-12 h-10 rounded-md flex items-center justify-center transition-all"
                            style={{
                              background: cellColor(m),
                              color: m != null ? (m > 0.6 ? 'var(--color-bg)' : 'var(--color-text)') : 'var(--color-text-faint)',
                              fontSize: 10, fontWeight: 600,
                              border: cell ? '1px solid color-mix(in oklab, currentColor 25%, transparent)' : 'none',
                              cursor: cell ? 'pointer' : 'default',
                            }}
                            title={cell ? `${(m*100).toFixed(0)}% (${n} cards)` : '없음'}
                          >
                            {m != null ? `${Math.round(m * 100)}` : '·'}
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {!loading && (
        <div className="mt-6 mb-4 flex items-center gap-2 text-xs text-text-dim flex-wrap">
          <span>범례:</span>
          <Legend color="#dee2e7" label="미학습" />
          <Legend color="#EE6677" label="<30%" />
          <Legend color="#CCBB44" label="30-70%" />
          <Legend color="#66CCEE" label="70-85%" />
          <Legend color="#228833" label="≥85% (마스터)" />
        </div>
      )}

      {!loading && recommendations.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-warning" />
            <h3 className="text-sm font-semibold text-text-bright">다음 세션 추천</h3>
          </div>
          <div className="space-y-2">
            {recommendations.map((r, i) => (
              <button
                key={i}
                onClick={() => onJumpTo?.(r.topic, r.bloom)}
                className="w-full p-3 rounded-xl bg-surface border border-border-soft hover:bg-surface-2 text-left transition-all"
                data-tap
              >
                <div className="flex items-center gap-3">
                  <Target size={14} className="text-accent flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-text-bright">
                      {r.topic} · {r.bloom}
                      <span className="ml-2 text-text-dim font-normal">{r.n} 카드</span>
                    </div>
                    <div className="text-xs text-text-dim mt-0.5 truncate">{r.reason}</div>
                  </div>
                  <div className="text-xs font-semibold tabular-nums" style={{ color: cellColor(r.current_mastery) }}>
                    {Math.round((r.current_mastery || 0) * 100)}%
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, color, sub }) {
  return (
    <div className="p-3 rounded-xl bg-surface border border-border-soft">
      <div className="text-xs text-text-dim mb-1">{label}</div>
      <div className="text-2xl font-bold tabular-nums" style={{ color }}>
        {value}
        {sub && <span className="text-xs text-text-dim font-normal ml-1">{sub}</span>}
      </div>
    </div>
  )
}

function Legend({ color, label }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="w-3 h-3 rounded" style={{ background: color }} />
      {label}
    </span>
  )
}
