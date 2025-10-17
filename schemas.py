from __future__ import annotations
from dataclasses import dataclass
from typing import TypedDict, Literal, NotRequired, Any

# ---- Config ----

class UnitsConfig(TypedDict):
    target: Literal["m"]               # neste projeto, padronizamos para "m"
    arc_segment_len: float             # passo de discretização de arcos (m)
    snap_tolerance: float              # tolerância p/ unir nós (m)
    intersect_tolerance: float         # tolerância p/ descartar segmentos minúsculos (m)

class NormalizeConfig(TypedDict):
    remove_prefixes: list[str]
    uppercase: bool
    strip_chars: list[str]

class SemanticRule(TypedDict):
    match: str                         # regex
    semantic: str                      # ex: "WALL", "DOOR", ...

class LayersConfig(TypedDict):
    normalize: NormalizeConfig
    semantic_map: list[SemanticRule]
    include_semantics: list[str]
    exclude_semantics: list[str]

class ExportConfig(TypedDict):
    formats: list[Literal["graphml", "json"]]
    out_basename: str

class PipelineConfig(TypedDict):
    units: UnitsConfig
    layers: LayersConfig
    export: ExportConfig

# ---- Grafo / Geometrias ----

@dataclass(frozen=True)
class Node:
    """Nó do grafo topológico."""
    x: float
    y: float
    # você pode incluir z/opcionais depois (ex.: z: NotRequired[float])

@dataclass
class Edge:
    """Aresta do grafo topológico."""
    u: tuple[float, float]     # coord do nó A (x,y)
    v: tuple[float, float]     # coord do nó B (x,y)
    length: float
    wkt: str
    semantic: str | None = None
    # campos extras (opcionais)
    attrs: NotRequired[dict[str, Any]] = None

# ---- Resultados / Relatórios (opcional) ----

class QACounts(TypedDict, total=False):
    entities_total: int
    kept_lines: int
    dropped_by_semantics: int
    layers_seen: dict[str, int]
    semantics_seen: dict[str, int]

class PipelineResult(TypedDict):
    """Se você quiser padronizar retornos da pipeline além do networkx.Graph."""
    graph_stats: dict[str, int]   # nodes/edges etc.
    qa_counts: NotRequired[QACounts]
