# PROOF.bend: proofs of every law in LAWS.bend. No law is assumed: each is
# a def checked by the compiler. Helper lemmas are ordinary typed defs.
import Base
import ./Graph.bend as G
import ./LAWS.bend as Laws

# Booleans
# --------

def BDisc(b: Bool) -> Type:
  match b:
    case False{}:
      Unit
    case True{}:
      Empty

def false_ne_true(h: {False{} == True{} : Bool}) -> Empty:
  %h : BDisc(_)
  Unit{}

def absurd(-A: Type, h: {False{} == True{} : Bool}) -> A:
  Empty.absurd(A, false_ne_true(h))

def and_l(a: Bool, -b: Bool, h: {Bool.and(a, b) == True{} : Bool}) ->
  {a == True{} : Bool}:
  match a:
    case True{}:
      {==}
    case False{}:
      absurd({False{} == True{} : Bool}, h)

def and_r(a: Bool, -b: Bool, h: {Bool.and(a, b) == True{} : Bool}) ->
  {b == True{} : Bool}:
  match a:
    case True{}:
      h
    case False{}:
      absurd({b == True{} : Bool}, h)

def and_intro(-a: Bool, -b: Bool, ha: {a == True{} : Bool},
  hb: {b == True{} : Bool}) -> {Bool.and(a, b) == True{} : Bool}:
  %Equal.sym(Bool, a, True{}, ha) : {Bool.and(_, b) == True{} : Bool}
  hb

def or_elim(a: Bool, -b: Bool, h: {Bool.or(a, b) == True{} : Bool}) ->
  Either<{a == True{} : Bool}, {b == True{} : Bool}>:
  match a:
    case True{}:
      Inl{{==}}
    case False{}:
      Inr{h}

def or_l(-a: Bool, -b: Bool, h: {a == True{} : Bool}) ->
  {Bool.or(a, b) == True{} : Bool}:
  %Equal.sym(Bool, a, True{}, h) : {Bool.or(_, b) == True{} : Bool}
  {==}

def or_r(a: Bool, -b: Bool, h: {b == True{} : Bool}) ->
  {Bool.or(a, b) == True{} : Bool}:
  match a:
    case True{}:
      {==}
    case False{}:
      h

def either(-A: Type, -B: Type, -C: Type, e: Either<A, B>, f: A -> C, g: B -> C) -> C:
  match e:
    case Inl{x}:
      f(x)
    case Inr{y}:
      g(y)

def imp_from(c: Bool, -d: Bool, f: {c == True{} : Bool} -> {d == True{} : Bool}) ->
  {G.imp(c, d) == True{} : Bool}:
  match c:
    case False{}:
      {==}
    case True{}:
      f({==})

def imp_use(c: Bool, -d: Bool, h: {G.imp(c, d) == True{} : Bool},
  hc: {c == True{} : Bool}) -> {d == True{} : Bool}:
  match c:
    case True{}:
      h
    case False{}:
      absurd({d == True{} : Bool}, hc)

# Naturals
# --------

def eqn_refl(a: Nat) -> {G.eqn(a, a) == True{} : Bool}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      eqn_refl(p)

def eqn_sound(a: Nat, b: Nat, h: {G.eqn(a, b) == True{} : Bool}) -> {a == b : Nat}:
  match a b:
    case 0n 0n:
      {==}
    case 0n 1n+bp:
      absurd({0n == 1n+bp : Nat}, h)
    case 1n+ap 0n:
      absurd({1n+ap == 0n : Nat}, h)
    case 1n+ap 1n+bp:
      %eqn_sound(ap, bp, h) : {1n+ap == 1n+_ : Nat}
      {==}

# Edge sets
# ---------

def meme_mono.hit(+E2: +List<G.Edge>, +x: Nat, +y: Nat, +u: Nat, +v: Nat,
  hxy: {G.meme(E2, x, y) == True{} : Bool},
  +h1: {Bool.and(G.eqn(x, u), G.eqn(y, v)) == True{} : Bool}) ->
  {G.meme(E2, u, v) == True{} : Bool}:
  %eqn_sound(x, u, and_l(G.eqn(x, u), G.eqn(y, v), h1)) : {G.meme(E2, _, v) == True{} : Bool}
  %eqn_sound(y, v, and_r(G.eqn(x, u), G.eqn(y, v), h1)) : {G.meme(E2, x, _) == True{} : Bool}
  hxy

def meme_mono(+E1: +List<G.Edge>, +E2: +List<G.Edge>, +u: Nat, +v: Nat,
  +hs: {G.sub(E1, E2) == True{} : Bool},
  hm: {G.meme(E1, u, v) == True{} : Bool}) -> {G.meme(E2, u, v) == True{} : Bool}:
  match E1:
    case Nil{}:
      absurd({G.meme(E2, u, v) == True{} : Bool}, hm)
    case G.Ed{+x, +y} <> t:
      either({Bool.and(G.eqn(x, u), G.eqn(y, v)) == True{} : Bool},
        {G.meme(t, u, v) == True{} : Bool}, {G.meme(E2, u, v) == True{} : Bool},
        or_elim(Bool.and(G.eqn(x, u), G.eqn(y, v)), G.meme(t, u, v), hm),
        h1 => meme_mono.hit(E2, x, y, u, v, and_l(G.meme(E2, x, y), G.sub(t, E2), hs), h1),
        h2 => meme_mono(t, E2, u, v, and_r(G.meme(E2, x, y), G.sub(t, E2), hs), h2))

def adj_mono(+E1: +List<G.Edge>, +E2: +List<G.Edge>, +u: Nat, +v: Nat,
  +hs: {G.sub(E1, E2) == True{} : Bool},
  h: {G.adj(E1, u, v) == True{} : Bool}) -> {G.adj(E2, u, v) == True{} : Bool}:
  either({G.meme(E1, u, v) == True{} : Bool}, {G.meme(E1, v, u) == True{} : Bool},
    {G.adj(E2, u, v) == True{} : Bool},
    or_elim(G.meme(E1, u, v), G.meme(E1, v, u), h),
    h1 => or_l(G.meme(E2, u, v), G.meme(E2, v, u), meme_mono(E1, E2, u, v, hs, h1)),
    h2 => or_r(G.meme(E2, u, v), G.meme(E2, v, u), meme_mono(E1, E2, v, u, hs, h2)))

# L1d
def Laws.path_mono(p, E1, E2, a, b, hs, hp):
  match p:
    case Nil{}:
      hp
    case +w <> t:
      and_intro(G.adj(E2, a, w), G.is_path(t, E2, w, b),
        adj_mono(E1, E2, a, w, hs, and_l(G.adj(E1, a, w), G.is_path(t, E1, w, b), hp)),
        Laws.path_mono(t, E1, E2, w, b, hs,
          and_r(G.adj(E1, a, w), G.is_path(t, E1, w, b), hp)))

# Implication algebra
# -------------------

def imp_or(a1: Bool, b1: Bool, a2: Bool, -b2: Bool,
  h1: {G.imp(a1, a2) == True{} : Bool}, h2: {G.imp(b1, b2) == True{} : Bool}) ->
  {G.imp(Bool.or(a1, b1), Bool.or(a2, b2)) == True{} : Bool}:
  match a1:
    case True{}:
      or_l(a2, b2, h1)
    case False{}:
      match b1:
        case True{}:
          or_r(a2, b2, h2)
        case False{}:
          {==}

def imp_and(z: Bool, -x: Bool, -y: Bool, h: {G.imp(x, y) == True{} : Bool}) ->
  {G.imp(Bool.and(z, x), Bool.and(z, y)) == True{} : Bool}:
  match z:
    case False{}:
      {==}
    case True{}:
      h

def imp_not(a: Bool, b: Bool, h: {G.imp(a, b) == True{} : Bool}) ->
  {G.imp(Bool.not(b), Bool.not(a)) == True{} : Bool}:
  match a b:
    case True{} True{}:
      {==}
    case True{} False{}:
      absurd({G.imp(Bool.not(False{}), Bool.not(True{})) == True{} : Bool}, h)
    case False{} True{}:
      {==}
    case False{} False{}:
      {==}

# L1a
def Laws.closable_mono(nc, i):
  match nc i:
    case True{} _:
      {==}
    case False{} False{}:
      {==}
    case False{} True{}:
      {==}

# L1b
def Laws.cut_mono(V, n):
  match V:
    case Nil{}:
      {==}
    case G.Valve{+m, +nc, +i} <> t:
      imp_or(Bool.and(G.eqn(m, n), G.closable(nc, G.Real{}, i)), G.cut(t, G.Real{}, n),
        Bool.and(G.eqn(m, n), G.closable(nc, G.Paper{}, i)), G.cut(t, G.Paper{}, n),
        imp_and(G.eqn(m, n), G.closable(nc, G.Real{}, i), G.closable(nc, G.Paper{}, i),
          Laws.closable_mono(nc, i)),
        Laws.cut_mono(t, n))

# Subsets of edge lists
# ---------------------

def meme_cons(e: G.Edge, -B: +List<G.Edge>, +x: Nat, +y: Nat,
  h: {G.meme(B, x, y) == True{} : Bool}) -> {G.meme(e <> B, x, y) == True{} : Bool}:
  match e:
    case G.Ed{a, b}:
      or_r(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(B, x, y), h)

def sub_cons(+A: +List<G.Edge>, +B: +List<G.Edge>, +e: G.Edge,
  +h: {G.sub(A, B) == True{} : Bool}) -> {G.sub(A, e <> B) == True{} : Bool}:
  match A:
    case Nil{}:
      {==}
    case G.Ed{+x, +y} <> t:
      and_intro(G.meme(e <> B, x, y), G.sub(t, e <> B),
        meme_cons(e, B, x, y, and_l(G.meme(B, x, y), G.sub(t, B), h)),
        sub_cons(t, B, e, and_r(G.meme(B, x, y), G.sub(t, B), h)))

def meme_app_l(+A: +List<G.Edge>, +C: +List<G.Edge>, +x: Nat, +y: Nat,
  h: {G.meme(A, x, y) == True{} : Bool}) ->
  {G.meme(G.appe(A, C), x, y) == True{} : Bool}:
  match A:
    case Nil{}:
      absurd({G.meme(G.appe(Nil{}, C), x, y) == True{} : Bool}, h)
    case G.Ed{+a, +b} <> t:
      either({Bool.and(G.eqn(a, x), G.eqn(b, y)) == True{} : Bool},
        {G.meme(t, x, y) == True{} : Bool},
        {G.meme(G.appe(G.Ed{a, b} <> t, C), x, y) == True{} : Bool},
        or_elim(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(t, x, y), h),
        h1 => or_l(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(G.appe(t, C), x, y), h1),
        h2 => or_r(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(G.appe(t, C), x, y),
          meme_app_l(t, C, x, y, h2)))

def meme_app_r(+A: +List<G.Edge>, +C: +List<G.Edge>, +x: Nat, +y: Nat,
  h: {G.meme(C, x, y) == True{} : Bool}) ->
  {G.meme(G.appe(A, C), x, y) == True{} : Bool}:
  match A:
    case Nil{}:
      h
    case G.Ed{+a, +b} <> t:
      or_r(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(G.appe(t, C), x, y),
        meme_app_r(t, C, x, y, h))

def sub_app_l(+A: +List<G.Edge>, +B: +List<G.Edge>, +C: +List<G.Edge>,
  +h: {G.sub(A, B) == True{} : Bool}) -> {G.sub(A, G.appe(B, C)) == True{} : Bool}:
  match A:
    case Nil{}:
      {==}
    case G.Ed{+x, +y} <> t:
      and_intro(G.meme(G.appe(B, C), x, y), G.sub(t, G.appe(B, C)),
        meme_app_l(B, C, x, y, and_l(G.meme(B, x, y), G.sub(t, B), h)),
        sub_app_l(t, B, C, and_r(G.meme(B, x, y), G.sub(t, B), h)))

def sub_app_r(+A: +List<G.Edge>, +B: +List<G.Edge>, +C: +List<G.Edge>,
  +h: {G.sub(A, C) == True{} : Bool}) -> {G.sub(A, G.appe(B, C)) == True{} : Bool}:
  match A:
    case Nil{}:
      {==}
    case G.Ed{+x, +y} <> t:
      and_intro(G.meme(G.appe(B, C), x, y), G.sub(t, G.appe(B, C)),
        meme_app_r(B, C, x, y, and_l(G.meme(C, x, y), G.sub(t, C), h)),
        sub_app_r(t, B, C, and_r(G.meme(C, x, y), G.sub(t, C), h)))

def sub_app(+A: +List<G.Edge>, +B: +List<G.Edge>, +C: +List<G.Edge>,
  +ha: {G.sub(A, C) == True{} : Bool}, hb: {G.sub(B, C) == True{} : Bool}) ->
  {G.sub(G.appe(A, B), C) == True{} : Bool}:
  match A:
    case Nil{}:
      hb
    case G.Ed{+x, +y} <> t:
      and_intro(G.meme(C, x, y), G.sub(G.appe(t, B), C),
        and_l(G.meme(C, x, y), G.sub(t, C), ha),
        sub_app(t, B, C, and_r(G.meme(C, x, y), G.sub(t, C), ha), hb))

def sub_put_r(c: Bool, +x: Nat, +y: Nat, +A: +List<G.Edge>, +B: +List<G.Edge>,
  +hs: {G.sub(A, B) == True{} : Bool}) ->
  {G.sub(A, G.pute(c, G.Ed{x, y}, B)) == True{} : Bool}:
  match c:
    case False{}:
      hs
    case True{}:
      sub_cons(A, B, G.Ed{x, y}, hs)

def put_sub(cp: Bool, cr: Bool, +x: Nat, +y: Nat, +A: +List<G.Edge>,
  +B: +List<G.Edge>, himp: {G.imp(cp, cr) == True{} : Bool},
  +hs: {G.sub(A, B) == True{} : Bool}) ->
  {G.sub(G.pute(cp, G.Ed{x, y}, A), G.pute(cr, G.Ed{x, y}, B)) == True{} : Bool}:
  match cp:
    case False{}:
      sub_put_r(cr, x, y, A, B, hs)
    case True{}:
      match cr:
        case False{}:
          absurd({G.sub(G.Ed{x, y} <> A, B) == True{} : Bool}, himp)
        case True{}:
          and_intro(G.meme(G.Ed{x, y} <> B, x, y), G.sub(A, G.Ed{x, y} <> B),
            or_l(Bool.and(G.eqn(x, x), G.eqn(y, y)), G.meme(B, x, y),
              and_intro(G.eqn(x, x), G.eqn(y, y), eqn_refl(x), eqn_refl(y))),
            sub_cons(A, B, G.Ed{x, y}, hs))

def inner_mono(+J: +List<G.Inc>, +V: +List<G.Valve>, +n: Nat, +k: Nat) ->
  {G.sub(G.joins_at(J, V, G.Paper{}, n, k), G.joins_at(J, V, G.Real{}, n, k)) == True{} : Bool}:
  match J:
    case Nil{}:
      {==}
    case G.Inc{+m, +k2} <> t:
      put_sub(Bool.and(G.eqn(n, m), Bool.not(G.cut(V, G.Paper{}, n))),
        Bool.and(G.eqn(n, m), Bool.not(G.cut(V, G.Real{}, n))), k, k2,
        G.joins_at(t, V, G.Paper{}, n, k), G.joins_at(t, V, G.Real{}, n, k),
        imp_and(G.eqn(n, m), Bool.not(G.cut(V, G.Paper{}, n)), Bool.not(G.cut(V, G.Real{}, n)),
          imp_not(G.cut(V, G.Real{}, n), G.cut(V, G.Paper{}, n), Laws.cut_mono(V, n))),
        inner_mono(t, V, n, k))

def joins_mono(+I: +List<G.Inc>, +J: +List<G.Inc>, +V: +List<G.Valve>) ->
  {G.sub(G.joins(I, J, V, G.Paper{}), G.joins(I, J, V, G.Real{})) == True{} : Bool}:
  match I:
    case Nil{}:
      {==}
    case G.Inc{+n, +k} <> t:
      sub_app(G.joins_at(J, V, G.Paper{}, n, k), G.joins(t, J, V, G.Paper{}),
        G.appe(G.joins_at(J, V, G.Real{}, n, k), G.joins(t, J, V, G.Real{})),
        sub_app_l(G.joins_at(J, V, G.Paper{}, n, k), G.joins_at(J, V, G.Real{}, n, k),
          G.joins(t, J, V, G.Real{}), inner_mono(J, V, n, k)),
        sub_app_r(G.joins(t, J, V, G.Paper{}), G.joins_at(J, V, G.Real{}, n, k),
          G.joins(t, J, V, G.Real{}), joins_mono(t, J, V)))

# L1c
def Laws.join_mono(inc, V):
  joins_mono(inc, inc, V)

# L1e
def Laws.connected_mono(p, inc, V, a, b, hp):
  Laws.path_mono(p, G.join_edges(inc, V, G.Paper{}), G.join_edges(inc, V, G.Real{}),
    a, b, Laws.join_mono(inc, V), hp)

# L2a, L2b: G - v is a subgraph of G
# ----------------------------------

def meme_head(+x: Nat, +y: Nat, -t: +List<G.Edge>) ->
  {G.meme(G.Ed{x, y} <> t, x, y) == True{} : Bool}:
  or_l(Bool.and(G.eqn(x, x), G.eqn(y, y)), G.meme(t, x, y),
    and_intro(G.eqn(x, x), G.eqn(y, y), eqn_refl(x), eqn_refl(y)))

def sub_put_l(c: Bool, -x: Nat, -y: Nat, -R: +List<G.Edge>, -B: +List<G.Edge>,
  h1: {G.meme(B, x, y) == True{} : Bool}, h2: {G.sub(R, B) == True{} : Bool}) ->
  {G.sub(G.pute(c, G.Ed{x, y}, R), B) == True{} : Bool}:
  match c:
    case False{}:
      h2
    case True{}:
      and_intro(G.meme(B, x, y), G.sub(R, B), h1, h2)

# L2a
def Laws.remove_sub(E, v):
  match E:
    case Nil{}:
      {==}
    case G.Ed{+x, +y} <> t:
      sub_put_l(Bool.not(Bool.or(G.eqn(x, v), G.eqn(y, v))), x, y, G.remove(t, v),
        G.Ed{x, y} <> t, meme_head(x, y, t),
        sub_cons(G.remove(t, v), t, G.Ed{x, y}, Laws.remove_sub(t, v)))

# L2b
def Laws.path_without(p, E, v, s, x, hp):
  Laws.path_mono(p, G.remove(E, v), E, s, x, Laws.remove_sub(E, v), hp)

# Vertex sets
# -----------

def memv_hit(-S: +List<Nat>, +h: Nat, +x: Nat, hh: {G.memv(S, h) == True{} : Bool},
  he: {G.eqn(h, x) == True{} : Bool}) -> {G.memv(S, x) == True{} : Bool}:
  %eqn_sound(h, x, he) : {G.memv(S, _) == True{} : Bool}
  hh

def memv_mono(+S1: +List<Nat>, +S2: +List<Nat>, +x: Nat,
  +hs: {G.subv(S1, S2) == True{} : Bool}, hm: {G.memv(S1, x) == True{} : Bool}) ->
  {G.memv(S2, x) == True{} : Bool}:
  match S1:
    case Nil{}:
      absurd({G.memv(S2, x) == True{} : Bool}, hm)
    case +h <> t:
      either({G.eqn(h, x) == True{} : Bool}, {G.memv(t, x) == True{} : Bool},
        {G.memv(S2, x) == True{} : Bool},
        or_elim(G.eqn(h, x), G.memv(t, x), hm),
        h1 => memv_hit(S2, h, x, and_l(G.memv(S2, h), G.subv(t, S2), hs), h1),
        h2 => memv_mono(t, S2, x, and_r(G.memv(S2, h), G.subv(t, S2), hs), h2))

def memv_cons(e: Nat, -B: +List<Nat>, +x: Nat, h: {G.memv(B, x) == True{} : Bool}) ->
  {G.memv(e <> B, x) == True{} : Bool}:
  or_r(G.eqn(e, x), G.memv(B, x), h)

def subv_cons(+A: +List<Nat>, +B: +List<Nat>, +e: Nat,
  +h: {G.subv(A, B) == True{} : Bool}) -> {G.subv(A, e <> B) == True{} : Bool}:
  match A:
    case Nil{}:
      {==}
    case +x <> t:
      and_intro(G.memv(e <> B, x), G.subv(t, e <> B),
        memv_cons(e, B, x, and_l(G.memv(B, x), G.subv(t, B), h)),
        subv_cons(t, B, e, and_r(G.memv(B, x), G.subv(t, B), h)))

def memv_head(+x: Nat, -t: +List<Nat>) -> {G.memv(x <> t, x) == True{} : Bool}:
  or_l(G.eqn(x, x), G.memv(t, x), eqn_refl(x))

def subv_refl(+S: +List<Nat>) -> {G.subv(S, S) == True{} : Bool}:
  match S:
    case Nil{}:
      {==}
    case +h <> t:
      and_intro(G.memv(h <> t, h), G.subv(t, h <> t), memv_head(h, t),
        subv_cons(t, t, h, subv_refl(t)))

def subv_trans(+A: +List<Nat>, +B: +List<Nat>, +C: +List<Nat>,
  +hab: {G.subv(A, B) == True{} : Bool}, +hbc: {G.subv(B, C) == True{} : Bool}) ->
  {G.subv(A, C) == True{} : Bool}:
  match A:
    case Nil{}:
      {==}
    case +x <> t:
      and_intro(G.memv(C, x), G.subv(t, C),
        memv_mono(B, C, x, hbc, and_l(G.memv(B, x), G.subv(t, B), hab)),
        subv_trans(t, B, C, and_r(G.memv(B, x), G.subv(t, B), hab), hbc))

def subv_putv_r(c: Bool, +z: Nat, +A: +List<Nat>, +B: +List<Nat>,
  +h: {G.subv(A, B) == True{} : Bool}) -> {G.subv(A, G.putv(c, z, B)) == True{} : Bool}:
  match c:
    case False{}:
      h
    case True{}:
      subv_cons(A, B, z, h)

def subv_putv_l(c: Bool, -z: Nat, -R: +List<Nat>, -B: +List<Nat>,
  hc: {G.imp(c, G.memv(B, z)) == True{} : Bool}, hr: {G.subv(R, B) == True{} : Bool}) ->
  {G.subv(G.putv(c, z, R), B) == True{} : Bool}:
  match c:
    case False{}:
      hr
    case True{}:
      and_intro(G.memv(B, z), G.subv(R, B), hc, hr)

def memv_putv(c: Bool, +z: Nat, -R: +List<Nat>, +y: Nat, h: {G.memv(R, y) == True{} : Bool}) ->
  {G.memv(G.putv(c, z, R), y) == True{} : Bool}:
  match c:
    case False{}:
      h
    case True{}:
      or_r(G.eqn(z, y), G.memv(R, y), h)

def putv_hit(c: Bool, +z: Nat, -R: +List<Nat>, hc: {c == True{} : Bool}) ->
  {G.memv(G.putv(c, z, R), z) == True{} : Bool}:
  match c:
    case False{}:
      absurd({G.memv(G.putv(False{}, z, R), z) == True{} : Bool}, hc)
    case True{}:
      memv_head(z, R)

# One BFS round is monotone
# -------------------------

def nbrs_acc(+E: +List<G.Edge>, +S: +List<Nat>, +acc: +List<Nat>) ->
  {G.subv(acc, G.nbrs(E, S, acc)) == True{} : Bool}:
  match E:
    case Nil{}:
      subv_refl(acc)
    case G.Ed{+x, +y} <> t:
      subv_putv_r(G.memv(S, x), y, acc, G.putv(G.memv(S, y), x, G.nbrs(t, S, acc)),
        subv_putv_r(G.memv(S, y), x, acc, G.nbrs(t, S, acc), nbrs_acc(t, S, acc)))

def memv_eq(-S: +List<Nat>, +a: Nat, +x: Nat, ha: {G.eqn(a, x) == True{} : Bool},
  hx: {G.memv(S, x) == True{} : Bool}) -> {G.memv(S, a) == True{} : Bool}:
  %Equal.sym(Nat, a, x, eqn_sound(a, x, ha)) : {G.memv(S, _) == True{} : Bool}
  hx

def hit_fwd.here(+S: +List<Nat>, -R: +List<Nat>, +a: Nat, +b: Nat, +x: Nat, +y: Nat,
  +h1: {Bool.and(G.eqn(a, x), G.eqn(b, y)) == True{} : Bool},
  hs: {G.memv(S, x) == True{} : Bool}) ->
  {G.memv(G.putv(G.memv(S, a), b, R), y) == True{} : Bool}:
  %eqn_sound(b, y, and_r(G.eqn(a, x), G.eqn(b, y), h1)) :
    {G.memv(G.putv(G.memv(S, a), b, R), _) == True{} : Bool}
  putv_hit(G.memv(S, a), b, R,
    memv_eq(S, a, x, and_l(G.eqn(a, x), G.eqn(b, y), h1), hs))

def hit_fwd(+E: +List<G.Edge>, +S: +List<Nat>, +acc: +List<Nat>, +x: Nat, +y: Nat,
  hm: {G.meme(E, x, y) == True{} : Bool}, +hs: {G.memv(S, x) == True{} : Bool}) ->
  {G.memv(G.nbrs(E, S, acc), y) == True{} : Bool}:
  match E:
    case Nil{}:
      absurd({G.memv(G.nbrs(Nil{}, S, acc), y) == True{} : Bool}, hm)
    case G.Ed{+a, +b} <> t:
      either({Bool.and(G.eqn(a, x), G.eqn(b, y)) == True{} : Bool},
        {G.meme(t, x, y) == True{} : Bool},
        {G.memv(G.nbrs(G.Ed{a, b} <> t, S, acc), y) == True{} : Bool},
        or_elim(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(t, x, y), hm),
        h1 => hit_fwd.here(S, G.putv(G.memv(S, b), a, G.nbrs(t, S, acc)), a, b, x, y, h1, hs),
        h2 => memv_putv(G.memv(S, a), b, G.putv(G.memv(S, b), a, G.nbrs(t, S, acc)), y,
          memv_putv(G.memv(S, b), a, G.nbrs(t, S, acc), y,
            hit_fwd(t, S, acc, x, y, h2, hs))))

def hit_bwd.here(+S: +List<Nat>, -R: +List<Nat>, +a: Nat, +b: Nat, +x: Nat, +y: Nat,
  +h1: {Bool.and(G.eqn(a, x), G.eqn(b, y)) == True{} : Bool},
  hs: {G.memv(S, y) == True{} : Bool}) ->
  {G.memv(G.putv(G.memv(S, a), b, G.putv(G.memv(S, b), a, R)), x) == True{} : Bool}:
  %eqn_sound(a, x, and_l(G.eqn(a, x), G.eqn(b, y), h1)) :
    {G.memv(G.putv(G.memv(S, a), b, G.putv(G.memv(S, b), a, R)), _) == True{} : Bool}
  memv_putv(G.memv(S, a), b, G.putv(G.memv(S, b), a, R), a,
    putv_hit(G.memv(S, b), a, R,
      memv_eq(S, b, y, and_r(G.eqn(a, x), G.eqn(b, y), h1), hs)))

def hit_bwd(+E: +List<G.Edge>, +S: +List<Nat>, +acc: +List<Nat>, +x: Nat, +y: Nat,
  hm: {G.meme(E, x, y) == True{} : Bool}, +hs: {G.memv(S, y) == True{} : Bool}) ->
  {G.memv(G.nbrs(E, S, acc), x) == True{} : Bool}:
  match E:
    case Nil{}:
      absurd({G.memv(G.nbrs(Nil{}, S, acc), x) == True{} : Bool}, hm)
    case G.Ed{+a, +b} <> t:
      either({Bool.and(G.eqn(a, x), G.eqn(b, y)) == True{} : Bool},
        {G.meme(t, x, y) == True{} : Bool},
        {G.memv(G.nbrs(G.Ed{a, b} <> t, S, acc), x) == True{} : Bool},
        or_elim(Bool.and(G.eqn(a, x), G.eqn(b, y)), G.meme(t, x, y), hm),
        h1 => hit_bwd.here(S, G.nbrs(t, S, acc), a, b, x, y, h1, hs),
        h2 => memv_putv(G.memv(S, a), b, G.putv(G.memv(S, b), a, G.nbrs(t, S, acc)), x,
          memv_putv(G.memv(S, b), a, G.nbrs(t, S, acc), x,
            hit_bwd(t, S, acc, x, y, h2, hs))))

def nbrs_mono(+E1: +List<G.Edge>, +E2: +List<G.Edge>, +S1: +List<Nat>, +S2: +List<Nat>,
  +acc1: +List<Nat>, +acc2: +List<Nat>,
  +he: {G.sub(E1, E2) == True{} : Bool}, +hs: {G.subv(S1, S2) == True{} : Bool},
  ha: {G.subv(acc1, G.nbrs(E2, S2, acc2)) == True{} : Bool}) ->
  {G.subv(G.nbrs(E1, S1, acc1), G.nbrs(E2, S2, acc2)) == True{} : Bool}:
  match E1:
    case Nil{}:
      ha
    case G.Ed{+x, +y} <> t:
      subv_putv_l(G.memv(S1, x), y, G.putv(G.memv(S1, y), x, G.nbrs(t, S1, acc1)),
        G.nbrs(E2, S2, acc2),
        imp_from(G.memv(S1, x), G.memv(G.nbrs(E2, S2, acc2), y),
          hx => hit_fwd(E2, S2, acc2, x, y,
            and_l(G.meme(E2, x, y), G.sub(t, E2), he), memv_mono(S1, S2, x, hs, hx))),
        subv_putv_l(G.memv(S1, y), x, G.nbrs(t, S1, acc1), G.nbrs(E2, S2, acc2),
          imp_from(G.memv(S1, y), G.memv(G.nbrs(E2, S2, acc2), x),
            hy => hit_bwd(E2, S2, acc2, x, y,
              and_l(G.meme(E2, x, y), G.sub(t, E2), he), memv_mono(S1, S2, y, hs, hy))),
          nbrs_mono(t, E2, S1, S2, acc1, acc2,
            and_r(G.meme(E2, x, y), G.sub(t, E2), he), hs, ha)))

# L1f
def Laws.reach_mono(k, E1, E2, S1, S2, he, hs):
  match k:
    case 0n:
      hs
    case 1n+p:
      Laws.reach_mono(p, E1, E2, G.nbrs(E1, S1, S1), G.nbrs(E2, S2, S2), he,
        nbrs_mono(E1, E2, S1, S2, S1, S2, he, hs,
          subv_trans(S1, S2, G.nbrs(E2, S2, S2), hs, nbrs_acc(E2, S2, S2))))

# L1g
def Laws.seg_mono(k, inc, V, a):
  Laws.reach_mono(k, G.join_edges(inc, V, G.Paper{}), G.join_edges(inc, V, G.Real{}),
    [a], [a], Laws.join_mono(inc, V), subv_refl([a]))

# Customer weights
# ----------------

def le_refl(a: Nat) -> {G.le(a, a) == True{} : Bool}:
  match a:
    case 0n:
      {==}
    case 1n+p:
      le_refl(p)

def le_succ(c: Nat, e: Nat, h: {G.le(c, e) == True{} : Bool}) ->
  {G.le(c, 1n+e) == True{} : Bool}:
  match c e:
    case 0n _:
      {==}
    case 1n+cp 0n:
      absurd({G.le(1n+cp, 1n) == True{} : Bool}, h)
    case 1n+cp 1n+ep:
      le_succ(cp, ep, h)

def le_add_l(+b: Nat, +c: Nat, +d: Nat, +h: {G.le(c, d) == True{} : Bool}) ->
  {G.le(c, Nat.add(b, d)) == True{} : Bool}:
  match b:
    case 0n:
      h
    case 1n+bp:
      le_succ(c, Nat.add(bp, d), le_add_l(bp, c, d, h))

def le_add(a: Nat, b: Nat, +c: Nat, +d: Nat, h1: {G.le(a, b) == True{} : Bool},
  +h2: {G.le(c, d) == True{} : Bool}) ->
  {G.le(Nat.add(a, c), Nat.add(b, d)) == True{} : Bool}:
  match a b:
    case 0n _:
      le_add_l(b, c, d, h2)
    case 1n+ap 0n:
      absurd({G.le(Nat.add(1n+ap, c), Nat.add(0n, d)) == True{} : Bool}, h1)
    case 1n+ap 1n+bp:
      le_add(ap, bp, c, d, h1, h2)

def pick_le(c1: Bool, c2: Bool, +w: Nat, h: {G.imp(c1, c2) == True{} : Bool}) ->
  {G.le(G.pickn(c1, w), G.pickn(c2, w)) == True{} : Bool}:
  match c1:
    case False{}:
      {==}
    case True{}:
      match c2:
        case False{}:
          absurd({G.le(w, 0n) == True{} : Bool}, h)
        case True{}:
          le_refl(w)

def csum_mono(+C: +List<G.Cust>, +S1: +List<Nat>, +S2: +List<Nat>,
  +hs: {G.subv(S1, S2) == True{} : Bool}) ->
  {G.le(G.csum(C, S1), G.csum(C, S2)) == True{} : Bool}:
  match C:
    case Nil{}:
      {==}
    case G.Cust{+k, +w} <> t:
      le_add(G.pickn(G.memv(S1, k), w), G.pickn(G.memv(S2, k), w),
        G.csum(t, S1), G.csum(t, S2),
        pick_le(G.memv(S1, k), G.memv(S2, k), w,
          imp_from(G.memv(S1, k), G.memv(S2, k), hk => memv_mono(S1, S2, k, hs, hk))),
        csum_mono(t, S1, S2, hs))

# L1h
def Laws.customers_mono(C, k, inc, V, a):
  csum_mono(C, G.seg(k, inc, V, G.Paper{}, a), G.seg(k, inc, V, G.Real{}, a),
    Laws.seg_mono(k, inc, V, a))

# L2c-L2e: supply loss
# --------------------

def imp_true(c: Bool, -d: Bool, hd: {d == True{} : Bool}) -> {G.imp(c, d) == True{} : Bool}:
  match c:
    case False{}:
      {==}
    case True{}:
      hd

def dropv_sub(+S: +List<Nat>, +v: Nat) -> {G.subv(G.dropv(S, v), S) == True{} : Bool}:
  match S:
    case Nil{}:
      {==}
    case +h <> t:
      subv_putv_l(Bool.not(G.eqn(h, v)), h, G.dropv(t, v), h <> t,
        imp_true(Bool.not(G.eqn(h, v)), G.memv(h <> t, h), memv_head(h, t)),
        subv_cons(G.dropv(t, v), t, h, dropv_sub(t, v)))

# L2c
def Laws.supply_mono(k, E, src, v):
  Laws.reach_mono(k, G.remove(E, v), E, G.dropv(src, v), src, Laws.remove_sub(E, v),
    dropv_sub(src, v))

# L2d
def Laws.supplied_without_sound(k, E, src, v, x, h):
  memv_mono(G.supplied_without(k, E, src, v), G.supplied(k, E, src), x,
    Laws.supply_mono(k, E, src, v), h)

def and_false(a: Bool) -> {Bool.and(a, False{}) == False{} : Bool}:
  match a:
    case False{}:
      {==}
    case True{}:
      {==}

# L2e
def Laws.lost_sound(k, E, src, v, x, h):
  %Equal.sym(Bool, G.memv(G.supplied_without(k, E, src, v), x), True{}, h) :
    {Bool.and(G.memv(G.supplied(k, E, src), x), Bool.not(_)) == False{} : Bool}
  and_false(G.memv(G.supplied(k, E, src), x))
