# Reproducing this repository

Built on {{TODAY}} from the mevzuat.gov.tr answers retrieved on {{RETRIEVED}} (UTC), by the scripts in `tools/build/` (copied there as run). The scripts live in the Lexifina repository at `scripts/turkey-law/`.

| Script | sha256 |
| --- | --- |
| build.py | `{{SHA_BUILD_PY}}` |
| docs.py | `{{SHA_DOCS_PY}}` |
| check_repo.py | `{{SHA_CHECK_REPO_PY}}` |
| history.py | `{{SHA_HISTORY_PY}}` |
| convert_doc.ps1 | `{{SHA_CONVERT_DOC_PS1}}` |

Tools: Python 3.12 (standard library only), git 2.46, Microsoft Word (Microsoft 365, Office16) driven from Windows PowerShell 5.1 over COM to convert the earlier texts. [`data/source-sha256.tsv`](data/source-sha256.tsv) has the sha256 of every retrieved file the build read.

## Steps

```sh
# 1. The retrieved files: the act lists (3 kinds), each act's text and the "Onceki metinler" lists (see SOURCES.md).
# 2. The earlier texts themselves, as .doc files. data/source-sha256.tsv lists every file the build read.
# 3. Convert each .doc with Microsoft Word: Word HTML (the format the site serves) and Word's plain text.
#    Two invisible Word instances were run, one with -Reverse; finished files are skipped.
powershell -NoProfile -ExecutionPolicy Bypass -File convert_doc.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File convert_doc.ps1 -Reverse
# 4. Build. --today is the latest date allowed and is recorded as corpus.json "built"; commit dates come from
#    the data. The target must be empty or an earlier build of this repository.
python -X utf8 build.py ../turkey-law --today {{TODAY}}
# 5. Check every current text against the site's HTML and every earlier version against Word's text of its .doc.
python -X utf8 check_repo.py ../turkey-law
# 6. Global preflight.
python scripts/global-law/check_corpus.py ../turkey-law
```

## Terms

See [`SOURCES.md`](SOURCES.md): the legal basis for reuse is FSEK (Law No. 5846) art. 31. The terms notice named in the footer was not found, so it was not read. There is no bulk download.

## What the build produced

- {{BUILT}} acts of {{ACTS}} listed: {{KANUN}} laws, {{OSMANLI}} Ottoman-era laws, {{KHK}} decree-laws, {{CBK}} presidential decrees; {{ARTICLES}} article files in the current texts, {{FOOTNOTES}} footnotes.
- History for {{HISTORY_LAWS}} laws: {{OLD_VERSIONS}} earlier versions plus their current texts, from {{FIRST_VERSION}} (`data/versions.csv`, one tag each). {{CURRENT_ONLY}} acts are current-only.
- {{COMMITS}} commits on `main`: {{BASELINE_COMMITS}} first texts, {{AMENDMENT_COMMITS}} amendment commits ({{CREDITED_FILES}} file changes credited), {{UNEXPLAINED_COMMITS}} unexplained ({{UNEXPLAINED_FILES}} file changes), {{EDITORIAL_COMMITS}} editorial, {{CONSOLIDATED}} current texts, and one documentation commit. {{FUTURE_COMMITS}} commits on `future`.
- {{NOTES}} amendment notes naming {{AMENDING_LAWS}} distinct amending acts (`data/amendments.csv`); {{INFORCE_ROWS}} in-force-table rows from {{INFORCE_ACTS}} acts (`data/in-force-list.csv`).
- {{UNREADABLE}} rows in `data/unreadable.csv`.

## Decisions made by hand

- Earlier texts: the `.doc` files, not the PDFs. Word itself opens them and saves the same "Word filtered HTML" the site serves for current texts, so one parser reads both, and typesetting differences between versions stay small. The PDFs (same content) were not used. Word ran invisible with macros disabled, was quit through COM after every 40 files and never killed.
- An earlier text's first line names its version ("Kanunun ilk hali", "6525 sayılı Kanun ile değişik hali"); it is kept out of the files and recorded in `data/versions.csv`.
- Versions run in the order of their file dates; each is dated by the latest in-force-table date of its act(s), or by the act's Resmî Gazete date when no table lists it. A version date earlier than the one before it is moved up to it (`date_note` in `data/versions.csv`).
- Crediting (history.py): a changed article goes to the one act named by amendment notes newly present in it; if no note was added, to the version's act when its in-force-table row lists the article; otherwise it is labelled unexplained. Its date is the act's in-force-table date (for that article where the table gives several); it must fall between the two versions' dates, or the change is labelled. Typesetting-only changes (whitespace, dash and quote variants, footnote numbers, underscore rules, lines moved between files) are editorial.
- Headings are recognised by their text (short, no closing punctuation, not a list item), because older Word files do not mark them bold.

- Scope: law-rank acts in force (Kanun, including the Ottoman-era laws the site lists among them; KHK; Cumhurbaşkanlığı Kararnamesi). Regulations, by-laws and repealed laws are left out.
- The Constitution's page (`1.5.2709`) is the copy retrieved while the source was being examined; it is the same page as every other act's.
- The publisher's appendices ("İŞLENEMEYEN HÜKÜMLER", "YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE") are recognised by their all-capital headings and cut off before articles are split, so the amending acts' articles they quote do not become articles; 3-column rows ending in a date go to data/in-force-list.csv.
- Ottoman-era (Rumi/Hijri) dates, years before 1800, are not converted.
- One commit per act, dated by the retrieval day, because the source publishes current text only (corpus.json `history: "current-only"`). The publisher, not a law, is the author.
- Split at paragraphs that start with an article heading (`Madde 21 –`, `MADDE 4/A-`, `Geçici Madde 1 –`, `Ek Madde 3 –`, `Mükerrer Madde`, Ottoman-era `Muvakkat Madde` = `gecici-madde`), never inside an open “quotation”. Heading-only paragraphs (all bold/italic, under 200 characters, at most 6) right before an article move into that article's file.
- Text kept as published: whitespace collapsed, soft hyphens and zero-width characters dropped, nothing else changed. Footnote markers (`[12]`) stay in the text; the footnotes go to `dipnotlar.md`.
- Commit times are noon UTC+3 (Turkey has kept UTC+3 all year since 7 September 2016).
- The documentation commit is dated by the retrieval day, not the run day, so a rebuild on another day gives the same hashes.

## Checks

{{CHECK}}

```sh
git rev-list --merges --count main      # 0
python tools/in_force_on.py {{RETRIEVED}} kanun/2709 madde-21
```

Two builds from the same retrieved files give the same `git rev-parse HEAD`.

## What AI did and did not do

The scripts, documentation and checks were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`), following Lexifina's shared rules for these repositories. No AI model wrote or changed any legal text, and no model runs during fetching, converting, building or checking: the text is the publisher's, converted by Microsoft Word and split by fixed rules.
