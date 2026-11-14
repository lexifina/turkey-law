# The plan: every source a Turkish lawyer or citizen needs

This is the plan for this repository, part by part, with what is published so far. The aim is everything a Turkish lawyer or citizen needs, in one dated git history: every act with its versions, secondary legislation, case law, local law, the Resmî Gazete and the legislative history behind each act.

**41.1%** of the plan is published, weighted by how binding each source is and how often it is used. Targets are the official counts read from each source on 2026-11-13; parts whose count is only an estimate have no target yet and count 0. Counted from `83881dfc4e` on 2026-11-14 by [`monitoring/make_plan.py`](monitoring/make_plan.py).

| Part | Will be in | Weight | Progress | How | Status |
| --- | --- | ---: | --- | --- | --- |
| **Primary legislation (Mevzuat Bilgi Sistemi)** | | | | | |
| Laws in force (Kanunlar), with the Constitution | law/<year>/<number>/ | 19.3% | 908 of 917 laws in force · 99.0% | mevzuat.gov.tr; current text checked word for word against the site | collecting |
| Earlier consolidated texts of laws ("Önceki metinler") | the history of law/<year>/<number>/ | 3.9% | 280 of 280 laws with earlier texts · 100.0% | mevzuat.gov.tr .doc files, read through Microsoft Word and checked word for word | done |
| Repealed laws (mülga kanunlar) | law/<year>/<number>/, labelled repealed | 1.9% | 63 of 185 repealed laws · 34.1% | mevzuat.gov.tr MulgaKanun | collecting |
| Ottoman-era laws still in force | ottoman/<year>/<number>/ | 0.5% | 9 of 9 laws · 100.0% | mevzuat.gov.tr | done |
| Decree-laws (KHK) | decree-law/<year>/<number>/ | 1.9% | 63 of 63 decree-laws · 100.0% | mevzuat.gov.tr | done |
| Presidential decrees (CBK), in force and amending or repealed ones | presidential-decree/<year>/<number>/ | 3.9% | 33 of 203 decrees in the official list · 16.3% | mevzuat.gov.tr; the 170 not in force from the list's PDFs | collecting |
| By-laws (tüzükler) | bylaw/<year>/<number>/ | 1.0% | 105 of 107 by-laws · 98.1% | mevzuat.gov.tr | collecting |
| Index of every law ever passed, with its Resmî Gazete issue and repeal | data/m4-all/ | 1.9% | 15,623 of 15,623 laws in the official index · 100.0% | mevzuat.gov.tr law index (MevzuatFihristDatatable) | done |
| **Secondary legislation** | | | | | |
| Presidential and Council of Ministers regulations | regulation/presidency/, regulation/council-of-ministers/ | 3.9% | 147 of 327 regulations · 45.0% | mevzuat.gov.tr | collecting |
| Regulations of ministries, agencies and other bodies (kurum ve kuruluş yönetmelikleri) | regulation/<issuer>/<year>/<number>/ | 6.8% | 0 of 3,662 regulations · 0.0% | mevzuat.gov.tr | planned |
| University regulations | regulation/<university>/<year>/<number>/ | 1.9% | 3,149 of 5,046 regulations · 62.4% | mevzuat.gov.tr | collecting |
| Communiqués (tebliğler) | communique/<issuer>/<year>/<number>/ | 6.8% | 0 of 4,482 communiqués · 0.0% | mevzuat.gov.tr | planned |
| Presidential decisions (CB kararları, since 2018) | presidential-decision/<year>/<number>/ | 3.9% | 0 of 4,374 decisions · 0.0% | mevzuat.gov.tr PDFs; expropriation parcel lists as links only | planned |
| Presidential circulars (CB genelgeleri) | presidential-circular/<year>/<number>/ | 1.0% | 1 of 158 circulars · 0.6% | mevzuat.gov.tr PDFs | collecting |
| Council of Ministers decisions before 2018 (BKK) | council-of-ministers-decision/<year>/<number>/ | 1.9% | 0 held; target about 25,000 (estimate) | Resmî Gazete items, from the daily index | planned |
| **Case law** | | | | | |
| Constitutional Court: norm review (Norm Denetimi) | case-law/constitutional-court/norm/<year>/<number>/ | 5.8% | 1,396 of 5,620 decisions · 24.8% | the Court's decisions database (normkararlarbilgibankasi.anayasa.gov.tr) | collecting |
| Constitutional Court: individual applications (index; text where the Court anonymises) | data/aym-individual-<year>.csv | 3.9% | 17,999 of 18,003 decisions · 100.0% | kararlarbilgibankasi.anayasa.gov.tr; applicants' names as published, text only with initials | done |
| Constitutional Court: political parties, Yüce Divan, immunity | case-law/constitutional-court/party/, supreme-criminal/, immunity/ | 0.5% | 1,965 of 1,993 decisions · 98.6% | the same database | collecting |
| Uyuşmazlık Mahkemesi (jurisdiction conflicts) | case-law/uyusmazlik/<year>/<number>/ | 1.9% | 414 of 15,083 decisions the court lists · 2.7% | kararlar.uyusmazlik.gov.tr; the list is data/ledger-m31-uyusmazlik.csv | collecting |
| Unification decisions of the Yargıtay and the Danıştay (İBK) | case-law/yargitay/ibk/, case-law/danistay/ibk/ | 2.9% | 0 held; target about 1,500 (estimate) | Resmî Gazete, judicial section | planned |
| Competition Authority (Rekabet Kurulu) | decision/rekabet/<year>/<number>/ | 1.9% | 1,997 of 10,476 decisions · 19.1% | rekabet.gov.tr decisions list | collecting |
| Other boards: insurance arbitration, broadcasting (RTÜK), BDDK, SPK, EPDK, GİB, KVKK, BTK | decision/<body>/, case-law/sigorta-tahkim/, norm/<issuer>/ | 3.9% | 121 held; target about 45,000 (estimate) | each body's own site; sanctions on individuals as metadata and link | collecting |
| **Local law** | | | | | |
| Ankara Metropolitan Council decisions | local/ankara/buyuksehir/<year>/<number>/ | 2.9% | 246 held; target about 24,000 (estimate) | ankara.bel.tr council decisions, 2012 on | collecting |
| Other metropolitan councils (İstanbul, İzmir, Bursa and 27 more) | local/<province>/buyuksehir/<year>/<number>/ | 3.9% | 18 held; target being counted | each council's site; İstanbul's register not found yet | collecting |
| District and town councils, provincial councils, governors' orders | local/<province>/<body>/<year>/<number>/ | 1.9% | 0 held; target about 1,390 councils | municipal sites and e-Devlet's council-decision services | planned |
| **Elections, audit and oversight** | | | | | |
| Supreme Election Council (YSK): decisions, principle decisions, rules | election/ysk/ | 1.0% | 455 of 1,778 decisions and rules · 25.6% | ysk.gov.tr indexes (kararlar.txt) | collecting |
| Court of Accounts (Sayıştay): judgments and audit reports | audit/sayistay/ | 1.4% | 7 held; target about 15,000 (estimate) | sayistay.gov.tr | collecting |
| Ombudsman (KDK) decisions and reports | ombudsman/ | 0.5% | about 10,000 (estimate) | kararlar.ombudsman.gov.tr refused connections on 2026-11-13 | blocked |
| **Parliament and the Resmî Gazete** | | | | | |
| Decisions of the Grand National Assembly (TBMM kararları) | parliament-decision/<year>/<number>/ | 0.5% | 9 held; target about 1,500 (estimate) | tbmm.gov.tr | collecting |
| Bills and committee reports, labelled not law | bill/<term>/<number>/ | 1.9% | 0 held; target about 30,000 (estimate) | tbmm.gov.tr | planned |
| Resmî Gazete daily index since 2001 (every issue's sections and items) | data/rg-<year>.csv | 2.9% | 7,028 of 9,449 days since 2001-01-01 · 74.4% | resmigazete.gov.tr daily index pages | collecting |
| Treaties | treaty/<year>/<number>/ | 1.9% | 0 held; target about 5,000 (estimate) | Resmî Gazete, with the approving law | planned |
| **Blocked or out of scope** | | | | | |
| All decisions of the Yargıtay, the Danıştay and the regional and first-instance courts | none | – | millions | Yargıtay's search timed out; the Danıştay and UYAP Emsal need a reCAPTCHA on every search; never worked around | blocked |
| Notices in the Resmî Gazete (ilanlar) and on ilan.gov.tr | none | – | – | court and enforcement notices name private persons | not planned |

Progress counts what is on `main`: a record is one folder `<kind>/.../<year>/<number>/`, and index tables count their rows. Targets: mevzuat.gov.tr's own search table for each type of act (2026-11-13), its law index (15,623 laws of every tertip), the Constitutional Court's database (5,620 norm-review decisions, 18,003 individual applications, 1,993 other decisions), the Competition Authority's list (10,476 decisions) and YSK's indexes (982 decisions, 787 principle decisions, 9 rules). The Resmî Gazete is published every day, so its target is the number of days since 2001-01-01. Parts with an estimate are being counted.
