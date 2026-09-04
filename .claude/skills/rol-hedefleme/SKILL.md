---
name: rol-hedefleme
description: Hangi unvanlara ve sektörlere başvurulacağını belirleyen çift ajan akışını yürütür — rol-onerici-profil ve rol-onerici-gecmis ajanlarını bağımsız çalıştırır, çıktılarını karşılaştırır, dört mutabakat sınıfına ayırır ve data/role_targets.json'a yazar. "Hangi işlere başvurabilirim", "CV'me göre ne aramalıyım", "rol hedeflerini güncelle" dendiğinde ve Profil sayfasındaki rol önerileri bölümü değiştirilirken kullan. İki ajanı tek çıktıya indirgeme — ayrıştıkları yer asıl bilgi.
---

# Rol hedefleme

Kullanıcının üç sorusundan ikincisinin ("enerjimi nereye harcamalıyım")
ileri hali: *hangi unvanı aramalıyım?* Yanıtı tek bir ajana sordurmuyoruz
— **iki ajan birbirini denetliyor.**

## Neden iki ajan

Tek ajan CV'ye bakıp "bunları yapabilirsin" der ve iyimser çıkar; ya da
yalnızca geçmişe bakıp "burada başarısız oldun" der ve daraltır. İkisi
ayrı kanıta baktığı için **anlaşmazlıkları bilgi taşır:**

- `rol-onerici-profil` → yalnızca `data/profile.json` + CV. Yukarı doğru:
  *bu profil ne yapabilir?*
- `rol-onerici-gecmis` → yalnızca `data/applications.json` + `insights.py`
  + Indeed ilan varlığı. Aşağı doğru: *sahada ne oldu, ne var?*

Kanıt tabanları **kesişmez** ve bu kasıtlı. Bir ajana ötekinin verisini
verirsen iki ajan tek ajana döner, karşılaştırmanın anlamı kalmaz.

## Akış

1. İkisini **aynı turda, birbirinden habersiz** çalıştır. Birinin
   çıktısını ötekine girdi olarak verme.
2. Çıktıları unvan bazında eşleştir. Eşleştirme unvan varyantlarını da
   kapsar — "Ticari Analist" ile "Commercial Analyst" aynı satırdır
   (`unvan_varyantlari` alanı bunun için var).
3. Her unvanı dört mutabakat sınıfından birine koy.
4. `data/role_targets.json`'a yaz.

## Dört mutabakat sınıfı

| Sınıf | Ne demek | Kullanıcıya ne denir |
|---|---|---|
| **`teyitli`** | İkisi de öneriyor | En güçlü hedef — hem profil destekliyor hem sahada karşılığı var |
| **`profil_destekli`** | Yalnızca profil kanadı öneriyor | Profil uygun ama bu rolde henüz kanıt yok — denenmemiş olabilir, deneme sayısı azdır |
| **`kanit_destekli`** | Yalnızca geçmiş kanadı öneriyor | Sahada karşılığı var ama profilde dayanağı zayıf — açığı kapatmak gerekebilir |
| **`celiskili`** | Biri öneriyor, öteki açıkça kaçınılması gerekenler listesine koymuş | Karar kullanıcıya bırakılır, iki gerekçe de yan yana gösterilir |

**Çelişkiyi ortalama alarak çözme.** İki ajan "bu rol iyi" ve "bu rolde
6 başvurudan 5'i kapandı" diyorsa doğru çıktı ortalama bir puan değil,
iki cümlenin yan yana durmasıdır. Kullanıcı hangi kanıta ağırlık
vereceğine kendi karar verir — bu projenin iki eksen kuralının aynısı.

## `data/role_targets.json` şeması

```json
{
  "meta": {
    "uretim_tarihi": "YYYY-MM-DD",
    "profil_surumu": "profile.json'daki cv_version",
    "basvuru_sayisi": 68
  },
  "hedefler": [
    {
      "unvan": "Ticari Analist",
      "unvan_varyantlari": ["Commercial Analyst"],
      "kidem_bandi": "uzman",
      "sektorler": ["e-ticaret", "q-commerce"],
      "mutabakat": "teyitli | profil_destekli | kanit_destekli | celiskili",
      "profil_dayanak": "profil kanadının gerekçesi | null",
      "gecmis_dayanak": "geçmiş kanadının gerekçesi + örnek sayısı | null",
      "ornek_sayisi": 6,
      "ilan_var_mi": "Indeed İstanbul: 12 sonuç | bakılmadı",
      "engel": "iki kanattan gelen engeller, yoksa null",
      "arama_sorgusu": "Indeed/LinkedIn aramasına birebir yazılacak metin"
    }
  ],
  "kacinilacaklar": [
    { "unvan": "…", "sebep": "…", "kanat": "profil | gecmis | ikisi" }
  ]
}
```

## Kurallar

**`ornek_sayisi` n<4 ise geçmiş kanadının gerekçesi "veri yetersiz"
etiketiyle gösterilir.** 68 başvuru 40 `track`'e dağılmış; tek kayıtlı
bir track'ten sonuç çıkmaz.

**Şirket ve tekil ilan önerilmez.** Çıktı unvan + sektör düzeyinde kalır.
İlan sağlayıcılarla anlaşmamız yok; Indeed yalnızca "bu unvanın ilanı
var mı" sorusunu yanıtlamak için kullanılır, sonuçtaki şirketler
listelenmez.

**Indeed dışında ilan kaynağı kazınmaz.** LinkedIn'in Kullanıcı
Sözleşmesi kazımayı yasaklıyor ve fiilen takip ediyor. LinkedIn'den
gelen tek meşru veri, kullanıcının kendi gelen kutusundaki maillerdir.

**Maaş ve piyasa büyüklüğü verisi yok.** İlan sayısı talep göstergesi
değildir; "bu alan büyüyor" cümlesi kurulmaz.

**`kariyer-danismani` ile karıştırma.** O ajan konumlandırma stratejisi
ve İK ekranı kritiği üretir (nerede eleniyorsun, enerji nerede israf).
Bu akış somut bir **arama listesi** üretir. Biri "neden", öteki "ne
arayacaksın".

## Yeniden üretim

`profile.json` değiştiğinde (yeni CV) veya başvuru sayısı anlamlı
şekilde arttığında akış yeniden koşulur. `meta.profil_surumu` eski
kalmışsa liste bayattır — arayüzde tarih gösterilir.
