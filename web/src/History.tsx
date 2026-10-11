import { useEffect, useState } from 'react'
import { API } from './Timeline'

type History = {
  source: string; calls: number; closed: number; first: string; last: string
  months: { month: string; calls: number; closed: number }[]
  leak_hours_to_close: { p25: number; median: number; p75: number; n: number }
  assumed_repair_hours: number
  leak_share_transmission: number; pipe_length_share_transmission: number
}
const OPEN = '#c07d10', CLOSED = '#6a7fe0'  // validated (dataviz validator, dark, surface #171a21)
const fmt = (n: number) => n.toLocaleString('en-US')
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** Every month from first to last, zero-filled (the aggregate only has months with calls). */
function months(h: History) {
  const got = new Map(h.months.map(m => [m.month.slice(0, 7), m]))
  const out: { key: string; label: string; calls: number; closed: number }[] = []
  const d = new Date(h.months[0].month + 'T00:00:00Z'), end = h.months[h.months.length - 1].month.slice(0, 7)
  for (;;) {
    const key = d.toISOString().slice(0, 7)
    const m = got.get(key)
    out.push({ key, label: `${MON[d.getUTCMonth()]} ${d.getUTCFullYear()}`, calls: m?.calls ?? 0, closed: m?.closed ?? 0 })
    if (key === end) return out
    d.setUTCMonth(d.getUTCMonth() + 1)
  }
}

export function History() {
  const [h, setH] = useState<History | null>(null)
  const [err, setErr] = useState(false)
  useEffect(() => {
    fetch(`${API}/history`).then(r => (r.ok ? r.json() : Promise.reject())).then(setH).catch(() => setErr(true))
  }, [])
  if (err || !h) return null

  const ms = months(h)
  const W = 320, H = 124, top = 16, base = H - 18
  const max = Math.max(...ms.map(m => m.calls))
  const bw = W / ms.length
  const y = (v: number) => base - (v / max) * (base - top)
  const ratio = h.pipe_length_share_transmission / Math.max(h.leak_share_transmission, 1e-9)
  return (
    <section className="history">
      <h2>Real break calls (311)</h2>
      <p className="lede">
        {fmt(h.calls)} water-break calls on the City's 311 dashboard, {h.first.slice(0, 7)} to {h.last.slice(0, 7)},
        stored in Tiger Data (hypertable + weekly continuous aggregate).
      </p>
      <div className="legend-row">
        <span><i style={{ background: OPEN }} /> still open</span>
        <span><i style={{ background: CLOSED }} /> closed</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="311 water-break calls per month, open and closed">
        <line x1={0} x2={W} y1={base} y2={base} className="axis" />
        {ms.map((m, i) => {
          const x = i * bw + 1, w = Math.max(bw - 2, 1)  // 2px surface gap between bars
          const open = m.calls - m.closed
          return (
            <g key={m.key}>
              <title>{`${m.label}: ${fmt(m.calls)} calls, ${fmt(m.closed)} closed, ${fmt(open)} still open`}</title>
              <rect x={i * bw} y={top} width={bw} height={base - top} fill="transparent" />
              {open > 0 && <rect x={x} y={y(m.calls)} width={w} height={base - y(open)} fill={OPEN} rx={1.5} />}
              {m.closed > 0 && <rect x={x} y={y(m.closed)} width={w} height={base - y(m.closed)} fill={CLOSED} rx={1.5} />}
            </g>
          )
        })}
        {ms.map((m, i) => (m.key.endsWith('-01') ? (  // year ticks only: month labels collide at this width
          <text key={m.key} x={i * bw + 1} y={H - 4} className="tick">{m.key.slice(0, 4)}</text>
        ) : null))}
        <text x={W - 2} y={y(ms[ms.length - 1].calls) - 3} textAnchor="end" className="tick">{fmt(ms[ms.length - 1].calls)}</text>
      </svg>
      <ul className="facts">
        <li>
          <b>{h.leak_hours_to_close.median} h</b> median from call to close for leak calls (middle half {h.leak_hours_to_close.p25}–{h.leak_hours_to_close.p75} h,
          {' '}{fmt(h.leak_hours_to_close.n)} calls). The model assumes a {h.assumed_repair_hours} h repair.
        </li>
        <li>
          <b>{(h.leak_share_transmission * 100).toFixed(1)}%</b> of leak calls are on mains 24 in+, which are {(h.pipe_length_share_transmission * 100).toFixed(1)}% of
          pipe length: spreading breaks by length gives large mains about {ratio.toFixed(1)}× too many.
        </li>
      </ul>
      <p className="fine">
        Snapshot, not a full history: the dashboard froze on 2024-06-20 showing every still-open call plus that month's closures, so
        older months count only calls never closed, and close times are biased toward quick repairs. Street addresses are not stored;
        each call is matched to its nearest main.
      </p>
    </section>
  )
}
