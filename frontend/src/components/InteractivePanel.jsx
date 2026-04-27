import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Sliders, BookOpen, FlaskConical } from 'lucide-react'
import Markdown from './Markdown'

/**
 * Interactive parameter explorer for BRI610 core equations.
 *
 * 실험실 (Lab) tab — 4 high-fidelity widgets:
 *   1. Membrane RC  — V(t) = V_∞ + (V0-V_∞)e^{-t/τ}           [L3]
 *   2. Alpha function — g(t) = A·t·e^{-t/t_peak}              [L4]
 *   3. Shunting synapse — ODE with alpha g_syn, twin Y axes     [L4]
 *   4. Hodgkin–Huxley full — 4-var ODE, forward Euler           [L5]
 *
 * Plus 7 classic demos preserved below.
 *
 * Palette (Tol BRIGHT):
 *   Blue  #4477AA — main curve
 *   Red   #EE6677 — reference / second curve
 *   Ochre #CCBB44 — callout markers
 */

// ─────────────────────────────── tab config ──────────────────────────────────
const LAB_TABS = [
  { id: 'memrc',   label: 'Membrane RC',    badge: 'L3' },
  { id: 'alpha',   label: 'Alpha function', badge: 'L4' },
  { id: 'shunt',   label: 'Shunting',       badge: 'L4' },
  { id: 'hh',      label: 'Hodgkin–Huxley', badge: 'L5' },
]

const CLASSIC_TABS = [
  { id: 'cable',  label: '케이블 감쇠',  slide: 'L6 p.11' },
  { id: 'hhgate', label: 'HH 게이팅',    slide: 'L5 p.24' },
  { id: 'nernst', label: 'Nernst 평형', slide: 'L3 p.27' },
  { id: 'ghk',    label: 'GHK 가중평균', slide: 'L3 p.32' },
  { id: 'lif',    label: 'LIF f–I 곡선', slide: 'L7 p.16' },
]

function readStoredTab(pool, key) {
  try { const v = localStorage.getItem(key); if (pool.some(t => t.id === v)) return v } catch {}
  return pool[0].id
}

export default function InteractivePanel() {
  const [labTab,    setLabTabState]    = useState(() => readStoredTab(LAB_TABS,    'bri610.lab.tab'))
  const [classic,   setClassicState]   = useState(() => readStoredTab(CLASSIC_TABS,'bri610.lab.classic'))
  const [showExtra, setShowExtra]      = useState(false)

  const setLabTab = (id) => { setLabTabState(id); try { localStorage.setItem('bri610.lab.tab', id) } catch {} }
  const setClassic = (id) => { setClassicState(id); try { localStorage.setItem('bri610.lab.classic', id) } catch {} }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <FlaskConical size={18} className="text-accent" />
        <h2 className="text-xl font-bold text-text-bright">실험실</h2>
        <span className="text-sm text-text-dim ml-1">— 핵심 방정식 인터랙티브 탐험</span>
      </div>

      {/* Primary lab tabs */}
      <div className="flex gap-1 mb-1 flex-wrap">
        {LAB_TABS.map(t => (
          <button key={t.id} onClick={() => setLabTab(t.id)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              labTab === t.id
                ? 'bg-accent text-[var(--color-bg)]'
                : 'bg-surface-2 text-text-dim border border-border-soft hover:bg-surface-3'
            }`}>
            {t.label}
            <span className="ml-1.5 text-[10px] opacity-70">[{t.badge}]</span>
          </button>
        ))}
      </div>

      {/* Primary widget */}
      <div className="mb-6">
        {labTab === 'memrc'  && <MembraneRCDemo />}
        {labTab === 'alpha'  && <AlphaFunctionDemo />}
        {labTab === 'shunt'  && <ShuntingDemo />}
        {labTab === 'hh'     && <HodgkinHuxleyDemo />}
      </div>

      {/* Classic demos */}
      <div>
        <button onClick={() => setShowExtra(v => !v)}
          className="flex items-center gap-1.5 text-xs text-text-dim hover:text-text transition-colors mb-2">
          <Sliders size={12} />
          {showExtra ? '추가 탐험 접기 ▲' : '추가 탐험 열기 ▼ (케이블·Nernst·GHK·LIF·HH 게이팅)'}
        </button>
        {showExtra && (
          <>
            <div className="flex gap-1 mb-3 flex-wrap">
              {CLASSIC_TABS.map(d => (
                <button key={d.id} onClick={() => setClassic(d.id)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    classic === d.id
                      ? 'bg-surface text-text border border-accent'
                      : 'bg-surface-2 text-text-dim border border-border-soft hover:bg-surface-3'
                  }`}>
                  {d.label}
                  <span className="ml-2 text-[10px] opacity-70">[{d.slide}]</span>
                </button>
              ))}
            </div>
            {classic === 'cable'  && <CableDecayDemo />}
            {classic === 'hhgate' && <HHGatingDemo />}
            {classic === 'nernst' && <NernstDemo />}
            {classic === 'ghk'    && <GHKDemo />}
            {classic === 'lif'    && <LIFDemo />}
          </>
        )}
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// COMMON COMPONENTS
// ═════════════════════════════════════════════════════════════════════════════

function Slider({ label, value, min, max, step, unit, onChange, color }) {
  const decimals = step < 1 ? (step < 0.1 ? 2 : 2) : 0
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1.5">
        <label className="text-sm text-text-dim font-medium">{label}</label>
        <span className="text-sm font-semibold tabular-nums" style={{ color: color || 'var(--color-accent)' }}>
          {Number(value).toFixed(decimals)} {unit}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full" style={{ accentColor: color || 'var(--color-accent)' }} />
    </div>
  )
}

/** SVG plot container. viewBox = 0 0 600 360 */
function PlotFrame({ children, width = 600, height = 360 }) {
  return (
    <div className="bg-surface border border-border-soft rounded-xl p-3 mb-3 overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="auto"
        style={{ display: 'block', minWidth: 300 }}>
        <rect width={width} height={height} fill="var(--color-bg)" />
        {children}
      </svg>
    </div>
  )
}

/** Intuition callout box */
function Intuition({ children }) {
  return (
    <div className="mt-3 px-3 py-2 rounded-lg border-l-4 border-[#4477AA] bg-surface-2 text-sm text-text-dim">
      <span className="text-[#4477AA] font-semibold mr-1">직관 한 줄</span>{children}
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// 1. MEMBRANE RC DEMO  (L3)
//    V(t) = V_∞ + (V0 − V_∞) e^{−t/τ_m}
// ═════════════════════════════════════════════════════════════════════════════
function MembraneRCDemo() {
  // Parameters
  const [tau,   setTau]   = useState(10)   // ms  1–50
  const [EL,    setEL]    = useState(-65)  // mV  -90 to -50
  const [RmI,   setRmI]   = useState(20)   // mV  -30 to +50  (R_m * I_inj offset)
  const [V0off, setV0off] = useState(0)    // offset from EL in mV

  const Vinf = EL + RmI
  const V0   = EL + V0off

  // Plot domain: 0 to 5*tau ms
  const W = 540, H = 300, L = 60, T = 30, B = 330   // margins
  const tmax = 5 * tau

  // V at t ms
  const Vat = (t) => Vinf + (V0 - Vinf) * Math.exp(-t / tau)
  const V_tau = Vat(tau)  // value at 1 time constant

  // Voltage range for y axis
  const Vlo = Math.min(V0, Vinf) - 5
  const Vhi = Math.max(V0, Vinf) + 5
  const Vspan = Vhi - Vlo || 10

  const toX = (t) => L + (t / tmax) * W
  const toY = (V) => B - ((V - Vlo) / Vspan) * H

  // Curve samples
  const pts = useMemo(() => {
    const N = 300
    return Array.from({ length: N + 1 }, (_, i) => {
      const t = (i * tmax) / N
      return [toX(t), toY(Vat(t))]
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tau, EL, RmI, V0off])

  const pathD = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ')

  const tauPx  = toX(tau)
  const tauPy  = toY(V_tau)
  const VinfPy = toY(Vinf)
  const V0Py   = toY(V0)

  // 63% fraction: (V_tau - V0)/(Vinf - V0)*100  — should be ≈63%
  const pct63 = V0 === Vinf ? 100 : Math.round(Math.abs((V_tau - V0) / (Vinf - V0)) * 100)

  // x-axis tick labels (ms)
  const xTicks = [0, 1, 2, 3, 4, 5].map(k => ({ t: k * tau, label: k === 0 ? '0' : `${k}τ` }))
  // y-axis ticks
  const yTickVals = [Vlo, (Vlo + Vhi) / 2, Vhi].map(v => Math.round(v))

  return (
    <div className="grid md:grid-cols-[1fr_1.4fr] gap-4">
      {/* Controls */}
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="τ_m (time constant)" value={tau}   min={1}   max={50} step={1}   unit="ms" onChange={setTau} color="#4477AA" />
        <Slider label="E_L (leak reversal)" value={EL}    min={-90} max={-50} step={1}  unit="mV" onChange={setEL}  color="#888" />
        <Slider label="R_m·I_inj (step)"    value={RmI}   min={-30} max={50}  step={1}  unit="mV" onChange={setRmI} color="#EE6677" />
        <Slider label="V₀ offset from E_L"  value={V0off} min={-30} max={30}  step={1}  unit="mV" onChange={setV0off} color="#CCBB44" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft space-y-1.5">
          <div className="text-xs text-text-dim">현재 값</div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">V₀ =</span> <span style={{color:'#CCBB44'}}>{V0.toFixed(1)} mV</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">V_∞ =</span> <span style={{color:'#EE6677'}}>{Vinf.toFixed(1)} mV</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">V(τ) =</span> <span style={{color:'#CCBB44'}} className="font-bold">{V_tau.toFixed(1)} mV</span>
            <span className="ml-2 text-[11px] text-text-faint">({pct63}% 도달)</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">τ_m =</span> <span style={{color:'#4477AA'}}>{tau} ms</span>
          </div>
        </div>

        <div className="mt-3 text-xs text-text-faint italic">
          1 시간상수 후 진폭의 63% 도달 (1 − 1/e ≈ 63.2%)
        </div>
      </div>

      {/* Plot */}
      <PlotFrame height={360}>
        {/* axes */}
        <line x1={L} y1={T} x2={L} y2={B} stroke="var(--color-text)" strokeWidth="1" />
        <line x1={L} y1={B} x2={L+W} y2={B} stroke="var(--color-text)" strokeWidth="1" />

        {/* V_∞ dashed red */}
        <line x1={L} y1={VinfPy} x2={L+W} y2={VinfPy} stroke="#EE6677" strokeWidth="1.2" strokeDasharray="5 3" opacity="0.85" />
        <text x={L+W+3} y={VinfPy+4} fontSize="10" fill="#EE6677">V_∞</text>

        {/* V₀ line at t=0 */}
        <line x1={L-6} y1={V0Py} x2={L+W} y2={V0Py} stroke="#CCBB44" strokeWidth="0.7" strokeDasharray="3 3" opacity="0.5" />

        {/* Curve */}
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.5" />

        {/* τ vertical dotted */}
        <line x1={tauPx} y1={T} x2={tauPx} y2={B} stroke="#CCBB44" strokeWidth="0.9" strokeDasharray="4 3" opacity="0.8" />

        {/* 63% dot */}
        <circle cx={tauPx} cy={tauPy} r="5.5" fill="#CCBB44" />
        {/* horizontal guide to y-axis */}
        <line x1={L} y1={tauPy} x2={tauPx} y2={tauPy} stroke="#CCBB44" strokeWidth="0.7" strokeDasharray="2 2" opacity="0.7" />

        {/* x ticks */}
        {xTicks.map(({ t, label }) => {
          const x = toX(t)
          return (
            <g key={label}>
              <line x1={x} y1={B} x2={x} y2={B+4} stroke="var(--color-text)" strokeWidth="0.8" />
              <text x={x} y={B+14} fontSize="10" fill={label.includes('τ') ? '#CCBB44' : 'var(--color-text-dim)'}
                textAnchor="middle" fontWeight={label === 'τ' ? '700' : '400'}>{label}</text>
            </g>
          )
        })}

        {/* y ticks */}
        {yTickVals.map(v => {
          const y = toY(v)
          return (
            <g key={v}>
              <line x1={L-4} y1={y} x2={L} y2={y} stroke="var(--color-text)" strokeWidth="0.8" />
              <text x={L-6} y={y+4} fontSize="9" fill="var(--color-text-dim)" textAnchor="end">{v}</text>
            </g>
          )
        })}

        {/* axis labels */}
        <text x={L} y={T-8} fontSize="11" fill="var(--color-text-dim)" textAnchor="middle">V (mV)</text>
        <text x={L+W} y={B+26} fontSize="11" fill="var(--color-text-dim)" textAnchor="end">t (ms)</text>

        {/* τ label */}
        <text x={tauPx} y={B+26} fontSize="11" fill="#CCBB44" textAnchor="middle" fontWeight="700">τ_m</text>
      </PlotFrame>

      <div className="md:col-span-2">
        <Markdown>{`**방정식**: $V(t) = V_\\infty + (V_0 - V_\\infty)\\,e^{-t/\\tau_m}$, where $V_\\infty = E_L + R_m I_{\\text{inj}}$

ODE 원형: $\\tau_m\\,\\dfrac{dV}{dt} = -(V - V_\\infty)$.`}</Markdown>
        <Intuition>τ_m 가 클수록 막은 느리게 반응 — RC 시상수는 막의 "게으름" 지표다.</Intuition>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// 2. ALPHA FUNCTION DEMO  (L4)
//    g(t) = A · t · e^{−t / t_peak}
// ═════════════════════════════════════════════════════════════════════════════
function AlphaFunctionDemo() {
  const [A,      setA]      = useState(0.5)   // 0–1
  const [tpeak,  setTpeak]  = useState(2)     // ms 0.5–10

  // g_max = A * t_peak / e  (peak at t = t_peak, g = A·t_peak·e^{-1})
  const gmax = A * tpeak / Math.E
  const tmax = 5 * tpeak

  const W = 540, H = 290, L = 60, T = 30, B = 320

  const g = (t) => A * t * Math.exp(-t / tpeak)

  const pts = useMemo(() => {
    const N = 400
    return Array.from({ length: N + 1 }, (_, i) => {
      const t = (i * tmax) / N
      return t
    }).map(t => [t, g(t)])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [A, tpeak])

  const ymax = gmax * 1.15 || 0.01
  const toX = (t) => L + (t / tmax) * W
  const toY = (v) => B - (v / ymax) * H

  const pathD = pts.map(([t, v], i) => `${i === 0 ? 'M' : 'L'}${toX(t).toFixed(1)} ${toY(v).toFixed(1)}`).join(' ')

  const peakX = toX(tpeak)
  const peakY = toY(gmax)

  // x ticks: 0, t_peak, 2t, 3t, 4t, 5t
  const xTicks = [0, 1, 2, 3, 4, 5].map(k => ({ t: k * tpeak, label: k === 0 ? '0' : `${k}t_p` }))

  return (
    <div className="grid md:grid-cols-[1fr_1.4fr] gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="A (amplitude)"     value={A}     min={0.01} max={1}  step={0.01} unit="" onChange={setA}     color="#4477AA" />
        <Slider label="t_peak (rise time)" value={tpeak} min={0.5}  max={10} step={0.5}  unit="ms" onChange={setTpeak} color="#EE6677" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft space-y-1.5">
          <div className="text-xs text-text-dim">피크 값</div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">g_max =</span>{' '}
            <span style={{color:'#4477AA'}} className="font-bold">{gmax.toFixed(4)}</span>
            <span className="text-text-faint text-xs ml-1">= A·t_peak/e</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">피크 시각 =</span>{' '}
            <span style={{color:'#EE6677'}} className="font-bold">{tpeak.toFixed(1)} ms</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">A=1, t_p=2 → g_max =</span>{' '}
            <span className="font-bold text-text-bright">2/e ≈ 0.7358</span>
          </div>
        </div>
      </div>

      <PlotFrame height={360}>
        {/* axes */}
        <line x1={L} y1={T} x2={L} y2={B} stroke="var(--color-text)" strokeWidth="1" />
        <line x1={L} y1={B} x2={L+W} y2={B} stroke="var(--color-text)" strokeWidth="1" />

        {/* g_max dashed */}
        <line x1={L} y1={peakY} x2={L+W} y2={peakY} stroke="#CCBB44" strokeWidth="1" strokeDasharray="4 3" opacity="0.7" />
        <text x={L+W+3} y={peakY+4} fontSize="10" fill="#CCBB44">g_max</text>

        {/* curve */}
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.5" />

        {/* t_peak vertical */}
        <line x1={peakX} y1={T} x2={peakX} y2={B} stroke="#EE6677" strokeWidth="0.9" strokeDasharray="4 3" opacity="0.7" />

        {/* peak dot */}
        <circle cx={peakX} cy={peakY} r="5.5" fill="#EE6677" />

        {/* coordinate label */}
        <text x={peakX+8} y={peakY-6} fontSize="10" fill="#EE6677" fontWeight="600">
          ({tpeak.toFixed(1)}, {gmax.toFixed(3)})
        </text>

        {/* x ticks */}
        {xTicks.map(({ t, label }) => {
          const x = toX(t)
          return (
            <g key={label}>
              <line x1={x} y1={B} x2={x} y2={B+4} stroke="var(--color-text)" strokeWidth="0.8" />
              <text x={x} y={B+14} fontSize="10" fill={t === tpeak ? '#EE6677' : 'var(--color-text-dim)'}
                textAnchor="middle">{label}</text>
            </g>
          )
        })}

        {/* axis labels */}
        <text x={L} y={T-8} fontSize="11" fill="var(--color-text-dim)" textAnchor="middle">g(t)</text>
        <text x={L+W} y={B+26} fontSize="11" fill="var(--color-text-dim)" textAnchor="end">t (ms)</text>
      </PlotFrame>

      <div className="md:col-span-2">
        <Markdown>{`**방정식**: $g(t) = A \\cdot t \\cdot e^{-t/t_{\\text{peak}}}$

피크: $t = t_{\\text{peak}}$, $g_{\\max} = A \\cdot t_{\\text{peak}} / e$.`}</Markdown>
        <Intuition>t_peak 가 작으면 AMPA-like (빠른 개폐), 크면 NMDA/GABA_B-like (느린 개폐).</Intuition>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// 3. SHUNTING / FUSION DEMO  (L4)
//    C_m dV/dt = -g_L(V-E_L) - g_syn(t)(V-E_syn) + I_inj
//    g_syn(t) = alpha function with t_peak
//    Twin Y: V(t) left, τ_eff(t) = C_m/(g_L+g_syn) right
// ═════════════════════════════════════════════════════════════════════════════
function ShuntingDemo() {
  const [gL,      setGL]     = useState(10)    // nS
  const [gsynMax, setGsynMax]= useState(20)    // nS  peak g_syn
  const [tpeak,   setTpeak]  = useState(2)     // ms
  const [Esyn,    setEsyn]   = useState(-65)   // mV
  const [Einj,    setEinj]   = useState(0)     // pA injected (0=none)

  const EL   = -65  // mV fixed
  const Cm   = 100  // pF (100 pF ≈ 10 nF/cm² × small cell)
  const dt   = 0.1  // ms
  const T    = 50   // ms
  const t0   = 5    // ms stimulus onset

  // g_syn(t) = gsynMax * (t-t0) * exp(-(t-t0)/tpeak) / (tpeak * exp(-1))^{-1}
  // normalised so peak = gsynMax at t = t0+tpeak
  // g(t) = gsynMax * ((t-t0)/tpeak) * exp(1-(t-t0)/tpeak)  for t>t0
  const gsynAt = useCallback((t) => {
    const dt_ = t - t0
    if (dt_ <= 0) return 0
    return gsynMax * (dt_ / tpeak) * Math.exp(1 - dt_ / tpeak)
  }, [gsynMax, tpeak])

  // Forward Euler
  const { Vpts, tauPts } = useMemo(() => {
    const N = Math.round(T / dt)
    const Vpts   = []
    const tauPts = []
    let V = EL
    for (let i = 0; i <= N; i++) {
      const t   = i * dt
      const gs  = gsynAt(t)
      const tauE = Cm / (gL + gs)   // pF/nS = ms
      Vpts.push([t, V])
      tauPts.push([t, tauE])
      // Euler step
      const dV = (-(gL * (V - EL)) - gs * (V - Esyn) + Einj) / Cm
      V += dV * dt
    }
    return { Vpts, tauPts }
  }, [gL, gsynMax, tpeak, Esyn, Einj, gsynAt])

  // Layout
  const W = 500, H = 250, L = 65, T_top = 30, B = 280
  const tmax = T

  const Vlo = Math.min(...Vpts.map(([,v]) => v)) - 2
  const Vhi = Math.max(...Vpts.map(([,v]) => v)) + 2
  const Vspan = Math.max(Vhi - Vlo, 2)

  const tauMin = Math.min(...tauPts.map(([,t]) => t))
  const tauMax_val = Math.max(...tauPts.map(([,t]) => t))
  const tauSpan = Math.max(tauMax_val - tauMin, 0.5)

  const toX  = (t)   => L + (t / tmax) * W
  const toYV = (V)   => B - ((V - Vlo) / Vspan) * H
  const toYT = (tau) => B - ((tau - tauMin) / tauSpan) * H

  const pathV = Vpts.map(([t, V], i) =>
    `${i === 0 ? 'M' : 'L'}${toX(t).toFixed(1)} ${toYV(V).toFixed(1)}`).join(' ')
  const pathT = tauPts.map(([t, tau], i) =>
    `${i === 0 ? 'M' : 'L'}${toX(t).toFixed(1)} ${toYT(tau).toFixed(1)}`).join(' ')

  // Shunting highlight: is V staying near E_L while tau_eff dips?
  const isPureShunt = Math.abs(Esyn - EL) < 3
  const tauAtPeak = Cm / (gL + gsynMax)

  // EL line
  const ELpy = toYV(EL)

  // Axis tick values for V
  const Vticks = [Math.round(Vlo), Math.round((Vlo+Vhi)/2), Math.round(Vhi)]
  const tauTicks = [tauMin, (tauMin+tauMax_val)/2, tauMax_val].map(v => v.toFixed(1))

  return (
    <div className="grid md:grid-cols-[1fr_1.5fr] gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="g_L (leak cond.)"      value={gL}      min={5}   max={20}  step={1}    unit="nS" onChange={setGL}      color="#888" />
        <Slider label="g_syn peak"            value={gsynMax} min={0}   max={50}  step={1}    unit="nS" onChange={setGsynMax} color="#4477AA" />
        <Slider label="t_peak (alpha rise)"   value={tpeak}   min={0.5} max={10}  step={0.5}  unit="ms" onChange={setTpeak}   color="#4477AA" />
        <Slider label="E_syn (reversal)"      value={Esyn}    min={-90} max={0}   step={1}    unit="mV" onChange={setEsyn}    color="#EE6677" />
        <Slider label="I_inj"                 value={Einj}    min={-50} max={200} step={5}    unit="pA" onChange={setEinj}    color="#CCBB44" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft space-y-1.5">
          <div className="text-xs text-text-dim">τ_eff 분석</div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">τ_rest =</span>{' '}
            <span className="font-bold text-text-bright">{(Cm / gL).toFixed(1)} ms</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">τ_min (peak syn) =</span>{' '}
            <span style={{color:'#EE6677'}} className="font-bold">{tauAtPeak.toFixed(1)} ms</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">단축 비율 =</span>{' '}
            <span className="font-bold text-text-bright">{((Cm / gL) / tauAtPeak).toFixed(1)}×</span>
          </div>
          {isPureShunt && (
            <div className="text-xs text-[#CCBB44] font-semibold mt-2">
              ⚡ E_syn ≈ E_L: 전압은 거의 안 움직이지만 τ_eff 가 급감 — 순수 shunting!
            </div>
          )}
        </div>
      </div>

      {/* Plot: twin y-axis */}
      <div>
        <PlotFrame width={620} height={360}>
          {/* axes */}
          <line x1={L} y1={T_top} x2={L} y2={B} stroke="var(--color-text)" strokeWidth="1.2" />
          <line x1={L+W} y1={T_top} x2={L+W} y2={B} stroke="#EE6677" strokeWidth="1" strokeOpacity="0.7" />
          <line x1={L} y1={B} x2={L+W} y2={B} stroke="var(--color-text)" strokeWidth="1" />

          {/* E_L reference */}
          <line x1={L} y1={ELpy} x2={L+W} y2={ELpy} stroke="#888" strokeWidth="0.7" strokeDasharray="3 3" opacity="0.5" />
          <text x={L-4} y={ELpy+4} fontSize="9" fill="#888" textAnchor="end">E_L</text>

          {/* τ_eff curve (red, dashed) */}
          <path d={pathT} fill="none" stroke="#EE6677" strokeWidth="1.8" strokeDasharray="5 2" opacity="0.9" />

          {/* V curve (blue, solid) */}
          <path d={pathV} fill="none" stroke="#4477AA" strokeWidth="2.5" />

          {/* Stimulus onset */}
          <line x1={toX(t0)} y1={T_top} x2={toX(t0)} y2={B} stroke="#CCBB44" strokeWidth="0.7" strokeDasharray="3 3" opacity="0.6" />
          <text x={toX(t0)} y={T_top-4} fontSize="9" fill="#CCBB44" textAnchor="middle">stim</text>

          {/* V y-ticks (left) */}
          {Vticks.map(v => {
            const y = toYV(v)
            return (
              <g key={v}>
                <line x1={L-4} y1={y} x2={L} y2={y} stroke="var(--color-text)" strokeWidth="0.7" />
                <text x={L-6} y={y+4} fontSize="9" fill="var(--color-text-dim)" textAnchor="end">{v}</text>
              </g>
            )
          })}

          {/* τ_eff y-ticks (right) */}
          {tauTicks.map((v, i) => {
            const yy = [toYT(tauMin), toYT((tauMin+tauMax_val)/2), toYT(tauMax_val)][i]
            return (
              <g key={v}>
                <line x1={L+W} y1={yy} x2={L+W+4} y2={yy} stroke="#EE6677" strokeWidth="0.7" />
                <text x={L+W+6} y={yy+4} fontSize="9" fill="#EE6677" textAnchor="start">{v}</text>
              </g>
            )
          })}

          {/* x ticks */}
          {[0, 10, 20, 30, 40, 50].map(t => {
            const x = toX(t)
            return (
              <g key={t}>
                <line x1={x} y1={B} x2={x} y2={B+4} stroke="var(--color-text)" strokeWidth="0.7" />
                <text x={x} y={B+14} fontSize="9" fill="var(--color-text-dim)" textAnchor="middle">{t}</text>
              </g>
            )
          })}

          {/* axis labels */}
          <text x={L-40} y={(T_top+B)/2} fontSize="11" fill="#4477AA" textAnchor="middle"
            transform={`rotate(-90, ${L-40}, ${(T_top+B)/2})`}>V (mV)</text>
          <text x={L+W+38} y={(T_top+B)/2} fontSize="11" fill="#EE6677" textAnchor="middle"
            transform={`rotate(90, ${L+W+38}, ${(T_top+B)/2})`}>τ_eff (ms)</text>
          <text x={L+W} y={B+26} fontSize="11" fill="var(--color-text-dim)" textAnchor="end">t (ms)</text>

          {/* Legend */}
          <line x1={L+10} y1={T_top+12} x2={L+35} y2={T_top+12} stroke="#4477AA" strokeWidth="2.5" />
          <text x={L+40} y={T_top+16} fontSize="10" fill="#4477AA">V(t)</text>
          <line x1={L+80} y1={T_top+12} x2={L+105} y2={T_top+12} stroke="#EE6677" strokeWidth="2" strokeDasharray="5 2" />
          <text x={L+110} y={T_top+16} fontSize="10" fill="#EE6677">τ_eff(t)</text>
        </PlotFrame>
      </div>

      <div className="md:col-span-2">
        <Markdown>{`**ODE**: $C_m\\,\\dfrac{dV}{dt} = -g_L(V-E_L) - g_{\\text{syn}}(t)(V-E_{\\text{syn}}) + I_{\\text{inj}}$

유효 시상수: $\\tau_m^{\\text{eff}}(t) = \\dfrac{C_m}{g_L + g_{\\text{syn}}(t)}$`}</Markdown>
        <Intuition>
          E_syn = E_L 로 설정: 전압은 움직이지 않지만 τ_eff 가 급감 — "shunting inhibition은
          전압이 아닌 시상수를 변화시킨다" (L4 핵심 포인트).
        </Intuition>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// 4. HODGKIN–HUXLEY FULL MODEL  (L5)
//    Standard HH 1952 parameters, forward Euler dt=0.01 ms
// ═════════════════════════════════════════════════════════════════════════════

// HH α/β rate functions — absolute-voltage convention (rest ≈ −65 mV).
// Uses the standard absolute-V form from Sterratt et al. (2011) and many
// modern computational neuroscience courses, which gives a true quiescent
// resting state at V = −65 mV and action potential threshold ~6–8 μA/cm².
//
//   α_m = 0.1(V+40) / (1−exp(−(V+40)/10))   [Na activation]
//   β_m = 4·exp(−(V+65)/18)
//   α_h = 0.07·exp(−(V+65)/20)               [Na inactivation]
//   β_h = 1 / (1+exp(−(V+35)/10))
//   α_n = 0.01(V+55) / (1−exp(−(V+55)/10))  [K activation]
//   β_n = 0.125·exp(−(V+65)/80)

function hhRates(V) {
  // m: Na activation
  const am = Math.abs(V + 40) < 1e-7 ? 1.0 : 0.1 * (V + 40) / (1 - Math.exp(-(V + 40) / 10))
  const bm = 4.0 * Math.exp(-(V + 65) / 18)

  // h: Na inactivation
  const ah = 0.07 * Math.exp(-(V + 65) / 20)
  const bh = 1.0 / (1 + Math.exp(-(V + 35) / 10))

  // n: K activation
  const an = Math.abs(V + 55) < 1e-7 ? 0.1 : 0.01 * (V + 55) / (1 - Math.exp(-(V + 55) / 10))
  const bn = 0.125 * Math.exp(-(V + 65) / 80)

  return { am, bm, ah, bh, an, bn }
}

// Precompute HH trace — returns arrays for t, V, m, h, n
function computeHH(Iext) {
  const dt   = 0.01  // ms
  const Tmax = 50    // ms
  const N    = Math.round(Tmax / dt)

  // HH standard conductances / reversals (mS/cm², mV, μF/cm²)
  const gNa = 120, gK = 36, gL_hh = 0.3
  const ENa  = 50,  EK = -77, EL_hh = -54.4
  const Cm   = 1

  // Initial conditions at true resting state V=−65 mV
  // (the absolute-V rate functions give I_net≈0 at V=−65 with E_L=−54.4)
  let V = -65
  const { am, bm, ah, bh, an, bn } = hhRates(V)
  let m = am / (am + bm)
  let h = ah / (ah + bh)
  let n = an / (an + bn)

  // Downsample storage: store every 10 steps (0.1 ms resolution)
  const stride  = 10
  const tArr    = []
  const VArr    = []
  const mArr    = []
  const hArr    = []
  const nArr    = []

  for (let i = 0; i <= N; i++) {
    if (i % stride === 0) {
      tArr.push(i * dt)
      VArr.push(V)
      mArr.push(m)
      hArr.push(h)
      nArr.push(n)
    }
    const { am: am_, bm: bm_, ah: ah_, bh: bh_, an: an_, bn: bn_ } = hhRates(V)
    const INa = gNa * m * m * m * h * (V - ENa)
    const IK  = gK  * n * n * n * n * (V - EK)
    const IL  = gL_hh * (V - EL_hh)

    const dV = (Iext - INa - IK - IL) / Cm
    const dm = am_ * (1 - m) - bm_ * m
    const dh = ah_ * (1 - h) - bh_ * h
    const dn = an_ * (1 - n) - bn_ * n

    V += dV * dt
    m += dm * dt
    h += dh * dt
    n += dn * dt
  }
  return { tArr, VArr, mArr, hArr, nArr }
}

function HodgkinHuxleyDemo() {
  const [Iext, setIext] = useState(10)   // μA/cm²

  // Debounced computation
  const [trace, setTrace] = useState(() => computeHH(10))
  const timerRef = useRef(null)
  const pendingI = useRef(Iext)

  const handleIext = useCallback((val) => {
    setIext(val)
    pendingI.current = val
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setTrace(computeHH(pendingI.current))
    }, 60)
  }, [])

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const { tArr, VArr, mArr, hArr, nArr } = trace

  // Count spikes (threshold crossings upward at V > -20 mV)
  let spikes = 0
  for (let i = 1; i < VArr.length; i++) {
    if (VArr[i] > -20 && VArr[i-1] <= -20) spikes++
  }
  const firingRate = spikes / 0.05   // Hz (50 ms window)

  // Current frame readout: values at last time point
  const last = VArr.length - 1
  const Vend = VArr[last].toFixed(1)
  const mend = mArr[last].toFixed(3)
  const hend = hArr[last].toFixed(3)
  const nend = nArr[last].toFixed(3)

  // Plot
  const W = 540, H = 290, L = 65, T_top = 30, B = 320
  const tmax = 50

  const Vlo = -90, Vhi = 60, Vspan = Vhi - Vlo
  const toX  = (t) => L + (t / tmax) * W
  const toYV = (V) => B - ((V - Vlo) / Vspan) * H

  const pathV = VArr.map((V, i) =>
    `${i === 0 ? 'M' : 'L'}${toX(tArr[i]).toFixed(1)} ${toYV(V).toFixed(1)}`).join(' ')

  // m, h, n scaled to same plot (0–1 → mapped to V -90 to 60)
  const gScale = (x) => toYV(-90 + x * 150)   // 0→-90, 1→+60 on y
  const pathM = mArr.map((m, i) => `${i === 0 ? 'M' : 'L'}${toX(tArr[i]).toFixed(1)} ${gScale(m).toFixed(1)}`).join(' ')
  const pathH = hArr.map((h, i) => `${i === 0 ? 'M' : 'L'}${toX(tArr[i]).toFixed(1)} ${gScale(h).toFixed(1)}`).join(' ')
  const pathN = nArr.map((n, i) => `${i === 0 ? 'M' : 'L'}${toX(tArr[i]).toFixed(1)} ${gScale(n).toFixed(1)}`).join(' ')

  // Spike markers
  const spikeTs = []
  for (let i = 1; i < VArr.length; i++) {
    if (VArr[i] > -20 && VArr[i-1] <= -20) spikeTs.push(tArr[i])
  }

  // Threshold line
  const threshY = toYV(-55)

  // V-axis ticks
  const Vticks = [-90, -65, -40, -20, 0, 20, 40, 60]

  return (
    <div className="grid md:grid-cols-[1fr_1.6fr] gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="I_ext (DC step)" value={Iext} min={0} max={30} step={0.5} unit="μA/cm²" onChange={handleIext} color="#4477AA" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft space-y-1.5">
          <div className="text-xs text-text-dim">50 ms 시뮬레이션 결과</div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">스파이크 수 =</span>{' '}
            <span style={{color:'#4477AA'}} className="text-lg font-bold">{spikes}</span>
          </div>
          <div className="text-sm tabular-nums">
            <span className="text-text-dim">발화율 ≈</span>{' '}
            <span style={{color:'#4477AA'}} className="font-bold">{firingRate.toFixed(0)} Hz</span>
          </div>
          <hr className="border-border-soft my-1.5" />
          <div className="text-xs text-text-dim">t=50 ms 게이팅 변수</div>
          <div className="text-sm tabular-nums grid grid-cols-3 gap-1">
            <span className="text-[#CCBB44]">m={mend}</span>
            <span className="text-[#EE6677]">h={hend}</span>
            <span className="text-[#44BB99]">n={nend}</span>
          </div>
          <div className="text-xs text-text-faint">V(50ms) = {Vend} mV</div>
        </div>

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-2">HH 파라미터 (표준)</div>
          <div className="text-[11px] text-text-faint space-y-0.5 font-mono">
            <div>ḡ_Na=120, ḡ_K=36, g_L=0.3 mS/cm²</div>
            <div>E_Na=+50, E_K=−77, E_L=−54.4 mV</div>
            <div>C_m=1 μF/cm², dt=0.01 ms</div>
          </div>
        </div>
      </div>

      <div>
        <PlotFrame width={640} height={380}>
          {/* Background */}
          <rect x={L} y={T_top} width={W} height={H+30} fill="var(--color-bg)" />

          {/* Axes */}
          <line x1={L} y1={T_top} x2={L} y2={B} stroke="var(--color-text)" strokeWidth="1.2" />
          <line x1={L} y1={B} x2={L+W} y2={B} stroke="var(--color-text)" strokeWidth="1" />

          {/* Threshold line */}
          <line x1={L} y1={threshY} x2={L+W} y2={threshY} stroke="#CCBB44" strokeWidth="0.8" strokeDasharray="4 3" opacity="0.7" />
          <text x={L-4} y={threshY+3} fontSize="9" fill="#CCBB44" textAnchor="end">thr</text>

          {/* Rest line */}
          <line x1={L} y1={toYV(-65)} x2={L+W} y2={toYV(-65)} stroke="#888" strokeWidth="0.6" strokeDasharray="2 3" opacity="0.5" />

          {/* Gating vars (thin, behind) */}
          <path d={pathM} fill="none" stroke="#CCBB44" strokeWidth="1.2" opacity="0.7" />
          <path d={pathH} fill="none" stroke="#EE6677" strokeWidth="1.2" opacity="0.7" />
          <path d={pathN} fill="none" stroke="#44BB99" strokeWidth="1.2" opacity="0.7" />

          {/* V trace */}
          <path d={pathV} fill="none" stroke="#4477AA" strokeWidth="2.5" />

          {/* Spike triangles */}
          {spikeTs.map((t, i) => {
            const sx = toX(t)
            return <polygon key={i} points={`${sx},${T_top+2} ${sx-5},${T_top+12} ${sx+5},${T_top+12}`} fill="#CCBB44" opacity="0.9" />
          })}

          {/* V-axis ticks */}
          {Vticks.map(v => {
            const y = toYV(v)
            if (y < T_top - 5 || y > B + 5) return null
            return (
              <g key={v}>
                <line x1={L-4} y1={y} x2={L} y2={y} stroke="var(--color-text)" strokeWidth="0.7" />
                <text x={L-6} y={y+4} fontSize="9" fill="var(--color-text-dim)" textAnchor="end">{v}</text>
              </g>
            )
          })}

          {/* x ticks */}
          {[0, 10, 20, 30, 40, 50].map(t => {
            const x = toX(t)
            return (
              <g key={t}>
                <line x1={x} y1={B} x2={x} y2={B+4} stroke="var(--color-text)" strokeWidth="0.7" />
                <text x={x} y={B+14} fontSize="9" fill="var(--color-text-dim)" textAnchor="middle">{t}</text>
              </g>
            )
          })}

          {/* Labels */}
          <text x={L-50} y={(T_top+B)/2} fontSize="11" fill="var(--color-text-dim)" textAnchor="middle"
            transform={`rotate(-90, ${L-50}, ${(T_top+B)/2})`}>V (mV)</text>
          <text x={L+W} y={B+26} fontSize="11" fill="var(--color-text-dim)" textAnchor="end">t (ms)</text>

          {/* Legend */}
          <line x1={L+10} y1={T_top+10} x2={L+32} y2={T_top+10} stroke="#4477AA" strokeWidth="2.5" />
          <text x={L+36} y={T_top+14} fontSize="9" fill="#4477AA">V</text>
          <line x1={L+56} y1={T_top+10} x2={L+76} y2={T_top+10} stroke="#CCBB44" strokeWidth="1.5" opacity="0.8" />
          <text x={L+80} y={T_top+14} fontSize="9" fill="#CCBB44">m</text>
          <line x1={L+96} y1={T_top+10} x2={L+116} y2={T_top+10} stroke="#EE6677" strokeWidth="1.5" opacity="0.8" />
          <text x={L+120} y={T_top+14} fontSize="9" fill="#EE6677">h</text>
          <line x1={L+136} y1={T_top+10} x2={L+156} y2={T_top+10} stroke="#44BB99" strokeWidth="1.5" opacity="0.8" />
          <text x={L+160} y={T_top+14} fontSize="9" fill="#44BB99">n</text>
          <polygon points={`${L+180},${T_top+6} ${L+175},${T_top+15} ${L+185},${T_top+15}`} fill="#CCBB44" opacity="0.9" />
          <text x={L+190} y={T_top+14} fontSize="9" fill="#CCBB44">AP</text>
        </PlotFrame>
      </div>

      <div className="md:col-span-2">
        <Markdown>{`**Hodgkin–Huxley (1952)**: $C_m \\dfrac{dV}{dt} = I_{\\text{ext}} - \\bar{g}_{\\text{Na}} m^3 h (V-E_{\\text{Na}}) - \\bar{g}_K n^4 (V-E_K) - g_L(V-E_L)$

게이팅 ODE: $\\dfrac{dm}{dt} = \\alpha_m(1-m) - \\beta_m m$ (유사하게 h, n).`}</Markdown>
        <Intuition>
          I_ext ≈ 7 μA/cm² 이상에서 스파이크 발화; 10 μA/cm² → ~50–80 Hz 스파이크 트레인.
          m(Na 활성화)이 먼저 열리고, h(Na 불활성화)와 n(K 활성화)이 뒤따른다.
        </Intuition>
      </div>
    </div>
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// CLASSIC DEMOS (preserved from v0.4)
// ═════════════════════════════════════════════════════════════════════════════

function CableDecayDemo() {
  const [lambda, setLambda] = useState(1.0)
  const [v0,     setV0]     = useState(1.0)

  const samples = useMemo(() => {
    const N = 200, xmax = 5
    return Array.from({ length: N + 1 }, (_, i) => {
      const x = (i * xmax) / N
      return [x, v0 * Math.exp(-x / lambda)]
    })
  }, [lambda, v0])

  const px = (x) => 60 + (x / 5) * 480
  const py = (V) => 280 - (V / 1.1) * 240
  const pathD = samples.map(([x, V], i) => `${i === 0 ? 'M' : 'L'} ${px(x).toFixed(1)} ${py(V).toFixed(1)}`).join(' ')
  const oneLamX = px(lambda), oneLamY = py(v0 / Math.E)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <Slider label="공간상수 λ" value={lambda} min={0.3} max={2.5} step={0.05} unit="mm" onChange={setLambda} />
        <Slider label="V₀"         value={v0}     min={0.2} max={1.0} step={0.05} unit=""   onChange={setV0}     color="var(--color-accent)" />
        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft text-sm">
          λ 한 거리에서 신호가 <span className="font-semibold text-accent">37%</span>로 감쇠.
        </div>
      </div>
      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60"  y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.4" />
        <circle cx={oneLamX} cy={oneLamY} r="5" fill="#CCBB44" />
        <line x1={oneLamX} y1={oneLamY} x2={oneLamX} y2={py(0)+4} stroke="#CCBB44" strokeWidth="0.7" strokeDasharray="2 2" />
        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)">V/V₀</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">x</text>
        <text x={oneLamX} y="296" fontSize="11" fill="#CCBB44" textAnchor="middle" fontWeight="600">λ</text>
        <text x={oneLamX+8} y={oneLamY-6} fontSize="10" fill="#CCBB44" fontWeight="600">37%</text>
      </PlotFrame>
      <div className="md:col-span-2 prose">
        <Markdown>{`$V(x) = V_0\\,e^{-x/\\lambda}$, $\\lambda = \\sqrt{d\\,R_m/(4R_i)}$`}</Markdown>
      </div>
    </div>
  )
}

function HHGatingDemo() {
  const [vh, setVh] = useState(-50)
  const [k,  setK]  = useState(8)

  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const V = -100 + (i * 150) / N
      return [V, 1 / (1 + Math.exp(-(V - vh) / k))]
    })
  }, [vh, k])

  const px = (V) => 60 + ((V + 100) / 150) * 480
  const py = (p) => 280 - p * 240
  const pathD = samples.map(([V, p], i) => `${i === 0 ? 'M' : 'L'} ${px(V).toFixed(1)} ${py(p).toFixed(1)}`).join(' ')

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <Slider label="반활성 V_½" value={vh} min={-80} max={-20} step={1} unit="mV" onChange={setVh} />
        <Slider label="기울기 k"   value={k}  min={3}   max={20}  step={1} unit="mV" onChange={setK}  color="var(--color-secondary)" />
      </div>
      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60"  y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1={py(0.5)} x2="540" y2={py(0.5)} stroke="var(--color-text-faint)" strokeWidth="0.6" strokeDasharray="3 3" />
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.4" />
        <circle cx={px(vh)} cy={py(0.5)} r="5" fill="#CCBB44" />
        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)">n∞</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">V (mV)</text>
      </PlotFrame>
      <div className="md:col-span-2 prose">
        <Markdown>{`$n_\\infty(V) = \\dfrac{1}{1+e^{-(V-V_{1/2})/k}}$`}</Markdown>
      </div>
    </div>
  )
}

function NernstDemo() {
  const [Ko,    setKo]    = useState(5.5)
  const [Ki,    setKi]    = useState(140)
  const [tempC, setTempC] = useState(37)

  const T = tempC + 273.15
  const RT_F = 8.314 * T / 96485 * 1000
  const Ek = RT_F * Math.log(Ko / Ki)

  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const ko = 0.5 + (i * 50) / N
      return [ko, RT_F * Math.log(ko / Ki)]
    })
  }, [Ki, RT_F])

  const px = (x) => 60 + (x / 50) * 480
  const py = (e) => 280 - ((e + 120) / 150) * 240
  const pathD = samples.map(([k, e], i) => `${i === 0 ? 'M' : 'L'} ${px(k).toFixed(1)} ${py(e).toFixed(1)}`).join(' ')

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <Slider label="[K⁺]_o" value={Ko}    min={0.5} max={50}  step={0.1}  unit="mM" onChange={setKo} />
        <Slider label="[K⁺]_i" value={Ki}    min={50}  max={200} step={1}    unit="mM" onChange={setKi} />
        <Slider label="온도"   value={tempC}  min={0}   max={45}  step={0.5}  unit="°C" onChange={setTempC} />
        <div className="mt-3 text-2xl font-bold tabular-nums" style={{color:'var(--color-accent)'}}>{Ek.toFixed(1)} mV</div>
      </div>
      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60"  y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1={py(0)} x2="540" y2={py(0)} stroke="var(--color-text-faint)" strokeWidth="0.6" strokeDasharray="3 3" />
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.4" />
        <circle cx={px(Ko)} cy={py(Ek)} r="5" fill="#CCBB44" />
        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)">E_K (mV)</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">[K⁺]_o (mM)</text>
      </PlotFrame>
      <div className="md:col-span-2 prose">
        <Markdown>{`$E_X = \\dfrac{RT}{zF}\\ln\\dfrac{[X]_o}{[X]_i}$`}</Markdown>
      </div>
    </div>
  )
}

function GHKDemo() {
  const [pK,  setPK]  = useState(1.0)
  const [pNa, setPNa] = useState(0.04)
  const [pCl, setPCl] = useState(0.45)

  const Ko = 5, Ki = 140, Nao = 145, Nai = 12, Clo = 110, Cli = 7
  const RTF = 8.314 * 310 / 96485 * 1000
  const num = pK*Ko + pNa*Nao + pCl*Cli
  const den = pK*Ki + pNa*Nai + pCl*Clo
  const Vm  = RTF * Math.log(num / den)
  const total = pK + pNa + pCl
  const fracK = pK/total, fracNa = pNa/total, fracCl = pCl/total

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <Slider label="P_K"  value={pK}  min={0.01} max={2} step={0.01} unit="" onChange={setPK}  color="var(--color-secondary)" />
        <Slider label="P_Na" value={pNa} min={0}    max={2} step={0.01} unit="" onChange={setPNa} color="var(--color-accent)" />
        <Slider label="P_Cl" value={pCl} min={0}    max={2} step={0.01} unit="" onChange={setPCl} color="#228833" />
        <div className="mt-3 text-2xl font-bold tabular-nums" style={{color:'var(--color-accent)'}}>{Vm.toFixed(1)} mV</div>
      </div>
      <PlotFrame width={600} height={300}>
        <text x="300" y="22" textAnchor="middle" fontSize="13" fontWeight="600" fill="var(--color-text)">상대 투과도</text>
        <rect x="80" y="60"  width={fracK  * 440} height="40" fill="#66CCEE" />
        <text x="76" y="86"  textAnchor="end" fontSize="12" fill="var(--color-text)">P_K</text>
        <rect x="80" y="120" width={fracNa * 440} height="40" fill="#4477AA" />
        <text x="76" y="146" textAnchor="end" fontSize="12" fill="var(--color-text)">P_Na</text>
        <rect x="80" y="180" width={fracCl * 440} height="40" fill="#228833" />
        <text x="76" y="206" textAnchor="end" fontSize="12" fill="var(--color-text)">P_Cl</text>
        <text x="300" y="270" textAnchor="middle" fontSize="11" fill="var(--color-text-dim)">→ V_m = {Vm.toFixed(1)} mV</text>
      </PlotFrame>
      <div className="md:col-span-2 prose">
        <Markdown>{`**GHK**: $V_m = \\dfrac{RT}{F}\\ln\\dfrac{P_K[K]_o + P_{Na}[Na]_o + P_{Cl}[Cl]_i}{P_K[K]_i + P_{Na}[Na]_i + P_{Cl}[Cl]_o}$`}</Markdown>
      </div>
    </div>
  )
}

function LIFDemo() {
  const [tau,  setTau]  = useState(15)
  const [Vth,  setVth]  = useState(15)
  const [tref, setTref] = useState(2)

  const Ith = Vth / tau
  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const I = (i * 3 * Ith) / N
      let r = 0
      if (I > Ith) {
        const isi = tau * Math.log(I / (I - Ith))
        r = 1000 / (isi + tref)
      }
      return [I, r]
    })
  }, [tau, Vth, tref, Ith])

  const Imax  = 3 * Ith
  const rmax  = Math.max(...samples.map(([, r]) => r), 50)
  const px    = (i) => 60 + (i / Imax) * 480
  const py    = (r) => 280 - (r / rmax) * 240
  const pathD = samples.map(([i, r], k) => `${k === 0 ? 'M' : 'L'} ${px(i).toFixed(1)} ${py(r).toFixed(1)}`).join(' ')

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <Slider label="τ_m"       value={tau}  min={5}  max={40} step={1}   unit="ms" onChange={setTau} />
        <Slider label="V_th-V_rest" value={Vth} min={5}  max={30} step={1}   unit="mV" onChange={setVth} color="var(--color-warning)" />
        <Slider label="τ_ref"     value={tref} min={0}  max={10} step={0.5} unit="ms" onChange={setTref} color="var(--color-error)" />
        <div className="mt-3 text-sm">Rheobase: <span className="font-bold text-accent">{Ith.toFixed(2)}</span> a.u.</div>
      </div>
      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60"  y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <path d={pathD} fill="none" stroke="#4477AA" strokeWidth="2.4" />
        <line x1={px(Ith)} y1="40" x2={px(Ith)} y2="280" stroke="var(--color-warning)" strokeWidth="0.8" strokeDasharray="3 3" />
        <text x="60" y="32" fontSize="11" fill="var(--color-text-dim)">발화율 (Hz)</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">I</text>
      </PlotFrame>
      <div className="md:col-span-2 prose">
        <Markdown>{`$r = 1/(\\tau_m\\ln(I/(I-I_{th})) + \\tau_{ref})$`}</Markdown>
      </div>
    </div>
  )
}
