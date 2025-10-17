from pathlib import Path
import subprocess
import ezdxf

class CADLoader:
    def __init__(self, dwg2dxf_cmd: str | None = None):
        self.dwg2dxf_cmd = dwg2dxf_cmd

    def to_dxf(self, input_path: Path) -> Path:
        p = Path(input_path)
        if p.suffix.lower() == ".dxf":
            return p

        if p.suffix.lower() == ".dwg":
            if not self.dwg2dxf_cmd:
                raise RuntimeError("Arquivo .DWG detectado e nenhum conversor DWG->DXF foi configurado.")
            out = p.with_suffix(".dxf")
            subprocess.run([self.dwg2dxf_cmd, str(p), str(out)], check=True)
            return out

        raise ValueError(f"Formato não suportado: {p.suffix}")

    def read_dxf(self, dxf_path: Path):
        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()
        return doc, msp
