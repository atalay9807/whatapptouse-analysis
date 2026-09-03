---
name: rapor-formati
description: Gauge'un günlük ve haftalık raporlarını üretir: aciliyet puanlaması, hatırlatma eşikleri, e-posta gövdesinin yapısı ve pazartesi geri bildirim bloğu. Günlük rapor yazılırken, "raporu üret", "bugün ne yapmalıyım", "hatırlatmaları çıkar" dendiğinde, Routine'in prompt'u düzenlenirken ve takip maili taslağı hazırlanırken bu skill'i kullan. Eşikleri ve tablo kolonlarını ezberden yazma — burada. Rapor sessiz kalmamalı; kritik gelişme yoksa bunu da açıkça söylemeli.
---

# Rapor formatı

Gauge'un çıktı katmanı. İki şeyi ayrı tutar: **aciliyet** ("bugün ne
yapmalıyım") ve **eşleşme** ("enerjimi nereye harcamalıyım"). Rapor ikisini
ayrı kolonda gösterir ve kararı kullanıcıya bırakır — birleştirilmiş tek bir
"öncelik" puanı üretmez, çünkü zayıf eşleşmeli bir ilanın deadline'ı da acil
olabilir ve bunu kullanıcı bilmek ister.

Üretim `python3 src/pipeline.py` ile yapılır. Formülleri ve eşikleri elle
hesaplama — sabitler `src/pipeline.py` başındadır.

---

## Aciliyet puanı

```
aciliyet = aşama_ağırlığı + (uyum × 4) + deadline_aciliyeti − sessizlik_cezası
```

**Aşama ağırlıkları:** teklif 100 · mülakat planlama 88 · değerlendirme/test 85 ·
sonraki aşama 82 · mülakat yapıldı 78 · başvuru yarım 70 · süreçte 60 ·
incelemede 35 · yetenek havuzu 20 · kapandı 0

**Deadline aciliyeti:** geçmiş +40 · bugün/yarın +35 · 2-3 gün +25 ·
4-7 gün +15 · 8-14 gün +8

**Sessizlik cezası:** 12+ gün −8 · 21+ gün −20

Bantlar: 🔴 Kritik (≥100 ya da `action_required` + deadline ≤3 gün) ·
🟠 Yüksek (≥75) · 🟡 Normal (≥45) · ⚪ Düşük

## Hatırlatma eşikleri

| Koşul | Hatırlatma |
|---|---|
| Deadline geçti | "⏳ Deadline N gün önce doldu — uzatma iste ya da kapat." |
| Deadline bugün | "🔥 Deadline BUGÜN." |
| Deadline ≤2 gün | "⏰ Deadline N gün sonra." |
| Deadline 3-7 gün | "📅 Deadline N gün sonra." |
| Mülakattan 5+ gün, dönüş yok | "✉️ Mülakattan N gün geçti — nazik takip maili at." |
| 12+ gün sessizlik | "✉️ N gündür sessiz — takip maili zamanı." |
| 21+ gün sessizlik | "💤 N gündür sessiz — kapanmış say, listeden düşür." |

Bu eşikler keyfi değil: taranan veride şirketlerin **medyan yanıt süresi 10
gün**. 12 gün, "artık normal süreyi aştı" demek için makul ilk sinyal.

---

## Günlük rapor e-postası

Konu: `📋 Günlük İş Takip Raporu — <gün> <Ay> <yıl>`

Gövde sırası:

1. **🔴 Bugün kapatılacaklar** — kritik banttaki her iş için şirket, pozisyon,
   *tam olarak ne yapılacağı* ve deadline durumu. Genel laf değil, eylem yaz:
   "TestGorilla testini bitir ve 3 soruya mail at" — "Nebil sürecini ilerlet" değil.
2. **Son 24 saat** — yeni mülakat davetleri, testler, teklifler, redler, yeni
   başvuru onayları. Hiçbiri yoksa bunu açıkça yaz.
3. **Öncelik tablosu** — kritik ve yüksek banttakiler:
   `Şirket | Pozisyon | Aşama | Deadline | Sessiz gün | Aciliyet | Eşleşme | Sonraki adım`
4. **⏰ Hatırlatmalar** — yukarıdaki eşiklerden çıkanlar.
5. **Otomatik bildirimler** — gürültü sayısı tek satır: "23 ilan bildirimi,
   4 bülten (rapora alınmadı)."

### Sessiz kalma

Kritik gelişme yoksa rapor **yine gönderilir** ve şu ikisini yapar: durumu
açıkça söyler ("Son 24 saatte yeni mülakat daveti, test, teklif veya red
gelmedi.") ve açık kalan aksiyonları tekrar hatırlatır. Boş rapor, kullanıcının
sisteme güvenini bir günde bitirir.

## Pazartesi geri bildirim bloğu

Pazartesileri rapora `💬 Senden beklenen geri bildirim` bölümü eklenir:

1. Bu hafta hangi **3 role** odaklanmak istiyorsun?
2. Sessizleşen süreçlerden hangilerini **kapatalım**?
3. Hedef sektör, rol ya da lokasyon tercihin değişti mi?
4. Maaş beklentin güncellenmeli mi?

Bu blok kozmetik değil: `data/engagement.json`'a göre **hiç geri bildirim
yazılmamış** ve kullanıcı bu yüzden "alışkanlık" aşamasına geçemiyor. Döngü
kapanmadan sistem tercihleri öğrenemiyor.

**Her gün** ayrıca önceki rapora yanıt gelip gelmediği kontrol edilir:

```
from:<kullanıcı> newer_than:2d subject:"İş Takip Raporu"
```

Yanıt varsa istekleri o çalışmada uygulanır (kapatılması istenen süreçler
arşive taşınır, öncelik değişiklikleri puanlamaya yansır) ve raporun en başına
tek satır teyit yazılır: *"Geri bildirimin uygulandı: …"*

## Takip maili şablonları

`links_actions` içinde `mailto:` olarak üretilir. `contact` alanında e-posta
yoksa üretilmez. Duruma göre üç şablon:

**Mülakat sonrası takip** (`stage: interviewed`)
> Konu: `<rol> pozisyonu — görüşme sonrası takip`
> Görüşme için teşekkür + sürecin bir sonraki adımı hakkında bilgi talebi.

**Süre uzatımı** (`status: action_required`, deadline geçmiş)
> Konu: `<rol> başvurusu — süre uzatımı talebi`
> Adımı tamamlayamadığını söyle, süreç açıksa ek süre iste.

**Durum sorusu** (diğer)
> Konu: `<rol> başvurusu — durum sorusu`
> Mevcut durum hakkında bilgi talebi + ilginin sürdüğünü belirt.

Üçü de kısa, üç paragrafı geçmez, imzada ad + e-posta + telefon olur.
Abartılı nezaket ve dolgu cümlesi yok.

## Diğer çıktı biçimleri

```bash
python3 src/pipeline.py --format text    # e-posta gövdesine uygun düz metin
python3 src/pipeline.py --format csv     # Sheets'e aktarılabilir tablo
python3 src/pipeline.py --format json    # makine okunur
python3 src/pipeline.py --weekly         # geri bildirim bölümü dahil
python3 src/insights.py                  # sekiz raporun tamamı
```

## Ölçülemeyen şey raporlanmaz

Rapor üç şeyi **asla** kesin gibi sunmaz:

- **Red gerekçeleri** — hiçbir red maili sebep belirtmiyor. Eksik yetkinlikler
  "çıkarım" diye etiketlenir.
- **Görüntülenen ilan sayısı** — LinkedIn bildirmiyor. Huninin ilk adımı
  "alt sınır" olarak işaretlenir, ondan sonraki dönüşüm oranı hesaplanmaz.
- **Kurs verisi** — simülasyon olarak etiketlidir.

Bu etiketler raporu zayıf göstermiyor, güvenilir kılıyor. Kaldırılmaz.
