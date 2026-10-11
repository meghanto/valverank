import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, MapMouseEvent } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Timeline, API, type Phase, type Params } from './Timeline'
import { Repair, type RepairData } from './Repair'
import { History } from './History'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { Protocol } from 'pmtiles'

// MapLibre v6 loads its worker from a file next to the bundle; Vite doesn't
// copy it, so emit it as an asset and point MapLibre at it.
maplibregl.setWorkerUrl(workerUrl)
maplibregl.addProtocol('pmtiles', new Protocol().tile)

const DATA = `${import.meta.env.BASE_URL}data/`
const BASEMAP = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

// [customers, hydrants, length_m, gallons, valveIds, deadValveIds, downstreamCustomers, downstreamHydrants]
type SegRow = [number, number, number, number, number[], number[], number, number]
type Segments = { paper: SegRow[]; real: SegRow[] }
type Stats = {
  paper: ScenarioStats
  real: ScenarioStats
  valves_on_mains: number
  valves_on_mains_inop: number
  valves_on_mains_last_inspected_5y_plus_share: number
  share_pipes_real_gt_2x: number
  data_snapshot: string
}
type ScenarioStats = {
  expected_customers_per_break: number
  expected_customers_per_break_with_downstream: number
  expected_hydrants_per_break: number
  expected_gallons_drained: number
  max_customers: number
}
type Break = {
  k: number
  lngLat: [number, number]
  sp: number
  sr: number
  diameter: number | null
  material: string | null
  year: number | null
  stage: 'paper' | 'real'
}
type ValveProps = { id: number; c: string; r: string | null; cy: number | null; d: number | null; iy: number | null }

const fmt = (n: number) => n.toLocaleString('en-US')
type Showcase = { repaired: number; cases: { piece: number; lon: number; lat: number; label: string }[] }

/** Screen distance (px) from (x, y) to a rendered line feature. */
function pixelDistance(map: maplibregl.Map, f: maplibregl.MapGeoJSONFeature, x: number, y: number) {
  const g = f.geometry
  const lines: number[][][] = g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : []
  let best = Infinity
  for (const line of lines) {
    const pts = (line as [number, number][]).map(c => map.project(c))
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], b = pts[i + 1]
      const dx = b.x - a.x, dy = b.y - a.y
      const u = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy || 1)))
      best = Math.min(best, Math.hypot(a.x + u * dx - x, a.y + u * dy - y))
    }
  }
  return best
}

export default function App() {
  const mapEl = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const segsRef = useRef<Segments | null>(null)
  const valveIndex = useRef<Map<number, ValveProps>>(new Map())
  const timer = useRef<number | undefined>(undefined)
  const [stats, setStats] = useState<Stats | null>(null)
  const [brk, setBrk] = useState<Break | null>(null)
  const [loading, setLoading] = useState(true)
  const [repair, setRepair] = useState<RepairData | null>(null)
  const [showcase, setShowcase] = useState<Showcase | null>(null)
  const [initial, setInitial] = useState<Partial<Params> | undefined>(undefined)
  const [ask, setAsk] = useState<{ q: string; busy?: boolean; err?: string }>({ q: '' })

  useEffect(() => {
    fetch(`${DATA}stats.json`).then(r => r.json()).then(setStats)
    fetch(`${DATA}repair.json`).then(r => r.json()).then(setRepair).catch(() => setRepair(null))
    fetch(`${DATA}showcase.json`).then(r => r.json()).then(setShowcase).catch(() => setShowcase(null))
    fetch(`${DATA}segments.json`).then(r => r.json()).then(s => (segsRef.current = s))
    fetch(`${DATA}valves_inop.json`)
      .then(r => r.json())
      .then((o: Record<string, [string | null, number | null, number | null]>) => {
        for (const [id, [r, cy, d]] of Object.entries(o)) valveIndex.current.set(+id, { id: +id, c: 'INOP', r, cy, d, iy: null })
      })

    const map = new maplibregl.Map({
      container: mapEl.current!,
      style: BASEMAP,
      center: [-95.43, 29.81],
      zoom: 12.2,
      attributionControl: { compact: true },
    })
    mapRef.current = map
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      // whole City network as one PMTiles file (pipes, valves, hydrants layers), fetched by range requests
      map.addSource('city', { type: 'vector', url: `pmtiles://${new URL(`${DATA}city.pmtiles`, location.href).href}` })
      map.addSource('break', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })

      map.addLayer({
        id: 'pipes', type: 'line', source: 'city', 'source-layer': 'pipes',
        paint: {
          'line-color': ['case', ['<', ['coalesce', ['get', 'y'], 2000], 1970], '#6b7c93', '#3d4a5c'],
          'line-width': ['interpolate', ['linear'], ['zoom'], 11, ['case', ['>=', ['to-number', ['get', 'd'], 0], 24], 2, 0.6],
                         16, ['case', ['>=', ['to-number', ['get', 'd'], 0], 24], 6, 2.5]],
        },
      })
      map.addLayer({
        id: 'pressure-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['in', ['get', 'k'], ['literal', []]],
        paint: { 'line-color': '#ffb000', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 2, 16, 5], 'line-opacity': 0.9 },
      })
      map.addLayer({
        id: 'real-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['==', ['get', 'sr'], -1],
        paint: { 'line-color': '#ff4f32', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 2.5, 16, 6] },
      })
      map.addLayer({
        id: 'fixed-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['in', ['get', 'k'], ['literal', []]],
        paint: { 'line-color': '#3ddc97', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 2.5, 16, 6] },
      })
      map.addLayer({
        id: 'paper-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['==', ['get', 'sp'], -1],
        paint: { 'line-color': '#4fb3ff', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 3, 16, 7] },
      })
      map.addLayer({
        id: 'hydrants-hl', type: 'circle', source: 'city', 'source-layer': 'hydrants', filter: ['==', ['get', 'sr'], -1],
        paint: { 'circle-radius': 4, 'circle-color': '#ffd166', 'circle-stroke-color': '#111318', 'circle-stroke-width': 1 },
      })
      map.addLayer({
        id: 'valves-inop', type: 'circle', source: 'city', 'source-layer': 'valves', filter: ['==', ['get', 'c'], 'INOP'],
        minzoom: 10,
        paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 12, 1.5, 16, 4], 'circle-color': '#ff4f32', 'circle-opacity': 0.55 },
      })
      map.addLayer({
        id: 'valves-close', type: 'circle', source: 'city', 'source-layer': 'valves', filter: ['in', ['get', 'id'], ['literal', []]],
        paint: { 'circle-radius': 6, 'circle-color': '#f5f3ee', 'circle-stroke-color': '#111318', 'circle-stroke-width': 2 },
      })
      map.addLayer({
        id: 'valves-dead', type: 'symbol', source: 'city', 'source-layer': 'valves', filter: ['in', ['get', 'id'], ['literal', []]],
        layout: { 'text-field': '✕', 'text-size': 18, 'text-allow-overlap': true },
        paint: { 'text-color': '#ff4f32', 'text-halo-color': '#111318', 'text-halo-width': 2 },
      })
      map.addLayer({
        id: 'break', type: 'circle', source: 'break',
        paint: { 'circle-radius': 9, 'circle-color': '#ff4f32', 'circle-stroke-color': '#fff', 'circle-stroke-width': 3 },
      })

      map.addSource('repair', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      map.addLayer({
        id: 'repair', type: 'circle', source: 'repair', filter: ['<', ['get', 'rank'], 0],
        paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 2.5, 16, 7], 'circle-color': '#3ddc97',
                 'circle-stroke-color': '#111318', 'circle-stroke-width': 1 },
      })
      map.once('idle', () => setLoading(false))
      map.on('mouseenter', 'pipes', () => (map.getCanvas().style.cursor = 'crosshair'))
      map.on('mouseleave', 'pipes', () => (map.getCanvas().style.cursor = ''))
      // pipes are ~1 px wide at city zoom: accept clicks within a few pixels, nearest box first
      map.on('click', (e: MapMouseEvent) => {
        const { x, y } = e.point
        const t = 12
        const near = map.queryRenderedFeatures([[x - t, y - t], [x + t, y + t]], { layers: ['pipes'] })
        // nearest first; within 2 px (pipes meeting at a junction) prefer the bigger main
        const diam = (g: maplibregl.MapGeoJSONFeature) => Number(g.properties.d) || 0
        const f = near.map(g => ({ g, d: Math.round(pixelDistance(map, g, x, y) / 2) }))
          .sort((a, b) => a.d - b.d || diam(b.g) - diam(a.g))[0]?.g
        if (!f) return
        const p = f.properties as { k: number; sp: number; sr: number; d: number | null; m: string | null; y: number | null }
        setInitial(undefined)  // a clicked break uses default assumptions, not the last question's
        breakAt([e.lngLat.lng, e.lngLat.lat], p)
      })
    })
    return () => map.remove()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const showRepairs = useCallback((n: number) => {
    const map = mapRef.current
    if (!map || !map.getLayer('repair')) return
    map.setFilter('repair', ['<', ['get', 'rank'], n])
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !repair) return
    const set = () => (map.getSource('repair') as GeoJSONSource | undefined)?.setData({
      type: 'FeatureCollection',
      features: repair.valves.map((v, i) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [v.lon, v.lat] }, properties: { rank: i, id: v.id } })),
    })
    if (map.getSource('repair')) set()
    else map.once('load', set)
  }, [repair])

  function showPressure(pieces: number[], kind: Phase['phase'] | null) {
    const map = mapRef.current
    if (!map) return
    // isolated-phase pieces are already drawn as the outage areas; pressure layer shows gushing phases
    map.setFilter('pressure-hl', ['in', ['get', 'k'], ['literal', kind && kind !== 'isolated' ? pieces : []]])
  }

  function showFixed(pieces: number[]) {
    mapRef.current?.setFilter('fixed-hl', ['in', ['get', 'k'], ['literal', pieces]])
  }

  /** Jump to a showcase break: fly there, then break the pipe with that piece id once its tile is loaded. */
  function submitAsk(e: FormEvent) {
    e.preventDefault()
    if (!ask.q.trim()) return
    setAsk({ ...ask, busy: true, err: undefined })
    fetch(`${API}/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: ask.q }) })
      .then(r => r.json().then(j => {
        if (!r.ok) throw new Error(j.detail ?? `HTTP ${r.status}`)
        setInitial(j.run.params)
        setAsk({ q: ask.q })
        goTo({ piece: j.piece, lon: j.lonlat[0], lat: j.lonlat[1] })
      }))
      .catch(err => setAsk({ q: ask.q, err: String(err.message ?? err) }))
  }

  function goTo(c: { piece: number; lon: number; lat: number }) {
    const map = mapRef.current
    if (!map) return
    map.flyTo({ center: [c.lon, c.lat], zoom: 15.5, duration: 1200 })
    map.once('idle', () => {
      const f = map.querySourceFeatures('city', { sourceLayer: 'pipes', filter: ['==', ['get', 'k'], c.piece] })[0]
      if (f) breakAt([c.lon, c.lat], f.properties as { k: number; sp: number; sr: number; d: number | null; m: string | null; y: number | null })
    })
  }

  function breakAt(lngLat: [number, number], p: { k: number; sp: number; sr: number; d: number | null; m: string | null; y: number | null }) {
    const map = mapRef.current
    const segs = segsRef.current
    if (!map || !segs) return
    window.clearTimeout(timer.current)
    ;(map.getSource('break') as GeoJSONSource).setData({
      type: 'FeatureCollection',
      features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: lngLat }, properties: {} }],
    })
    // distribution outages are a few hundred metres of pipe (zoom in); transmission breaks
    // drop pressure across whole districts while gushing (zoom out to show it)
    const big = (Number(p.d) || 0) >= 24
    if (big) map.easeTo({ center: lngLat, zoom: 11.5, duration: 900 })
    else if (map.getZoom() < 15) map.easeTo({ center: lngLat, zoom: 15.5, duration: 900 })
    const paper = segs.paper[p.sp]
    map.setFilter('paper-hl', ['==', ['get', 'sp'], p.sp])
    map.setFilter('real-hl', ['==', ['get', 'sr'], -1])
    map.setFilter('valves-close', ['in', ['get', 'id'], ['literal', paper[4]]])
    map.setFilter('valves-dead', ['in', ['get', 'id'], ['literal', []]])
    map.setFilter('hydrants-hl', ['==', ['get', 'sp'], p.sp])
    map.setFilter('pressure-hl', ['in', ['get', 'k'], ['literal', []]])
    showFixed([])
    const b: Break = { k: p.k, lngLat, sp: p.sp, sr: p.sr, diameter: p.d, material: p.m, year: p.y, stage: 'paper' }
    setBrk(b)
    timer.current = window.setTimeout(() => {
      const real = segs.real[p.sr]
      map.setFilter('real-hl', ['==', ['get', 'sr'], p.sr])
      map.setFilter('valves-close', ['in', ['get', 'id'], ['literal', real[4]]])
      map.setFilter('valves-dead', ['in', ['get', 'id'], ['literal', real[5]]])
      map.setFilter('hydrants-hl', ['==', ['get', 'sr'], p.sr])
      setBrk({ ...b, stage: 'real' })
    }, 1400)
  }

  function clearBreak() {
    const map = mapRef.current
    window.clearTimeout(timer.current)
    setBrk(null)
    setInitial(undefined)
    showPressure([], null)
    showFixed([])
    if (!map) return
    ;(map.getSource('break') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
    for (const id of ['paper-hl', 'real-hl']) map.setFilter(id, ['==', ['get', id === 'paper-hl' ? 'sp' : 'sr'], -1])
    map.setFilter('hydrants-hl', ['==', ['get', 'sr'], -1])
    for (const id of ['valves-close', 'valves-dead']) map.setFilter(id, ['in', ['get', 'id'], ['literal', []]])
  }

  const segs = segsRef.current
  const paper = brk && segs ? segs.paper[brk.sp] : null
  const real = brk && segs ? segs.real[brk.sr] : null
  const dead = real ? real[5].map(id => valveIndex.current.get(id)).filter(Boolean) as ValveProps[] : []

  return (
    <div className="app">
      <aside className="panel">
        <header>
          <h1>Shutoff</h1>
          <p className="lede">
            When a Houston water main breaks, crews close the nearest valves. The City's own records mark many of
            those valves as broken or lost, so the outage spreads to the next ones out.
          </p>
        </header>

        {!brk && stats && (
          <section>
            <p className="hint">Click any water main on the map to break it, or ask:</p>
            <form className="ask" onSubmit={submitAsk}>
              <input value={ask.q} onChange={e => setAsk({ q: e.target.value })} disabled={ask.busy}
                placeholder="What if the main at Westheimer and Kirby bursts and crews take 2 hours?" aria-label="Ask about a break" />
              <button disabled={ask.busy}>{ask.busy ? 'Finding…' : 'Ask'}</button>
            </form>
            {ask.err && <p className="err">{ask.err}</p>}
            <div className="kpis">
              <Kpi label="Main valves recorded inoperable" value={fmt(stats.valves_on_mains_inop)} sub={`of ${fmt(stats.valves_on_mains)} on mains`} />
              <Kpi label="Last inspected 5+ years ago" value={`${Math.round(stats.valves_on_mains_last_inspected_5y_plus_share * 100)}%`} sub="industry practice: every valve within 5 years" />
              <Kpi label="Customers out, average break" value={`${stats.paper.expected_customers_per_break_with_downstream} → ${stats.real.expected_customers_per_break_with_downstream}`} sub="all valves work → City-recorded valve status; includes customers cut off downstream" />
              <Kpi label="Fire hydrants out, average break" value={`${stats.paper.expected_hydrants_per_break} → ${stats.real.expected_hydrants_per_break}`} sub="hydrants on the shut-off pipes" />
            </div>
          </section>
        )}
        {!brk && repair && repair.valves.length > 0 && <Repair data={repair} onChange={showRepairs} />}
        {!brk && <History />}
        {!brk && showcase && (
          <section className="showcase">
            <h2>What the top {showcase.repaired} repairs change</h2>
            {showcase.cases.map(c => (
              <button key={c.piece} onClick={() => goTo(c)}>{c.label}</button>
            ))}
          </section>
        )}

        {brk && paper && real && (
          <section className="break">
            <div className="break-head">
              <span className="dot" /> Break on a {brk.diameter ? `${brk.diameter}″ ` : ''}{brk.material ?? ''} main
              {brk.year ? `, laid ${brk.year}` : ''}
            </div>
            <table className="compare">
              <thead>
                <tr><th /><th className="paper">If every valve worked</th><th className="real">With the City's valve records</th></tr>
              </thead>
              <tbody>
                <Row label="Customers without water" a={paper[0] + paper[6]} b={real[0] + real[6]} show={brk.stage === 'real'} />
                <Row label="… of which cut off downstream" a={paper[6]} b={real[6]} show={brk.stage === 'real'} sub />
                <Row label="Fire hydrants dry" a={paper[1] + paper[7]} b={real[1] + real[7]} show={brk.stage === 'real'} />
                <Row label="Pipe shut off (m)" a={paper[2]} b={real[2]} show={brk.stage === 'real'} />
                <Row label="Water drained (gal)" a={paper[3]} b={real[3]} show={brk.stage === 'real'} />
                <Row label="Valves crews must close" a={paper[4].length} b={real[4].length} show={brk.stage === 'real'} />
              </tbody>
            </table>
            {brk.stage === 'real' && (
              dead.length ? (
                <div className="dead">
                  <h3>{dead.length} valve{dead.length > 1 ? 's' : ''} in the way {dead.length > 1 ? 'are' : 'is'} recorded inoperable</h3>
                  <ul>
                    {dead.slice(0, 6).map(v => (
                      <li key={v.id}>
                        <b>#{v.id}</b> {v.d ? `${v.d}″` : ''} · {(v.r ?? 'inoperable').replace(/_/g, ' ').toLowerCase()}
                        {v.cy ? ` · last checked ${v.cy}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="ok">Every valve around this break is recorded as working.</p>
              )
            )}
            {brk.stage === 'real' && <Timeline key={brk.k} piece={brk.k} onShow={showPressure} onFixed={showFixed} repaired={showcase?.repaired} initial={initial} />}
            <button className="reset" onClick={clearBreak}>Back to overview</button>
          </section>
        )}

        <footer>
          {loading ? 'Loading Houston water network…' : `Model results from ${stats?.data_snapshot ?? 'City GIS'}. Customers are utility accounts, not people.`}
        </footer>
      </aside>
      <div ref={mapEl} className="map" />
      <div className="legend">
        <span><i style={{ background: '#4fb3ff' }} /> outage if every valve worked</span>
        <span><i style={{ background: '#ff4f32' }} /> outage with recorded broken valves</span>
        <span><i style={{ background: '#3ddc97' }} /> after top {showcase?.repaired ?? 100} repairs</span>
        <span><i className="round" style={{ background: '#f5f3ee' }} /> valves crews close</span>
        <span><b style={{ color: '#ff4f32' }}>✕</b> recorded inoperable</span>
        <span><i style={{ background: '#ffb000' }} /> loses ≥15 psi while gushing</span>
      </div>
    </div>
  )
}

function Kpi({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  )
}

function Row({ label, a, b, show, sub }: { label: string; a: number; b: number; show: boolean; sub?: boolean }) {
  const worse = b > a
  return (
    <tr className={sub ? 'sub' : undefined}>
      <td>{label}</td>
      <td className="paper">{fmt(a)}</td>
      <td className={`real ${worse ? 'worse' : ''}`}>{show ? fmt(b) : '…'}</td>
    </tr>
  )
}
