---
name: cv-analizi
description: Bir CV'yi data/profile.json şemasına çevirirken izlenecek çıkarım kuralları — kıdem bandı nasıl belirlenir, araç seviyeleri 1-5 nasıl atanır, güçlü alan/sektör/açık listeleri nasıl doldurulur, lokasyon politikası nasıl kurulur. Yeni CV yüklendiğinde, profile.json güncellenirken, "CV'mi analiz et" dendiğinde ve Bağlan sayfasındaki CV yükleme akışı değiştirilirken bu skill'i kullan. Seviyeleri ve bantları göz kararı atama — rubrik burada; profile.json eşleşme motorunun tek referansı, keyfi bir değer bütün puanları kaydırır.
---

# CV analizi

`data/profile.json`, CV'den türetilmiş profildir ve **eşleşme motorunun
tek referansıdır** (`src/match.py` onu okur). Buradaki bir değer keyfi
atanırsa 68 başvurunun tamamının puanı kayar. O yüzden çıkarım kuralları
yazılı.

## Şema

```json
{
  "name": "…", "cv_version": "YYYY-MM (dosya adı)", "location": "…",
  "headline": "tek satır — rol + alan + süre",
  "summary": "2-3 cümle, CV'nin kendi iddiası",
  "seniority": { "current_title": "…", "level": "…",
                 "years_professional": 0.0, "years_total_incl_early": 0.0,
                 "target_bands": [], "stretch_bands": [], "overreach_bands": [],
                 "note": "…" },
  "experience": [ { "title": "…", "company": "…", "from": "YYYY-MM",
                    "to": "YYYY-MM|null", "highlights": [] } ],
  "education": { "school": "…", "degree": "…", "graduated": "YYYY-MM" },
  "skills": { "Araç adı": 1-5 },
  "languages": { "Dil": "anadil|ileri|orta|başlangıç" },
  "domains_strong": [], "industries_strong": [], "industries_transferable": [],
  "gaps": [ "tek cümle, neyin eksik olduğu ve nerede sorun çıkaracağı" ],
  "location_policy": { "istanbul_onsite": 0, "remote_tr": 0, "hybrid_istanbul": 0,
                       "remote_eu": -8, "relocation_required": -12,
                       "language_barrier": -20 }
}
```

## Kıdem bandı

`years_professional`, **staj hariç** tam zamanlı profesyonel süredir.
Stajı `years_total_incl_early` içine kat, ikisini karıştırma — çoğu İK
ekranı stajı saymıyor, biz de saymıyoruz.

Üç bant listesi şöyle kurulur:

- **`target_bands`** — mevcut kıdemin doğal karşılığı ve altı. 2 yıllık
  bir uzman için: intern, trainee, junior, associate, analyst, specialist
- **`stretch_bands`** — bir tık üstü, esneyerek girilebilir: senior
  specialist, senior analyst
- **`overreach_bands`** — kıdem açığı olan bantlar: manager, senior
  manager, lead, head, director

**Ekip yönetimi deneyimi yoksa `manager` ve üstü daima `overreach`'tir.**
Bu keyfi değil: veride 15 redden 7'sinde eksik olan şey buydu. `note`
alanına sebebi yazılır.

## Araç seviyeleri (1–5)

CV'de "biliyorum" yazması 5 demek değil. Seviye, **ne yaptığından**
türetilir:

| Seviye | Ölçüt |
|---|---|
| 5 | Günlük iş aracı; onunla üretilmiş somut çıktı CV'de anlatılıyor |
| 4 | Düzenli kullanıyor, bir projede belirleyici rol oynamış |
| 3 | Kullanabiliyor ama derinliği yok — sorgu yazar, mimari kurmaz |
| 2 | Eğitim/kurs düzeyinde, işte kullanılmamış |
| 1 | Adını biliyor |
| — | CV'de hiç geçmiyorsa **listeye eklenmez**, 0 yazılmaz |

Seviyeyi CV'nin iddiasından değil, deneyim maddelerinden doğrula. "İleri
SQL" yazıyor ama hiçbir maddede SQL ile yapılmış bir iş yoksa 3'ü geçme.

## `gaps` yazımı

Her açık **tek cümle** ve iki parça taşır: ne eksik + nerede sorun
çıkaracak.

İyi: *"Python ve ileri veri bilimi CV'de yok — DS/ML ağırlıklı ilanlarda
dezavantaj"*
Kötü: *"Python bilmiyor"* — nerede sorun olacağını söylemiyor.

Açıklar `eslesme-puanlama`'daki beceri boyutunu ve `gap_skills`
atamasını doğrudan besler; eksik yazılan bir açık orada da eksik kalır.

## Sektör listeleri

- **`industries_strong`** — içinde fiilen çalıştığı sektörler
- **`industries_transferable`** — çalışmadığı ama iş modeli benzer
  olduğu için deneyimin taşındığı sektörler; gerekçesi olmalı
- **`domains_strong`** — sektör değil **iş alanı** (growth analitiği,
  FP&A, ticari strateji). İkisini karıştırma; `eslesme-puanlama`'da
  rol ailesi ile sektör ayrı boyutlar.

## Lokasyon politikası

`location_policy` değerleri `eslesme-puanlama`'daki lokasyon cezalarıyla
**aynı olmak zorunda**; ikisi ayrışırsa puanlar tutarsızlaşır. Değeri
burada değiştiriyorsan skill'i de güncelle.

`language_barrier: -20` yalnızca adayda olmayan bir dilin **şart**
koşulduğu ilanlar için. "İngilizce artı" bir engel değildir.

## Sık yapılan hatalar

- **CV'nin pazarlama dilini veri sanmak.** "Stratejik dönüşüme liderlik
  etti" cümlesi ekip yönetimi kanıtı değildir. Doğrudan rapor eden ekip
  aranır.
- **Staj süresini profesyonel süreye katmak.** Kıdem bandını yukarı
  kaydırır, bütün eşleşme puanlarını bozar.
- **CV'de olmayan aracı "muhtemelen biliyordur" diye eklemek.** Yoksa
  listeye girmez.
- **`cv_version` güncellememek.** Yeni CV yüklendiğinde bu alan
  değişmezse hangi sürümden türetildiği kaybolur.
