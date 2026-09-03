---
name: egitim-onerisi
description: data/skills_catalog.json'a yeni bir beceri/kaynak eklerken veya Eğitim sayfası ile red-anındaki kurs kartının içeriğini değiştirirken izlenecek kurallar — kaynak şeması, çizik-fiyat/indirim alanları, öncelik sıralaması (src/insights.py'deki skill_gaps formülü) ve üç yerde zorunlu simülasyon etiketi. "gap_skills"e yeni bir anahtar eklerken, eğitim sayfasını veya kurs kartını değiştirirken, ya da journey.json'daki {top_gap_name}/{top_gap_count} kalıplarına dokunurken bu skill'i kullan. Simülasyon etiketini kaldırma veya "gerçek kurs" gibi göster — CLAUDE.md'nin kaldırılmaz üç sınırından biri burada.
---

# Eğitim önerisi

Gauge'un üçüncü sorusuna ("neyi öğrenmem gerekiyor?") cevap veren blok.
`data/skills_catalog.json` tek doğruluk kaynağı — Eğitim sayfası ve
başvuru detayındaki red-anı kurs kartı **aynı veriyi** okur, ikisi asla
ayrışmaz. Biri değişirse öteki otomatik değişir çünkü ikisi de
`src/insights.py`'deki `learning_plan()` çıktısını kullanır.

## Kurs kayıtları simülasyondur — kaldırılmaz kural

`data/skills_catalog.json`'ın `_note` alanı bunu zaten söylüyor: başlıklar,
puanlar, süreler, fiyatlar örnek amaçlı; `url` her zaman `"#"`; gerçek bir
sayfaya gitmez. Bu proje henüz bir kurs sağlayıcı API'sine bağlı değil.

**Bu üç yerde ayrı ayrı etiketlenir, üçü de zorunlu:**

1. **Sayfa bandı** — Eğitim sayfasının üstünde "Kurs kayıtları
   simülasyondur; bağlantılar gerçek sayfa açmaz." gibi bir uyarı
2. **Liste etiketi** — her kaynak kartında `simtag`/"simülasyon" rozeti
3. **Tıklama bildirimi** — bir kaynağa tıklandığında toast: "Simülasyon
   verisi — bu kurs bağlantısı gerçek değil."

Yeni bir kaynak eklerken veya arayüzü değiştirirken bu üçünü kontrol et.
Biri eksilirse kullanıcı gerçek bir kursa tıkladığını sanabilir — bu
CLAUDE.md'nin "ölçülemeyen şey uydurulmaz" ilkesinin ihlali sayılır,
tasarım tercihi değildir.

## Yeni bir skills_catalog girişi ekleme

Bir `gap_skills` anahtarı kataloğa henüz girmemişse (`eslestirici` veya
`ilan-cozumleyici` bunu fark edip `notlar`'a yazar, kendi eklemez — bu
skill devreye girip senin eklemen için var):

```json
"anahtar": {
  "name": "Görünen ad",
  "cv_level": 0,
  "target_level": 5,
  "why": "Bu eksikliğin kaç ilanı, hangi gerekçeyle etkilediği — tek-iki cümle",
  "effort": "X hafta, haftada ~Y saat",
  "resources": [
    {
      "title": "…", "provider": "Udemy | DataCamp | Coursera | Pluralsight | …",
      "rating": 4.6, "students": 50000, "duration": "…",
      "cost": "₺XXX", "level": "Başlangıç | Orta | İleri",
      "note": "Bu kaynağın neden seçildiği — tek cümle",
      "url": "#", "simulated": true,
      "price_now": "₺XXX", "price_was": "₺YYY", "discount_pct": 60
    }
  ]
}
```

`cv_level`/`target_level` `data/profile.json`'daki gerçek beceri seviyeleriyle
tutarlı olmalı — CV'de olmayan bir şey için `cv_level: 0`, CV'de zayıf bir
şey için mevcut puanı yaz, uydurma.

**Fiyat alanları tutarlı olmalı:** `price_now` ≈ `price_was` × (1 −
`discount_pct`/100). Rastgele bir indirim yüzdesi yazıp iki fiyatı
ilgisiz bırakma — sayılar sahte olsa da birbiriyle tutarlı olmalı, yoksa
"düşünülmemiş" görünür.

3-4 kaynak yeterli; farklı sağlayıcılardan ve farklı seviyelerden seç
(başlangıç + ileri gibi) ki öneri tek kaynağa bağımlı görünmesin.

## Öncelik sıralaması — burada yeniden tanımlama

Hangi eksikliğin listenin başında çıkacağı `src/insights.py` →
`skill_gaps()` içinde hesaplanır:

```
öncelik = red_sayısı × 3 + açık_süreç_sayısı × 1 + (target_level − cv_level) × 2
```

Bu formülü burada kopyalayıp elle uygulama — kod tek kaynak, burada sadece
mantığı bil: bir eksiklik **redlerde görüldüyse** en ağır basan sinyal
(×3), hâlâ açık süreçleri etkiliyorsa orta (×1), CV ile hedef arasındaki
seviye farkı da katkı yapar (×2). Yeni bir kayıt eklerken `cv_level`/
`target_level` farkını gerçekçi tut — abartılı bir fark, o eksikliği
olduğundan önemli gösterir.

**"Redlerde görüldü" bir çıkarımdır, red gerekçesi değil** — `basis` alanı
bunu zaten söylüyor: "taranan 15 red e-postasının hiçbiri gerekçe
belirtmiyor." Bir kaynağın `why` metninde bunu "X yüzünden reddedildin"
gibi kesin bir dille yazma; "bu ilanlar X bekliyordu, CV'de zayıf" de.

## journey.json'daki şablon değişkenleri

`egitim` sayfasının `engaged` aşaması nudge metni `{top_gap_name}` ve
`{top_gap_count}` kalıplarını taşır — bunlar render sırasında
`learning_plan()`'ın ilk sırasındaki eksiklikle doldurulur. **Bu sayıyı
elle yazma.** Daha önce "21 başvuruyu etkiliyor" diye sabit bir sayı
yazılmıştı, gerçek sayı 34'tü — kalıp bunun için var, sabit metin tekrar
ayrışır.

## Yapmayacakların

- `url` alanına gerçek bir bağlantı yazma — bu proje henüz bir kurs
  sağlayıcı API'sine bağlı değil, bağlanana kadar hepsi `"#"`
- Üç etiketten birini "arayüz sadeleşsin" diye kaldırma
- `skill_gaps()`'in öncelik formülünü bu dosyada yeniden tanımlama —
  kod değişirse burası ayrışır
