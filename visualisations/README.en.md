# Turkish law in 20 charts

[Türkçe](README.md) · **English**

Charts on every country's law, from the whole of global-law: [global-law visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations). These are the charts on Türkiye alone.

Twenty charts on Turkish law, drawn only from the data in this repository: the index of every law published in the Resmî Gazete, the index of plenary minutes and the decisions of the Grand National Assembly, the amendment notes and in-force tables of the laws in force, the Constitution, the daily index of the Resmî Gazete since 2001, the decisions of three metropolitan councils and the decisions of the Constitutional Court (Anayasa Mahkemesi).

Open [`20-grafikte-turk-hukuku.html`](20-grafikte-turk-hukuku.html) in a browser. The page is one file with all its data inside; it loads only the d3 and topojson libraries, the world map of chart 5 and its fonts from the web. The controls at the top right switch the language (Turkish or English) and the theme (light or dark). Each chart names its data path in the repository, its record count and its limits, and has a table of every number under it. Hover over a mark for the exact values.

The charts are descriptive: they show what the sources record, not why.

## The charts

### I. The Assembly and its laws

1. **Laws a year.** The laws published in the Resmî Gazete each year since 1921: 221 a year on average in the 1930s, 61 in the 2020s.
   ![1](stills/en/01.png)
2. **What the laws were about.** The kinds of law by decade: in the 2010s, 73% of laws approved an international agreement.
   ![2](stills/en/02.png)
3. **Omnibus laws.** Omnibus laws by legislative term, and the acts that changed the most others: 80% of the 28th term's laws, treaties and budgets aside.
   ![3](stills/en/03.png)
4. **Vetoes.** The 168 law numbers the law index marks as VETO, never published, by President; 72 fall in Ahmet Necdet Sezer's term.
   ![4](stills/en/04.png)
5. **Agreements.** The states named in the titles of approval laws, on a map and by period.
   ![5](stills/en/05.png)

### II. Sittings, states of emergency and troop mandates

6. **The plenary.** Every sitting and closed session since 1920: the First Assembly held 552 sittings and 177 closed sessions in three years.
   ![6](stills/en/06.png)
7. **States of emergency.** The Assembly's decisions approving and extending states of emergency, with the number of provinces their titles give.
   ![7](stills/en/07.png)
8. **Mandates to send troops abroad.** The Assembly's authorisations to deploy the armed forces abroad, by mission: 84 decisions since 2006.
   ![8](stills/en/08.png)

### III. How the laws in force change

9. **Laws were changed by decree too.** Amendment notes by year, by law and by decree-law; decree-law 703 of 2 July 2018 changed 144 acts.
   ![9](stills/en/09.png)
10. **The most-changed laws.** The amendment notes of 25 laws and decree-laws, year by year.
    ![10](stills/en/10.png)
11. **The 1982 Constitution.** Every article and the amending law that last left a note on it: 97 of its 177 articles carry amendment notes.
    ![11](stills/en/11.png)
12. **Entry into force.** Whether changes took effect on the day they were published, later, or from a date before publication.
    ![12](stills/en/12.png)
13. **What became of the laws.** Laws by decade: in force, repealed by a law or repealed by a decree-law.
    ![13](stills/en/13.png)

### IV. The executive, the Resmî Gazete and municipalities

14. **The Resmî Gazete.** Every item published in 2001–2016 and 2021–2026, by kind: presidential decisions replaced the Council of Ministers'.
    ![14](stills/en/14.png)
15. **Urgent expropriation.** Urgent-expropriation decisions by purpose: since 2012, 65% were for power lines and plants.
    ![15](stills/en/15.png)
16. **Universities.** The share of the Resmî Gazete's regulations issued by universities.
    ![16](stills/en/16.png)
17. **Metropolitan councils.** The decisions of the metropolitan councils of Bursa, Mersin and Tekirdağ, by topic.
    ![17](stills/en/17.png)

### V. The Constitutional Court

18. **The Constitutional Court.** Decisions recorded in the in-force tables as changing laws, and the acts most often changed.
    ![18](stills/en/18.png)
19. **Individual applications.** Published individual-application decisions by year and outcome.
    ![19](stills/en/19.png)
20. **Waiting.** The gap between the year of application and the year of decision.
    ![20](stills/en/20.png)

## Data

As of commit `d02b49ef22` (15 November 2026).

| Dataset | Where in the repository | Records | Coverage |
| --- | --- | ---: | --- |
| Git history | branch `main` | 49,559 commits | a commit is dated the day its text took effect or a decision was given or published (`In-force:`) |
| Law index | `data/m4-all/` | 15,623 rows (15,409 distinct laws) | 1921–2026; the 211 undated laws and the 168 unpublished VETO numbers have no year |
| Amendment notes | `data/amendments.csv` | 20,203 notes | the texts of 683 laws and decree-laws in force |
| In-force tables | `data/in-force-list.csv` | 8,721 rows | the 717 acts the publisher keeps tables for |
| Constitution | `law/1982/2709/` | 198 article files | the current text and its amendment notes |
| Resmî Gazete index | `data/rg-*.csv`, `data/rg-index/` | 81,283 items, 7,732 days | 2001–2016 and 2021–2026; notices left out |
| Plenary minutes index | `data/minutes-*.csv` | 10,924 records | 1920–2026; terms 15 and 16 (1973–1980) missing |
| Assembly decisions | `parliament-decision/` | 1,131 decisions | 1983–2026; titles from the commits and the Resmî Gazete index |
| Metropolitan councils | `local/` | 5,200 decisions | Bursa 2024–2026, Mersin 2025–2026, Tekirdağ 2026 (titled); Ankara (untitled) |
| Individual-application index | `data/aym-individual-*.csv` | 17,999 decisions | 2013–2026; published decisions |

## Limits

- **Amendment notes are those printed in the current text.** When a provision changes again its older note is gone, so earlier years are undercounted in charts 9, 10 and 11.
- **Categories are read from titles.** The kind of law (chart 2), omnibus laws (3), the other party to an agreement (5), the mission (8), the kind of Resmî Gazete item (14), the purpose of an expropriation (15) and the topic of a council decision (17) come from words in titles, by the rules in `src/prep.py`. Whatever no rule recognises is shown as "Other".
- **The record has gaps.** The Resmî Gazete index lacks 2017–2020 (14–16); the plenary minutes index lacks terms 15 and 16 (6); Assembly decisions without a title cannot be drawn (7, 8); the outcome of the individual-application decisions of 2021–2024 is not in the index (19); the individual-application index holds published decisions only (19, 20).
- **Vetoes (4)** are only the numbers the index marks as VETO; each is dated by the published law number before it.
- **Partial periods** (2026, the 28th term, the 2020s) are drawn lighter and labelled as such.

## Rebuilding

```sh
python visualisations/src/make.py            # git objects -> src/.build/ -> 20-grafikte-turk-hukuku.html
node visualisations/src/stills.cjs           # images for these READMEs (needs Playwright; PLAYWRIGHT=<path> if not global)
```

`make.py` reads everything from git objects, so it also works in a blobless or `--no-checkout` clone: it fetches the blobs it needs in one batch. It reads `origin/main` (or `HEAD`) by default; `--ref` picks another branch or commit. It writes nothing into the repository except the page and the `src/.build/` folder (which git ignores).

| File | What it does |
| --- | --- |
| `src/make.py` | extracts the tables it needs and the git history into `src/.build/`, then runs `prep.py` and `build.py` |
| `src/prep.py` | computes every number for the 20 charts and the data profile into `src/.build/data.json` |
| `src/page.tpl.html` | the page: text in both languages, the charts (d3), the tables |
| `src/build.py` | puts `data.json` into the template and writes the page |
| `src/stills.cjs` | draws each chart as a PNG into `stills/tr/` and `stills/en/` |
