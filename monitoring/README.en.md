# Monitoring: does Türkiye keep up?

[Türkçe](README.md)

How global-law monitors every corpus (a pass every 15 minutes, a check of every commit, a public status): [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). This page is the state of this repository alone.

**Status 2026-11-14**

| | |
| --- | --- |
| Last commit | reached main 2026-11-14 18:13 UTC: Üniversite Yönetmeliği 46376: İSTANBUL ÜNİVERSİTESİ SÜREKLİ EĞİTİM UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ |
| Last 24 hours | Mevzuat Bilgi Sistemi 3,483; Anayasa Mahkemesi 3,368; Rekabet Kurumu 2,031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; documentation 11; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| Last 7 days | Mevzuat Bilgi Sistemi 3,484; Anayasa Mahkemesi 3,368; Rekabet Kurumu 2,031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; documentation 12; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| Last 30 days | Mevzuat Bilgi Sistemi 5,845; Anayasa Mahkemesi 3,368; Rekabet Kurumu 2,031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; documentation 15; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| global-law | `turkey/national/acts` `stale`, pinned at `20521f6996`, 10,174 newer commits here |
| Stale sources | none ([FRESHNESS.en.md](../FRESHNESS.en.md)) |

Times are when each commit reached `main` ([`landed.tsv`](landed.tsv)); commit dates are the days of effect or decision.

## How new changes arrive

1. Each source's lane reads its list of new texts (see [WATCHING.en.md](../WATCHING.en.md)) and publishes each change as a commit dated the day it took effect or was given.
2. Before publishing, every commit goes through this repository's checks: the text against the source, the dates against the publisher's own (see [REPRODUCE.md](../REPRODUCE.md)).
3. Every 15 minutes global-law checks new commits and moves its pin on `turkey/national/acts` (see [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring)).

## Check it yourself

```
git fetch && git log -1 --format="%h %s" origin/main
python monitoring/make_pages.py --github lexifina/turkey-law    # rebuild these three pages with GitHub's push log
python monitoring/make_plan.py                                  # count PLAN.md again
```

## Watch it yourself: a fork and GitHub Actions

Anyone can fork this repository and keep their copy current without us. GitHub Actions is free for public repositories.

1. Fork it: <https://github.com/lexifina/turkey-law/fork>.
2. In the fork, copy [`monitoring/fork-workflow.yml`](fork-workflow.yml) to `.github/workflows/refresh.yml` and commit it to `main`.
3. On the fork's **Actions** tab, enable workflows (GitHub turns them off in forks by default) and run **Refresh from lexifina/turkey-law** once.

Every 6 hours the workflow takes the new commits from this repository into your fork's `main` (through GitHub's own "Sync fork", so your `main` is this repository plus your workflow file), rebuilds WATCHING, FRESHNESS and this page for your copy, grows the landing log (`landed.tsv`) by one row a run, publishes them to a `status` branch and shows FRESHNESS in the run summary. A run takes a few minutes. The workflow does not read the official sources: it checks how current this repository is.
