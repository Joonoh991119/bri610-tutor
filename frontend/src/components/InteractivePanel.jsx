import { useState, useMemo } from 'react'
import { Sliders, BookOpen } from 'lucide-react'
import Markdown from './Markdown'

/**
 * Interactive parameter explorer for BRI610 core equations.
 *
 * Students manipulate parameters with sliders and see the math + plot update
 * in real time. Builds intuition that no static figure can.
 *
 * Three demos:
 *   1. RC charging:   V(t) = V_∞(1 − e^{−t/τ})         — slide L3 p.24
 *   2. Cable decay:   V(x) = V_0·e^{−x/λ}              — slide L6 p.11
 *   3. HH gating:     n_∞(V) = 1 / (1 + e^{−(V−V_h)/k}) — slide L5 p.24
 */
const DEMOS = [
  { id: 'rc',    label: 'RC 충전', slide: 'L3 p.24' },
  { id: 'cable', label: '케이블 감쇠', slide: 'L6 p.11' },
  { id: 'hh',    label: 'HH 게이팅', slide: 'L5 p.24' },
]

export default function InteractivePanel() {
  const [demo, setDemo] = useState('rc')
  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <div className="mb-4 flex items-center gap-2">
        <Sliders size={18} className="text-accent" />
        <h2 className="text-xl font-bold text-text-bright">매개변수 탐험</h2>
      </div>
      <p className="text-sm text-text-dim mb-4">
        슬라이더를 움직이며 식이 어떻게 반응하는지 직접 확인해보세요. 같은 식, 다른 직관.
      </p>

      <div className="flex gap-1 mb-4 flex-wrap" data-tap>
        {DEMOS.map(d => (
          <button
            key={d.id}
            onClick={() => setDemo(d.id)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              demo === d.id
                ? 'bg-accent text-[var(--color-bg)]'
                : 'bg-surface-2 text-text-dim border border-border-soft hover:bg-surface-3'
            }`}
          >
            {d.label}
            <span className="ml-2 text-[10px] opacity-70">[{d.slide}]</span>
          </button>
        ))}
      </div>

      {demo === 'rc'    && <RCChargingDemo />}
      {demo === 'cable' && <CableDecayDemo />}
      {demo === 'hh'    && <HHGatingDemo />}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// Common parameter slider
// ──────────────────────────────────────────────────────────────
function Slider({ label, value, min, max, step, unit, onChange, color }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1.5">
        <label className="text-sm text-text-dim font-medium">{label}</label>
        <span className="text-sm font-semibold tabular-nums" style={{ color: color || 'var(--color-accent)' }}>
          {Number(value).toFixed(step < 1 ? 2 : 0)} {unit}
        </span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full"
        style={{ accentColor: color || 'var(--color-accent)' }}
      />
    </div>
  )
}

function PlotFrame({ children, width = 600, height = 320 }) {
  return (
    <div className="bg-surface border border-border-soft rounded-xl p-3 mb-3 overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="auto"
           style={{ display: 'block', minWidth: 320 }}>
        <rect width={width} height={height} fill="var(--color-bg)" />
        {children}
      </svg>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// RC charging
// ──────────────────────────────────────────────────────────────
function RCChargingDemo() {
  const [tau,    setTau]    = useState(1.0)   // τ in arbitrary units
  const [vinf,   setVinf]   = useState(1.0)   // V_∞ normalised
  const [vrest,  setVrest]  = useState(0.0)

  // V(t) = V_rest + (V_∞ − V_rest)(1 − e^{−t/τ})
  const samples = useMemo(() => {
    const N = 200, tmax = 5
    return Array.from({ length: N + 1 }, (_, i) => {
      const t = (i * tmax) / N
      const V = vrest + (vinf - vrest) * (1 - Math.exp(-t / tau))
      return [t, V]
    })
  }, [tau, vinf, vrest])

  // Map data to plot pixels: x ∈ [0, 5τ window] → [60, 540]; y ∈ [-1, 1.2] → [280, 40]
  const px = (t) => 60 + (t / 5) * 480
  const py = (V) => 280 - ((V + 1) / 2.2) * 240
  const pathD = samples.map(([t, V], i) => `${i === 0 ? 'M' : 'L'} ${px(t).toFixed(1)} ${py(V).toFixed(1)}`).join(' ')

  // Marker at t = τ, V = V_rest + (V_∞ − V_rest)·(1 − 1/e)
  const tauX = px(tau)
  const tauV = vrest + (vinf - vrest) * (1 - 1 / Math.E)
  const tauY = py(tauV)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="시상수 τ" value={tau} min={0.2} max={3.0} step={0.1} unit="ms" onChange={setTau} />
        <Slider label="V_∞ (목표 전압)" value={vinf} min={-0.8} max={1.0} step={0.05} unit="" onChange={setVinf} color="var(--color-accent)" />
        <Slider label="V_rest" value={vrest} min={-1.0} max={0.5} step={0.05} unit="" onChange={setVrest} color="var(--color-text-dim)" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">관찰 포인트</div>
          <div className="text-sm">
            t = τ 시점에 V는 V<sub>rest</sub>와 V<sub>∞</sub> 사이의 <span className="font-semibold text-accent">63%</span> 지점에 도달한다.
            <br /><span className="text-text-dim">(1 − 1/e ≈ 0.632)</span>
          </div>
        </div>
      </div>

      <PlotFrame>
        {/* Axes */}
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />
        {/* Zero line */}
        <line x1="60" y1={py(0)} x2="540" y2={py(0)} stroke="var(--color-text-faint)" strokeWidth="0.6" strokeDasharray="3 3" />
        {/* V_∞ asymptote */}
        <line x1="60" y1={py(vinf)} x2="540" y2={py(vinf)} stroke="var(--color-accent)" strokeWidth="0.6" strokeDasharray="3 3" opacity="0.5" />

        {/* Curve */}
        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />

        {/* τ marker */}
        <circle cx={tauX} cy={tauY} r="5" fill="var(--color-warning)" />
        <line x1={tauX} y1={tauY} x2={tauX} y2={py(0) + 4} stroke="var(--color-warning)" strokeWidth="0.7" strokeDasharray="2 2" opacity="0.8" />

        {/* Labels */}
        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">V</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">t</text>
        <text x={tauX} y="296" fontSize="11" fill="var(--color-warning)" textAnchor="middle" fontWeight="600">τ</text>
        <text x="544" y={py(vinf) - 4} fontSize="10" fill="var(--color-accent)" textAnchor="end">V∞</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation**: $V(t) = V_{rest} + (V_\\infty - V_{rest})(1 - e^{-t/\\tau})$

τ 가 작을수록 곡선이 가파르게 V∞에 도달; τ 가 커지면 더 천천히 접근. 막의 RC 시상수는 단위 면적 당 정의 (소문자 r, c) 또는 절대량 (대문자 R_m, C_m)으로 모두 가능.`}
        </Markdown>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// Cable decay
// ──────────────────────────────────────────────────────────────
function CableDecayDemo() {
  const [lambda, setLambda] = useState(1.0)   // λ
  const [v0,     setV0]     = useState(1.0)   // V₀

  const samples = useMemo(() => {
    const N = 200, xmax = 5
    return Array.from({ length: N + 1 }, (_, i) => {
      const x = (i * xmax) / N
      const V = v0 * Math.exp(-x / lambda)
      return [x, V]
    })
  }, [lambda, v0])

  const px = (x) => 60 + (x / 5) * 480
  const py = (V) => 280 - (V / 1.1) * 240
  const pathD = samples.map(([x, V], i) => `${i === 0 ? 'M' : 'L'} ${px(x).toFixed(1)} ${py(V).toFixed(1)}`).join(' ')

  const oneLamX = px(lambda)
  const oneLamY = py(v0 / Math.E)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="공간상수 λ" value={lambda} min={0.3} max={2.5} step={0.05} unit="mm" onChange={setLambda} />
        <Slider label="V₀ (시작 전압)" value={v0} min={0.2} max={1.0} step={0.05} unit="" onChange={setV0} color="var(--color-accent)" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">관찰 포인트</div>
          <div className="text-sm">
            λ 한 거리만큼 떨어지면 신호가 <span className="font-semibold text-accent">37%</span>로 감쇠.
            <br />2λ에서는 14%, 3λ에서 5% 미만.
          </div>
        </div>
      </div>

      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />

        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />

        <circle cx={oneLamX} cy={oneLamY} r="5" fill="var(--color-warning)" />
        <line x1={oneLamX} y1={oneLamY} x2={oneLamX} y2={py(0) + 4} stroke="var(--color-warning)" strokeWidth="0.7" strokeDasharray="2 2" opacity="0.8" />

        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">V/V₀</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">x/λ</text>
        <text x={oneLamX} y="296" fontSize="11" fill="var(--color-warning)" textAnchor="middle" fontWeight="600">λ</text>
        <text x={oneLamX + 8} y={oneLamY - 6} fontSize="10" fill="var(--color-warning)" fontWeight="600">37%</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation**: $V(x) = V_0 \\, e^{-x/\\lambda}$, where $\\lambda = \\sqrt{\\dfrac{d\\,R_m}{4 R_i}}$

λ는 축삭 반지름의 제곱근에 비례 — 굵은 축삭이 신호를 멀리 보낸다. 무수초(unmyelinated) 축삭에서는 R_m이 작아 λ도 작고, 신호가 빠르게 사라진다.`}
        </Markdown>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// HH gating
// ──────────────────────────────────────────────────────────────
function HHGatingDemo() {
  const [vh, setVh] = useState(-50)   // half-activation voltage
  const [k,  setK]  = useState(8)     // slope factor mV

  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const V = -100 + (i * 150) / N    // -100 to +50
      const n_inf = 1 / (1 + Math.exp(-(V - vh) / k))
      return [V, n_inf]
    })
  }, [vh, k])

  const px = (V) => 60 + ((V + 100) / 150) * 480
  const py = (p) => 280 - p * 240
  const pathD = samples.map(([V, p], i) => `${i === 0 ? 'M' : 'L'} ${px(V).toFixed(1)} ${py(p).toFixed(1)}`).join(' ')

  const halfX = px(vh)
  const halfY = py(0.5)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="반활성 전압 V_½" value={vh} min={-80} max={-20} step={1} unit="mV" onChange={setVh} />
        <Slider label="기울기 인자 k" value={k} min={3} max={20} step={1} unit="mV" onChange={setK} color="var(--color-secondary)" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">관찰 포인트</div>
          <div className="text-sm">
            k 가 작을수록 곡선이 가파르게 (스위치처럼) 켜짐.
            <br />V_½ 는 50% 활성 지점 — 채널의 "임계 전압".
          </div>
        </div>
      </div>

      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />

        {/* Half line */}
        <line x1="60" y1={py(0.5)} x2="540" y2={py(0.5)} stroke="var(--color-text-faint)" strokeWidth="0.6" strokeDasharray="3 3" />

        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />

        <circle cx={halfX} cy={halfY} r="5" fill="var(--color-warning)" />
        <line x1={halfX} y1={halfY} x2={halfX} y2={py(0) + 4} stroke="var(--color-warning)" strokeWidth="0.7" strokeDasharray="2 2" opacity="0.8" />

        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">n∞</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)" textAnchor="start">V (mV)</text>
        <text x={halfX} y="296" fontSize="11" fill="var(--color-warning)" textAnchor="middle" fontWeight="600">V½</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation**: $n_\\infty(V) = \\dfrac{1}{1 + e^{-(V - V_{1/2})/k}}$

이 시그모이드는 채널 게이팅 입자의 *Boltzmann 분포*에서 유래한다. k 는 "전압 감수성" — 작을수록 작은 전압 변화에도 큰 반응. HH 모델의 m_∞, h_∞, n_∞ 모두 같은 형태, 다른 V_½ 와 k 값.`}
        </Markdown>
      </div>
    </div>
  )
}
