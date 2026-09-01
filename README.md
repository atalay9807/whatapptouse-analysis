# İş Başvurusu Takip Otomasyonu

Atalay Denizer'in LinkedIn ve ATS üzerinden yaptığı iş başvurularını Gmail
(`atalay.denizer0@gmail.com`) ile entegre biçimde takip eden otomasyon ve
raporlama sistemi.

Sistem üç parçadan oluşur:

| Parça | Ne yapar | Nerede çalışır |
|---|---|---|
| **Günlük Routine** | Her sabah 09:00 (TSİ) Gmail'i tarar, panoyu günceller, özet e-posta atar | Claude Routine (`trig_01UdkGdW5SJxvPVB2X3ZSgYJ`) |
| **Veri katmanı** | Tüm başvuruların tek doğruluk kaynağı | `data/applications.json` |
| **Eşleşme motoru** | CV ↔ ilan uyumunu puanlar ve segmentler | `src/match.py`, `data/profile.json` |
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

# CV eşleşme özeti (segmentler + en iyi/en zayıf eşleşmeler)
python3 src/match.py
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

## CV eşleşme motoru

`data/profile.json`, CV'den türetilmiş profildir: kıdem bandı, güçlü alanlar,
araç seviyeleri ve bilinen açıklar. Her ilan bu profile karşı **0–100** arası
puanlanır:

```
eşleşme = rol_ailesi(35) + kıdem(25) + beceri_örtüşmesi(25) + sektör(15) − lokasyon_cezası
```

| Boyut | Neyi ölçer |
|---|---|
| **Rol ailesi (35)** | Rolün growth analitiği / FP&A / ticari strateji / iş-veri analizi çekirdeğine yakınlığı |
| **Kıdem (25)** | İlanın bandı ile 2 yıllık Specialist seviyesinin uyumu. Manager/Lead ilanları esneme sayılır |
| **Beceri örtüşmesi (25)** | İlanın beklediği araç seti ile CV'nin örtüşmesi (Excel/Tableau güçlü, SQL orta, Python yok) |
| **Sektör (15)** | q-commerce / e-ticaret / teslimat deneyimine yakınlık |
| **Lokasyon cezası** | Uzaktan EU −8, taşınma zorunluluğu −12, dil engeli −20 |

Segmentler:

| Segment | Aralık | Ne yapmalı |
|---|---|---|
| 🟢 Güçlü | 78–100 | Öncelikli kovala, takip maili at, hazırlık yap |
| 🔵 İyi | 62–77 | Sağlam aday, süreci canlı tut |
| 🟡 Orta | 45–61 | Kısmi uyum, zaman kalırsa ilerlet |
| 🔴 Zayıf | 0–44 | Düşük getiri, kapatmayı değerlendir |

Her başvurunun `match.rationale` alanı puanın **neden** o değerde olduğunu tek
cümleyle açıklar; pano bu gerekçeyi ve dört boyutun dökümünü gösterir.

**Aciliyet ve eşleşme iki ayrı eksendir.** Aciliyet "bugün ne yapmalıyım"ı,
eşleşme "enerjimi nereye harcamalıyım"ı yanıtlar. Zayıf eşleşmeli bir ilanın
deadline'ı da acil olabilir — pano ikisini ayrı kolonlarda gösterir ki karar
sende kalsın.

## Aksiyon linkleri

Her başvuru kaydı `links_actions` dizisi taşır. Üç tür link üretilir:

- **Gerçek aksiyon URL'i** — yalnızca e-postada doğrulanmış bağlantılar
  (ör. Nebil Project'in TestGorilla test linki). Uydurulmaz.
- **Hazır takip maili** — `contact` alanında e-posta varsa, duruma göre
  (mülakat sonrası / süre uzatımı / durum sorusu) konusu ve gövdesi doldurulmuş
  bir `mailto:` bağlantısı.
- **Gmail'de yazışmayı aç** — şirket adına göre Gmail araması açan derin bağlantı.
  Her kayıt için üretilir; şirketin kendi portal linkine oradan ulaşılır.

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
data/applications.json          Tek doğruluk kaynağı — tüm başvurular + eşleşme boyutları
data/profile.json               CV'den türetilmiş profil (eşleşmenin referansı)
config/rules.yaml               Gmail sorguları, sınıflandırma, puanlama, hatırlatmalar
src/match.py                    CV ↔ ilan eşleşme motoru ve segmentasyon
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

Eşleşme dağılımı: 22 güçlü, 29 iyi, 13 orta, 4 zayıf. Başvuruların %25'i
orta/zayıf eşleşmeye gitmiş; güçlü segmentin ileri aşamaya geçme oranı %18,2.

## Sonraki adım: uygulama

Bu repo, planlanan uygulamanın veri ve mantık katmanıdır. Uygulama yazılmadan
önce burada olgunlaştırılan parçalar:

- ✅ Tek doğruluk kaynağı şeması (`applications.json` + `profile.json`)
- ✅ Önceliklendirme ve hatırlatma kuralları
- ✅ CV tabanlı eşleşme puanlaması ve segmentasyon
- ✅ Aksiyon linki üretimi
- ✅ Arayüz prototipi (`reports/pano.html`)
- ⬜ Kullanıcı başına çoklu profil desteği
- ⬜ İlan metninin otomatik çekilip beceri çıkarımı yapılması
  (şu an `match` boyutları elle atanıyor)
- ⬜ Kalıcı veritabanı ve oturum yönetimi
