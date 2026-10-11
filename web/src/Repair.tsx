import { useEffect, useState } from 'react'

export type RepairData = {
  breaks_per_year: number
  coverage_share_of_pipe_length: number
  customer_hours_per_year: { paper: number; real: number }
  dead_valve_cost_per_year: number
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
  const real = data.customer_hours_per_year.real
  const after = real - saved
  return (
    <section className="repair">
      <h2>Repair planner</h2>
      <p className="lede">
        Each year the City's dead valves cost an estimated <b className="real">{fmt(data.dead_valve_cost_per_year)}</b> customer-hours
        without water across Houston. Pick how many to fix; we choose the ones that matter most.
      </p>
      <label className="slider">
        <span>Valves repaired<b>{fmt(n)}</b></span>
        <input type="range" min={0} max={max} step={max > 500 ? 10 : 1} value={n} onChange={e => setN(Number(e.target.value))} />
      </label>
      <div className="ch">
        <div><span className="real">{fmt(real)}</span><small>customer-hours/yr without water today</small></div>
        <div><span className="fixed">{fmt(after)}</span><small>after repairing {fmt(n)} valves (−{fmt(saved)}, {real ? Math.round((saved / real) * 100) : 0}%)</small></div>
      </div>
      <p className="fine">
        One simulated break per isolation segment ({Math.round(data.coverage_share_of_pipe_length * 100)}% of pipe length so far), weighted by
        pipe length × {fmt(data.breaks_per_year)} breaks/yr (HPW FY2023). Green dots on the map are the chosen valves.
      </p>
    </section>
  )
}
