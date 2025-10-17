# CAD Preproc – Pipeline de Pré-processamento Vetorial (DXF/DWG → Grafo)

Pipeline em Python para normalizar plantas CAD (DXF/DWG), filtrar layers por semântica, padronizar unidades e converter a geometria 2D em um **grafo topológico** (nós/arestas) para usos em IA/QA/validações.

## Recursos

* **Suporte a DXF** nativo (`ezdxf`)
* **Suporte a DWG** via conversão para DXF com uma **CLI externa** (configurável)
* **Normalização de unidades** (ex.: tudo para **metros**)
* **Normalização de layers** (uppercase, remoção de prefixos, limpeza)
* **Mapeamento semântico de layers por regex** (ex.: `WALL`, `DOOR`, `WINDOW`, `GRID`…)
* **Filtros por semântica** (incluir/excluir)
* **Explosão virtual de blocos** e **discretização de arcos/círculos**
* **Construção de grafo topológico** com snapping e interseções
* **Exportações** em GraphML e JSON (fácil integrar com Gephi, NetworkX, etc.)

---

## Arquitetura

```
cad-preproc/
├─ cad_preproc/
│  ├─ __init__.py
│  ├─ io.py              # leitura DWG/DXF, conversão DWG->DXF (via CLI externa)
│  ├─ units.py           # normalização de unidades (INSUNITS → metros)
│  ├─ layers.py          # normalização e filtros semânticos (regex/whitelist/blacklist)
│  ├─ geometry.py        # explode/discretiza entidades em segmentos LineString
│  ├─ graph.py           # snapping, interseção e montagem do grafo (networkx)
│  ├─ pipeline.py        # orquestra o fluxo ponta-a-ponta
│  └─ schemas.py         # tipos/estruturas auxiliares
├─ configs/
│  └─ default.yml        # tolerâncias, mapeamentos, exportação
├─ tests/
├─ cli.py                # interface de linha de comando
├─ pyproject.toml
└─ README.md
```

---

## Requisitos

* **Python** ≥ 3.10
* **Dependências**:

  * `ezdxf` (leitura DXF, entities e “itervirtualentities” para blocos)
  * `shapely` (geometrias robustas e interseções)
  * `networkx` (grafo)
  * `pyyaml` (configuração YAML)
* **(Opcional) Conversor DWG → DXF (CLI)**
  Para abrir **DWG**, o projeto usa um **conversor externo** para produzir um **DXF** equivalente. Você aponta o executável via `--dwg2dxf`.
  Exemplos de categorias de conversores que costumam ser usados em pipelines:

  * **ODA File Converter** (ferramenta de linha de comando da Open Design Alliance / Teigha).
  * Ferramentas CAD com **modo batch/CLI** que exportam DWG→DXF (por ex., versões com automação/script).
  * Outros conversores DWG→DXF confiáveis com **uso via terminal**.

> Observação: este repositório **não inclui** nenhum conversor DWG por questões de licença/redistribuição. Você deve instalar/configurar o seu e passar o caminho do binário via `--dwg2dxf`.

---

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install ezdxf shapely networkx pyyaml
```

(Se for usar DWG: instale seu conversor CLI e anote o caminho do executável.)

---

## Configuração (`configs/default.yml`)

```yaml
units:
  target: "m"              # unidade final da pipeline (metros)
  arc_segment_len: 0.05    # tamanho alvo do segmento para discretizar arcos (m)
  snap_tolerance: 0.01     # tolerância para unir vértices (m)
  intersect_tolerance: 1e-6

layers:
  normalize:
    remove_prefixes: ["A-", "E-", "S-", "ARQ-"]
    uppercase: true
    strip_chars: [" ", "\t"]
  semantic_map:
    - {match: "WALL|PAREDE|ALV|ALVENARIA", semantic: "WALL"}
    - {match: "DOOR|PORTA",                semantic: "DOOR"}
    - {match: "WIN(DOW)?|JANELA",          semantic: "WINDOW"}
    - {match: "GRID|EIXO|AXIS",            semantic: "GRID"}
    - {match: "TEXT|MTEXT|ANNOT|NOTE",     semantic: "TEXT"}
    - {match: "DIM|COTA",                  semantic: "DIM"}
    - {match: "HATCH|HACHURA",             semantic: "HATCH"}
  include_semantics: ["WALL", "DOOR", "WINDOW", "GRID"]
  exclude_semantics: ["TEXT", "DIM", "HATCH"]

export:
  formats: ["graphml", "json"]
  out_basename: "graph"
```

### Como ajustar

* **Unidades**: se o desenho estiver em polegadas/pés/mm, o pipeline lê `$INSUNITS` do DXF e faz a **conversão para metros**.
* **Semântica**: edite/adicione regex para refletir a nomenclatura do seu escritório/projeto/cidade.
* **Filtros**: controle o que entra na análise (ex.: excluir `TEXT/DIM/HATCH` para reduzir ruído).
* **Tolerâncias**: `snap_tolerance` governa o “encaixe” de nós; `arc_segment_len` controla o detalhamento de arcos/círculos.

---

## Uso (CLI)

### DXF direto

```bash
python cli.py /caminho/planta.dxf \
  --config configs/default.yml \
  --outdir out/
```

### DWG (com conversor externo)

```bash
python cli.py /caminho/planta.dwg \
  --dwg2dxf "/caminho/para/seu/conversor" \
  --config configs/default.yml \
  --outdir out/
```

**Saídas padrão**:

* `out/graph.graphml` – grafo para Gephi/NetworkX
* `out/graph.json` – nós/arestas + WKT para debug/integração

---

## O que acontece etapa por etapa

1. **Leitura & Conversão (io.py)**

   * Se for **DWG**, chamamos o binário configurado em `--dwg2dxf` para gerar um **DXF** temporário.
   * Para **DXF**, lemos com `ezdxf` e iteramos o **modelspace**.

2. **Unidades (units.py)**

   * Lemos `$INSUNITS` do header DXF e obtemos o **fator de escala → metros**.
   * Todos os vértices/segmentos são multiplicados pelo fator, padronizando a métrica.

3. **Normalização de Layers (layers.py)**

   * Limpeza de string (espaços/tabs), **uppercase**, remoção de **prefixos** padrão.
   * Cada layer é classificado contra um **mapa semântico** (regex → `WALL`, `DOOR` etc.).

4. **Filtros Semânticos**

   * Mantemos apenas os layers cujo **semântico** esteja em `include_semantics` e não esteja em `exclude_semantics`.

5. **Explosão & Discretização (geometry.py)**

   * **Blocos** (`INSERT`) são lidos virtualmente via `itervirtualentities` (sem alterar o arquivo).
   * **ARC/CIRCLE** são discretizados em segmentos lineares com passo definido por `arc_segment_len`.

6. **Grafo Topológico (graph.py)**

   * **Snapping**: endpoints próximos se unem (grade por tolerância).
   * **Interseções**: linhas são unidas/particionadas para produzir **segmentos atômicos**.
   * Montamos o **grafo** (`networkx`) com nós (x,y) e arestas (comprimento, WKT, semântica).

7. **Exportação**

   * Salvamos **GraphML** e **JSON** com atributos úteis (comprimento, WKT, semântica → “MIXED/UNKNOWN” por padrão, pode evoluir).

---

## Exemplo rápido (API Python)

```python
from cad_preproc.pipeline import run_pipeline

G = run_pipeline(
    input_path="exemplos/plantas/planta_teste.dxf",
    config_path="configs/default.yml",
    dwg2dxf_cmd=None,  # ou "/caminho/ODAFileConverter" para DWG
)

print(G.number_of_nodes(), G.number_of_edges())
# -> use G para métricas, buscas de caminhos, conectividade, etc.
```

---

## Conversor DWG → DXF (Detalhes práticos)

* **Por que converter?**
  Leitura de DWG diretamente em Python costuma exigir SDKs/licenças específicas. A conversão para DXF via **CLI** torna o pipeline **reprodutível** e **portável**.

* **Como configurar?**

  * Instale uma ferramenta que **exporte DWG para DXF por linha de comando**.
  * Passe o caminho do binário na execução: `--dwg2dxf "/caminho/para/conversor"`.
  * O `io.py` chama essa CLI e espera um arquivo `.dxf` como resultado ao lado do DWG.

* **Formatos DXF**

  * Caso o conversor permita, prefira DXF em versões amplamente compatíveis (ex.: R2010/R2007).
  * Se seu desenho usa recursos mais novos (e.g., splines complexas), mantenha uma versão de DXF que preserve a geometria.

> Importante: **nós não distribuímos** o conversor. Verifique licenças/termos de uso do conversor que você escolher.

---

## Extensões recomendadas

* **Relatórios de QA** (CSV/HTML): contagens por layer/semântica, nós/arestas, comprimentos médios, alertas.
* **Atribuição semântica por aresta**: majoritária por sobreposição/interseção com as linhas filtradas.
* **Export Geo**: GeoJSON/GeoPackage (nós/arestas) para abrir no QGIS.
* **3D**: incluir Z quando relevante.
* **Índices espaciais**: STRtree (Shapely) para acelerar operações em plantas muito grandes.
* **Multiprocessamento** com tiling espacial.

---

## Dicas de performance

* Aumente `arc_segment_len` para **menos segmentos** (menos detalhamento, mais rápido).
* Ajuste `snap_tolerance` com cuidado: grandes demais podem **fundir geometria** que não deveria.
* Pré-filtre layers cedo (evite carregar/guardar entidades que você sabe que serão descartadas).
* Em plantas enormes, **divida por tiles** (ex.: grade 50m×50m), processe em paralelo e depois una resultados.

---

## Solução de problemas (FAQ)

**1) Meu arquivo DWG não abre.**
→ Confirme se o conversor DWG→DXF funciona no terminal e gere manualmente um DXF. Depois rode a pipeline com o DXF.

**2) As unidades parecem erradas.**
→ Verifique `$INSUNITS` no cabeçalho do DXF. Se o desenho veio “unitless” (0), defina um fator explícito no código/`units.py` ou padronize o CAD antes.

**3) Há muita perda de detalhe em arcos.**
→ Diminua `arc_segment_len` (ex.: 0.01 m). Isso aumenta o número de segmentos e a fidelidade.

**4) O grafo está com nós “grudados” demais.**
→ Reduza `snap_tolerance` para ser mais conservador no encaixe de vértices.

**5) Quero manter textos/cotas para alguma análise específica.**
→ Remova `TEXT`/`DIM` de `exclude_semantics` e/ou adicione regras dedicadas no `semantic_map`.

## Contribuindo

* Issues com exemplos mínimos (DXF recortado) ajudam muito.
* Pull requests: seguir o estilo PEP8/Black, adicionar testes quando possível.

---

## Créditos & Referências

* **ezdxf** – parsing DXF em Python.
* **Shapely** – operações geométricas robustas.
* **NetworkX** – grafos.
* Conversores **DWG→DXF** (não incluídos) – usar conforme suas licenças/ambiente.
