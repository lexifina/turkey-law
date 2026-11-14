# Kaynakların izlenmesi: Türkiye için neler izleniyor

[English](WATCHING.en.md)

global-law'un her ülkenin kaynaklarını nasıl izlediği (değişiklik dedektörleri, günlük yoklama, bir isabetin ne anlama geldiği): [global-law WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md). Bu sayfa aynı şeyin yalnızca Türkiye için olanıdır: bu deponun metin aldığı her resmî kaynak, yeni bir şey olup olmadığını görmek için onda neyin okunduğu ve en son ne zaman okunduğu.

14.11.2026 tarihinde git geçmişinden (`83881dfc4e`) oluşturuldu: her commit kaynağını `Source:` satırında adlandırır ve "en son okunma", bu deponun o kaynaktan en son bir şey yayımladığı gündür. Bu depoda bir commit'in tarihi, metnin yürürlüğe girdiği ya da kararın verildiği gündür; yayımlandığı gün değildir. Her commit'in `main` dalına ulaştığı gün [`monitoring/landed.tsv`](monitoring/landed.tsv) dosyasındaki iniş kaydından gelir (GitHub'ın push kaydı ve `make_pages.py`'nin her çalışması).

| Kaynak | Neler okunuyor | Klasörler | Commit | En son okunma | Durum |
| --- | --- | --- | ---: | --- | --- |
| [Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı)](https://www.mevzuat.gov.tr) | her mevzuat türünün arama tablosu (MevzuatDatatable), her düzenlemenin metin sayfası ve kanunların önceki metinleri | `regulation/`, `kanun/`, `bylaw/`, `law/` … | 5.845 | 14.11.2026 | güncel |
| [Resmî Gazete](https://www.resmigazete.gov.tr) | her günün sayı fihristi (eskiler/YYYY/MM/YYYYMMDD.htm) | `data/` | 6 | 14.11.2026 | güncel |
| [Türkiye Büyük Millet Meclisi](https://www.tbmm.gov.tr) | Meclis kararları listesi ve karar metinleri | `parliament-decision/` | 9 | 14.11.2026 | güncel |
| [Anayasa Mahkemesi](https://normkararlarbilgibankasi.anayasa.gov.tr) | karar bilgi bankalarının arama API'si (norm denetimi, bireysel başvuru, siyasi parti, Yüce Divan, yasama dokunulmazlığı) | `case-law/constitutional-court/party/`, `case-law/constitutional-court/norm/`, `case-law/constitutional-court/immunity/`, `data/` … | 3.368 | 14.11.2026 | güncel |
| [Uyuşmazlık Mahkemesi](https://kararlar.uyusmazlik.gov.tr) | karar arama sayfası ve karar PDF'leri | `case-law/uyusmazlik/`, `data/` | 415 | 14.11.2026 | güncel |
| [Rekabet Kurumu](https://www.rekabet.gov.tr) | kararlar listesi (/tr/Kararlar) ve her kararın sayfası | `data/`, `decision/rekabet/` | 2.031 | 14.11.2026 | güncel |
| [Sigorta Tahkim Komisyonu](https://www.sigortatahkim.org) | Hakem Karar Dergisi sayıları | `case-law/sigorta-tahkim/`, `data/` | 121 | 14.11.2026 | güncel |
| [Radyo ve Televizyon Üst Kurulu](https://www.rtuk.gov.tr) | Üst Kurul kararları | `decision/rtuk/` | 1 | 14.11.2026 | güncel |
| [Yüksek Seçim Kurulu](https://www.ysk.gov.tr) | kararların tam listesi (doc/karar/kararlar.txt) ve karar PDF'leri | `election/ysk/`, `data/` | 456 | 14.11.2026 | güncel |
| [Sayıştay](https://www.sayistay.gov.tr) | Genel Kurul, Temyiz Kurulu ve daire kararları listeleri | `audit/sayistay/`, `data/` | 8 | 14.11.2026 | güncel |
| [Ankara Büyükşehir Belediyesi](https://www.ankara.bel.tr) | Meclis kararları listesi (/meclis/kararlar) ve karar dosyaları | `local/ankara/buyuksehir/`, `data/` | 247 | 14.11.2026 | güncel |
| [Bursa Büyükşehir Belediyesi](https://www.bursa.bel.tr) | Meclis kararları ve karar PDF'leri | `local/bursa/buyuksehir/` | 18 | 14.11.2026 | güncel |

Ayrıca [`data/`](data/) klasöründe Resmî Gazete'nin günlük fihristi (7.028 gün, 02.01.2001 ile 14.11.2026 arası) ve Anayasa Mahkemesinin bireysel başvuru kararları dizini (17.999 satır, en yenisi 14.10.2026) bulunur; her satır resmî adresini taşır.

## İzlenmeyenler

- **Yargıtay karar arama (karararama.yargitay.gov.tr)**: bağlantı zaman aşımına uğradı (2026-11-13).
- **Danıştay karar arama ve UYAP Emsal**: her aramada reCAPTCHA isteniyor.
- **Kamu Denetçiliği Kurumu kararları (kararlar.ombudsman.gov.tr)**: bağlantıyı reddetti (2026-11-13).

Bunlar aşılmaz: engel kalkana kadar bu kaynaklardan hiçbir şey alınmaz (bkz. [PLAN.md](PLAN.md)).

## Nasıl izleniyor

- **Türkiye için henüz otomatik günlük izleme yok.** global-law'un değişiklik dedektörleri hazır, ancak açılmadı. Her kaynak, bu depodaki şeridi çalıştığında yeniden okunur; yukarıdaki tarih bunun en son ne zaman olduğunu gösterir.
- **Görgü kuralları.** Her kaynak robots.txt dosyasına uyularak ve istekler arasında beklenerek okunur; metin her zaman resmî kaynaktan gelir, hiçbir zaman bir dedektörden gelmez.
- **Bir isabet.** Bir kaynak yeni bir şey yayımladığında, bu, yürürlüğe girdiği ya da verildiği günle tarihlenmiş yeni bir commit olur; global-law onu bir sonraki geçişinde alır ([monitoring/](monitoring/)).

Yalnızca resmî yayın (Resmî Gazete, mahkemelerin ve kurumların kendi siteleri) hukuken bağlayıcıdır.
