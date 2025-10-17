import math
from shapely.ops import unary_union, split
from shapely.geometry import Point, LineString
import networkx as nx

def round_pt(pt, tol):
    return (round(pt[0]/tol)*tol, round(pt[1]/tol)*tol)

def build_topology(lines: list[LineString], snap_tol: float, intersect_tol: float):
    """
    1) Snap de endpoints próximos
    2) Interseções entre linhas → split
    3) Nós = endpoints (após split); Arestas = segmentos
    """
    # 1) Snap simples por “grid rounding” (rápido e robusto)
    snapped = []
    for ln in lines:
        x1, y1 = round_pt(ln.coords[0], snap_tol)
        x2, y2 = round_pt(ln.coords[-1], snap_tol)
        if (x1, y1) != (x2, y2):
            snapped.append(LineString([(x1, y1), (x2, y2)]))

    # 2) Interseções globais
    merged = unary_union(snapped)    # MultiLineString/GeometryCollection
    # gerar segmentos atômicos (linemerge ajuda a colar, split pelo merged também pode ser usado)
    # Para garantir segmentação em interseções, fazemos:
    if merged.geom_type == "LineString":
        parts = [merged]
    elif merged.geom_type == "MultiLineString":
        parts = list(merged.geoms)
    else:
        parts = []

    # 3) Montar grafo
    G = nx.Graph()
    def add_edge(ls: LineString):
        u = (ls.coords[0][0], ls.coords[0][1])
        v = (ls.coords[-1][0], ls.coords[-1][1])
        if u == v: 
            return
        length = ls.length
        G.add_node(u, x=u[0], y=u[1])
        G.add_node(v, x=v[0], y=v[1])
        G.add_edge(u, v, length=length, wkt=ls.wkt)

    for seg in parts:
        if seg.length > intersect_tol:
            add_edge(seg)

    return G
