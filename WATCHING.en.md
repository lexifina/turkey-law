# Watching the sources: what is watched for Türkiye

[Türkçe](WATCHING.md)

How global-law watches every country's sources (change detectors, the daily poll, what a hit means): [global-law WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md). This page is the same thing for Türkiye only: every official source this repository takes text from, what is read on it to see whether anything is new, and when it was last read.

Built on 2026-11-14 from the git history (`83881dfc4e`): each commit names its source in its `Source:` line, and "last read" is the day this repository last published something from that source. In this repository a commit's date is the day its text took effect or the decision was given, not the day it was published. The day each commit reached `main` comes from the landing log, [`monitoring/landed.tsv`](monitoring/landed.tsv) (GitHub's push log and every run of `make_pages.py`).

| Source | What is read | Folders | Commits | Last read | State |
| --- | --- | --- | ---: | --- | --- |
| [Mevzuat Bilgi Sistemi (the Presidency's legislation database)](https://www.mevzuat.gov.tr) | the search table of each type of act (MevzuatDatatable), each act's text page and the earlier texts of laws | `regulation/`, `kanun/`, `bylaw/`, `law/` … | 5,845 | 2026-11-14 | current |
| [Resmî Gazete (Official Gazette)](https://www.resmigazete.gov.tr) | each day's issue index (eskiler/YYYY/MM/YYYYMMDD.htm) | `data/` | 6 | 2026-11-14 | current |
| [Grand National Assembly (TBMM)](https://www.tbmm.gov.tr) | the list of Assembly decisions and their texts | `parliament-decision/` | 9 | 2026-11-14 | current |
| [Constitutional Court (Anayasa Mahkemesi)](https://normkararlarbilgibankasi.anayasa.gov.tr) | the decision databases' search API (norm review, individual applications, political parties, Yüce Divan, immunity) | `case-law/constitutional-court/party/`, `case-law/constitutional-court/norm/`, `case-law/constitutional-court/immunity/`, `data/` … | 3,368 | 2026-11-14 | current |
| [Court of Jurisdictional Disputes (Uyuşmazlık Mahkemesi)](https://kararlar.uyusmazlik.gov.tr) | the decision search and the decisions' PDFs | `case-law/uyusmazlik/`, `data/` | 415 | 2026-11-14 | current |
| [Competition Authority (Rekabet Kurumu)](https://www.rekabet.gov.tr) | the decisions list (/tr/Kararlar) and each decision's page | `data/`, `decision/rekabet/` | 2,031 | 2026-11-14 | current |
| [Insurance Arbitration Commission (Sigorta Tahkim Komisyonu)](https://www.sigortatahkim.org) | the issues of the arbitral awards journal (Hakem Karar Dergisi) | `case-law/sigorta-tahkim/`, `data/` | 121 | 2026-11-14 | current |
| [Radio and Television Supreme Council (RTÜK)](https://www.rtuk.gov.tr) | the Council's decisions | `decision/rtuk/` | 1 | 2026-11-14 | current |
| [Supreme Election Council (YSK)](https://www.ysk.gov.tr) | the full list of decisions (doc/karar/kararlar.txt) and their PDFs | `election/ysk/`, `data/` | 456 | 2026-11-14 | current |
| [Court of Accounts (Sayıştay)](https://www.sayistay.gov.tr) | the lists of decisions of the General Assembly, the Appeals Board and the chambers | `audit/sayistay/`, `data/` | 8 | 2026-11-14 | current |
| [Ankara Metropolitan Municipality](https://www.ankara.bel.tr) | the council decisions list (/meclis/kararlar) and the decision files | `local/ankara/buyuksehir/`, `data/` | 247 | 2026-11-14 | current |
| [Bursa Metropolitan Municipality](https://www.bursa.bel.tr) | the council decisions and their PDFs | `local/bursa/buyuksehir/` | 18 | 2026-11-14 | current |

In addition, [`data/`](data/) holds the Resmî Gazete's daily index (7,028 days, 2001-01-02 to 2026-11-14) and the Constitutional Court's index of individual-application decisions (17,999 rows, the newest 2026-10-14); every row carries its official address.

## Not watched

- **Yargıtay decision search (karararama.yargitay.gov.tr)**: the connection timed out (2026-11-13).
- **Danıştay decision search and UYAP Emsal**: every search asks for a reCAPTCHA.
- **Ombudsman decisions (kararlar.ombudsman.gov.tr)**: refused the connection (2026-11-13).

These are never worked around: nothing is taken from these sources until the block is gone (see [PLAN.md](PLAN.md)).

## How it is watched

- **There is no automatic daily watch for Türkiye yet.** global-law's change detectors are built but not switched on. Each source is re-read when its lane in this repository runs, and the date above shows when that last happened.
- **Manners.** Every source is read within its robots.txt, with pauses between requests; text always comes from the official source, never from a detector.
- **A hit.** When a source publishes something new, it becomes a new commit dated the day it applies or was given; global-law picks it up on its next pass ([monitoring/](monitoring/README.en.md)).

Only the official publication (the Resmî Gazete, the courts' and bodies' own sites) has legal force.
