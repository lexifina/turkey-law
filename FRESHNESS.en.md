# Freshness: is it true right now?

[Türkçe](FRESHNESS.md)

How global-law measures freshness for every corpus (the statuses, the 7- and 30-day thresholds, the `freshness.py` tool): [global-law FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md). Here is the same measure for Türkiye, source by source.

## How global-law sees it

| Corpus | Status | Last checked | Method | Commit pinned in global-law | Newer commits here |
| --- | --- | --- | --- | --- | ---: |
| `turkey/national/acts` | `stale` | 2026-10-28 | `stated` | `20521f6996` | 10,174 |

`stale`: the threshold for national law is 7 days since the last check. global-law takes commits newer than the pinned one on its next pass; until then, read them here.

## Source by source

"Newest record" is the latest day of effect or decision that is not in the future (for the Resmî Gazete, the last issue in the index); "last read" is the day this repository last published something from the source. Threshold: 7 days for national law, 30 for court and board decisions, local acts and other records.

| Source | Commits | Newest record | Last read | Days since | State | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| Mevzuat Bilgi Sistemi (the Presidency's legislation database) | 5,845 | 2026-11-11 | 2026-11-14 | 0 | current |  |
| Resmî Gazete (Official Gazette) | 6 | 2026-11-14 | 2026-11-14 | 0 | current |  |
| Grand National Assembly (TBMM) | 9 | 1993-07-21 | 2026-11-14 | 0 | current |  |
| Constitutional Court (Anayasa Mahkemesi) | 3,368 | 2026-10-14 | 2026-11-14 | 0 | current |  |
| Court of Jurisdictional Disputes (Uyuşmazlık Mahkemesi) | 415 | 2026-06-15 | 2026-11-14 | 0 | current |  |
| Competition Authority (Rekabet Kurumu) | 2,031 | 2018-05-03 | 2026-11-14 | 0 | current |  |
| Insurance Arbitration Commission (Sigorta Tahkim Komisyonu) | 121 | 2026-09-29 | 2026-11-14 | 0 | current |  |
| Radio and Television Supreme Council (RTÜK) | 1 | 2024-04-17 | 2026-11-14 | 0 | current |  |
| Supreme Election Council (YSK) | 456 | 2026-10-07 | 2026-11-14 | 0 | current |  |
| Court of Accounts (Sayıştay) | 8 | 2017-10-16 | 2026-11-14 | 0 | current |  |
| Ankara Metropolitan Municipality | 247 | 2022-02-10 | 2026-11-14 | 0 | current |  |
| Bursa Metropolitan Municipality | 18 | 2026-01-15 | 2026-11-14 | 0 | current |  |

## Check it yourself

```
git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- law/    # the last law commit published, and the day it applies
git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- case-law/constitutional-court/norm/    # the last norm-review decision published
tail -n 3 monitoring/landed.tsv    # the last pushes to main
```

When the date you care about is after the last check, confirm the text against the official source. Only the official publication has legal force.
