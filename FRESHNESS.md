# Güncellik: bugün de doğru mu?

[English](FRESHNESS.en.md)

global-law'un her derlemin güncelliğini nasıl ölçtüğü (durumlar, 7 ve 30 günlük eşikler, `freshness.py` aracı): [global-law FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md). Burada aynı ölçü Türkiye için, kaynak kaynak verilir.

## global-law onu nasıl görüyor

| Derlem | Durum | Son denetim | Yöntem | global-law'daki commit | Buradaki daha yeni commit |
| --- | --- | --- | --- | --- | ---: |
| `turkey/national/acts` | `stale` | 28.10.2026 | `stated` | `20521f6996` | 10.174 |

`stale`: ulusal mevzuat için eşik, son denetimden bu yana 7 gündür. global-law sabitlenmiş commit'ten daha yeni olanları bir sonraki geçişinde alır; o zamana kadar onları burada okuyun.

## Kaynak kaynak

"En yeni kayıt", gelecekte olmayan en geç yürürlük ya da karar günüdür (Resmî Gazete için fihristteki en son sayı); "en son okunma", bu deponun kaynaktan en son bir şey yayımladığı gündür. Eşik: ulusal mevzuat için 7 gün, mahkeme ve kurul kararları, yerel düzenlemeler ve diğer kayıtlar için 30 gün.

| Kaynak | Commit | En yeni kayıt | En son okunma | Geçen gün | Durum | Not |
| --- | ---: | --- | --- | ---: | --- | --- |
| Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı) | 5.845 | 11.11.2026 | 14.11.2026 | 0 | güncel |  |
| Resmî Gazete | 6 | 14.11.2026 | 14.11.2026 | 0 | güncel |  |
| Türkiye Büyük Millet Meclisi | 9 | 21.07.1993 | 14.11.2026 | 0 | güncel |  |
| Anayasa Mahkemesi | 3.368 | 14.10.2026 | 14.11.2026 | 0 | güncel |  |
| Uyuşmazlık Mahkemesi | 415 | 15.06.2026 | 14.11.2026 | 0 | güncel |  |
| Rekabet Kurumu | 2.031 | 03.05.2018 | 14.11.2026 | 0 | güncel |  |
| Sigorta Tahkim Komisyonu | 121 | 29.09.2026 | 14.11.2026 | 0 | güncel |  |
| Radyo ve Televizyon Üst Kurulu | 1 | 17.04.2024 | 14.11.2026 | 0 | güncel |  |
| Yüksek Seçim Kurulu | 456 | 07.10.2026 | 14.11.2026 | 0 | güncel |  |
| Sayıştay | 8 | 16.10.2017 | 14.11.2026 | 0 | güncel |  |
| Ankara Büyükşehir Belediyesi | 247 | 10.02.2022 | 14.11.2026 | 0 | güncel |  |
| Bursa Büyükşehir Belediyesi | 18 | 15.01.2026 | 14.11.2026 | 0 | güncel |  |

## Kendiniz denetleyin

```
git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- law/    # yayımlanan son kanun commit'i ve yürürlük günü
git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- case-law/constitutional-court/norm/    # Anayasa Mahkemesinin yayımlanan son norm denetimi kararı
tail -n 3 monitoring/landed.tsv    # main dalına son push'lar
```

İlgilendiğiniz tarih son denetimden sonraysa metni resmî kaynakla karşılaştırın. Yalnızca resmî yayın hukuken bağlayıcıdır.
