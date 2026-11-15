# Tools

The scripts behind this Türkiye-only run of global-law's vulnerability detectors. They run inside a copy of
[global-law/vulnerabilities/scripts](https://github.com/lexifina/global-law/tree/main/vulnerabilities/scripts) (Python 3.11+,
`pip install duckdb pyarrow`), with a bare clone of this repository at `sources/corpus/turkey-law.git`, a blobless bare
clone of global-law at `sources/global-law.git`, and a `pins.json` that names only turkey-law and its commit.
`build_vulns.py`, `flags_chart.py`, `late_ext_select.py` and `late_ext_rebut.py` sit two folders above the scripts, next to
`config.json`.

| Script | What it does |
| --- | --- |
| `run.sh` | Indexes the history and texts, adds this repository's history rows, and runs the detectors (`bash run.sh <shards>`) |
| `add_root.py` | Builds the history rows from this repository's own commits (global-law replays it only up to an earlier commit), so the history detectors read every change |
| `run_triage.sh` | The model review: the 40 strongest flags per category, the 40 strongest lapsed time limits in law texts, and the empty periods |
| `late_ext_select.py` | Chooses the empty periods for global-law's review of that category (there were none here) |
| `late_ext_rebut.py` | Adds the second, arguing-against pass to the empty-period review, as `triage.py` does for the other categories |
| `build_vulns.py` | Builds `data/flags.csv`, `data/reviewed.csv` and `data/by_category.csv` from the findings and the model review |
| `flags_chart.py` | Draws the chart at the top of the READMEs, in Turkish and English, light and dark |
| `config.json` | The repository, the Turkish category names, the top-level folders that are not law, and the chart's labels |

The model review needs `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` and `LLM_AUTH` set for an OpenAI-compatible Responses API.
It was run as `bash run_triage.sh '^(case-law|decision|norm|election|audit|data|tools|monitoring|visualisations|vulnerabilities)/'`.

Changes made for this repository:

- `add_root.py` counts as law not only amendments (`Kind: amendment`) but also an act's first text, which this repository
  marks `as-enacted`, `enacted`, `consolidated` or `current-text`. Without them, the text and reference scans, which read
  only rows of kind `law`, would leave out every act held only as its current text.
- `build_vulns.py` maps a file path from before 10 November 2026, when act folders were renamed (`kanun/4857/madde-53.md`
  to `law/2003/4857/madde-53.md`), to its folder today through `data/paths.json`, for both the `path` and the `url` columns.
- `build_vulns.py` gives each retroactive-date flag the path of the first file of its act or decision (global-law's detector
  names only the act), so that board and court decisions count as not law.
- `run.sh` was run with 3 shards: with 8, the text and reference scans ran out of memory on the shared machine.
