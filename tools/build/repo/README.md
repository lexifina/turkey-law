# The laws of Türkiye, as a git repository

The law-rank legislation of Türkiye in force, as a git repository: {{KANUN}} laws (Kanunlar, including the Constitution, `kanun/2709`, and the codes, such as the Türk Medeni Kanunu `kanun/4721`, Türk Borçlar Kanunu `kanun/6098` and Türk Ceza Kanunu `kanun/5237`), {{OSMANLI}} Ottoman-era laws still in force (`osmanli/`), {{KHK}} decree-laws (Kanun Hükmünde Kararnameler, `khk/`) and {{CBK}} presidential decrees (Cumhurbaşkanlığı Kararnameleri, `cbk/`). The source is the official [Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr), run by the Presidency's Directorate General of Law and Legislation (T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü). Every article is one file ({{ARTICLES}} article files), with one paragraph per line, so `git blame` and `git diff` work line by line. The text is Turkish, exactly as published.

**This is not a history, and there is no line-by-line history before {{RETRIEVED}}.** mevzuat.gov.tr publishes the current consolidated text of each act. Each act is therefore one commit holding its whole current text, as published on {{RETRIEVED}}. Nothing earlier can be rebuilt from that text. Later builds will add new commits when the text changes, so the history grows forward from that date. What the publisher records about the past stays in the text: every amendment note such as `(Değişik: 3/10/2001-4709/6 md.)` (changed by Law 4709, art. 6, of 3 October 2001) is kept where it stands and listed in [`data/amendments.csv`](data/amendments.csv) ({{NOTES}} notes naming {{AMENDING_LAWS}} amending acts), and the footnotes are in each act's `dipnotlar.md`.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What does Article 21 of the Constitution say? | `python tools/in_force_on.py {{RETRIEVED}} kanun/2709 madde-21` |
| The whole of an act, in order | `python tools/in_force_on.py {{RETRIEVED}} kanun/5237` |
| Which acts changed an article, and when they were adopted | `grep '^kanun/2709,madde-21,' data/amendments.csv` |
| Every article an amending act touched (here Law 6771) | `grep ',6771,' data/amendments.csv` |
| Temporary articles (geçici maddeler) of an act | `ls kanun/2709/gecici-madde-*` |
| Which acts cite the Türk Ceza Kanunu | `git grep -l '5237 sayılı'` |
| What changed in an act since this build (after later builds) | `git log -p --word-diff -- kanun/2709` |
| The list of acts, with their dates and Gazette numbers | [`laws.csv`](laws.csv) |
| When each amending act entered into force, per act | `grep '^kanun/5237,' data/in-force-list.csv` |
| Earlier consolidated texts the site offers as files | [`data/previous-texts.csv`](data/previous-texts.csv) |

Files: `<kind>/<number>/` per act. `baslangic.md` holds the title, the numbers (Kanun Numarası, Kabul Tarihi, Resmî Gazete, Düstur) and anything before the first article. Articles are named after their heading: `madde-21.md` (Madde 21), `madde-4a.md` (Madde 4/A), `ek-madde-3.md` (Ek Madde 3), `gecici-madde-1.md` (Geçici Madde 1), `ek-gecici-madde-2.md`. Section headings (KISIM, BÖLÜM) and marginal article titles that stand right before an article are the first lines of its file. Ottoman-era acts numbered by `Bend` have `bend-21.md`. A heading that occurs twice in one act gets `~2`, `~3`. The publisher's appendices after an act are files of their own: `islenemeyen-hukumler.md` ("... KANUNA İŞLENEMEYEN HÜKÜMLER", provisions of amending acts that could not be worked into the text) and `yururluk-listesi.md` ("... YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE", when each amending act or Constitutional Court annulment entered into force). Annexed schedules (cetveller) that follow the last article stay in that article's file. Acts of law number used in two Düstur series (tertip) keep the plain number for the newer one and `-t3` for the older one. `dipnotlar.md` holds the publisher's footnotes, one per line, and `index.txt` gives the reading order. Table rows are one line with cells joined by ` | `.

## The dates, and which one we use

Every act commit is dated {{RETRIEVED}}, the day its text was retrieved, at noon Turkey time (UTC+3). That date is also the `In-force:` and `Consolidated:` trailer: the text is the one in force that day according to the publisher. It is not the day any provision took effect. Each commit also carries `Enacted:` (kabul tarihi), `Published:` (Resmî Gazete date) and `Gazette:` (its issue number) for the act itself. The dates in the amendment notes are the adoption dates of the amending acts (`7/5/2010-5982/2 md.` = Law 5982 of 7 May 2010, article 2), not their entry-into-force dates. [`data/amendments.csv`](data/amendments.csv) keeps them as adoption dates. {{INFORCE_ACTS}} acts end with the publisher's own list of when each amending act entered into force (`yururluk-listesi.md`); its {{INFORCE_ROWS}} rows are also in [`data/in-force-list.csv`](data/in-force-list.csv) (act, amending act or court decision, articles, in-force date). Those are the publisher's entry-into-force dates; they are not used to date commits here, because the text before each change is not published.

`tools/in_force_on.py DATE PATH [ARTICLE]` reads the `In-force:` trailers. It answers for {{RETRIEVED}} and later. For earlier dates it says there is no version, because the source has none here. Query by trailer, not by `git rev-list --before`, which depends on your time zone.

## What "author" means

Every act commit has the same author: `Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı) <mevzuat@mevzuat-gov-tr.invalid>`, with `Kind: consolidated`. The address cannot exist. The author is the publisher of the consolidation, not a lawmaker. No line is credited to an amending act, because without the earlier text nobody can tell which words an amendment wrote. In the shared design for these repositories, a change is credited to an amending act only when the source shows the text before and after it. When a later build finds a changed text, the change will be credited to an act only where a new amendment note names one; otherwise it is labelled `Kind: unexplained` and authored by the publisher.

There are {{CONSOLIDATED}} consolidated commits and one documentation commit.

## What it does not show

- Any text before {{RETRIEVED}}. For {{PREVIOUS_TEXT_ACTS}} laws the site also offers earlier consolidated texts as Word/PDF files ("Önceki metinler", {{PREVIOUS_TEXTS}} files). They are listed in [`data/previous-texts.csv`](data/previous-texts.csv) but not built into history yet.
- Provisions adopted but not yet in force are printed in the current text where the publisher prints them; they cannot be separated, so there is no `future` branch.
- Regulations (yönetmelikler), by-laws (tüzükler), communiqués and presidential decisions; repealed laws (mülga kanunlar).
- Ottoman-era dates (Rumi or Hijri calendar) are not converted: those commits carry `Enacted-as-printed:` and `Published-as-printed:` instead of `Enacted:` and `Published:`.
- Pictures, and formatting (bold, italics, indentation). Amendment notes are bold in the source and plain text here.
- Acts the site would not serve, or with no recognisable article headings ({{UNREADABLE}} rows in [`data/unreadable.csv`](data/unreadable.csv); the latter would be kept whole in `metin.md`).

This is a research aid. The authoritative text is the one published in the Resmî Gazete.

## How it is checked

Before publishing, `tools/build/check_repo.py` read every act back from git and compared it word for word with the HTML the site served (joining text with spaces at block boundaries only): every word, in order, nothing added or dropped. Also checked: every commit's trailers parse with `git interpret-trailers`; there are no merges, no dates that go backwards and no dates after the build date; `tools/in_force_on.py` gives the right article for sample paths; and two builds from the same cache give the same HEAD. The results are in [`REPRODUCE.md`](REPRODUCE.md).

## How it is built

`fetch.py` reads the site's own search table (`/Anasayfa/MevzuatDatatable`, the list of every act in force by kind), then the text of each act (`/anasayfa/MevzuatFihristDetayIframe`, the Word-generated HTML the site shows), and the list of earlier texts where there is one (`/EskiKanunlar/EskiKanunlarList`). `build.py` splits each act at its article headings, ignoring headings inside quotation marks (an amending act quoting another act), and writes one commit per act with `git fast-import`. No AI model takes part in building or checking it. See [`REPRODUCE.md`](REPRODUCE.md) and [`SOURCES.md`](SOURCES.md).

## Licence

Source: Mevzuat Bilgi Sistemi, https://www.mevzuat.gov.tr, T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü. Officially published laws are free to use in Türkiye: Fikir ve Sanat Eserleri Kanunu (Law No. 5846, FSEK) article 31, as published on mevzuat.gov.tr (`kanun/5846/madde-31.md`), reads: "Resmen yayımlanan veya ilan olunan kanun, Cumhurbaşkanlığı kararnamesi, yönetmelik, tebliğ, genelge ve kazai kararların çoğaltılması, yayılması, işlenmesi veya her hangi bir suretle bunlardan faydalanma serbesttir." (The reproduction, distribution, adaptation or any other use of officially published or announced laws, presidential decrees, regulations, communiqués, circulars and judicial decisions is free.) The site's footer reads "Tüm Hakları Saklıdır" (all rights reserved) and refers to a privacy, use and copyright notice. That notice could not be reached on {{RETRIEVED}} (the address redirects to the Presidency's home page), so its terms were not read. The footer cannot take away the free use FSEK art. 31 gives to the legal text itself; it may cover the site's own material (design, software, editorial notes). The site's own description says the service is offered free of charge and without conditions ("ücretsiz ve koşulsuz olarak herkesin kullanımına sunulmuştur"). The wording was not changed; it was only split into files and lines. **This repository is private.** Lexifina's own contributions (the tools, the arrangement and the commit messages) are CC0. See [`LICENSE`](LICENSE).
