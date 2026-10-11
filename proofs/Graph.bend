# Graph.bend: an abstract, executable specification of the two algorithms in
# pipeline/network.py (valve-isolation segments, "paper" vs "real") and
# pipeline/supply.py (downstream supply loss when a segment is removed).
#
# Vertices are Nat ids. Sets are lists (duplicates allowed). Every predicate
# is a Bool-valued function, so the laws in LAWS.bend are equations of the form
# {f(..) == True{} : Bool}.
import Base

# Booleans and naturals
# ---------------------

def eqn(a: Nat, b: Nat) -> Bool:
  match a b:
    case 0n 0n:
      True{}
    case 0n 1n+bp:
      False{}
    case 1n+ap 0n:
      False{}
    case 1n+ap 1n+bp:
      eqn(ap, bp)

# boolean implication: imp(a, b) == True{} means "a implies b"
def imp(a: Bool, b: Bool) -> Bool:
  Bool.or(Bool.not(a), b)

def le(a: Nat, b: Nat) -> Bool:
  match a b:
    case 0n _:
      True{}
    case 1n+ap 0n:
      False{}
    case 1n+ap 1n+bp:
      le(ap, bp)

# Edge lists and vertex sets
# --------------------------

type Edge is Data:
  Ed{u: Nat, v: Nat}

# (u, v) is listed in E
def meme(E: +List<Edge>, +u: Nat, +v: Nat) -> Bool:
  match E:
    case Nil{}:
      False{}
    case Ed{x, y} <> t:
      Bool.or(Bool.and(eqn(x, u), eqn(y, v)), meme(t, u, v))

# undirected adjacency
def adj(+E: +List<Edge>, +u: Nat, +v: Nat) -> Bool:
  Bool.or(meme(E, u, v), meme(E, v, u))

# every edge of A is listed in B  (A is a subset of B)
def sub(A: +List<Edge>, +B: +List<Edge>) -> Bool:
  match A:
    case Nil{}:
      True{}
    case Ed{x, y} <> t:
      Bool.and(meme(B, x, y), sub(t, B))

def pute(c: Bool, e: Edge, E: +List<Edge>) -> +List<Edge>:
  match c:
    case False{}:
      E
    case True{}:
      e <> E

def appe(A: +List<Edge>, B: +List<Edge>) -> +List<Edge>:
  match A:
    case Nil{}:
      B
    case h <> t:
      h <> appe(t, B)

def memv(S: +List<Nat>, +x: Nat) -> Bool:
  match S:
    case Nil{}:
      False{}
    case h <> t:
      Bool.or(eqn(h, x), memv(t, x))

# every vertex of A is in B
def subv(A: +List<Nat>, +B: +List<Nat>) -> Bool:
  match A:
    case Nil{}:
      True{}
    case h <> t:
      Bool.and(memv(B, h), subv(t, B))

def putv(c: Bool, x: Nat, S: +List<Nat>) -> +List<Nat>:
  match c:
    case False{}:
      S
    case True{}:
      x <> S

# Reachability
# ------------

# p = [w1, .., wn] is a walk a - w1 - .. - wn in E that ends at b
# (the empty walk requires a == b)
def is_path(p: +List<Nat>, +E: +List<Edge>, +a: Nat, +b: Nat) -> Bool:
  match p:
    case Nil{}:
      eqn(a, b)
    case +w <> t:
      Bool.and(adj(E, a, w), is_path(t, E, w, b))

# one BFS round: acc plus every neighbour (in E) of a vertex in S
def nbrs(E: +List<Edge>, +S: +List<Nat>, acc: +List<Nat>) -> +List<Nat>:
  match E:
    case Nil{}:
      acc
    case Ed{+x, +y} <> t:
      putv(memv(S, x), y, putv(memv(S, y), x, nbrs(t, S, acc)))

# k BFS rounds from the set S (the connectivity closure; with k >= number of
# vertices it is the whole connected component of S)
def reach(k: Nat, +E: +List<Edge>, +S: +List<Nat>) -> +List<Nat>:
  match k:
    case 0n:
      S
    case 1n+p:
      reach(p, E, nbrs(E, S, S))

# Water network: pieces, valves, segments  (pipeline/network.py)
# ---------------------------------------------------------------

type Scen is Data:
  Paper{}
  Real{}

# A valve at a node. nclosed: normally closed (NORMALPOSITION = 0).
# inop: the City records it as inoperable (CONDITION = 'INOP').
type Valve is Data:
  Valve{node: Nat, nclosed: Bool, inop: Bool}

# network.py is_closable: a normally closed valve is always a boundary; in
# the "real" scenario an INOP valve cannot be closed; on paper every valve can.
def closable(nc: Bool, s: Scen, inop: Bool) -> Bool:
  match nc:
    case True{}:
      True{}
    case False{}:
      match s:
        case Paper{}:
          True{}
        case Real{}:
          Bool.not(inop)

# a node is a cut point when some valve there is closable
def cut(V: +List<Valve>, +s: Scen, +n: Nat) -> Bool:
  match V:
    case Nil{}:
      False{}
    case Valve{m, nc, i} <> t:
      Bool.or(Bool.and(eqn(m, n), closable(nc, s, i)), cut(t, s, n))

# piece k has an end at node n
type Inc is Data:
  Inc{node: Nat, piece: Nat}

# join edges contributed by incidence (n, k): k is joined to every piece k2
# that also ends at n, unless n is a cut point
def joins_at(J: +List<Inc>, +V: +List<Valve>, +s: Scen, +n: Nat, +k: Nat) ->
  +List<Edge>:
  match J:
    case Nil{}:
      Nil{}
    case Inc{+m, k2} <> t:
      pute(Bool.and(eqn(n, m), Bool.not(cut(V, s, n))), Ed{k, k2},
        joins_at(t, V, s, n, k))

def joins(I: +List<Inc>, +J: +List<Inc>, +V: +List<Valve>, +s: Scen) ->
  +List<Edge>:
  match I:
    case Nil{}:
      Nil{}
    case Inc{+n, +k} <> t:
      appe(joins_at(J, V, s, n, k), joins(t, J, V, s))

# the join-edge set of a scenario (network.py: union of pieces at non-cut nodes)
def join_edges(+inc: +List<Inc>, +V: +List<Valve>, +s: Scen) -> +List<Edge>:
  joins(inc, inc, V, s)

# the segment of piece a: closure of {a} under the join edges, k rounds
def seg(k: Nat, +inc: +List<Inc>, +V: +List<Valve>, +s: Scen, a: Nat) ->
  +List<Nat>:
  reach(k, join_edges(inc, V, s), [a])

# customers snapped to pieces, with a non-negative weight (Nat)
type Cust is Data:
  Cust{piece: Nat, w: Nat}

def pickn(c: Bool, w: Nat) -> Nat:
  match c:
    case False{}:
      0n
    case True{}:
      w

# total weight of customers whose piece lies in S
def csum(C: +List<Cust>, +S: +List<Nat>) -> Nat:
  match C:
    case Nil{}:
      0n
    case Cust{+k, w} <> t:
      Nat.add(pickn(memv(S, k), w), csum(t, S))

# Supply loss  (pipeline/supply.py)
# ---------------------------------

# G minus v: drop every edge touching v
def remove(E: +List<Edge>, +v: Nat) -> +List<Edge>:
  match E:
    case Nil{}:
      Nil{}
    case Ed{+x, +y} <> t:
      pute(Bool.not(Bool.or(eqn(x, v), eqn(y, v))), Ed{x, y}, remove(t, v))

# the source set minus v
def dropv(S: +List<Nat>, +v: Nat) -> +List<Nat>:
  match S:
    case Nil{}:
      Nil{}
    case +h <> t:
      putv(Bool.not(eqn(h, v)), h, dropv(t, v))

# vertices reachable from a source in G
def supplied(k: Nat, +E: +List<Edge>, src: +List<Nat>) -> +List<Nat>:
  reach(k, E, src)

# vertices reachable from a source in G - v
def supplied_without(k: Nat, +E: +List<Edge>, src: +List<Nat>, +v: Nat) ->
  +List<Nat>:
  reach(k, remove(E, v), dropv(src, v))

# x is lost when v is removed: supplied in G, not supplied in G - v
def lost(+k: Nat, +E: +List<Edge>, +src: +List<Nat>, +v: Nat, +x: Nat) -> Bool:
  Bool.and(memv(supplied(k, E, src), x),
    Bool.not(memv(supplied_without(k, E, src, v), x)))
