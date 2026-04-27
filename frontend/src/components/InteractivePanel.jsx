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
  { id: 'rc',     label: 'RC 충전',      slide: 'L3 p.24' },
  { id: 'cable',  label: '케이블 감쇠',  slide: 'L6 p.11' },
  { id: 'hh',     label: 'HH 게이팅',    slide: 'L5 p.24' },
  { id: 'nernst', label: 'Nernst 평형', slide: 'L3 p.27' },
  { id: 'ghk',    label: 'GHK 가중평균', slide: 'L3 p.32' },
  { id: 'lif',    label: 'LIF f–I 곡선', slide: 'L7 p.16' },
  { id: 'alpha',  label: 'Alpha 시냅스', slide: 'L4 p.27' },
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

      {demo === 'rc'     && <RCChargingDemo />}
      {demo === 'cable'  && <CableDecayDemo />}
      {demo === 'hh'     && <HHGatingDemo />}
      {demo === 'nernst' && <NernstDemo />}
      {demo === 'ghk'    && <GHKDemo />}
      {demo === 'lif'    && <LIFDemo />}
      {demo === 'alpha'  && <AlphaSynapseDemo />}
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

// ──────────────────────────────────────────────────────────────
// Nernst equilibrium  E_X = (RT/zF) ln([X]_o / [X]_i)
// ──────────────────────────────────────────────────────────────
function NernstDemo() {
  const [Ko,   setKo]   = useState(5.5)     // mM extracellular
  const [Ki,   setKi]   = useState(140)     // mM intracellular
  const [tempC, setTempC] = useState(37)    // °C

  const T = tempC + 273.15
  const RT_F = 8.314 * T / 96485 * 1000     // mV (RT/F at given temp)
  // K+ has z=+1
  const Ek = RT_F * Math.log(Ko / Ki)

  // Plot E_K vs [K]_o sweep at fixed [K]_i and T
  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const ko = 0.5 + (i * 50) / N      // 0.5 to 50.5 mM
      const e = RT_F * Math.log(ko / Ki)
      return [ko, e]
    })
  }, [Ki, RT_F])

  const px = (x) => 60 + (x / 50) * 480
  const py = (e) => 280 - ((e + 120) / 150) * 240
  const pathD = samples.map(([k, e], i) => `${i === 0 ? 'M' : 'L'} ${px(k).toFixed(1)} ${py(e).toFixed(1)}`).join(' ')

  const cx = px(Ko), cy = py(Ek)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="[K⁺]_o (extracellular)" value={Ko} min={0.5} max={50} step={0.1} unit="mM" onChange={setKo} />
        <Slider label="[K⁺]_i (intracellular)"  value={Ki} min={50}  max={200} step={1}   unit="mM" onChange={setKi} />
        <Slider label="온도"                    value={tempC} min={0} max={45} step={0.5} unit="°C" onChange={setTempC} />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">현재 E_K</div>
          <div className="text-2xl font-bold tabular-nums" style={{ color: 'var(--color-accent)' }}>
            {Ek.toFixed(1)} mV
          </div>
          <div className="text-xs text-text-dim mt-2">
            $E_K = \frac{`{RT}`}{`{zF}`} \ln \dfrac{`{[K]_o}`}{`{[K]_i}`}$
          </div>
          <div className="text-[11px] text-text-faint mt-1">
            온도 ↑ → |E_K| 약간 ↑. [K]_o ↑ → E_K 양의 방향.
          </div>
        </div>
      </div>

      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1={py(0)} x2="540" y2={py(0)} stroke="var(--color-text-faint)" strokeWidth="0.6" strokeDasharray="3 3" />

        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />
        <circle cx={cx} cy={cy} r="5" fill="var(--color-warning)" />
        <line x1={cx} y1={cy} x2={cx} y2={py(0) + 4} stroke="var(--color-warning)" strokeWidth="0.7" strokeDasharray="2 2" />

        <text x="60"  y="32" fontSize="11" fill="var(--color-text-dim)">E_K (mV)</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">[K⁺]_o (mM)</text>
        <text x={cx + 6} y={cy - 4} fontSize="10" fill="var(--color-warning)" fontWeight="600">{Ek.toFixed(0)} mV</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation**: $E_X = \\dfrac{RT}{zF} \\ln \\dfrac{[X]_o}{[X]_i}$

K⁺의 *전기화학 평형 전위*. 농도 비율의 *log* 에 비례 — 10× 차이가 나면 약 60 mV (37°C) 만큼 변한다. 휴지 막전위가 음수인 이유는 바로 [K]_i ≫ [K]_o 이기 때문.`}
        </Markdown>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// GHK weighted log  V_m = (RT/F) ln (Σ P[X]_o / Σ P[X]_i)
// ──────────────────────────────────────────────────────────────
function GHKDemo() {
  const [pK,    setPK]   = useState(1.0)
  const [pNa,   setPNa]  = useState(0.04)
  const [pCl,   setPCl]  = useState(0.45)

  const Ko = 5, Ki = 140
  const Nao = 145, Nai = 12
  const Clo = 110, Cli = 7

  const RTF = 8.314 * 310 / 96485 * 1000   // mV at body temp

  const num = pK*Ko  + pNa*Nao + pCl*Cli
  const den = pK*Ki  + pNa*Nai + pCl*Clo
  const Vm  = RTF * Math.log(num / den)

  // Bars: relative permeability
  const total = pK + pNa + pCl
  const fracK  = pK  / total
  const fracNa = pNa / total
  const fracCl = pCl / total

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">투과도 비율 (rest = 1 : 0.04 : 0.45)</h3>
        <Slider label="P_K"  value={pK}  min={0.01} max={2}    step={0.01} unit="" onChange={setPK}  color="var(--color-secondary)" />
        <Slider label="P_Na" value={pNa} min={0}    max={2}    step={0.01} unit="" onChange={setPNa} color="var(--color-accent)" />
        <Slider label="P_Cl" value={pCl} min={0}    max={2}    step={0.01} unit="" onChange={setPCl} color="#228833" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">현재 V_m</div>
          <div className="text-2xl font-bold tabular-nums" style={{ color: 'var(--color-accent)' }}>
            {Vm.toFixed(1)} mV
          </div>
          <div className="text-[11px] text-text-faint mt-1">
            P_Na ↑ → V_m 탈분극 (+58 쪽). P_Cl ↑ → 약간 hyperpolarize.
          </div>
        </div>
      </div>

      <PlotFrame width={600} height={300}>
        {/* Bar chart of relative permeabilities */}
        <text x="300" y="22" textAnchor="middle" fontSize="13" fontWeight="600" fill="var(--color-text)">상대 투과도</text>

        {/* P_K bar */}
        <rect x="80" y="60" width={fracK * 440} height="40" fill="#66CCEE" />
        <text x="76" y="86" textAnchor="end" fontSize="12" fill="var(--color-text)">P_K</text>
        <text x={88 + fracK * 440} y="86" fontSize="11" fill="var(--color-text-dim)">{(fracK*100).toFixed(0)}%</text>

        <rect x="80" y="120" width={fracNa * 440} height="40" fill="#4477AA" />
        <text x="76" y="146" textAnchor="end" fontSize="12" fill="var(--color-text)">P_Na</text>
        <text x={88 + fracNa * 440} y="146" fontSize="11" fill="var(--color-text-dim)">{(fracNa*100).toFixed(0)}%</text>

        <rect x="80" y="180" width={fracCl * 440} height="40" fill="#228833" />
        <text x="76" y="206" textAnchor="end" fontSize="12" fill="var(--color-text)">P_Cl</text>
        <text x={88 + fracCl * 440} y="206" fontSize="11" fill="var(--color-text-dim)">{(fracCl*100).toFixed(0)}%</text>

        <text x="300" y="270" textAnchor="middle" fontSize="11" fill="var(--color-text-dim)">
          → V_m = {Vm.toFixed(1)} mV
        </text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation (GHK)**: $V_m = \\dfrac{RT}{F} \\ln \\dfrac{P_K[K]_o + P_{Na}[Na]_o + P_{Cl}[Cl]_i}{P_K[K]_i + P_{Na}[Na]_i + P_{Cl}[Cl]_o}$

휴지에서 *P_K 가 압도* 하므로 $V_m \\approx E_K$. AP 정점에서는 *P_Na 가 일시적으로 압도* 하면서 $V_m \\approx E_{Na}$ 로 끌어올림. 슬라이더로 P_Na 를 1 까지 올려보면 그 효과가 보임.`}
        </Markdown>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// LIF f–I curve   r = 1 / (τ ln((I−I_th)/(I−I_th−ΔV/R)))
// ──────────────────────────────────────────────────────────────
function LIFDemo() {
  const [tau,    setTau]    = useState(15)    // ms
  const [Vth,    setVth]    = useState(15)    // mV above rest
  const [tref,   setTref]   = useState(2)     // ms refractory

  // r(I) for I from 0 to 3*Ith
  const Ith = Vth / tau               // rheobase current ~ Vth/τ
  const samples = useMemo(() => {
    const N = 200
    return Array.from({ length: N + 1 }, (_, i) => {
      const I = (i * 3 * Ith) / N
      let r = 0
      if (I > Ith) {
        const isi = tau * Math.log(I / (I - Ith))   // ms
        r = 1000 / (isi + tref)                     // Hz
      }
      return [I, r]
    })
  }, [tau, Vth, tref, Ith])

  const Imax = 3 * Ith
  const rmax = Math.max(...samples.map(([, r]) => r), 50)
  const px = (i) => 60 + (i / Imax) * 480
  const py = (r) => 280 - (r / rmax) * 240
  const pathD = samples.map(([i, r], k) => `${k === 0 ? 'M' : 'L'} ${px(i).toFixed(1)} ${py(r).toFixed(1)}`).join(' ')

  const xIth = px(Ith)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="τ_m (시상수)"        value={tau}  min={5}  max={40} step={1}   unit="ms" onChange={setTau} />
        <Slider label="V_th − V_rest"      value={Vth}  min={5}  max={30} step={1}   unit="mV" onChange={setVth} color="var(--color-warning)" />
        <Slider label="τ_ref (불응기)"      value={tref} min={0}  max={10} step={0.5} unit="ms" onChange={setTref} color="var(--color-error)" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">Rheobase (최소 발화 전류)</div>
          <div className="text-2xl font-bold tabular-nums" style={{ color: 'var(--color-warning)' }}>
            {Ith.toFixed(2)} <span className="text-sm">a.u.</span>
          </div>
          <div className="text-[11px] text-text-faint mt-1">
            I &lt; I_th 이면 무발화. τ_ref 가 클수록 고주파 saturation.
          </div>
        </div>
      </div>

      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />

        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />

        {/* Rheobase line */}
        <line x1={xIth} y1="40" x2={xIth} y2="280" stroke="var(--color-warning)" strokeWidth="0.8" strokeDasharray="3 3" />
        <text x={xIth} y="296" textAnchor="middle" fontSize="11" fill="var(--color-warning)" fontWeight="600">I_th</text>

        <text x="60"  y="32" fontSize="11" fill="var(--color-text-dim)">발화율 (Hz)</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">I (a.u.)</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**ISI**: $\\Delta t = \\tau_m \\ln\\dfrac{I}{I - I_{th}}$, **firing rate**: $r = \\dfrac{1}{\\Delta t + \\tau_{ref}}$

LIF 의 *f–I* 곡선은 *I_th 임계값* 에서 0 으로 꺾이고, 큰 I 에서는 1/τ_ref 로 saturate. *불응기* 가 짧을수록 직선적, 길수록 빨리 평평해진다.`}
        </Markdown>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────
// Alpha synapse  α(t) = (t/τ_p) e^{1 − t/τ_p}
// ──────────────────────────────────────────────────────────────
function AlphaSynapseDemo() {
  const [tauPeak, setTauPeak] = useState(5)   // ms
  const [gMax,    setGMax]    = useState(1.0) // arbitrary

  const samples = useMemo(() => {
    const N = 300, tmax = 50
    return Array.from({ length: N + 1 }, (_, i) => {
      const t = (i * tmax) / N
      const g = gMax * (t / tauPeak) * Math.exp(1 - t / tauPeak)
      return [t, g]
    })
  }, [tauPeak, gMax])

  const px = (t) => 60 + (t / 50) * 480
  const py = (g) => 280 - (g / 1.2) * 240
  const pathD = samples.map(([t, g], i) => `${i === 0 ? 'M' : 'L'} ${px(t).toFixed(1)} ${py(g).toFixed(1)}`).join(' ')

  const peakX = px(tauPeak)
  const peakY = py(gMax)

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="text-sm font-semibold mb-3 text-text-bright">매개변수</h3>
        <Slider label="τ_peak"       value={tauPeak} min={0.5} max={20} step={0.5} unit="ms" onChange={setTauPeak} />
        <Slider label="g_max"        value={gMax}    min={0.2} max={1.5} step={0.05} unit="" onChange={setGMax} color="var(--color-accent)" />

        <div className="mt-4 p-3 rounded-lg bg-surface-2 border border-border-soft">
          <div className="text-xs text-text-dim mb-1">관찰 포인트</div>
          <div className="text-sm">
            *t = τ_peak* 시점에 g 가 *최대값 g_max* 에 도달.
            <br />τ_peak 가 작으면 *AMPA-like*, 크면 *NMDA-like* 동역학.
          </div>
        </div>
      </div>

      <PlotFrame>
        <line x1="60" y1="280" x2="540" y2="280" stroke="var(--color-text)" strokeWidth="1" />
        <line x1="60" y1="40"  x2="60" y2="280"  stroke="var(--color-text)" strokeWidth="1" />

        <path d={pathD} fill="none" stroke="var(--color-accent)" strokeWidth="2.4" />

        <circle cx={peakX} cy={peakY} r="5" fill="var(--color-warning)" />
        <line x1={peakX} y1={peakY} x2={peakX} y2={py(0) + 4} stroke="var(--color-warning)" strokeWidth="0.7" strokeDasharray="2 2" />

        <text x="60"  y="32" fontSize="11" fill="var(--color-text-dim)">g_syn</text>
        <text x="544" y="290" fontSize="11" fill="var(--color-text-dim)">t (ms)</text>
        <text x={peakX} y="296" textAnchor="middle" fontSize="11" fill="var(--color-warning)" fontWeight="600">τ_peak</text>
      </PlotFrame>

      <div className="md:col-span-2 prose">
        <Markdown>
{`**Equation**: $g_{syn}(t) = g_{max} \\dfrac{t}{\\tau_{peak}} e^{1 - t/\\tau_{peak}}$

알파 함수는 *생물학적으로 그럴듯한* 시냅스 응답 모양 — 0에서 시작해 *τ_peak 에서 정점*, 그 후 지수적 감쇠. AMPA (~1ms), NMDA (~50ms), GABA_A (~5ms), GABA_B (~100ms).`}
        </Markdown>
      </div>
    </div>
  )
}
