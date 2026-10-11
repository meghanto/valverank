import { useEffect, useRef, useState } from 'react'
import { API } from './Timeline'

type Hit = { label: string; lon: number; lat: number }

/** Street intersection or address search: live suggestions from the City's intersection index; Enter locates. */
export function Search({ onGo }: { onGo: (c: { piece: number; lon: number; lat: number }) => void }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const timer = useRef<number | undefined>(undefined)
  const seq = useRef(0)

  useEffect(() => {
    window.clearTimeout(timer.current)
    if (q.trim().length < 2 || /^\s*\d/.test(q)) { setHits([]); return }
    const id = ++seq.current
    timer.current = window.setTimeout(() => {
      fetch(`${API}/search?q=${encodeURIComponent(q)}`).then(r => r.json())
        .then(j => { if (id === seq.current) { setHits(j.results ?? []); setActive(-1) } })
        .catch(() => {})
    }, 120)
    return () => window.clearTimeout(timer.current)
  }, [q])

  function go(text: string) {
    if (!text.trim()) return
    setBusy(true); setErr(null); setOpen(false)
    fetch(`${API}/locate?q=${encodeURIComponent(text)}`)
      .then(r => r.json().then(j => (r.ok ? j : Promise.reject(new Error(j.detail ?? `HTTP ${r.status}`)))))
      .then(j => { setQ(j.label); onGo({ piece: j.piece, lon: j.lon, lat: j.lat }) })
      .catch(e => setErr(String(e.message ?? e)))
      .finally(() => setBusy(false))
  }

  return (
    <div className="search">
      <form onSubmit={e => { e.preventDefault(); go(active >= 0 && hits[active] ? hits[active].label : q) }}>
        <input
          value={q} disabled={busy} autoComplete="off" spellCheck={false}
          placeholder="Your street corner or address, e.g. Westheimer & Kirby"
          role="combobox" aria-expanded={open && hits.length > 0} aria-controls="search-list" aria-label="Find a street corner or address"
          onChange={e => { setQ(e.target.value); setOpen(true); setErr(null) }}
          onFocus={() => setOpen(true)}
          onBlur={() => window.setTimeout(() => setOpen(false), 120)}
          onKeyDown={e => {
            if (e.key === 'ArrowDown') { e.preventDefault(); setActive(a => Math.min(a + 1, hits.length - 1)) }
            else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(a => Math.max(a - 1, -1)) }
            else if (e.key === 'Escape') setOpen(false)
          }}
        />
        <button disabled={busy || !q.trim()}>{busy ? 'Finding…' : 'Go'}</button>
      </form>
      {open && hits.length > 0 && (
        <ul id="search-list" role="listbox" className="search-list">
          {hits.map((h, i) => (
            <li key={h.label} role="option" aria-selected={i === active} className={i === active ? 'active' : ''}
                onMouseDown={e => { e.preventDefault(); setQ(h.label); go(h.label) }}>
              {h.label}
            </li>
          ))}
        </ul>
      )}
      {err && <p className="err">{err}</p>}
    </div>
  )
}
