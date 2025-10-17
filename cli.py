import argparse
from pathlib import Path
import networkx as nx
from cad_preproc.pipeline import run_pipeline

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="arquivo .dxf ou .dwg")
    ap.add_argument("--config", default="configs/default.yml", help="yaml de configuração")
    ap.add_argument("--dwg2dxf", default=None, help="binário conversor DWG->DXF (opcional)")
    ap.add_argument("--outdir", default="out", help="pasta de saída")
    args = ap.parse_args()

    G = run_pipeline(args.input, args.config, dwg2dxf_cmd=args.dwg2dxf)

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, outdir / "graph.graphml")
    # exportar JSON simples de edges:
    data = {
        "nodes": [{"id": f"{n[0]}_{n[1]}", "x": n[0], "y": n[1]} for n in G.nodes()],
        "edges": [
            {
                "u": f"{u[0]}_{u[1]}",
                "v": f"{v[0]}_{v[1]}",
                "length": d.get("length"),
                "wkt": d.get("wkt"),
                "semantic": d.get("semantic"),
            }
            for u, v, d in G.edges(data=True)
        ],
    }
    (outdir / "graph.json").write_text(__import__("json").dumps(data), encoding="utf-8")

if __name__ == "__main__":
    main()
