# Reproducing this repository

Built on 2026-10-28 from the mevzuat.gov.tr answers retrieved on 2026-10-28 (UTC), by the scripts in `tools/build/` (copied there as run). The scripts live in the Lexifina repository at `scripts/turkey-law/`.

| Script | sha256 |
| --- | --- |
| fetch.py | `0c41ab43d2bb5680f5deb8c81be37c4ef192c79db19b5ad91e5f489bf710e676` |
| build.py | `56beddfdd5712ed1a2a588c398cd5a8d4db74968fbb7918d89ea90d9070faeff` |
| docs.py | `35f70361b3a907ef46889ccc931f440da5afba6f0cf51dff87aa99255fb9f601` |
| check_repo.py | `004d8f1f2b4245d510782a278607a0e63f6e8b71d694e066b79938f6481058c6` |

Tools: Python 3.12 (standard library only), curl 8 (Windows), git 2.46. [`data/source-sha256.tsv`](data/source-sha256.tsv) has the sha256 of every cached answer the build read.

## Steps

```sh
# 1. The act lists (3 kinds, 100 rows a request, 2.1 s apart), each act's text (one request each, 3 at a time,
#    0.5 s apart per worker) and the "Onceki metinler" lists. Resumable; every answer is cached, misses too.
python -X utf8 fetch.py
# 2. Build. --today dates nothing in the history (every commit is dated by the retrieval day); it is the latest
#    date allowed and is recorded as corpus.json "built". The target must be empty or an earlier build.
python -X utf8 build.py ../turkey-law --today 2026-10-28
# 3. Check: every act read back from git equals the site's text word for word.
python -X utf8 check_repo.py ../turkey-law
# 4. Global preflight.
python scripts/global-law/check_corpus.py ../turkey-law
```

## robots.txt, terms and fetch rate

See [`SOURCES.md`](SOURCES.md): robots.txt has no rules for us (Googlebot `Noindex:` lines only, no Crawl-delay, no AI-agent rules); the terms notice named in the footer could not be reached, so it was not read; the legal basis for reuse is FSEK (Law No. 5846) art. 31. There is no bulk download. `fetch.py` used curl with `--compressed` (gzip) and a User-Agent naming Lexifina, at most 3 requests at a time, 0.5 s apart per worker; the search table was asked 2.1 s apart, as the site's own form waits 2 s. 1307 requests in all, logged in `.cache/requests.log`.

## What the build produced

- 1013 acts of 1013 listed: 908 laws, 9 Ottoman-era laws, 63 decree-laws, 33 presidential decrees; 36860 article files, 13014 footnotes.
- 1014 commits: 1013 consolidated (one per act, all dated 2026-10-28 at 12:00 +0300) and one documentation commit.
- 20188 amendment notes naming 1547 distinct amending acts (`data/amendments.csv`).
- 0 rows in `data/unreadable.csv` (acts not served, or with no article headings found).

## Decisions made by hand

- Scope: law-rank acts in force (Kanun, including the Ottoman-era laws the site lists among them; KHK; Cumhurbaşkanlığı Kararnamesi). Regulations, by-laws and repealed laws are left out.
- The Constitution's page (`1.5.2709`) was first fetched by hand with the same request while the source was being examined, and that copy was used; every other act was fetched by `fetch.py`.
- The publisher's appendices ("İŞLENEMEYEN HÜKÜMLER", "YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE") are recognised by their all-capital headings and cut off before articles are split, so the amending acts' articles they quote do not become articles; 3-column rows ending in a date go to data/in-force-list.csv.
- Ottoman-era (Rumi/Hijri) dates, years before 1800, are not converted.
- One commit per act, dated by the retrieval day, because the source publishes current text only (corpus.json `history: "current-only"`). The publisher, not a law, is the author.
- Split at paragraphs that start with an article heading (`Madde 21 –`, `MADDE 4/A-`, `Geçici Madde 1 –`, `Ek Madde 3 –`, `Mükerrer Madde`, Ottoman-era `Muvakkat Madde` = `gecici-madde`), never inside an open “quotation”. Heading-only paragraphs (all bold/italic, under 200 characters, at most 6) right before an article move into that article's file.
- Text kept as published: whitespace collapsed, soft hyphens and zero-width characters dropped, nothing else changed. Footnote markers (`[12]`) stay in the text; the footnotes go to `dipnotlar.md`.
- Commit times are noon UTC+3 (Turkey has kept UTC+3 all year since 7 September 2016).
- The documentation commit is dated by the retrieval day, not the run day, so a rebuild on another day gives the same hashes.

## Checks

check_repo.py on the previous identical-input build: 1013 acts read back from git, 4565058 words compared with the site's HTML, 0 mismatches; 1014 commits, 0 with unparseable trailers; tool samples 8/8 right.

```sh
git rev-list --merges --count main      # 0
python tools/in_force_on.py 2026-10-28 kanun/2709 madde-21
```

Two builds from the same cache give the same `git rev-parse HEAD`.

## What AI did and did not do

The scripts, documentation and checks were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`), following Lexifina's shared rules for these repositories. No AI model wrote or changed any legal text, and no model runs during fetching, building or checking: the text is the publisher's, split by fixed rules.
