# The laws of Türkiye, as a git repository

The law-rank legislation of Türkiye in force, as a git repository: {{KANUN}} laws (Kanunlar, including the Constitution, `kanun/2709`, and the codes, such as the Türk Medeni Kanunu `kanun/4721`, Türk Borçlar Kanunu `kanun/6098` and Türk Ceza Kanunu `kanun/5237`), {{OSMANLI}} Ottoman-era laws still in force (`osmanli/`), {{KHK}} decree-laws (Kanun Hükmünde Kararnameler, `khk/`) and {{CBK}} presidential decrees (Cumhurbaşkanlığı Kararnameleri, `cbk/`). The source is the official [Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr), run by the Presidency's Directorate General of Law and Legislation (T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü). Every article is one file ({{ARTICLES}} article files), with one paragraph per line, so `git blame` and `git diff` work line by line. The text is Turkish, exactly as published.

**History for {{HISTORY_LAWS}} laws; the current text only for the rest.** For {{HISTORY_LAWS}} laws, including the Constitution (`kanun/2709`, from its 1982 text), the publisher keeps earlier consolidated texts ("Önceki metinler", Word files). Each is a version here: {{OLD_VERSIONS}} earlier versions plus the current text, from {{FIRST_VERSION}}. Between two versions, every changed article is credited to the amending act that made the change, on the day it entered into force, or labelled when that cannot be told (see below). The list is [`data/history-laws.csv`](data/history-laws.csv), and every version is tagged (`git tag -l 'kanun/2709/*'`) and listed in [`data/versions.csv`](data/versions.csv). The other {{CURRENT_ONLY}} acts have one commit each: their current text as published on {{RETRIEVED}}, with no history before that day. For every act, the publisher's amendment notes such as `(Değişik: 3/10/2001-4709/6 md.)` (changed by Law 4709, art. 6, of 3 October 2001) stay in the text and are listed in [`data/amendments.csv`](data/amendments.csv) ({{NOTES}} notes naming {{AMENDING_LAWS}} amending acts); the footnotes are in each act's `dipnotlar.md`.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What does Article 21 of the Constitution say today? | `python tools/in_force_on.py {{RETRIEVED}} kanun/2709 madde-21` |
| What did it say on 1 January 2000? | `python tools/in_force_on.py 2000-01-01 kanun/2709 madde-21` |
| Which acts changed it, and when did each take effect? | `git log --format='%(trailers:key=In-force,valueonly,separator=) %an' -- kanun/2709/madde-21.md` |
| What exactly did an amendment change? | `git log -p --word-diff --author='Kanun 4709' -- kanun/2709` |
| Which act wrote each line of an article? | `git blame kanun/2709/madde-21.md` |
| Everything one amending act changed, in every law (here Law 6525) | `git log --stat --author='Kanun 6525'` |
| The whole of an act, in order, on a date | `python tools/in_force_on.py 2010-01-01 kanun/2547` |
| The publisher's versions of an act | `git tag -l 'kanun/2709/*'` |
| Which laws have history | [`data/history-laws.csv`](data/history-laws.csv) |
| Every article an amending act's notes name (all acts) | `grep ',6771,' data/amendments.csv` |
| When each amending act entered into force, per act | `grep '^kanun/5237,' data/in-force-list.csv` |
| Which acts cite the Türk Ceza Kanunu | `git grep -l '5237 sayılı'` |
| The list of acts, with their dates and Gazette numbers | [`laws.csv`](laws.csv) |

Files: `<kind>/<number>/` per act. `baslangic.md` holds the title, the numbers (Kanun Numarası, Kabul Tarihi, Resmî Gazete, Düstur) and anything before the first article. Articles are named after their heading: `madde-21.md` (Madde 21), `madde-4a.md` (Madde 4/A), `ek-madde-3.md` (Ek Madde 3), `gecici-madde-1.md` (Geçici Madde 1), `ek-gecici-madde-2.md`. Section headings (KISIM, BÖLÜM) and marginal article titles that stand right before an article are the first lines of its file. Ottoman-era acts numbered by `Bend` have `bend-21.md`. A heading that occurs twice in one act gets `~2`, `~3`. The publisher's appendices after an act are files of their own: `islenemeyen-hukumler.md` ("... KANUNA İŞLENEMEYEN HÜKÜMLER", provisions of amending acts that could not be worked into the text) and `yururluk-listesi.md` ("... YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE", when each amending act or Constitutional Court annulment entered into force). Annexed schedules (cetveller) that follow the last article stay in that article's file. Acts of law number used in two Düstur series (tertip) keep the plain number for the newer one and `-t3` for the older one. `dipnotlar.md` holds the publisher's footnotes, one per line, and `index.txt` gives the reading order. Table rows are one line with cells joined by ` | `.

## The dates, and which one we use

**Amendments are dated by the day they entered into force**, at noon Turkey time (UTC+3 since 7 September 2016; UTC+2 with summer time before), in the `In-force:` trailer and as the commit date. The date comes from the publisher's own in-force table at the end of each act ("... YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE": amending act | articles | in-force date), from the newest text that lists the act; where the table gives several dates for one act, the row that names the article is used (`Date-source: in-force-table`). Where the table names a day from which the change applies before it entered into force ("1/1/2008 tarihinden geçerli olmak üzere 8/5/2008"), that day is an `Applies-from:` trailer. A version whose act is not in any table is dated by the act's Resmî Gazete date (`Date-source: published`), and so is a law's own first text ("Kanunun ilk hali"). Dates before 1970 are clamped to 1970-01-01 in git; the real date is in `In-force:`. The dates inside amendment notes (`7/5/2010-5982/2 md.`) are adoption dates and are never used as in-force dates. {{INFORCE_ACTS}} acts carry the in-force table ({{INFORCE_ROWS}} rows in [`data/in-force-list.csv`](data/in-force-list.csv)).

Acts without history are dated {{RETRIEVED}}, the day the text was retrieved: the text in force that day according to the publisher. Each act's first commit also carries `Enacted:` (kabul tarihi), `Published:` (Resmî Gazete date) and `Gazette:`.

`tools/in_force_on.py DATE PATH [ARTICLE]` reads the `In-force:` trailers, so it does not depend on your time zone (unlike `git rev-list --before`). Before an act's first version it says there is no version. Changes whose in-force date is after {{RETRIEVED}} are on the `future` branch ({{FUTURE_COMMITS}} commits), never on `main`.

## What "author" means

- **An amending act** (`Kanun 6525 (...) <kanun-6525@mevzuat-gov-tr.invalid>`, `KHK 666`, `Anayasa Mahkemesi K. 2013/43`; the addresses cannot exist), `Kind: amendment`: the article changed between two of the publisher's texts, and exactly one act explains it, because a new amendment note in that article names the act, or (where no note was added) the act's in-force-table row lists the article. `Evidence:` says which, for each file. {{AMENDMENT_COMMITS}} commits, {{CREDITED_FILES}} file changes.
- **The publisher** (`Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı)`), `Kind: unexplained`: a change that no act, or more than one, explains, or whose act has no usable in-force date in its step. These are labelled and never credited; `Candidate:` names the possible acts and `Reason:` says why. Many are the publisher's own corrections and errors between texts (a changed word with no note), and the last step, from the newest earlier text to the current one, often covers several acts at once. {{UNEXPLAINED_COMMITS}} commits, {{UNEXPLAINED_FILES}} file changes.
- **The publisher**, `Kind: editorial`: typesetting only (spaces, dashes, quotation marks, footnote numbers, a heading moved to the next article) and the publisher's apparatus (footnotes, in-force list, provisions not worked in). No words of law change. {{EDITORIAL_COMMITS}} commits.
- **A law's first text**: authored by the law itself (`Kind: enacted`) when the publisher's earliest text is the law as first published, otherwise by the publisher (`Kind: consolidated`, with `Consolidated-by:`). {{BASELINE_COMMITS}} commits.
- **The current text of an act without history**: the publisher, `Kind: consolidated`. {{CONSOLIDATED}} commits.

One commit is one amending act on one in-force day, across all the laws it changed. Blame credits whole paragraphs; use `git log -p --word-diff` for the words.

## What it does not show

- History for the acts without earlier texts ({{CURRENT_ONLY}} acts): nothing before {{RETRIEVED}}.
- Steps the publisher did not keep: two versions can be several acts apart, and then changes that more than one act could explain are labelled, not credited.
- Regulations (yönetmelikler), by-laws (tüzükler), communiqués and presidential decisions; repealed laws (mülga kanunlar).
- Ottoman-era dates (Rumi or Hijri calendar) are not converted: those commits carry `Enacted-as-printed:` and `Published-as-printed:` instead of `Enacted:` and `Published:`.
- Pictures, and formatting (bold, italics, indentation). A Symbol-font character appears as its font code (for example `²` for ″), as on the site.
- Texts that could not be read ({{UNREADABLE}} rows in [`data/unreadable.csv`](data/unreadable.csv)).

This is a research aid. The authoritative text is the one published in the Resmî Gazete.

## How it is checked

Before publishing, `tools/build/check_repo.py` read every act back from git and compared it:
- the current text of every act, word for word, with the HTML the site served (text joined with spaces at block boundaries only);
- every earlier version, at its tag, with Microsoft Word's own plain text of the source `.doc` (body and footnotes, read through Word, not through the HTML the build used). Footnote markers are left out on both sides. Word's HTML drops a few tabs after list numbers, so those versions match character for character but not word for word; the count is given;
- every commit's trailers parse with `git interpret-trailers`; there are no merges, no dates that go backwards and no dates after the build day on `main`; `tools/in_force_on.py` gives the right article for sample paths; two builds from the same cache give the same HEAD.

The results are in [`REPRODUCE.md`](REPRODUCE.md).

## How it is built

`fetch.py` reads the site's own search table (`/Anasayfa/MevzuatDatatable`), the text of each act (`/anasayfa/MevzuatFihristDetayIframe`, the Word-generated HTML the site shows), the list of earlier texts where there is one (`/EskiKanunlar/EskiKanunlarList`), and those earlier texts as `.doc` files (`/MevzuatMetin/<...>.doc`). `convert_doc.ps1` opens each `.doc` in Microsoft Word and saves it as the same kind of Word HTML the site serves, plus Word's plain text for the check. `build.py` splits each text at its article headings (ignoring headings inside quotation marks), `history.py` compares consecutive versions and credits or labels each change, and one `git fast-import` stream writes it all. No AI model takes part in building or checking it. See [`REPRODUCE.md`](REPRODUCE.md) and [`SOURCES.md`](SOURCES.md).

## Licence

Source: Mevzuat Bilgi Sistemi, https://www.mevzuat.gov.tr, T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü. Officially published laws are free to use in Türkiye: Fikir ve Sanat Eserleri Kanunu (Law No. 5846, FSEK) article 31, as published on mevzuat.gov.tr (`kanun/5846/madde-31.md`), reads: "Resmen yayımlanan veya ilan olunan kanun, Cumhurbaşkanlığı kararnamesi, yönetmelik, tebliğ, genelge ve kazai kararların çoğaltılması, yayılması, işlenmesi veya her hangi bir suretle bunlardan faydalanma serbesttir." (The reproduction, distribution, adaptation or any other use of officially published or announced laws, presidential decrees, regulations, communiqués, circulars and judicial decisions is free.) The site's footer reads "Tüm Hakları Saklıdır" (all rights reserved) and refers to a privacy, use and copyright notice. That notice could not be reached on {{RETRIEVED}} (the address redirects to the Presidency's home page), so its terms were not read. The footer cannot take away the free use FSEK art. 31 gives to the legal text itself; it may cover the site's own material (design, software, editorial notes). The site's own description says the service is offered free of charge and without conditions ("ücretsiz ve koşulsuz olarak herkesin kullanımına sunulmuştur"). The wording was not changed; it was only split into files and lines. **This repository is private.** Lexifina's own contributions (the tools, the arrangement and the commit messages) are CC0. See [`LICENSE`](LICENSE).
