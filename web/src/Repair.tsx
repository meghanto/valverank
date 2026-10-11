import { useEffect, useState } from 'react'

export type RepairData = {
  breaks_per_year: number
  coverage_share_of_pipe_length: number
  customer_hours_per_year: { paper: number; real: number }
  dead_valve_cost_per_year: number
  by_class: Record<'distribution' | 'transmission', { breaks_per_year: number; paper: number; real: number; gushing_paper: number }>
  rate_weighting: string
  dead_valve_cost_by_mechanism: { shutoff: number; gushing: number }
  neighborhood_shutoff: { paper: number; real: number }
  dead_valves_in_some_ring: number
  curve: number[]
  valves: { id: number; lon: number; lat: number; gain: number }[]
}
const fmt = (n: number) => Math.round(n).toLocaleString('en-US')

export function Repair({ data, onChange }: { data: RepairData; onChange: (n: number) => void }) {
  const max = data.valves.length
  const [n, setN] = useState(Math.min(100, max))
  useEffect(() => onChange(n), [n, onChange])
  const saved = data.curve[n] ?? 0
  const cost = data.dead_valve_cost_per_year
  const after = Math.max(cost - saved, 0)
  const d = data.by_class.distribution
  const t = data.by_class.transmission
  const m = data.dead_valve_cost_by_mechanism
  const ns = data.neighborhood_shutoff
  return (
    <section className="repair">
      <h2>Repair planner</h2>
      <p className="lede">
        On neighborhood mains ({fmt(d.breaks_per_year)} breaks/yr), dead valves turn <b className="paper">{fmt(ns.paper)}</b> customer-hours
        of shut-off water into <b className="real">{fmt(ns.real)}</b> ({(ns.real / ns.paper).toFixed(1)}×). Citywide they cost an estimated{' '}
        <b className="real">{fmt(cost)}</b> customer-hours a year. Pick how many to fix; we choose the ones that matter most.
      </p>
      <ul className="split">
        <li><b>{fmt(m.shutoff)}</b> longer shut-offs <span>City valve records + network connectivity</span></li>
        <li><b>{fmt(m.gushing)}</b> longer gushing before a dead valve's ring is closed <span>uncalibrated pressure model</span></li>
      </ul>
      <label className="slider">
        <span>Valves repaired<b>{fmt(n)}</b></span>
        <input type="range" min={0} max={max} step={max > 500 ? 10 : 1} value={n} onChange={e => setN(Number(e.target.value))} />
      </label>
      <div className="ch">
        <div><span className="real">{fmt(cost)}</span><small>customer-hours/yr lost to dead valves today</small></div>
        <div><span className="fixed">{fmt(after)}</span><small>after repairing {fmt(n)} valves (−{cost ? Math.round((saved / cost) * 100) : 0}%)</small></div>
      </div>
      <p className="fine">
        One simulated break per isolation segment ({Math.round(data.coverage_share_of_pipe_length * 100)}% of pipe length), weighted by
        {fmt(data.breaks_per_year)} breaks/yr (HPW FY2023) spread by pipe length × a break rate per pipe size from 3,495 real 311 calls,
        default slider assumptions. Large mains also cost {fmt(t.paper)} customer-hours a year
        even if every valve worked (low pressure while gushing; no valve repair changes that). Green dots on the map are the chosen valves.
      </p>
    </section>
  )
}
