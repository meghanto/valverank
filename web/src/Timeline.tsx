import { useEffect, useRef, useState } from 'react'

export const API = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8787'

export type Phase = { phase: 'gush' | 'gush_dead' | 'isolated'; minutes: number; customers: number; hydrants: number; pieces: number[]; pending?: boolean }

/** Server sends large piece lists as a base64 bitset over all pieces (server/codec.py). */
type Wire = number[] | { bits: string }
function unpack(p: Wire): number[] {
  if (Array.isArray(p)) return p
  const bytes = Uint8Array.from(atob(p.bits), c => c.charCodeAt(0))
  const out: number[] = []
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i]
    if (b) for (let j = 0; j < 8; j++) if (b & (1 << j)) out.push(i * 8 + j)
  }
  return out
}
function decode(r: Run): Run {
  const sc = (x?: Scenario) => x && { ...x, phases: x.phases.map(ph => ({ ...ph, pieces: unpack(ph.pieces as unknown as Wire) })) }
  return { ...r, paper: sc(r.paper)!, real: sc(r.real)!, fixed: sc(r.fixed) }
}
function strip(r: Run) {  // the crew brief needs counts, not piece lists
  const sc = (x?: Scenario) => x && { ...x, phases: x.phases.map(ph => ({ ...ph, pieces: [] })) }
  return { ...r, paper: sc(r.paper), real: sc(r.real), fixed: sc(r.fixed) }
}
export type Scenario = { phases: Phase[]; customer_hours: number; segment_customers: number; downstream_customers: number }
export type Run = {
  piece: number; diameter: number; exact: boolean; dead_valves: number[]; solve_ms: number; cached?: boolean
  params: Params; paper: Scenario; real: Scenario
  partial?: boolean  // stage=outage: shut-off phases only, gushing phases pending the pressure solve
  fixed?: Scenario; repaired_valves?: number[]  // City records after the planner's top repairs (pipeline/fixed.py)
}
export type Params = { opening: number; t_first: number; t_dead: number; t_repair: number }

const LABEL: Record<Phase['phase'], string> = {
  gush: 'Break gushing',
  gush_dead: 'Still gushing: dead valve',
  isolated: 'Shut off for repair',
}
const fmt = (n: number) => Math.round(n).toLocaleString('en-US')

export function Timeline({ piece, onShow, onFixed, repaired, initial }: {
  piece: number
  initial?: Partial<Params>  // e.g. parsed from a typed question
  onShow: (pieces: number[], kind: Phase['phase'] | null) => void
  onFixed?: (pieces: number[]) => void
  repaired?: number
}) {
  const [params, setParams] = useState<Params>({ opening: 0.25, t_first: 60, t_dead: 90, t_repair: 360, ...initial })
  const [brief, setBrief] = useState<{ text?: string; err?: string; busy?: boolean }>({})
  const [run, setRun] = useState<Run | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [sel, setSel] = useState<number>(-1)
  const debounce = useRef<number | undefined>(undefined)
  const req = useRef(0)

  useEffect(() => {
    window.clearTimeout(debounce.current)
    debounce.current = window.setTimeout(() => {
      setBusy(true)
      const id = ++req.current
      let full = false
      const q = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
      const get = (stage: string) => fetch(`${API}/break/${piece}?${q}&stage=${stage}`)
        .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      // shut-off outage needs connectivity only (milliseconds): show it while the pressure solve runs
      get('outage').then((r: Run) => { if (id === req.current && !full) { setRun(decode(r)); setErr(null) } }).catch(() => {})
      get('full')
        .then((r: Run) => { if (id === req.current) { full = true; setRun(decode(r)); setErr(null); setSel(-1) } })
        .catch(e => { if (id === req.current) setErr(String(e.message ?? e)) })
        .finally(() => { if (id === req.current) setBusy(false) })
    }, 250)
    return () => window.clearTimeout(debounce.current)
  }, [piece, params])

  // show the worst gushing phase of the real timeline by default
  useEffect(() => {
    if (!run) return
    const ph = run.real.phases
    const i = sel >= 0 ? sel : ph.findIndex(p => p.phase !== 'isolated' && p.customers > 0)
    if (i >= 0) onShow(ph[i].pieces, ph[i].phase)
    else onShow([], null)
    onFixed?.(run.fixed && run.fixed.customer_hours < run.real.customer_hours ? run.fixed.phases[run.fixed.phases.length - 1].pieces : [])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, sel])

  if (err) return <p className="ok">Live pressure model unavailable ({err}). Outage areas above still use the City network.</p>
  if (!run) return <p className="ok">Running the pressure model…</p>

  const total = params.t_first + params.t_dead + params.t_repair  // longest (real) timeline; both tracks share the scale
  const extra = run.real.customer_hours - run.paper.customer_hours
  return (
    <div className={`timeline ${busy ? 'busy' : ''}`}>
      {run.partial && <p className="pending-note">Shut-off outage shown (network only). Solving pressure for the gushing phases…</p>}
      <div className="ch">
        <div><span className="paper">{fmt(run.paper.customer_hours)}</span><small>customer-hours without water if every valve worked</small></div>
        <div><span className="real">{fmt(run.real.customer_hours)}</span><small>with the City's valve records{extra > 0 ? ` (+${fmt(extra)})` : ''}</small></div>
        {run.fixed && (
          <div><span className="fixed">{fmt(run.fixed.customer_hours)}</span>
            <small>after the planner's top {repaired ?? ''} repairs{run.repaired_valves?.length ? ` (fixes ${run.repaired_valves.length} valve${run.repaired_valves.length > 1 ? 's' : ''} here)` : ' (none here)'}</small></div>
        )}
      </div>
      {(run.fixed ? (['paper', 'real', 'fixed'] as const) : (['paper', 'real'] as const)).map(s => (
        <div key={s} className="track">
          <div className={`track-label ${s}`}>{s === 'paper' ? 'Every valve works' : s === 'real' ? 'City valve records' : `After top ${repaired ?? ''} repairs`}</div>
          <div className="bar">
            {run[s]!.phases.map((p, i) => (
              <button
                key={i}
                className={`seg ${p.phase} ${s === 'real' && sel === i ? 'sel' : ''} ${p.pending ? 'pending' : ''}`}
                style={{ flexGrow: Math.max(p.minutes, 1) / total }}
                title={`${LABEL[p.phase]}: ${p.minutes} min, ${fmt(p.customers)} customers`}
                onClick={() => { if (s === 'real') setSel(i); else onShow(p.pieces, p.phase) }}
              >
                <span>{p.pending ? '…' : fmt(p.customers)}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
      <ul className="legend-phases">
        <li><i className="gush" /> gushing: loses ≥15 psi</li>
        <li><i className="gush_dead" /> still gushing (dead valve)</li>
        <li><i className="isolated" /> shut off</li>
      </ul>
      <div className="sliders">
        <Slider label="Break size" value={params.opening} min={0.05} max={1} step={0.05} show={v => `${Math.round(v * 100)}% of pipe bore`}
          onChange={v => setParams({ ...params, opening: v })} />
        <Slider label="Minutes until first valves close" value={params.t_first} min={15} max={240} step={15} show={v => `${v} min`}
          onChange={v => setParams({ ...params, t_first: v })} />
        <Slider label="Extra minutes when a valve is dead" value={params.t_dead} min={15} max={300} step={15} show={v => `${v} min`}
          onChange={v => setParams({ ...params, t_dead: v })} />
        <Slider label="Repair time" value={params.t_repair} min={60} max={720} step={30} show={v => `${(v / 60).toFixed(1)} h`}
          onChange={v => setParams({ ...params, t_repair: v })} />
      </div>
      <div className="brief">
        <button disabled={brief.busy} onClick={() => {
          setBrief({ busy: true })
          fetch(`${API}/brief`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ run: run && strip(run) }) })
            .then(r => r.json().then(j => (r.ok ? setBrief({ text: j.brief }) : setBrief({ err: j.detail ?? `HTTP ${r.status}` }))))
            .catch(e => setBrief({ err: String(e) }))
        }}>{brief.busy ? 'Writing crew brief…' : 'Crew brief (Gemini)'}</button>
        {brief.text && <p>{brief.text}</p>}
        {brief.err && <p className="err">Brief unavailable: {brief.err}</p>}
        <small>Gemini only rewords the numbers above; a brief containing any other number is rejected.</small>
      </div>
      <p className="fine">
        EPANET pressure model of all 290k City mains, {run.exact ? 'full-city solve' : 'local 4 km solve'} in {fmt(run.solve_ms)} ms
        {run.cached ? ' (cached)' : ''}. Gushing counts customers whose pressure falls 15 psi or more below normal. Uncalibrated: plant pressures, demand and times are assumptions (sliders).
      </p>
    </div>
  )
}

function Slider({ label, value, min, max, step, show, onChange }: {
  label: string; value: number; min: number; max: number; step: number; show: (v: number) => string; onChange: (v: number) => void
}) {
  return (
    <label className="slider">
      <span>{label}<b>{show(value)}</b></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(Number(e.target.value))} />
    </label>
  )
}
