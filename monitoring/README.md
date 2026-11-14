# İzleme: Türkiye kaydı ayak uyduruyor mu?

[English](README.en.md)

global-law'un tüm derlemleri nasıl izlediği (15 dakikada bir geçiş, her commit'in denetimi, herkese açık bir durum): [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring). Bu sayfa yalnızca bu deponun durumudur.

**Durum 14.11.2026**

| | |
| --- | --- |
| Son commit | main dalına ulaştı 2026-11-14 18:13 UTC: Üniversite Yönetmeliği 46376: İSTANBUL ÜNİVERSİTESİ SÜREKLİ EĞİTİM UYGULAMA VE ARAŞTIRMA MERKEZİ YÖNETMELİĞİ |
| Son 24 saat | Mevzuat Bilgi Sistemi 3.483; Anayasa Mahkemesi 3.368; Rekabet Kurumu 2.031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; belge 11; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| Son 7 gün | Mevzuat Bilgi Sistemi 3.484; Anayasa Mahkemesi 3.368; Rekabet Kurumu 2.031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; belge 12; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| Son 30 gün | Mevzuat Bilgi Sistemi 5.845; Anayasa Mahkemesi 3.368; Rekabet Kurumu 2.031; YSK 456; Uyuşmazlık Mahkemesi 415; Ankara Büyükşehir 247; Sigorta Tahkim Komisyonu 121; Bursa Büyükşehir 18; belge 15; TBMM 9; Sayıştay 8; Resmî Gazete 6; RTÜK 1 |
| global-law | `turkey/national/acts` `stale`, `20521f6996` commit'ine sabitli, burada 10.174 daha yeni commit |
| Gecikmiş kaynaklar | yok ([FRESHNESS.md](../FRESHNESS.md)) |

Zamanlar her commit'in `main` dalına ulaştığı andır ([`landed.tsv`](landed.tsv)); commit tarihleri yürürlük ya da karar günleridir.

## Yeni değişiklikler nasıl gelir

1. Her kaynağın şeridi yeni metinlerin listesini okur (bkz. [WATCHING.md](../WATCHING.md)) ve her değişikliği, yürürlüğe girdiği ya da verildiği günle tarihlenmiş bir commit olarak yayımlar.
2. Yayımlanmadan önce her commit bu deponun denetimlerinden geçer: metin kaynakla, tarihler yayıncının kendi tarihleriyle karşılaştırılır (bkz. [REPRODUCE.md](../REPRODUCE.md)).
3. global-law her 15 dakikada bir yeni commit'leri denetler ve `turkey/national/acts` üzerindeki işaretçisini ilerletir (bkz. [global-law monitoring/](https://github.com/lexifina/global-law/tree/main/monitoring)).

## Kendiniz denetleyin

```
git fetch && git log -1 --format="%h %s" origin/main
python monitoring/make_pages.py --github lexifina/turkey-law    # bu üç sayfayı GitHub'ın push kaydıyla yeniden oluştur
python monitoring/make_plan.py                                  # PLAN.md'yi yeniden say
```

## Kendiniz izleyin: bir fork ve GitHub Actions

Herkes bu depoyu fork'layabilir ve kendi kopyasını bize ihtiyaç duymadan güncel tutabilir. GitHub Actions herkese açık depolar için ücretsizdir.

1. Fork'layın: <https://github.com/lexifina/turkey-law/fork>.
2. Fork'ta [`monitoring/fork-workflow.yml`](fork-workflow.yml) dosyasını `.github/workflows/refresh.yml` olarak kopyalayın ve `main` dalına commit edin.
3. Fork'un **Actions** sekmesinde iş akışlarını etkinleştirin (GitHub fork'larda bunları varsayılan olarak kapatır) ve **Refresh from lexifina/turkey-law** iş akışını bir kez çalıştırın.

İş akışı her 6 saatte bir bu deponun yeni commit'lerini fork'unuzun `main` dalına alır (GitHub'ın kendi "Sync fork" özelliğiyle; böylece `main` bu depo artı sizin iş akışı dosyanızdır), kopyanız için WATCHING, FRESHNESS ve bu sayfayı yeniden oluşturur, iniş kaydını (`landed.tsv`) her çalışmada büyütür, bunları bir `status` dalına yayımlar ve FRESHNESS'ı çalışma özetinde gösterir. Bir çalışma birkaç dakika sürer. İş akışı resmî kaynakları okumaz: bu deponun ne kadar güncel olduğunu denetler.
