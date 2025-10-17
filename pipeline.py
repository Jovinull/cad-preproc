from pathlib import Path
import yaml
import ezdxf
from shapely.affinity import scale as shp_scale
from shapely.geometry import LineString
from ezdxf.addons import itervirtualentities

from .io import CADLoader
from .units import scale_factor_to_meters
from .layers import normalize_layer_name, semantic_from_name, decide_keep
from .geometry import _as_lines_from_entity
from .graph import build_topology

def run_pipeline(input_path: str, config_path: str, dwg2dxf_cmd: str | None = None):
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    loader = CADLoader(dwg2dxf_cmd=dwg2dxf_cmd)
    dxf_path = loader.to_dxf(Path(input_path))
    doc, msp = loader.read_dxf(dxf_path)

    # Unidades → metros
    sf = scale_factor_to_meters(doc)
    target = cfg["units"]["target"].lower()
    if target != "m":
        raise NotImplementedError("Exemplo implementado com alvo em metros. Ajuste conforme necessário.")

    # Normalização de layers
    rm_pfx = cfg["layers"]["normalize"]["remove_prefixes"]
    uppercase = cfg["layers"]["normalize"]["uppercase"]
    strip_chars = cfg["layers"]["normalize"]["strip_chars"]
    rules = cfg["layers"]["semantic_map"]
    include = set(cfg["layers"]["include_semantics"])
    exclude = set(cfg["layers"]["exclude_semantics"])

    arc_seg = float(cfg["units"]["arc_segment_len"])
    snap_tol = float(cfg["units"]["snap_tolerance"])
    inter_tol = float(cfg["units"]["intersect_tolerance"])

    # Coletar linhas (já discretizadas) com metadados
    lines_by_semantic = []

    # Explodir blocos virtualmente
    entities = list(itervirtualentities(msp))  # inclui inserts “explodidos”
    for e in entities:
        try:
            layer_raw = getattr(e.dxf, "layer", "0")
        except Exception:
            layer_raw = "0"

        norm = normalize_layer_name(layer_raw, rm_pfx, uppercase, strip_chars)
        semantic = semantic_from_name(norm, rules)

        if not decide_keep(semantic, include, exclude):
            continue

        # Discretizar em segmentos
        for ls in _as_lines_from_entity(e, arc_segment_len=arc_seg):
            # aplicar escala -> metros
            if sf != 1.0:
                # escala uniforme
                ls = LineString([(p[0]*sf, p[1]*sf) for p in ls.coords])
            lines_by_semantic.append((ls, semantic, norm))

    # Montar grafo topológico
    only_lines = [ls for (ls, _, __) in lines_by_semantic]
    G = build_topology(only_lines, snap_tol=snap_tol, intersect_tol=inter_tol)

    # Anexar atributos agregados por aresta (ex.: semântica majoritária, comprimento)
    # (opcional) cruzar cada aresta com as linhas originais para inferir semânticas
    # simples: guardar tudo como “desconhecido” se múltiplas; aqui vai um rascunho:
    for u, v, data in G.edges(data=True):
        # nada impede de deixar só comprimento + wkt já preenchidos
        data["semantic"] = "MIXED/UNKNOWN"

    return G
