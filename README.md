# İş Başvurusu Takip Otomasyonu

Atalay Denizer'in LinkedIn ve ATS üzerinden yaptığı iş başvurularını Gmail
(`atalay.denizer0@gmail.com`) ile entegre biçimde takip eden otomasyon ve
raporlama sistemi.

Sistem üç parçadan oluşur:

| Parça | Ne yapar | Nerede çalışır |
|---|---|---|
| **Günlük Routine** | Her sabah 09:00 (TSİ) Gmail'i tarar, panoyu günceller, özet e-posta atar | Claude Routine (`trig_01UdkGdW5SJxvPVB2X3ZSgYJ`) |
| **Veri katmanı** | Tüm başvuruların tek doğruluk kaynağı | `data/applications.json` |
| **Raporlama** | Önceliklendirme, hatırlatma ve tablo üretimi | `src/pipeline.py`, `src/build_dashboard.py` |

## Hızlı kullanım

```bash
# Bugünün raporu (Markdown)
python3 src/pipeline.py

# E-postaya uygun kısa düz metin
python3 src/pipeline.py --format text

# Excel/Sheets'e aktarılabilir tablo
python3 src/pipeline.py --format csv --out reports/tablo.csv

# Haftalık özet + geri bildirim soruları
python3 src/pipeline.py --weekly

# HTML kontrol panosu
python3 src/build_dashboard.py
```

Tarihi sabitlemek için (test): `--today 2026-09-05`.

## Önceliklendirme nasıl çalışır

Her başvuru 0–140 arası bir puan alır:

```
puan = aşama_ağırlığı + (uyum × 4) + deadline_aciliyeti − sessizlik_cezası
```

- **Aşama ağırlığı** — teklif 100, mülakat planlama 88, değerlendirme/test 85,
  sonraki aşama 82, mülakat yapıldı 78, başvuru yarım 70, incelemede 35.
- **Uyum (`fit`, 1–5)** — rolün hedef profile yakınlığı, elle atanır.
- **Deadline aciliyeti** — geçmiş deadline +40, bugün/yarın +35, 2-3 gün +25,
  4-7 gün +15, 8-14 gün +8.
- **Sessizlik cezası** — 12+ gün sessiz −8, 21+ gün sessiz −20.

Puan ve deadline birlikte bir öncelik bandına eşlenir:
🔴 Kritik · 🟠 Yüksek · 🟡 Normal · ⚪ Düşük · ⚫ Kapandı.

## Hatırlatma kuralları

`config/rules.yaml` içindeki `reminders` bölümünde tanımlı:

- Deadline'a 2 gün veya daha az kaldıysa → "bugün kapat"
- Deadline geçtiyse → "uzatma iste ya da kapat"
- Mülakattan 5+ gün geçtiyse → "nazik takip maili at"
- 12+ gün sessizlik → "takip maili zamanı"
- 21+ gün sessizlik → "kapanmış say"

## Geri bildirim döngüsü

Sistem tek yönlü rapor üretmez; haftalık olarak dört soru sorar
(`--weekly` çıktısında ve panonun altında):

1. Bu hafta hangi 3 role odaklanmak istiyorsun?
2. Sessizleşen süreçlerden hangilerini kapatalım?
3. Hedef sektör/rol/lokasyon tercihin değişti mi?
4. Maaş beklentin güncellenmeli mi?

Yanıtlar günlük rapor e-postasına cevap olarak yazılır ve bir sonraki taramada
`fit` puanlarına ve kapatılacak süreçlere yansıtılır.

## Dosya düzeni

```
data/applications.json          Tek doğruluk kaynağı — tüm başvurular
config/rules.yaml               Gmail sorguları, sınıflandırma, puanlama, hatırlatmalar
src/pipeline.py                 Önceliklendirme + rapor üretimi (md/text/csv/json)
src/build_dashboard.py          HTML pano üreticisi
src/dashboard.template.html     Pano şablonu (veri enjekte edilir)
reports/                        Üretilen raporlar ve pano
docs/otomasyon.md               Routine'in ayrıntılı işleyişi ve bakımı
```

## Kapsam

İlk tarama **1 Ağustos – 1 Eylül 2026** penceresini kapsar: 68 başvuru,
6 yanıtlanmamış recruiter mesajı. LinkedIn iş ilanı bildirimleri, Glassdoor ve
bülten e-postaları gürültü sayılır ve yalnızca adet olarak raporlanır.
