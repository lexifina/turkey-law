# Vulnerabilities in Turkish law

[Türkçe](README.md) · **English**

<picture>
<source media="(prefers-color-scheme: dark)" srcset="img/flags-by-category-dark.svg">
<img alt="4,461 flags in seven categories: lapsed time limits 1, repeal gaps 5, same-day conflicts 10, retroactive dates 2,093, references to repealed placeholders 1,029, dead fines 30, dead currencies 1,293, each split into flags in law texts and in other texts" src="img/flags-by-category.svg" width="880">
</picture>

The vulnerability detectors from [lexifina/global-law](https://github.com/lexifina/global-law/tree/main/vulnerabilities) look for mechanical mistakes in legislation: a rule applying "until" a date that has passed, a provision repealed before its replacement took effect, two amendments to the same provision on the same day, a penalty for breaching an article that has been repealed. global-law's published list (9 November 2026) covered Türkiye with 382 flags from an earlier copy of this repository, so this is a run over this repository only, as it stood at commit [`9c398d4`](https://github.com/lexifina/turkey-law/commit/9c398d4944beae7bada4325f4dea413ed98feaac) on 15 November 2026, with the regulations, communiqués, presidential decisions, court and board decisions and municipal council decisions it now holds.

**In short:** the detectors raised 4,461 flags. A language model reviewed 56 of the strongest, arguing each one for and against; none survived. Read by hand in this repository, 10 of the 56 come from how this repository rebuilt the history of its acts, 5 are lawful and 41 are not law at all (40 decisions of the Competition Board and this repository's README). The model does not review three categories; reading them by hand turned up four penalty provisions that still punish breaches of articles repealed since, and these look like real drafting mistakes. Article 68 of Law No. 1219 on the practice of medicine, rewritten by Law No. 5728 in 2008, fines nurses who exceed "the scope of practice shown in Article 64", which Law No. 6283 repealed in 1954. Article 55 of the same Law still fines midwives under Article 53, which Law No. 6514 repealed in 2014. Article 106 of the Forest Act (Law No. 6831) still punishes breaches of Articles 72 and 73, which Law No. 7139 rewrote and repealed in 2018. Article 67 of Law No. 6343 on veterinary practice still fines breaches of Article 43, repealed in 1963. Later, this will be formalised in Lean, similar to our work on [the US tax code](https://lexifina.com/blog/formalizing-the-us-tax-code) and [US case law](https://lexifina.com/blog/formalizing-all-us-case-law-in-lean).

A flag is a prompt to look, not legal advice, and nothing here has been tested in court.

## Flags by category

| Category | What it looks for | Flags | In law texts | Reviewed | Survived review |
| --- | --- | ---: | ---: | ---: | ---: |
| Lapsed time limits | Text still applying a rule "until" a date that has passed | 1 | 0 | 1 | 0 |
| Repeal gaps | A provision removed before its replacement took effect | 5 | 5 | 5 | 0 |
| Same-day conflicts | Two acts changing the same provision on the same day | 10 | 10 | 10 | 0 |
| Retroactive or pre-publication dates | A rule in force before it was made or published | 2,093 | 0 | 40 | 0 |
| References to repealed placeholders | A provision citing an article that now reads only "Mülga" (repealed) | 1,029 | 1,029 | 0 | 0 |
| Dead fines | A penalty for breaching an article that has been repealed | 30 | 30 | 0 | 0 |
| Dead currencies | Amounts in currencies no longer in use | 1,293 | 418 | 0 | 0 |

"In law texts" counts laws, decree-laws (KHK), presidential decrees, decisions and circulars, by-laws (tüzükler), regulations, communiqués (tebliğler), Council of Ministers and Assembly decisions, Ottoman-era laws and municipal council decisions. The other flags are in court decisions, board decisions (the Competition Board, RTÜK and others), tax rulings and circulars, decisions of the Supreme Election Council and the Court of Accounts, and this repository's README, which this repository also holds and labels as not law. The search for lapsed time limits found nothing in law texts: it reads "until" followed by a date, and Turkish puts the date first ("31/12/2020 tarihine kadar"), so it matched no Turkish sentence, and for the same reason it found no time limit extended after it had run out. A repealed article keeps its file here, reading only "(Mülga: ...)", so a reference to it counts as a reference to a repealed placeholder, not to a deleted provision. The search for stale amounts, duplicate numbering and publisher notes found nothing.

*Edge cases: the four likely mistakes, the 56 reviewed flags grouped by what they turned out to be, and what the other flags are, in [EDGE-CASES.en.md](EDGE-CASES.en.md).*

## Problems found in this repository

- **Articles missing from earlier texts:** 103 article files that an amending act removes in this history come back later, in 11 acts. For the five the detector ranked, the publisher's in-force table lists that act as amending the article, not repealing it: Articles 14 to 16 of the Engelliler Hakkında Kanun (5378) have no text from 3 May 2013 to 19 February 2014, Article 5 of the Kaçakçılıkla Mücadele Kanunu (5607) from 11 April 2013 to 15 April 2020, and Article 78 of the Sosyal Sigortalar ve Genel Sağlık Sigortası Kanunu (5510) from 8 May 2008 to 23 May 2015 ([Edge cases](EDGE-CASES.en.md)).
- **The rest of an act in one file:** in at least 13 acts, the text from one article to the end of the act is a single file, for example the Harçlar Kanunu (492) from Article 13, the Türk Silahlı Kuvvetleri Personel Kanunu (926) from Article 77 (312 article headings in [one file](https://github.com/lexifina/turkey-law/blob/9c398d4944beae7bada4325f4dea413ed98feaac/law/1967/926/madde-77.md)) and the Taşıt Kanunu (237) from Article 10. Detectors read such a file as one article (14 of the 30 dead fines).
- **Stray numbers in earlier texts:** lines holding only a number sit inside articles, such as "9946" in provisional Article 4 of the İskân Kanunu (5543) from 29 May 2013 until 28 October 2026, and "10539" in the 2010 text of Article 9 of the Biyogüvenlik Kanunu (5977).

## Files

| File | What it holds |
| --- | --- |
| [data/flags.csv](data/flags.csv) | Every flag, one row per provision and issue |
| [data/reviewed.csv](data/reviewed.csv) | The 56 flags the model reviewed, with its verdict and reason |
| [data/by_category.csv](data/by_category.csv) | The counts in the table above |
| [tools/](tools/) | The scripts that made this run |

Columns: `category` and `category_tr` (the category in English and Turkish), `detector`, `kind` (`law` or `other`), `path` (the file in this repository; for a retroactive date, the first file of the act or decision), `date` (the date the flag turns on), `reference` (the act or line involved), `summary`, `score` (the detector's ranking, 0 to 1), `review` (`artefact`, `lawful` or `candidate_defect`), `survives_rebuttal`, `review_note` (the model's reason, in English), `url` (the provision at the commit that was read, under its folder since act folders were renamed on 10 November 2026, or, for a retroactive date, the latest commit credited to the act or decision).

## How it was made

- **Detectors:** global-law's [vulnerabilities/scripts](https://github.com/lexifina/global-law/tree/main/vulnerabilities/scripts), run on this repository at commit `9c398d4`. global-law replays this repository only up to an earlier commit, so the history table the detectors read was built from this repository's own commits (the author, the act that made each change, and the `In-force` and `Kind` trailers; a first text marked `as-enacted`, `enacted`, `consolidated` or `current-text` counts as law, as an amendment does).
- **Model review:** gpt-5.4-mini, the 40 strongest flags per category, and for lapsed time limits also the 40 strongest in law texts; one pass says whether a flag is real, a second argues that it is not. Categories with fewer flags were reviewed in full. The model does not review references to repealed placeholders, dead fines or dead currencies. global-law's own list used a different model.
- **Hand check:** every reviewed flag was read in this repository's history and texts. Of the categories the model does not review, all 30 dead fines were read, 22 of the references in articles, and the dead currencies by the word matched. The four open cases rest on the publisher's consolidated text, its amendment notes and its in-force tables; this repository does not hold Laws No. 5728, 6514 and 7139 themselves, so they still need the Resmî Gazete.

To report a correction, open an issue with the provision and an official source.

## Licence

The lists and notes are Lexifina's, dedicated to the public domain under CC0 1.0, like the rest of this repository's own contributions. Quoted law text is as the Mevzuat Bilgi Sistemi and the other official sources publish it, which Article 31 of Law No. 5846 leaves free to reuse; see [LICENSE](../LICENSE).
