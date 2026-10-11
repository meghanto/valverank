import { useCallback, useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, MapMouseEvent } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Timeline, type Phase, type Params, type Run } from './Timeline'
import { Repair, type RepairData } from './Repair'
import { History } from './History'
import { YearPanel } from './Year'
import { Search } from './Search'
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

type PipeProps = { k: number; sp: number; sr: number; d: number | null; m: string | null; y: number | null }
const pipeProps = (f: { id?: string | number; properties: unknown }): PipeProps => ({ ...(f.properties as PipeProps), k: Number(f.id) })

/** Closest point on a rendered line to a screen position, as lng/lat: the break sits on the pipe, not on the click. */
function snapToPipe(map: maplibregl.Map, f: maplibregl.MapGeoJSONFeature, x: number, y: number): [number, number] {
  const g = f.geometry
  const lines: number[][][] = g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : []
  let best = Infinity, bx = x, by = y
  for (const line of lines) {
    const pts = (line as [number, number][]).map(c => map.project(c))
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], b = pts[i + 1], dx = b.x - a.x, dy = b.y - a.y
      const u = Math.max(0, Math.min(1, ((x - a.x) * dx + (y - a.y) * dy) / (dx * dx + dy * dy || 1)))
      const px = a.x + u * dx, py = a.y + u * dy, d = Math.hypot(px - x, py - y)
      if (d < best) { best = d; bx = px; by = py }
    }
  }
  const ll = map.unproject([bx, by])
  return [ll.lng, ll.lat]
}

/** Nearest pipe within 12 px; within 2 px (pipes meeting at a junction) prefer the bigger main. */
function nearestPipe(map: maplibregl.Map, x: number, y: number) {
  const t = 12
  const near = map.queryRenderedFeatures([[x - t, y - t], [x + t, y + t]], { layers: ['pipes'] })
  const diam = (g: maplibregl.MapGeoJSONFeature) => Number(g.properties.d) || 0
  return near.map(g => ({ g, d: Math.round(pixelDistance(map, g, x, y) / 2) }))
    .sort((a, b) => a.d - b.d || diam(b.g) - diam(a.g))[0]?.g
}

// pipe ids live in the tile feature id (tippecanoe --use-attribute-for-id=k), not in properties
const NONE: maplibregl.FilterSpecification = ['==', ['id'], -1]
/** Pipes whose id is in a (possibly 250k-long) list: 'match' is a hash lookup; 'in' over a literal array is a linear scan per feature. */
function inPieces(list: number[]): maplibregl.FilterSpecification {
  return list.length ? (['match', ['id'], [...new Set(list)], true, false] as never) : NONE
}

export default function App() {
  const mapEl = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const tipRef = useRef<HTMLDivElement>(null)
  const pulseRef = useRef<number>(0)
  const segsRef = useRef<Segments | null>(null)
  const valveIndex = useRef<Map<number, ValveProps>>(new Map())
  const timer = useRef<number | undefined>(undefined)
  const [stats, setStats] = useState<Stats | null>(null)
  const [brk, setBrk] = useState<Break | null>(null)
  const [loading, setLoading] = useState(true)
  const [repair, setRepair] = useState<RepairData | null>(null)
  const [showcase, setShowcase] = useState<Showcase | null>(null)
  const [initial, setInitial] = useState<Partial<Params> | undefined>(undefined)
  const [run, setRun] = useState<Run | null>(null)

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
      center: [-95.40, 29.78],
      zoom: 10.4,  // whole city: mains >= 12 in are in the tiles from zoom 8, every pipe from 12
      minZoom: 8,
      attributionControl: { compact: true },
    })
    mapRef.current = map
    if (location.hostname === 'localhost') (window as unknown as { __map: maplibregl.Map }).__map = map  // local debugging only
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      // whole City network as one PMTiles file (pipes, valves, hydrants layers), fetched by range requests
      map.addSource('city', { type: 'vector', url: `pmtiles://${new URL(`${DATA}city.pmtiles`, location.href).href}` })
      map.addSource('break', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })

      const D = ['to-number', ['get', 'd'], 8] as const
      const byDiam = <T,>(big: T, mid: T, small: T) => ['case', ['>=', D, 24], big, ['>=', D, 12], mid, small]
      map.addLayer({
        id: 'pipes', type: 'line', source: 'city', 'source-layer': 'pipes',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          // size reads as hierarchy: transmission brightest and widest; hovered pipe lights up
          'line-color': ['case', ['boolean', ['feature-state', 'hover'], false], '#f5f3ee', byDiam('#8fa6c4', '#5f7391', '#3f4b5e')] as never,
          'line-width': ['interpolate', ['linear'], ['zoom'],
            8, byDiam(1.6, 0.5, 0.2), 12, byDiam(3, 1.4, 0.8), 16, byDiam(7, 3.5, 2.2)] as never,
          'line-opacity-transition': { duration: 250 },
        },
      })
      const lineW = (a: number, b: number) => ['interpolate', ['linear'], ['zoom'], 10, a, 16, b] as never
      map.addLayer({
        id: 'pressure-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: NONE,
        layout: { 'line-cap': 'round' },
        paint: { 'line-color': '#ffb000', 'line-width': lineW(1.5, 5), 'line-opacity': 0.85 },
      })
      map.addLayer({
        id: 'real-glow', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['==', ['get', 'sr'], -1],
        layout: { 'line-cap': 'round' },
        paint: { 'line-color': '#ff4f32', 'line-width': lineW(8, 18), 'line-blur': 6, 'line-opacity': 0.35 },
      })
      map.addLayer({
        id: 'real-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['==', ['get', 'sr'], -1],
        layout: { 'line-cap': 'round' },
        paint: { 'line-color': '#ff4f32', 'line-width': lineW(2.5, 6) },
      })
      map.addLayer({
        id: 'fixed-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: NONE,
        layout: { 'line-cap': 'round' },
        paint: { 'line-color': '#3ddc97', 'line-width': lineW(2.5, 6) },
      })
      map.addLayer({
        id: 'paper-hl', type: 'line', source: 'city', 'source-layer': 'pipes', filter: ['==', ['get', 'sp'], -1],
        layout: { 'line-cap': 'round' },
        paint: { 'line-color': '#4fb3ff', 'line-width': lineW(3, 7) },
      })
      map.addLayer({
        id: 'hydrants-hl', type: 'circle', source: 'city', 'source-layer': 'hydrants', filter: ['==', ['get', 'sr'], -1],
        paint: { 'circle-radius': 4, 'circle-color': '#ffd166', 'circle-stroke-color': '#111318', 'circle-stroke-width': 1 },
      })
      map.addLayer({
        id: 'valves-inop', type: 'circle', source: 'city', 'source-layer': 'valves', filter: ['==', ['get', 'c'], 'INOP'],
        minzoom: 11,
        paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 11, 1.2, 16, 4], 'circle-color': '#ff4f32', 'circle-opacity': 0.6 },
      })
      map.addLayer({
        id: 'valves-close', type: 'circle', source: 'city', 'source-layer': 'valves', filter: ['in', ['get', 'id'], ['literal', []]],
        paint: { 'circle-radius': 6, 'circle-color': '#f5f3ee', 'circle-stroke-color': '#111318', 'circle-stroke-width': 2 },
      })
      map.addLayer({
        id: 'valves-dead', type: 'circle', source: 'city', 'source-layer': 'valves', filter: ['in', ['get', 'id'], ['literal', []]],
        paint: { 'circle-radius': 7, 'circle-color': '#ff4f32', 'circle-stroke-color': '#f5f3ee', 'circle-stroke-width': 2.5 },
      })
      map.addLayer({
        id: 'break-pulse', type: 'circle', source: 'break',
        paint: { 'circle-radius': 10, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#ff4f32', 'circle-stroke-width': 2, 'circle-stroke-opacity': 0.8 },
      })
      map.addLayer({
        id: 'break', type: 'circle', source: 'break',
        paint: { 'circle-radius': 8, 'circle-color': '#ff4f32', 'circle-stroke-color': '#f5f3ee', 'circle-stroke-width': 3 },
      })

      map.addSource('repair', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      map.addLayer({
        id: 'repair', type: 'circle', source: 'repair', filter: ['<', ['get', 'rank'], 0],
        paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2.5, 16, 7], 'circle-color': '#3ddc97',
                 'circle-stroke-color': '#111318', 'circle-stroke-width': 1 },
      })
      // loading ends when the network tiles arrive (not on 'idle': the break pulse keeps the map busy)
      const ready = () => { if (map.isSourceLoaded('city')) { setLoading(false); map.off('sourcedata', ready) } }
      map.on('sourcedata', ready)
      map.once('idle', () => setLoading(false))  // also fine now: nothing animates until a break is on the map


      // hover: nearest pipe within reach lights up with a label, so the click target is never a guess
      let hovered: number | null = null, pending = false
      map.on('mousemove', (e: MapMouseEvent) => {
        if (pending) return
        pending = true
        requestAnimationFrame(() => {
          pending = false
          const f = nearestPipe(map, e.point.x, e.point.y)
          const id = f?.id as number | undefined
          if (hovered !== null && hovered !== id) map.setFeatureState({ source: 'city', sourceLayer: 'pipes', id: hovered }, { hover: false })
          hovered = id ?? null
          const tip = tipRef.current
          if (f && id !== undefined) {
            map.setFeatureState({ source: 'city', sourceLayer: 'pipes', id }, { hover: true })
            map.getCanvas().style.cursor = 'pointer'
            if (tip) {
              const pr = f.properties as { d?: number; m?: string; y?: number }
              tip.textContent = `${pr.d ? `${pr.d}″ ` : ''}${pr.m ?? ''} main${pr.y ? `, laid ${pr.y}` : ''} · click to break`
              tip.style.transform = `translate(${e.point.x + 14}px, ${e.point.y + 14}px)`
              tip.style.opacity = '1'
            }
          } else {
            map.getCanvas().style.cursor = ''
            if (tip) tip.style.opacity = '0'
          }
        })
      })
      map.on('mouseout', () => { if (tipRef.current) tipRef.current.style.opacity = '0' })
      // pipes are ~1 px wide at city zoom: accept clicks within a few pixels, nearest box first
      map.on('click', (e: MapMouseEvent) => {
        const f = nearestPipe(map, e.point.x, e.point.y)
        if (!f) return
        setInitial(undefined)  // a clicked break uses default assumptions, not the last question's
        breakAt(snapToPipe(map, f, e.point.x, e.point.y), pipeProps(f))
      })
    })
    return () => { cancelAnimationFrame(pulseRef.current); map.remove() }
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
    map.setFilter('pressure-hl', inPieces(kind && kind !== 'isolated' ? pieces : []))
  }

  function showFixed(pieces: number[]) {
    mapRef.current?.setFilter('fixed-hl', inPieces(pieces))
  }

  /** Jump to a showcase break: fly there, then break the pipe with that piece id once its tile is loaded. */
  function goTo(c: { piece: number; lon: number; lat: number }) {
    const map = mapRef.current
    if (!map) return
    map.flyTo({ center: [c.lon, c.lat], zoom: 15.5, duration: 1200 })
    // tiles for the destination stream in after the flight: look for the pipe among loaded features, retrying briefly
    map.once('moveend', () => {
      let tries = 0
      const find = () => {
        const f = map.querySourceFeatures('city', { sourceLayer: 'pipes' }).find(g => Number(g.id) === c.piece)
        if (f) breakAt([c.lon, c.lat], pipeProps(f))
        else if (++tries < 15) window.setTimeout(find, 200)
      }
      find()
    })
  }

  /** The break marker's ring expands only while a break is on the map: one state-bearing motion, no idle repaint. */
  function startPulse() {
    const map = mapRef.current
    if (!map || pulseRef.current) return
    const step = (t: number) => {
      const ph = (t % 1600) / 1600
      map.setPaintProperty('break-pulse', 'circle-radius', 10 + 22 * (1 - Math.pow(1 - ph, 3)))
      map.setPaintProperty('break-pulse', 'circle-stroke-opacity', 0.8 * (1 - ph))
      pulseRef.current = requestAnimationFrame(step)
    }
    pulseRef.current = requestAnimationFrame(step)
  }
  function stopPulse() {
    cancelAnimationFrame(pulseRef.current)
    pulseRef.current = 0
  }

  function breakAt(lngLat: [number, number], p: PipeProps) {
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
    map.setFilter('real-glow', ['==', ['get', 'sr'], -1])
    map.setPaintProperty('pipes', 'line-opacity', 0.45)  // the outage is the subject; the network steps back
    map.setFilter('valves-close', ['in', ['get', 'id'], ['literal', paper[4]]])
    map.setFilter('valves-dead', ['in', ['get', 'id'], ['literal', []]])
    map.setFilter('hydrants-hl', ['==', ['get', 'sp'], p.sp])
    map.setFilter('pressure-hl', NONE)
    showFixed([])
    setRun(null)
    startPulse()
    const b: Break = { k: p.k, lngLat, sp: p.sp, sr: p.sr, diameter: p.d, material: p.m, year: p.y, stage: 'paper' }
    setBrk(b)
    timer.current = window.setTimeout(() => {
      const real = segs.real[p.sr]
      map.setFilter('real-hl', ['==', ['get', 'sr'], p.sr])
      map.setFilter('real-glow', ['==', ['get', 'sr'], p.sr])
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
    setRun(null)
    stopPulse()
    setInitial(undefined)
    showPressure([], null)
    showFixed([])
    if (!map) return
    ;(map.getSource('break') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
    for (const id of ['paper-hl', 'real-hl', 'real-glow']) map.setFilter(id, ['==', ['get', id === 'paper-hl' ? 'sp' : 'sr'], -1])
    map.setPaintProperty('pipes', 'line-opacity', 1)
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
          <h1>ValveRank</h1>
          <p className="lede">
            When a Houston water main breaks, crews close the nearest valves. The City's own records mark many of
            those valves as broken or lost, so the outage spreads to the next ones out.
          </p>
        </header>

        {!brk && stats && (
          <section>
            <p className="hint">Click any water main on the map, or find your street:</p>
            <Search onGo={c => { setInitial(undefined); goTo(c) }} />
            <div className="kpis">
              <Kpi label="Main valves recorded inoperable" value={fmt(stats.valves_on_mains_inop)} sub={`of ${fmt(stats.valves_on_mains)} on mains`} />
              <Kpi label="Last inspected 5+ years ago" value={`${Math.round(stats.valves_on_mains_last_inspected_5y_plus_share * 100)}%`} sub="industry practice: every valve within 5 years" />
              <Kpi label="Customers out, average break" value={`${stats.paper.expected_customers_per_break_with_downstream} → ${stats.real.expected_customers_per_break_with_downstream}`} sub="all valves work → City-recorded valve status; includes customers cut off downstream" />
              <Kpi label="Fire hydrants out, average break" value={`${stats.paper.expected_hydrants_per_break} → ${stats.real.expected_hydrants_per_break}`} sub="hydrants on the shut-off pipes" />
            </div>
          </section>
        )}
        {!brk && repair && repair.valves.length > 0 && <Repair data={repair} onChange={showRepairs} />}
        {!brk && <YearPanel repaired={showcase?.repaired} />}
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
            <Scenarios paper={paper} real={real} run={run} revealed={brk.stage === 'real'} repaired={showcase?.repaired ?? 100} />
            {brk.stage === 'real' && (
              dead.length ? (
                <div className="dead">
                  <h3><span className="dead-mark" />{dead.length} valve{dead.length > 1 ? 's' : ''} in the way {dead.length > 1 ? 'are' : 'is'} recorded inoperable</h3>
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
            <Timeline key={brk.k} piece={brk.k} onShow={showPressure} onFixed={showFixed} onRun={setRun} repaired={showcase?.repaired} initial={initial} />
            <details className="details">
              <summary>Segment details</summary>
              <table className="compare">
                <thead>
                  <tr><th /><th className="paper">Every valve works</th><th className="real">City valve records</th></tr>
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
            </details>
            <button className="reset" onClick={clearBreak}>Back to overview</button>
          </section>
        )}

        <footer>
          {loading ? 'Loading Houston water network…' : `Model results from ${stats?.data_snapshot ?? 'City GIS'}. Customers are utility accounts, not people.`}
        </footer>
      </aside>
      <div className="map-wrap">
        <div ref={mapEl} className="map" />
        <div ref={tipRef} className="hover-tip" aria-hidden="true" />
        <details className="legend" open>
          <summary>Legend</summary>
          <div className="legend-items">
          <span><i style={{ background: '#4fb3ff' }} /> outage if every valve worked</span>
          <span><i style={{ background: '#ff4f32' }} /> outage with the City's valve records</span>
          <span><i style={{ background: '#3ddc97' }} /> after the top {showcase?.repaired ?? 100} repairs</span>
          <span><i style={{ background: '#ffb000' }} /> loses 15+ psi while gushing</span>
          <span><i className="round" style={{ background: '#f5f3ee', boxShadow: '0 0 0 2px #111318' }} /> valve crews close</span>
          <span><i className="round" style={{ background: '#ff4f32', boxShadow: '0 0 0 2px #f5f3ee' }} /> valve recorded inoperable</span>
          </div>
        </details>
      </div>
    </div>
  )
}

type Seg = [number, number, number, number, number[], number[], number, number]

/** Every valve works / City records / after the top repairs, side by side in the map's colors. */
function Scenarios({ paper, real, run, revealed, repaired }: { paper: Seg; real: Seg; run: Run | null; revealed: boolean; repaired: number }) {
  const iso = (s?: { phases: Phase[] }) => s?.phases[s.phases.length - 1]
  const f = iso(run?.fixed)
  const cols = [
    { key: 'paper', name: 'Every valve works', cust: paper[0] + paper[6], hyd: paper[1] + paper[7], ch: run?.paper.customer_hours, show: true },
    { key: 'real', name: "City valve records", cust: real[0] + real[6], hyd: real[1] + real[7], ch: run?.real.customer_hours, show: revealed },
    { key: 'fixed', name: `After top ${repaired} repairs`, cust: f?.customers, hyd: f?.hydrants, ch: run?.fixed?.customer_hours, show: revealed && !!run?.fixed },
  ]
  const n = (v: number | undefined, show: boolean) => (show && v !== undefined ? fmt(Math.round(v)) : '…')
  return (
    <div className="scen" role="table" aria-label="Outage by scenario">
      {cols.map(c => (
        <div key={c.key} className={`scen-col ${c.key}`} role="row">
          <div className="scen-name" role="columnheader"><i />{c.name}</div>
          <div className="scen-big" role="cell">{n(c.cust, c.show)}</div>
          <div className="scen-unit">customers shut off</div>
          <div className="scen-row" role="cell"><b>{n(c.ch, c.show && !!run)}</b> customer-hours{run?.partial ? '*' : ''}</div>
          <div className="scen-row" role="cell"><b>{n(c.hyd, c.show)}</b> hydrants dry</div>
        </div>
      ))}
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
