# Türkiye: git'te hukukun geçmişi

**Türkçe** · **[Or read it in English](README.en.md)**

<picture>
<source media="(prefers-color-scheme: dark)" srcset="data/tr/effort-dark.svg">
<img alt="Bu depodaki Türkiye mevzuatı: neleri içerdiği, yürürlüğe girdiği yıla göre değişiklikler, resmî kaynaklara göre eksiksizlik ve mevcut içeriğin doğruluğu" src="data/tr/effort-light.svg" width="880">
</picture>

Türkiye hukuku bir git geçmişi olarak: her madde bir dosya, her sürüm yürürlüğe girdiği gün bir commit ve değişikliği yapan düzenleme commit'in yazarı. `git blame` her satırın arkasındaki düzenlemeyi adlandırır; `git log` bir maddenin her değişikliğini listeler; bir tarih seçmek o gün yürürlükte olan metni verir.

Her ülkenin hukuku için tek bir git geçmişi olan [lexifina/global-law](https://github.com/lexifina/global-law) projesinin parçası: bu, global-law'un `turkey/national/acts/` yolunda okuduğu Türkiye ulusal hukukudur.

**Şu anda içerdikleri:** Anayasa dahil yürürlükteki 908 kanun (bunların 280 tanesi yayıncının sakladığı tüm önceki metinleriyle) ve 65 mülga kanun; 9 Osmanlı dönemi kanunu, 63 kanun hükmünde kararname (KHK), 33 Cumhurbaşkanlığı kararnamesi (CBK), 107 tüzük, 159 Cumhurbaşkanlığı genelgesi, 4.375 Cumhurbaşkanı kararı ve Bakanlar Kurulunun 226 kararı; 11.507 yönetmelik (üniversitelerin ve diğer yükseköğretim kurumlarının 5.039, bakanlıkların, kurum ve kuruluşların ve diğer organların 3.570, Resmî Gazete'de yayımlandığı haliyle 2.571, Cumhurbaşkanlığının 179 ve Bakanlar Kurulunun 148 yönetmeliği) ve 5.149 tebliğ (bunların 865 tanesi Resmî Gazete'de yayımlandığı haliyle); Anayasa Mahkemesinin 7.577 kararı (bunların 5.612 tanesi norm denetimi kararı), 17.992 bireysel başvuru kararı (970 tanesi tam metniyle, 17.022 tanesi resmî karar bilgi bankasındaki kaydı ve resmî bağlantısıyla; özel kişi olan başvurucunun adı verilmez); Uyuşmazlık Mahkemesinin 9.841, Danıştayın 9 kararı, 121 sigorta tahkim kararı ve Sayıştayın 51.730 kararı ile 10 denetim raporu; Rekabet Kurulunun 10.314, RTÜK'ün 3.243, BDDK'nın 453 kararı, Türkiye Barolar Birliğinin 2.052 disiplin kararı ve diğer kurulların 363 kararı; Gelir İdaresi Başkanlığının 20.218 metni (18.873 özelge; 759 sirküler, iç genelge ve genel yazı; Bakanlar Kurulunun vergiyle ilgili 586 kararı) ile diğer düzenleyici kurumların, bakanlıkların ve meslek kuruluşlarının (BTK, EPDK, SPK, KVKK ve diğerleri) 3.197 kararı, genelgesi ve diğer metni; Yüksek Seçim Kurulunun 1.068 kararı; Türkiye Büyük Millet Meclisinin 4.707 kararı ve Genel Kurul tutanaklarının dizini (20. ile 28. dönemler arasında 3.532 birleşim); 46 belediye ve il genel meclisinin 125.638 meclis kararı ve toplantı kaydı ile 5 valiliğin 19 genelgesi; ve 1921'den 2026'ya 33.305 günün Resmî Gazete fihristi (120.826 öğe) ve ilân bölümünün 19.668 ilânı (2002'den itibaren ekleniyor); ve bugüne kadar kabul edilmiş 15.623 kanunun tamamının dizini ile metni burada olmayan, 1920'den beri kabul edilmiş 14.060 kanunun kaydı (tarihler, Resmî Gazete, resmî bağlantılar). [`PLAN.md`](PLAN.md) bu deponun içermesi gereken her bölümü ve her birinin ne kadar ilerlediğini listeler; birkaç bölüm şu anda dolduruluyor, bu yüzden bu sayılar 2026-11-16 tarihli `ccf6df7405` commit'inin sayılarıdır.

Her düzenleme bir klasördür, `<tür>/<yıl>/<sayı>/`, ve her maddesi bir dosyadır (`law/2003/4857/` 4857 sayılı İş Kanunu, `madde-53.md` de onun 53. maddesidir); Anayasa [`law/1982/2709/`](law/1982/2709/) klasöründedir. Kararlar da aynı biçimde klasörlerdir (`case-law/constitutional-court/norm/<yıl>/<sayı>/`). 2026-11-10'a kadar düzenleme klasörleri düzenlemenin kimliğiyle adlandırılıyordu (`kanun/4857`): `git log --follow` ve `git blame` bu taşımayı izler, `tools/in_force_on.py` taşımadan önceki bir gün için kimliği alır ve [`data/paths.json`](data/paths.json) her kimliği klasörüne eşler.

Metin Türkçedir, yayıncıların bastığı gibidir. İngilizce çeviri bu kaydın parçası değildir.

## Git komutları olarak sorular

| Soru | Komut |
| --- | --- |
| İş Kanununun 53. maddesindeki (yıllık ücretli izin) her değişiklik | `git log --follow -p --word-diff -- law/2003/4857/madde-53.md` |
| 53. maddenin her satırını hangi düzenleme yazdı? | `git blame law/2003/4857/madde-53.md` |
| 53. maddenin her sürümü, her birinin yürürlüğe girdiği günle | `git log --follow --format="%h %(trailers:key=In-force,valueonly,separator=) %an" -- law/2003/4857/madde-53.md` |
| 53. madde, 1 Ocak 2014'te yürürlükte olduğu hâliyle | `python tools/in_force_on.py 2014-01-01 kanun/4857 madde-53` |

**Git dışında** bu kaydı herkese açık ve ücretsiz olarak da sunuyoruz:

- **[Türk hukukunu Claude'a sorun](https://global-law.lexifina.com/v1/try_claude?country=turkey)**: Claude'u ilk sorusu hazır olarak açar.
- **[ChatGPT'ye sorun](https://global-law.lexifina.com/v1/try_chatgpt?country=turkey)**: aynı soru ChatGPT'de.
- **[Türk hukukunda sitemizde arayın](https://lexifina.com/law?country=turkey&q=y%C4%B1ll%C4%B1k+izin)**: "yıllık izin" araması, her hükmün metni ve sürümleriyle, hesap gerekmeden.
- **[Geliştiriciler için REST API](https://global-law.lexifina.com/v1/search_law?query=y%C4%B1ll%C4%B1k+izin&jurisdiction=turkey)**: aynı arama JSON olarak, anahtarsız. Belgeler [burada](https://lexifina.com/api/global-law).

İki asistan da kaydı ücretsiz Global law bağlayıcısı üzerinden okur (MCP, `https://global-law.lexifina.com/mcp`); ilk seferde sohbet size bağlayıcıyı ekleyen bağlantıyı verir. Türkçe ya da İngilizce sorun.

**Kolayca kendiniz barındırın.** Git ve Python yeterlidir; araçlar kendi bilgisayarınızda çalışır:

```sh
git clone --depth 1 https://github.com/lexifina/global-law && cd global-law
python3 tools/countries.py add turkey/national/acts
python3 tools/law.py show 2026-01-01 turkey/national/acts/law/2003/4857/madde-53.md
```

Claude Code, Cursor, VS Code ya da Codex'te açıldığında klon aynı araçlarla yerel bir MCP sunucusu da başlatır ([MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md)).

## Tarihler

Her commit, sürümünün yürürlüğe girdiği ya da bir kararın verildiği veya yayımlandığı günü `In-force:` trailer'ında taşır; `In-force-basis:` ya da `Date-source:` bu günün nereden geldiğini söyler:

- önceki metinleri olan 280 kanunda yayıncının her düzenlemenin sonundaki kendi yürürlük tablosu ("... YÜRÜRLÜĞE GİRİŞ TARİHİNİ GÖSTERİR LİSTE"); düzenlemesi hiçbir tabloda olmayan bir sürüm ve bir kanunun ilk metni düzenlemenin Resmî Gazete tarihini alır;
- yalnızca güncel metniyle tutulan bir düzenlemede, yürürlük maddesinin, metinde basılı son değişikliğinin ya da Resmî Gazete tarihinin verdiği gün; ilk derlemedeki 733 düzenleme, alındıkları gün olan 2026-10-28 tarihlidir;
- bir kararda, kaynağın bastığı gibi, mahkemenin ya da kurulun kararı verdiği ya da Resmî Gazete'nin yayımladığı gün.

Commit'lerin çoğu bu günün öğlen 12'sinde, Türkiye saatiyle (Europe/Istanbul) tarihlenir; istisnalar, git daha önceki tarihleri saklayamadığı için 1970-01-01 tarihli olan 1970 öncesi 28.838 commit ile 14 Kasım 2026'da eklenip o gün tarihlenen 1.885 karardır. Bir tarihi `git log --before` ile değil, `tools/in_force_on.py` ile sorun.

Bir düzenlemedeki her değişiklik onu yapan düzenlemeye atfedilir (`Kanun 6552`, `KHK 666`, `Anayasa Mahkemesi K. 2014/81`): 658 commit. Hiçbir düzenlemenin tek başına açıklamadığı bir değişiklik yayıncıya, `Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı)`, `Kind: unexplained` olarak ve olası düzenlemeler `Candidate:` içinde verilerek atfedilir (303 commit); yalnızca dizgi değişiklikleri `Kind: editorial` olarak işaretlenir (387). Kararlar ve diğer metinler, çoğunlukla numaralarıyla, onları çıkaran kuruma atfedilir (`Uyuşmazlık Mahkemesi K. 2025/582`, `Rekabet Kurulu`, `GIB sirkuler 614`). Düzeltmeler ayrı commit'ler olarak eklenir (`Kind: correction`, şu ana kadar 14).

## Ne kadar güncel

- [FRESHNESS.md](FRESHNESS.md): her kaynağın ne kadar güncel olduğu, kaynak kaynak, ve global-law'un bu depoyu nasıl gördüğü
- [WATCHING.md](WATCHING.md): Türkiye için izlenen her resmî kaynak, onda neyin okunduğu ve en son ne zaman okunduğu
- [monitoring/](monitoring/): bu deponun durumu (son commit'ler, neler geldi, neler gecikti) ve bir fork'un GitHub Actions ile nasıl güncel tutulacağı

## Nasıl denetlenir

- `tools/build/check_repo.py` ilk derlemenin her kanununu, KHK'sini ve CBK'sini git'ten geri okudu: her güncel metni sitenin sunduğu HTML ile sözcüğü sözcüğüne, her önceki sürümü yayıncının `.doc` dosyasının Microsoft Word'ün kendisinin ürettiği metniyle karşılaştırdı ve karakterlerde hiçbir fark bulmadı. Aynı dosyalardan yapılan iki derleme aynı commit özetlerini verir ([`REPRODUCE.md`](REPRODUCE.md)).
- O zamandan beri eklenen bölümler, kullandıkları kaynak dosyaların sha256 özetlerini (`data/` altındaki defterlerinde `source_sha256`, commit'lerinde `Source-sha256:`) kaydeder ve her commit'te tarihin nasıl seçildiğini söyler.
- Geçmiş yalnızca eklenerek büyür: `main` dalı yalnızca büyür, merge commit'i içermez ve yayımlanmış hiçbir commit yeniden yazılmaz.
- [vulnerabilities/](vulnerabilities/): global-law'un dedektörlerinin bulduğu ve elle denetlenen, Türk mevzuatındaki olası düzenleme hataları.

## Neleri göstermez

- **İçtihadın çoğu.** Yargıtayın ve alt mahkemelerin kararları ile Danıştayın 9 karar dışındaki kararları otomatik olarak okunamıyor ve bu engeller aşılmıyor; içtihadı birleştirme kararları Resmî Gazete'den alınmak üzere planlandı. Anayasa Mahkemesine bireysel başvurular, üst veri ve bağlantılardan oluşan bir dizindir; 970 karar tam metniyle buradadır.
- **Çoğu düzenlemenin geçmişi.** Önceki metinleri olan 280 kanun dışındaki her düzenleme güncel metniyle başlar; önceki geçmişi Resmî Gazete'deki değiştirici düzenlemelerden alınmak üzere planlandı.
- **Diğer tebliğler (4.482 tebliğin 4.284 tanesi burada), Cumhurbaşkanı kararları (4.374 kararın 1.740 tanesi burada) ve kurum ve kuruluş yönetmelikleri, milletlerarası andlaşmalar ve kanun teklifleri** ile 185 mülga kanunun ve yürürlükte olmayan 170 Cumhurbaşkanlığı kararnamesinin çoğu: planlanan bölümler (bkz. `PLAN.md`).
- **Özel kişiler.** Bir karar özel bir kişiyi adlandırıyor ve yayıncı bunu anonimleştirmiyorsa burada yalnızca üst verisi ve bağlantısı vardır.
- **Resimler ve biçimlendirme** (kalın, italik, girinti). Osmanlı dönemi tarihleri (Rumi ya da Hicri) dönüştürülmez, basıldığı gibi tutulur.

## Kaynaklar

| Kaynak | Tür | Önceki sürümler | Notlar |
| --- | --- | --- | --- |
| [Mevzuat Bilgi Sistemi](https://www.mevzuat.gov.tr) (T.C. Cumhurbaşkanlığı Hukuk ve Mevzuat Genel Müdürlüğü) | Konsolide mevzuat: kanunlar, KHK, CBK, tüzükler, yönetmelikler; kanun dizini | 280 kanun için sakladığı tüm önceki metinler ("Önceki metinler"); diğerleri için güncel metin | Hukuken bağlayıcı metin Resmî Gazete'deki metindir |
| [Resmî Gazete](https://www.resmigazete.gov.tr) | Resmî gazete: her sayının günlük fihristi | yayımlandığı gibi | İlanlar hiçbir zaman saklanmaz |
| [Anayasa Mahkemesi](https://normkararlarbilgibankasi.anayasa.gov.tr) | Norm denetimi, bireysel başvuru, siyasi partiler, Yüce Divan, yasama dokunulmazlığı | yayımlandığı gibi | Bireysel başvurular bir dizin olarak |
| [Uyuşmazlık Mahkemesi](https://kararlar.uyusmazlik.gov.tr), [Sigorta Tahkim Komisyonu](https://www.sigortatahkim.org) | Mahkeme kararları, hakem kararları | yayımlandığı gibi | |
| [Rekabet Kurumu](https://www.rekabet.gov.tr), [RTÜK](https://www.rtuk.gov.tr) | Kurul kararları | yayımlandığı gibi | Gizli bölümler yayıncının kararattığı gibi |
| [Gelir İdaresi Başkanlığı](https://www.gib.gov.tr) | Özelgeler, sirküler | yayımlandığı gibi | |
| [YSK](https://www.ysk.gov.tr), [Sayıştay](https://www.sayistay.gov.tr), [TBMM](https://www.tbmm.gov.tr) | Seçim kararları, Sayıştay kararları, Meclis kararları | yayımlandığı gibi | |
| [Ankara](https://www.ankara.bel.tr) ve [Bursa](https://www.bursa.bel.tr) Büyükşehir Belediyeleri | Meclis kararları | yayımlandığı gibi | Özel bir kişi adlandırılmışsa yalnızca üst veri ve bağlantı |

## Lisans

Bkz. [`LICENSE`](LICENSE). Fikir ve Sanat Eserleri Kanununun (5846 sayılı Kanun, [`law/1951/5846/madde-31.md`](law/1951/5846/madde-31.md)) 31. maddesi, resmen yayımlanan veya ilan olunan kanun, Cumhurbaşkanlığı kararnamesi, yönetmelik, tebliğ, genelge ve kazai kararların çoğaltılmasını, yayılmasını, işlenmesini veya her hangi bir suretle bunlardan faydalanmayı serbest kılar. Lexifina'nın kendi katkıları (araçlar, içeriğin düzenlenişi ve commit mesajları) CC0 1.0 kapsamındadır.

Hiçbir yapay zekâ modeli hukuki metni yazmadı ya da değiştirmedi; betikleri yapay zekâ modelleri yazdı (bkz. [`REPRODUCE.md`](REPRODUCE.md)).

Bu metin İngilizce sürümün ([README.en.md](README.en.md)) çevirisidir; aralarında fark olursa İngilizce sürüm geçerlidir.

## Görselleştirmeler

[visualisations/](visualisations/): bu depodan çizilmiş 20 grafikte Türk hukuku.

Bunlar arasında:

- Türkiye Büyük Millet Meclisinin kaç kanun çıkardığı, kanunların konusu ve torba kanunlar
- Olağanüstü hal, tezkereler ve yürürlükteki kanunların nasıl değiştiği
- Resmî Gazete, büyükşehir belediye meclisleri ve Anayasa Mahkemesi

## Daha fazla

[lexifina/global-law](https://github.com/lexifina/global-law) deposundan (İngilizce):

- [FEATURES.md](https://github.com/lexifina/global-law/blob/main/FEATURES.md): tüm özellikler ve her derlemin desteklemesi gerekenler (`git blame`, `law.py`, MCP araçları)
- [FAQ.md](https://github.com/lexifina/global-law/blob/main/FAQ.md): sorular ve yanıtlar · [CONTRIBUTING.md](https://github.com/lexifina/global-law/blob/main/CONTRIBUTING.md): değişiklik önermek · [MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md): MCP sunucusu · [REPRODUCE.md](https://github.com/lexifina/global-law/blob/main/REPRODUCE.md): nasıl oluşturulduğu · [CHANGELOG.md](https://github.com/lexifina/global-law/blob/main/CHANGELOG.md)
- [FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md): her derlemin ne kadar güncel olduğu · [İzleme](https://github.com/lexifina/global-law/tree/main/monitoring): güncellemelerin çalışıp çalışmadığı · [WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md): her resmî kaynağın değişiklikler için nasıl izlendiği
- [performance/](https://github.com/lexifina/global-law/tree/main/performance): araçların ölçülmüş hızı
- [visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations): tüm dünya hukuku genelinde grafikler ve bağlantılar
- [Zafiyetler](https://github.com/lexifina/global-law/tree/main/vulnerabilities): yayımlandığı hâliyle mevzuattaki hatalar
