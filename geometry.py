from shapely.geometry import LineString
from shapely.ops import linemerge
import math
import ezdxf
from ezdxf.math import ConstructionArc

def _as_lines_from_entity(e, arc_segment_len: float):
    """Gera segmentos LineString (x,y) a partir de uma entidade DXF."""
    dxftype = e.dxftype()

    if dxftype == "LINE":
        p1 = (e.dxf.start.x, e.dxf.start.y)
        p2 = (e.dxf.end.x, e.dxf.end.y)
        yield LineString([p1, p2])

    elif dxftype in ("LWPOLYLINE", "POLYLINE"):
        pts = [(p[0], p[1]) for p in e.get_points()] if dxftype=="LWPOLYLINE" else [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if getattr(e, "closed", False) or (hasattr(e, "closed") and e.closed):
            pts = pts + [pts[0]]
        # explodir em segmentos
        for i in range(len(pts)-1):
            yield LineString([pts[i], pts[i+1]])

    elif dxftype in ("ARC", "CIRCLE"):
        if dxftype == "CIRCLE":
            center = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            start_angle = 0.0
            end_angle = 360.0
        else:
            center = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            start_angle = e.dxf.start_angle
            end_angle = e.dxf.end_angle

        arc = ConstructionArc(center, r, math.radians(start_angle), math.radians(end_angle))
        length = arc.length()
        n = max(4, int(math.ceil(length / max(arc_segment_len, 1e-6))))
        pts = [arc.point_at(t) for t in [i/(n-1) for i in range(n)]]
        for i in range(len(pts)-1):
            yield LineString([pts[i], pts[i+1]])