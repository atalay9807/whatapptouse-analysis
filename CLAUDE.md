# Gauge — proje talimatları

İş başvurusu takip ve CV eşleştirme sistemi. Gmail'i tarar, başvuruları tek
yerde toplar, her ilanı CV'ye göre puanlar, eksik yetkinlikleri çıkarır ve
günlük hatırlatma üretir.

**Çıktı dili Türkçe.** Kod, değişken adı ve commit mesajı dahil her şey Türkçe
yazılır; yalnızca teknik terimlerin yerleşik İngilizce karşılıkları korunur
(`match`, `pipeline`, `commit`). Kullanıcıya "sen" diye hitap edilir.

---

## En kritik kural: ölçülemeyen şey uydurulmaz

Bu proje, ölçemediği şeyleri açıkça söylediği için güvenilir. Bu üç sınır
arayüzün her yerinde etiketlidir ve **kaldırılmaz, yumuşatılmaz:**

| Sınır | Neden | Nasıl gösterilir |
|---|---|---|
| **Red gerekçeleri bilinmiyor** | Taranan 15 red e-postasının hiçbiri sebep belirtmiyor, hepsi kalıp metin | Eksik yetkinlikler "ÇIKARIM" diye etiketlenir; şirketin söylediği gibi sunulmaz |
| **Görüntülenen ilan verisi yok** | LinkedIn bunu e-postayla bildirmiyor | Huninin ilk adımı taralı çubukla "alt sınır" işaretlenir; ondan sonraki dönüşüm oranı **hesaplanmaz** |
| **Kurs kayıtları simülasyon** | Gerçek kurs API'si bağlı değil | Sayfa bandı + liste etiketi + tıklama bildirimi olmak üzere üç yerde belirtilir |

Buna bağlı iki davranış kuralı:

- **URL uydurulmaz.** Yalnızca e-postada doğrulanmış bağlantılar `links_actions`
  içine gerçek URL olarak girer. Doğrulanmamışsa Gmail arama derin bağlantısı
  üretilir.
- **Üçüncü kişilerin adı ve e-postası depoya girmez.** Demo verisi anonimdir;
  İK çalışanları rol etiketiyle temsil edilir (`İK Müdürü — ik@x.example`).
  `.example` alan adı RFC 2606 gereği hiçbir zaman gerçek olamaz.

---

## Veri katmanı

`data/` altındaki JSON dosyaları **tek doğruluk kaynağıdır.** Kod bunları okur,
asla içine sabit veri gömülmez.

| Dosya | İçerik |
|---|---|
| `applications.json` | 68 başvuru: aşama, durum, deadline, `match` boyutları, `gap_skills`, `links_actions` |
| `profile.json` | CV'den türetilmiş profil — eşleşmenin referansı |
| `skills_catalog.json` | Beceri → kaynak eşlemesi. **Eğitim sayfası ve başvuru detayındaki kurs kartı buradan beslenir**, ikisi asla ayrışmaz |
| `journey.json` | Yaşam döngüsü aşamaları ve sayfa bazlı yönlendirmeler |
| `engagement.json` | Gerçek rapor gönderim günleri (streak hesabı) |
| `saved_jobs.json` | Kaydedilip başvurulmayan ilanlar (huninin üstü) |

---

## İki puanlama ekseni — karıştırılmaz

**Aciliyet** "bugün ne yapmalıyım", **eşleşme** "enerjimi nereye harcamalıyım"
sorusunu yanıtlar. Zayıf eşleşmeli bir ilanın deadline'ı da acil olabilir;
arayüz ikisini ayrı kolonda gösterir, karar kullanıcıya bırakılır.

```
aciliyet = aşama_ağırlığı + (uyum × 4) + deadline_aciliyeti − sessizlik_cezası
eşleşme  = rol_ailesi(35) + kıdem(25) + beceri_örtüşmesi(25) + sektör(15) − lokasyon_cezası
```

**Eşleşme segmentleri:** 🟢 Güçlü 78–100 · 🔵 İyi 62–77 · 🟡 Orta 45–61 · 🔴 Zayıf 0–44

**Hatırlatma eşikleri:** deadline ≤2 gün → bugün kapat · deadline geçti → uzatma
iste ya da kapat · mülakattan 5+ gün → takip maili · 12+ gün sessizlik → takip
maili · 21+ gün → kapanmış say

Ağırlıklar iki yerde yaşar: `config/rules.yaml` referans dokümandır, gerçek
değerler `src/pipeline.py` ve `src/match.py` başındaki sabitlerdedir.
**İkisi birlikte güncellenir.**

---

## Kod

Harici bağımlılık yok — yalnızca Python 3.11+ standart kütüphanesi. Arayüz tek
HTML dosyası, çerçeve kullanılmıyor.

```bash
python3 src/pipeline.py                 # rapor (md/text/csv/json)
python3 src/match.py                    # eşleşme özeti ve segmentler
python3 src/insights.py                 # sekiz rapor + eğitim planı
python3 src/build_dashboard.py          # arayüzü üret → reports/pano.html
```

`src/dashboard.template.html` şablondur; `/*__DATA__*/null` yerine veri enjekte
edilir. **`reports/pano.html` ve `site/app.html` türetilmiş dosyalardır** —
elle düzenlenmez, şablon değiştirilip yeniden üretilir.

Arayüz değiştiğinde sırayla: `build_dashboard.py` → `site/app.html`'e kopyala →
ekran görüntülerini yenile → `site/img`'i eşitle.

---

## Tasarım sistemi

Üç renk üç ayrı iş yapar, birbirine karışmaz:

- **İndigo** (`--brand`) — marka, gezinme, hacim grafikleri
- **Mor rampa** (`--m1`…`--m4`, sıralı) — yalnızca eşleşme kalitesi
- **Kırmızı / kehribar / yeşil** — boru hattı durumu, ayrılmış semantik renkler

Tipografi: **Newsreader** (başlık) + **Archivo** (gövde) + **IBM Plex Mono**
(etiket, sayı, veri).

Açık ve koyu tema ikisi de orta tonda — ne beyaz kâğıt ne siyah ekran. Yapı
gölgeyle değil ince çizgiyle kurulur.

**Renk eklerken kontrast ölçülür, göz kararı yapılmaz.** Metin kendi zeminine
karşı 4.5:1, grafik dolgusu 3:1 geçmeli; her iki temada ayrı ayrı. Rampalar
açıklık bakımından monotonik olmalı. Ölçüm için `dataviz` skill'indeki
`validate_palette.js` kullanılır.

---

## Depo

- Geliştirme dalı: `claude/linkedin-job-tracking-automation-6xiogy`
- `main`'e `--no-ff` ile merge edilir; `site/**` değişince Pages otomatik dağıtır
- Commit mesajları Türkçe, **ne yapıldığını değil neden yapıldığını** anlatır
- `site/_artifact.html` türetilmiştir, `.gitignore`'dadır

---

## Açık maddeler

- ⬜ **İlan metninin otomatik çekilip beceri çıkarımı** — `match` boyutları ve
  `gap_skills` şu an elle atanıyor. Projenin en zayıf halkası; ajan işi.
- ⬜ Kullanıcı başına çoklu profil desteği
- ⬜ Kalıcı veritabanı ve oturum yönetimi

---

## Referans

- `docs/TEKNIK.md` — formüller, bakım notları, tasarım kararları
- `docs/otomasyon.md` — günlük Routine'in işleyişi
- `docs/kaynak-claude-code-kursu.md` — ajan/skill mimarisi için izlenen kurs
