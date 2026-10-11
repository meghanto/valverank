# demo.bend: runs the specification in Graph.bend on a toy network.
#
#   n0 --p0-- n1 --p1-- n2 --p2-- n3 --p3-- n4 --p6-- n7
#                       |
#                       p4
#                       |
#                       n5 --p5-- n6 --p7-- n8
#
# Valves sit at n1, n2, n3, n4 and n5. The valve at n2 is INOP.
# On paper n2 is a cut point, so p1, p2 and p4 are three segments.
# In reality the INOP valve cannot close, so they merge into one.
import Base
import ./Graph.bend as G

def pieces() -> +List<G.Inc>:
  [G.Inc{0n, 0n}, G.Inc{1n, 0n},
   G.Inc{1n, 1n}, G.Inc{2n, 1n},
   G.Inc{2n, 2n}, G.Inc{3n, 2n},
   G.Inc{3n, 3n}, G.Inc{4n, 3n},
   G.Inc{2n, 4n}, G.Inc{5n, 4n},
   G.Inc{5n, 5n}, G.Inc{6n, 5n},
   G.Inc{4n, 6n}, G.Inc{7n, 6n},
   G.Inc{6n, 7n}, G.Inc{8n, 7n}]

def valves() -> +List<G.Valve>:
  [G.Valve{1n, False{}, False{}},
   G.Valve{2n, False{}, True{}},
   G.Valve{3n, False{}, False{}},
   G.Valve{4n, False{}, False{}},
   G.Valve{5n, False{}, False{}}]

# customers per piece
def customers() -> +List<G.Cust>:
  [G.Cust{0n, 12n}, G.Cust{1n, 30n}, G.Cust{2n, 25n}, G.Cust{3n, 8n},
   G.Cust{4n, 40n}, G.Cust{5n, 15n}, G.Cust{6n, 5n}, G.Cust{7n, 9n}]

# the vertices 0..n-1 that are in S, in order and without duplicates
def members(n: Nat, +S: +List<Nat>, +i: Nat) -> +List<Nat>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      G.putv(G.memv(S, i), i, members(p, S, 1n+i))

# the vertices 0..n-1 that are lost when v is removed
def lost_list(n: Nat, +E: +List<G.Edge>, +src: +List<Nat>, +v: Nat, +i: Nat) ->
  +List<Nat>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      G.putv(G.lost(5n, E, src, v, i), i, lost_list(p, E, src, v, 1n+i))

def show(xs: +List<Nat>) -> String:
  List.show(~&2, ~Nat, ~Nat.show, xs)

# a separate toy segment graph for supply loss: vertex 0 holds the plant;
# vertex 1 is an articulation point
def seg_edges() -> +List<G.Edge>:
  [G.Ed{0n, 1n}, G.Ed{1n, 2n}, G.Ed{2n, 3n}, G.Ed{1n, 4n}, G.Ed{3n, 2n}]

def main() -> IO(Unit):
  +paper = G.seg(8n, pieces(), valves(), G.Paper{}, 2n)
  +real = G.seg(8n, pieces(), valves(), G.Real{}, 2n)
  +full = G.supplied(5n, seg_edges(), [0n])
  +cut1 = G.supplied_without(5n, seg_edges(), [0n], 1n)
  do IO<Unit>:
    IO.print("segment of piece 2, paper: " ++ show(members(8n, paper, 0n))
      ++ "  customers " ++ Nat.show(G.csum(customers(), paper)))
    IO.print("segment of piece 2, real:  " ++ show(members(8n, real, 0n))
      ++ "  customers " ++ Nat.show(G.csum(customers(), real)))
    IO.print("supplied from source 0:        " ++ show(members(5n, full, 0n)))
    IO.print("supplied with vertex 1 removed: " ++ show(members(5n, cut1, 0n)))
    IO.print("lost when vertex 1 is removed:  " ++ show(lost_list(5n, seg_edges(), [0n], 1n, 0n)))
