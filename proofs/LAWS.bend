# LAWS.bend: the claims. Each law is proven by the def of the same name in
# PROOF.bend; `bend PROOF.bend` prints ALL PROOFS CHECK only when all hold.
import Base
import ./Graph.bend as G

# ---------------------------------------------------------------------------
# L1. A dead valve never shrinks an outage (pipeline/network.py)
# ---------------------------------------------------------------------------

# L1a. A valve closable in the real scenario is closable on paper.
law closable_mono:
  for +nc: Bool
  for +i: Bool
  {G.imp(G.closable(nc, G.Real{}, i), G.closable(nc, G.Paper{}, i)) == True{} : Bool}

# L1b. A node that is a cut point in reality is a cut point on paper.
law cut_mono:
  for +V: +List<G.Valve>
  for +n: Nat
  {G.imp(G.cut(V, G.Real{}, n), G.cut(V, G.Paper{}, n)) == True{} : Bool}

# L1c. The paper join-edge set is a subset of the real join-edge set.
law join_mono:
  for +inc: +List<G.Inc>
  for +V: +List<G.Valve>
  {G.sub(G.join_edges(inc, V, G.Paper{}), G.join_edges(inc, V, G.Real{})) == True{} : Bool}

# L1d (core). Reachability is monotone in the edge set: a walk in E1 is a
# walk in any E2 that contains E1.
law path_mono:
  for +p: +List<Nat>
  for +E1: +List<G.Edge>
  for +E2: +List<G.Edge>
  for +a: Nat
  for +b: Nat
  for +hs: {G.sub(E1, E2) == True{} : Bool}
  for +hp: {G.is_path(p, E1, a, b) == True{} : Bool}
  {G.is_path(p, E2, a, b) == True{} : Bool}

# L1e. Pieces connected on paper are connected in reality (same walk).
law connected_mono:
  for +p: +List<Nat>
  for +inc: +List<G.Inc>
  for +V: +List<G.Valve>
  for +a: Nat
  for +b: Nat
  for +hp: {G.is_path(p, G.join_edges(inc, V, G.Paper{}), a, b) == True{} : Bool}
  {G.is_path(p, G.join_edges(inc, V, G.Real{}), a, b) == True{} : Bool}

# L1f. The BFS closure is monotone in both the edge set and the start set,
# for every number of rounds k.
law reach_mono:
  for +k: Nat
  for +E1: +List<G.Edge>
  for +E2: +List<G.Edge>
  for +S1: +List<Nat>
  for +S2: +List<Nat>
  for +he: {G.sub(E1, E2) == True{} : Bool}
  for +hs: {G.subv(S1, S2) == True{} : Bool}
  {G.subv(G.reach(k, E1, S1), G.reach(k, E2, S2)) == True{} : Bool}

# L1g. The paper segment of piece a is a subset of the real segment of a.
law seg_mono:
  for +k: Nat
  for +inc: +List<G.Inc>
  for +V: +List<G.Valve>
  for +a: Nat
  {G.subv(G.seg(k, inc, V, G.Paper{}, a), G.seg(k, inc, V, G.Real{}, a)) == True{} : Bool}

# L1h. Hence customers_real(a) >= customers_paper(a) for any customer list
# with non-negative (Nat) weights.
law customers_mono:
  for +C: +List<G.Cust>
  for +k: Nat
  for +inc: +List<G.Inc>
  for +V: +List<G.Valve>
  for +a: Nat
  {G.le(G.csum(C, G.seg(k, inc, V, G.Paper{}, a)), G.csum(C, G.seg(k, inc, V, G.Real{}, a))) == True{} : Bool}

# ---------------------------------------------------------------------------
# L2. Supply loss is sound: removing a vertex never creates a path
# (pipeline/supply.py)
# ---------------------------------------------------------------------------

# L2a. G - v is a subgraph of G.
law remove_sub:
  for +E: +List<G.Edge>
  for +v: Nat
  {G.sub(G.remove(E, v), E) == True{} : Bool}

# L2b. A walk in G - v is a walk in G.
law path_without:
  for +p: +List<Nat>
  for +E: +List<G.Edge>
  for +v: Nat
  for +s: Nat
  for +x: Nat
  for +hp: {G.is_path(p, G.remove(E, v), s, x) == True{} : Bool}
  {G.is_path(p, E, s, x) == True{} : Bool}

# L2c. Everything supplied in G - v is supplied in G.
law supply_mono:
  for +k: Nat
  for +E: +List<G.Edge>
  for +src: +List<Nat>
  for +v: Nat
  {G.subv(G.supplied_without(k, E, src, v), G.supplied(k, E, src)) == True{} : Bool}

# L2d. Pointwise: if x is supplied in G - v, x is supplied in G ...
law supplied_without_sound:
  for +k: Nat
  for +E: +List<G.Edge>
  for +src: +List<Nat>
  for +v: Nat
  for +x: Nat
  for +h: {G.memv(G.supplied_without(k, E, src, v), x) == True{} : Bool}
  {G.memv(G.supplied(k, E, src), x) == True{} : Bool}

# L2e. ... so a vertex still supplied in G - v is never counted as lost.
law lost_sound:
  for +k: Nat
  for +E: +List<G.Edge>
  for +src: +List<Nat>
  for +v: Nat
  for +x: Nat
  for +h: {G.memv(G.supplied_without(k, E, src, v), x) == True{} : Bool}
  {G.lost(k, E, src, v, x) == False{} : Bool}
