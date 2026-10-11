# proofs/: machine-checked invariants of the segment and supply-loss model

This folder holds a small Bend 2 project. The Bend compiler checks two
invariants of the specification behind `pipeline/network.py` (valve-isolation
segments, "paper" vs "real") and `pipeline/supply.py` (downstream supply loss).
All 13 laws are proven. None is assumed.

| File | Role |
|---|---|
| `Graph.bend` | Executable spec: edge lists, walks, BFS closure, valves, cut points, join edges, segments, customer sums, `G - v`, supplied/lost |
| `LAWS.bend` | The 13 claims (human-readable statements) |
| `PROOF.bend` | One proof def per law (`def Laws.<name>`), plus 60 helper lemmas, all checked |
| `demo.bend` | Runs the spec on a 9-node / 8-piece toy network with one INOP valve |

## Version and commands

- Bend **2.0.36**. Install: `curl -fsSL https://bend-lang.com/install.sh | sh`. The binary is at `~/.bend/bin/bend`.
- `--verdict` rechecks the proofs with BendTT, Bend's small kernel, which has a proof in Lean. The kernel needs Lean **v4.34.0**: `elan toolchain install leanprover/lean4:v4.34.0`. The first run builds the kernel, which takes about 80 s.
- Set `BEND_NO_TELEMETRY=1` to stop bend's daily version check.

```
$ cd proofs
$ bend version
bend 2.0.36

$ bend PROOF.bend
ALL PROOFS CHECK
Use --verdict for mathematical validity.

$ bend PROOF.bend --verdict
ALL PROOFS CHECK

$ bend demo.bend
segment of piece 2, paper: [2]  customers 25
segment of piece 2, real:  [1, 2, 4]  customers 95
supplied from source 0:        [0, 1, 2, 3, 4]
supplied with vertex 1 removed: [0]
lost when vertex 1 is removed:  [1, 2, 3, 4]
```

The demo network: pipe pieces p1, p2 and p4 meet at node n2. The valve at n2
is INOP. On paper n2 is a cut point, so piece 2's segment is `{2}`. In reality
the valve cannot close, and the segment grows to `{1, 2, 4}` (25 → 95
customers). The last three lines run the supply-loss spec on a separate
5-vertex segment graph, where vertex 1 is an articulation point.

**Sanity check that the checker is not vacuous.** I reversed L1b to claim
`cut_paper ⇒ cut_real`, which is false, in a scratch copy. `bend PROOF.bend`
rejected it with `SOME PROOFS FAIL` and showed the mismatched goal. When the
laws were written but not yet proven, it reported `13 TODOs found`.

## The abstract model (Graph.bend)

- Vertex ids are `Nat`. Sets are `List`s, and duplicates are allowed.
- Every predicate returns `Bool`, so each law has the form `{f(..) == True{} : Bool}`.
- `is_path(p, E, a, b)`: the list `p` is a walk from `a` to `b` along undirected edges listed in `E`.
- `reach(k, E, S)`: `k` rounds of BFS from the set `S`. This is the connectivity closure.
- `Valve{node, nclosed, inop}` and `closable(nc, scen, inop)` copy `is_closable` in network.py:
  - a normally-closed valve is always closable;
  - in the real scenario, an INOP valve is not closable;
  - on paper, every valve is closable.
- `cut(V, s, n)`: some valve at node `n` is closable. This is network.py's `vs and any(is_closable(..))`.
- `Inc{node, piece}`: piece `k` has an end at node `n`. This matches network.py's `inc` map.
- `join_edges(inc, V, s)`: every pair of pieces that share a node `n` where `cut` is false.
- `seg(k, inc, V, s, a)` is `reach(k, join_edges(..), [a])`.
- `csum(C, S)` sums the customer weights (`Nat`, so never negative) of the pieces in `S`.
- `remove(E, v)` drops every edge that touches `v`. `dropv(src, v)` removes `v` from the source set.
- `supplied` is `reach` from the sources in G. `supplied_without` is `reach` in G − v from `src` minus `v`.
- `lost(.., x)` = supplied in G and not supplied in G − v.

## What is proved (LAWS.bend)

### L1: a dead valve never shrinks an outage

| Law | Statement |
|---|---|
| `closable_mono` (L1a) | `closable_real(v) ⇒ closable_paper(v)`, for every valve |
| `cut_mono` (L1b) | a real cut point is a paper cut point, for every valve list and node |
| `join_mono` (L1c) | `sub(join_edges(paper), join_edges(real))`: every paper join edge is a real join edge |
| `path_mono` (L1d, core) | `sub(E1, E2)` and a walk `p` from `a` to `b` in `E1` ⇒ `p` is a walk in `E2` |
| `connected_mono` (L1e) | pieces joined by a walk under paper edges are joined by the same walk under real edges |
| `reach_mono` (L1f) | `sub(E1,E2)` and `subv(S1,S2)` ⇒ `subv(reach(k,E1,S1), reach(k,E2,S2))`, for every `k` |
| `seg_mono` (L1g) | `subv(seg_paper(a), seg_real(a))`, for every network, valve list, piece `a` and round count `k` |
| `customers_mono` (L1h) | `customers_paper(a) ≤ customers_real(a)`, for every list of customers with non-negative weights |

L1c is derived from the valve model (L1a, then L1b), not assumed.

### L2: supply loss is sound (removing a vertex never creates a path)

| Law | Statement |
|---|---|
| `remove_sub` (L2a) | `sub(remove(E, v), E)`: G − v is a subgraph of G |
| `path_without` (L2b) | a walk in G − v is a walk in G (reuses L1d) |
| `supply_mono` (L2c) | `subv(supplied_without(k,E,src,v), supplied(k,E,src))` (reuses L1f) |
| `supplied_without_sound` (L2d) | if x is reachable from a source in G − v, x is reachable from a source in G |
| `lost_sound` (L2e) | a vertex still supplied in G − v always has `lost == False` |

L2 is stated over an arbitrary edge list, so it covers any segment graph that supply.py builds.

## What is NOT proved

- **The Python code itself.** `network.py` and `supply.py` are not verified. The proofs are about the algorithm's specification as written in `Graph.bend`. The spec mirrors the Python logic (`is_closable`, cut nodes, joining at non-cut nodes), but the two are not proved equivalent.
- **Union-find vs closure.** network.py unions `ks[0]` with every other piece at a node (a star), and the spec joins all pairs. Both give the same connectivity, but this is not proved. The spec computes segments with BFS, not with the DSU.
- **BFS completeness.** L1f and L1g hold for every round count `k`, so they do not depend on `k`. That `reach` with `k ≥ #pieces` equals the full connected component is not proved. Neither is the equivalence between walk-based connectivity (L1d, L1e) and closure-based connectivity (L1f, L1g).
- **Tarjan / articulation points.** supply.py's iterative Tarjan DFS (`articulation_loss`) is not proved. Only its specification is: reachability in G − v is contained in reachability in G. Also, the spec's `lost` set includes `v` itself, while supply.py reports downstream loss without `v`'s own customers.
- **Geometry and data cleaning.** None of the following is modelled:
  - node rounding (0.1 m grid);
  - valve snapping (`SNAP_M`, `SNAP_INLINE_M`, `NODE_M`);
  - splitting pipes at interior valves;
  - unnoded tees (`TEE_M`, `TEE_BIG_M`);
  - dropping lead and hydrant valves;
  - dropping abandoned and non-potable mains.

  The theorems apply to whatever incidence list and valve list that preprocessing produces.
- **Customer and hydrant snapping.** How customers are assigned to pieces (`CUSTOMER_M`, nearest piece) is not covered. L1h holds for any assignment with non-negative weights.
- **Source snapping** (`SNAP_M = 300`, `MIN_DIAM_IN`) is not covered.
- **Hydraulics.** This is connectivity only: no pressure and no flow. It matches the "lower bound" caveat in supply.py.

## Trusted base and assumptions

- **No axioms, no postulates.** There is no `@unsafe` def, no `?TODO`, and no open law. Every law in LAWS.bend has a proof def that the checker accepted. `--verdict` would reject anything that relied on `@unsafe` or foreign code.
- The only Base definitions used are ordinary computable ones: `Bool.and`, `Bool.or`, `Bool.not`, `Nat.add`, `Either`, `Empty.absurd`, `Equal.sym`, and `List.show` (demo only). The `F32`/IO laws in Base are not used.
- What you must trust:
  - the bend2 checker;
  - the BendTT kernel (its soundness proof is in `~/.bend/bend2/bendtt.lean`);
  - Bend's translation from source to BendTT. The guide says this translation has no proof. `bend PROOF.bend -o PROOF.bendtt` writes it out for inspection.
- The `+` markers on law parameters in LAWS.bend are resource annotations: they let a variable be used more than once. They do not change what a law states.
