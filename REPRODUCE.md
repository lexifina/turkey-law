# Reproducing this repository

Built on 2026-10-28 from the mevzuat.gov.tr answers retrieved on 2026-10-28 (UTC), by the scripts in `tools/build/` (copied there as run). The scripts live in the Lexifina repository at `scripts/turkey-law/`.

| Script | sha256 |
| --- | --- |
| fetch.py | `56f9abfabaf14f5f7b70b0a02396f32395d18f0d8725b8d17619836f86c795ab` |
| build.py | `a3136e73beaff2059b41a8f3fdffc71cadb6e07c48fb4b83c1c11b614a4349be` |
| docs.py | `0ecd6e0ce5ecf9452601e722cbddec58c86f50d13d974ddd4cd379ba06d48238` |
| check_repo.py | `39780d6dcb95936eb2c0dc942668497fb7464c252bc203b51c78c8b292b9a249` |
| history.py | `71d13fa5b72e4e4dfb86372bf55439dd6f3326054de764f8c9e7a3b0094789bd` |
| convert_doc.ps1 | `409b17379ebc1389f81b103f1142e1181bbfe010164e9c840ebfcb7b674aa923` |

Tools: Python 3.12 (standard library only), curl 8 (Windows), git 2.46, Microsoft Word (Microsoft 365, Office16) driven from Windows PowerShell 5.1 over COM to convert the earlier texts. [`data/source-sha256.tsv`](data/source-sha256.tsv) has the sha256 of every cached answer the build read.

## Steps

```sh
# 1. The act lists (3 kinds, 100 rows a request, 2.1 s apart), each act's text (one request each, 3 at a time,
#    0.5 s apart per worker) and the "Onceki metinler" lists. Resumable; every answer is cached, misses too.
python -X utf8 fetch.py
# 2. The earlier texts themselves, as .doc files (same rate).
python -X utf8 fetch.py --old-texts
# 3. Convert each .doc with Microsoft Word: Word HTML (the format the site serves) and Word's plain text.
#    Two invisible Word instances were run, one with -Reverse; finished files are skipped.
powershell -NoProfile -ExecutionPolicy Bypass -File convert_doc.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File convert_doc.ps1 -Reverse
# 4. Build. --today is the latest date allowed and is recorded as corpus.json "built"; commit dates come from
#    the data. The target must be empty or an earlier build of this repository.
python -X utf8 build.py ../turkey-law --today 2026-10-28
# 5. Check every current text against the site's HTML and every earlier version against Word's text of its .doc.
python -X utf8 check_repo.py ../turkey-law
# 6. Global preflight.
python scripts/global-law/check_corpus.py ../turkey-law
```

## robots.txt, terms and fetch rate

See [`SOURCES.md`](SOURCES.md): robots.txt has no rules for us (Googlebot `Noindex:` lines only, no Crawl-delay, no AI-agent rules); the terms notice named in the footer could not be reached, so it was not read; the legal basis for reuse is FSEK (Law No. 5846) art. 31. There is no bulk download. `fetch.py` used curl with `--compressed` (gzip) and a User-Agent naming Lexifina, at most 3 requests at a time, 0.5 s apart per worker; the search table was asked 2.1 s apart, as the site's own form waits 2 s. 2492 requests in all, logged in `.cache/requests.log`.

## What the build produced

- 1013 acts of 1013 listed: 908 laws, 9 Ottoman-era laws, 63 decree-laws, 33 presidential decrees; 36955 article files in the current texts, 13014 footnotes.
- History for 280 laws: 1187 earlier versions plus their current texts, from 1947-05-14 (`data/versions.csv`, one tag each). 733 acts are current-only.
- 2362 commits on `main`: 280 first texts, 658 amendment commits (4804 file changes credited), 303 unexplained (13517 file changes), 387 editorial, 733 current texts, and one documentation commit. 1 commits on `future`.
- 20203 amendment notes naming 1551 distinct amending acts (`data/amendments.csv`); 8721 in-force-table rows from 717 acts (`data/in-force-list.csv`).
- 0 rows in `data/unreadable.csv`.

## Decisions made by hand

- Earlier texts: the `.doc` files, not the PDFs. Word itself opens them and saves the same "Word filtered HTML" the site serves for current texts, so one parser reads both, and typesetting differences between versions stay small. The PDFs (same content) were not used. Word ran invisible with macros disabled, was quit through COM after every 40 files and never killed.
- An earlier text's first line names its version ("Kanunun ilk hali", "6525 sayılı Kanun ile değişik hali"); it is kept out of the files and recorded in `data/versions.csv`.
- Versions run in the order of their file dates; each is dated by the latest in-force-table date of its act(s), or by the act's Resmî Gazete date when no table lists it. A version date earlier than the one before it is moved up to it (`date_note` in `data/versions.csv`).
- Crediting (history.py): a changed article goes to the one act named by amendment notes newly present in it; if no note was added, to the version's act when its in-force-table row lists the article; otherwise it is labelled unexplained. Its date is the act's in-force-table date (for that article where the table gives several); it must fall between the two versions' dates, or the change is labelled. Typesetting-only changes (whitespace, dash and quote variants, footnote numbers, underscore rules, lines moved between files) are editorial.
- Headings are recognised by their text (short, no closing punctuation, not a list item), because older Word files do not mark them bold.

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

check_repo.py on the previous identical-input build: 1013 current texts read back from git, 4565058 words compared with the site's HTML, 0 mismatches; 1187 earlier versions read back at their tags, 15417930 words compared with Word's own text of each .doc, 0 mismatches in the characters (18 differ only in letter case, from Word's All caps formatting, and 8 only in where words break, from tabs Word leaves out of its HTML); 2362 commits, 0 with unparseable trailers, 0 backwards, 0 after the build day on main, 0 merges; tool samples 43/43 right.

```sh
git rev-list --merges --count main      # 0
python tools/in_force_on.py 2026-10-28 kanun/2709 madde-21
```

Two builds from the same cache give the same `git rev-parse HEAD`.

## What AI did and did not do

The scripts, documentation and checks were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`), following Lexifina's shared rules for these repositories. No AI model wrote or changed any legal text, and no model runs during fetching, converting, building or checking: the text is the publisher's, converted by Microsoft Word and split by fixed rules.
