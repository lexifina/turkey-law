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
| `patch_detectors.py` | Fixes blind spots found in runs on several country repositories in the copy of global-law's scripts (`python -X utf8 patch_detectors.py <scripts dir>`; a fix already in place is skipped) |
| `redo.py` | Runs `patch_detectors.py`, then again only the scans and detectors the fixes change, the model review of lapsed time limits, references to deleted provisions and empty periods, and the build (`python -X utf8 redo.py <run folder> [--keep-reviews]`; `EMBED_FONTS` names the script that embeds the chart's fonts) |
| `late_ext_check.py` | Hand-check helper: for each empty period that survived the review, the lines of the extending commit's diff that hold the old or the new date, in Turkish and numeric forms, following folders renamed on 10 November 2026 |
| `measure_missed.py` | Counts the places where "kadar", "dek" or "değin" follows a past date or year, which of them the time-limit search reads, and the forms of those it misses (the numbers in the READMEs) |

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
- The run was then repeated with `redo.py`. Of `patch_detectors.py`'s fixes, these change this repository's flags. Lapsed
  time limits now read Turkish, where the date comes before "kadar" ("31/12/2020 tarihine kadar", "31 Aralık 2020'ye kadar",
  "2020 yılı sonuna kadar"): 1 flag became 3,888, and the empty-period detector, which reads the same dates, found 14 where
  it had found none. A currency name other than "lira" counts only as a whole word, which removed matches inside other words
  ("intikal", "intifa", Marcoussis). A fourth round, made after this run's hand check, also reads the end of the day or a
  time after the date ("günü sonuna kadar", "günü saat 23.59'a kadar") and takes "lira" with its Turkish endings
  ("liradan", "lirası"); it was run with `redo.py --keep-reviews`, which keeps every review already made and sends only the
  strong flags not yet reviewed to the model: lapsed time limits went to 4,091 (115 reviewed, the same 4 surviving) and dead
  currencies from 1,293 before the fixes to 1,604. The other categories did not change.
- A fifth round fixed the sharded scans, which had split the acts between processes by Python's `hash()`, different in
  each process, so that some acts were read twice and others not at all (now a stable checksum), and breaks ties on score
  in a fixed order. A last `redo.py --keep-reviews` pass left the flags as they were and reviewed 41 more lapsed time limits
  that tied with the 40 strongest (156 in all; 8 survived, the 4 new ones checked by hand).
