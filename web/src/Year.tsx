import { useEffect, useState } from 'react'
import { API } from './Timeline'

type Year = {
  year: number; breaks: number; minute_rows: number
  totals: Record<'paper' | 'real' | 'fixed', { customer_hours: number; peak_customers: number }>
  weeks: { week: string; dead_valve_cost: number; after_repairs: number }[]
}
const STILL = '#d9472b', RECOVERED = '#2fa878'  // validated (dataviz validator, dark, surface #171a21)
const fmt = (n: number) => Math.round(n).toLocaleString('en-US')
const M = (n: number) => `${(n / 1e6).toFixed(2)} M`
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function YearPanel({ repaired }: { repaired?: number }) {
  const [y, setY] = useState<Year | null>(null)
  useEffect(() => {
    fetch(`${API}/year`).then(r => (r.ok ? r.json() : Promise.reject())).then(setY).catch(() => setY(null))
  }, [])
  if (!y) return null

  const { paper, real, fixed } = y.totals
  const cost = real.customer_hours - paper.customer_hours
  const saved = real.customer_hours - fixed.customer_hours
  const W = 320, H = 130, top = 16, base = H - 18
  const max = Math.max(...y.weeks.map(w => w.dead_valve_cost))
  const bw = W / y.weeks.length
  const h = (v: number) => (v / max) * (base - top)
  const worst = y.weeks.reduce((a, b) => (b.dead_valve_cost > a.dead_valve_cost ? b : a))
  const wi = y.weeks.indexOf(worst)
  const label = (d: string) => `${MON[Number(d.slice(5, 7)) - 1]} ${Number(d.slice(8, 10))}`
  return (
    <section className="year">
      <h2>A simulated year</h2>
      <p className="lede">
        {fmt(y.breaks)} breaks across {y.year}, each replayed minute by minute in all three scenarios. Dead valves cost{' '}
        <b className="real">{M(cost)}</b> customer-hours; the top {repaired ?? 100} repairs win back <b className="fixed">{M(saved)}</b>.
      </p>
      <div className="legend-row">
        <span><i style={{ background: RECOVERED }} /> recovered by top {repaired ?? 100} repairs</span>
        <span><i style={{ background: STILL }} /> still lost to dead valves</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Weekly customer-hours lost to dead valves in a simulated ${y.year}`}>
        <line x1={0} x2={W} y1={base} y2={base} className="axis" />
        {y.weeks.map((w, i) => {
          const x = i * bw + 0.5, bwid = Math.max(bw - 1.5, 1)
          const still = w.after_repairs, rec = w.dead_valve_cost - w.after_repairs
          return (
            <g key={w.week}>
              <title>{`Week of ${label(w.week)}: ${fmt(w.dead_valve_cost)} customer-hours lost to dead valves; ${fmt(rec)} recovered by repairs, ${fmt(still)} still lost`}</title>
              <rect x={i * bw} y={top} width={bw} height={base - top} fill="transparent" />
              {still > 0 && <rect x={x} y={base - h(still)} width={bwid} height={h(still)} fill={STILL} rx={1} />}
              {rec > 0 && <rect x={x} y={base - h(still) - h(rec) - (still > 0 ? 1 : 0)} width={bwid} height={h(rec)} fill={RECOVERED} rx={1} />}
            </g>
          )
        })}
        {[0, 3, 6, 9].map(m => {
          const i = y.weeks.findIndex(w => Number(w.week.slice(5, 7)) - 1 === m)
          return i < 0 ? null : <text key={m} x={i * bw + 1} y={H - 4} className="tick">{MON[m]}</text>
        })}
        <text x={Math.min(wi * bw + bw / 2, W - 2)} y={base - h(worst.dead_valve_cost) - 4} textAnchor={wi > y.weeks.length - 8 ? 'end' : 'middle'} className="tick">
          {fmt(worst.dead_valve_cost)}
        </text>
      </svg>
      <ul className="facts">
        <li>Worst week ({label(worst.week)}): <b>{fmt(worst.dead_valve_cost)}</b> customer-hours lost to dead valves, <b>{fmt(worst.after_repairs)}</b> after the repairs.</li>
        <li>Every valve working: {M(paper.customer_hours)} · City records: {M(real.customer_hours)} · after repairs: {M(fixed.customer_hours)} customer-hours.</li>
      </ul>
      <p className="fine">
        Seeded simulation, not a forecast: breaks at the planner's rates and random times, default assumptions. {fmt(y.minute_rows)} minute-level
        rows in a compressed Tiger Data hypertable; weekly bars come from its daily continuous aggregate. Partly repaired rings count as unrepaired.
      </p>
    </section>
  )
}
