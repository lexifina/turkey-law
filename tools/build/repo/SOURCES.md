# Sources

| Source | What it gives | Used |
| --- | --- | --- |
| [Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr) (T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü) | Current consolidated text of every act in force, with amendment notes and footnotes | Yes: the text of every act |
| `POST /Anasayfa/MevzuatDatatable` (the site's own search table) | Every act in force by kind: number, Düstur tertip, title, adoption date, Resmî Gazete date and issue | Yes: the act lists (Kanun, KHK, Cumhurbaşkanlığı Kararnameleri) |
| `GET /anasayfa/MevzuatFihristDetayIframe?MevzuatTur=&MevzuatNo=&MevzuatTertip=` | One act's text as Word-generated HTML | Yes |
| `GET /EskiKanunlar/EskiKanunlarList?kanunSayisi=&mevzuatTertip=` ("Önceki metinler") | Earlier consolidated texts of {{PREVIOUS_TEXT_ACTS}} laws, as .doc/.pdf files, each dated by the amending act | Yes: the list of versions (data/previous-texts.csv) |
| `GET /MevzuatMetin/<tur>.<tertip>.<no>-<yyyymmdd>.doc` | Each earlier text as a Word file (the same content is also offered as .pdf) | Yes: every earlier version, converted with Microsoft Word |
| [Resmî Gazete](https://www.resmigazete.gov.tr) | The official gazette (authoritative text) | No |

Retrieved {{RETRIEVED}} (UTC), {{REQUESTS}} requests.

## Checks made before fetching (2026-10-28)

- **robots.txt**: `https://www.mevzuat.gov.tr/robots.txt` (the same at `mevzuat.gov.tr`) has one group, `User-agent: Googlebot`, with only `Noindex:` lines for single documents. There is no `Disallow`, no `Crawl-delay`, no `Content-Signal`, and no rule for ClaudeBot, Claude-Web, anthropic-ai or GPTBot.
- **Terms**: the footer reads "© 2020 Tüm Hakları Saklıdır. Gizlilik, Kullanım ve Telif Hakları bildiriminde belirtilen kurallar çerçevesinde hizmet sunulmaktadır." The notice it names could not be reached: `https://www.tccb.gov.tr/gizlilik-kullanim-ve-telif-haklari/` and the site's own guesses redirect to the home page. So its terms were not read. The site's "Hakkımızda" page says the service is "ücretsiz ve koşulsuz olarak herkesin kullanımına sunulmuştur" (offered to everyone free of charge and without conditions).
- **Legal basis**: Fikir ve Sanat Eserleri Kanunu (Law No. 5846) art. 31 makes the reproduction, distribution, adaptation and any other use of officially published laws, presidential decrees, regulations, communiqués, circulars and court decisions free (`kanun/5846/madde-31.md`).
- **Bulk data**: none found. There is no API or dump beyond the site's own pages, hence one request per act.
- **History**: none on the main pages. The current text only; the "Önceki metinler" files exist for some laws only.

## Countries checked before Türkiye (2026-10-28)

Serbia (PIS terms forbid automated extraction without the Official Gazette's written consent), Greece (gazette PDFs only, no official consolidation reachable), Bulgaria (gazette only; consolidations are private services) and Sri Lanka (LawNet down) were checked first and dropped.
