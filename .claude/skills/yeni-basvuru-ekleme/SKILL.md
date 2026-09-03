---
name: yeni-basvuru-ekleme
description: data/applications.json'a yeni bir başvuru kaydı açarken izlenecek kurallar — id biçimi, channel/track/fit alanlarının nasıl belirlendiği, aynı şirkete tekrar başvuruda dedup, location/contact biçimi. Mail taraması yeni bir başvuru bulduğunda, ilan-cozumleyici+eslestirici çıktısı kayda dönüştürülürken veya kullanıcı "bu başvuruyu ekle" dediğinde kullan. Şema alanlarını uydurma veya CLAUDE.md'deki özetten hatırlamaya çalışma — biçim burada, 68 gerçek kayıttan çıkarıldı.
---

# Yeni başvuru ekleme

`mail-siniflandirma` bir maili "buna karşılık gelen kayıt yok" diye
işaretlediğinde, ya da `ilan-cozumleyici` + `eslestirici` ikilisinin
ürettiği veri `data/applications.json`'a inecekken bu skill devreye girer.
Amaç, 68 kaydın tutarlı olduğu biçimi bozmadan 69'uncuyu eklemek.

Zorunlu alanların şeması CLAUDE.md'de (`Veri katmanı` bölümü); burada onun
**nasıl doldurulacağı** var — gerçek 68 kayıttan çıkarılmış konvansiyonlar.

---

## `id`

`sirket-rol` biçiminde, küçük harf, kelimeler arası tire, Türkçe karakterler
ASCII'ye çevrilir (ş→s, ı→i, ğ→g, ü→u, ö→o, ç→c).

- `peks-global-ticari-analist`, `yapikredi-peoplise`
- Rol ilanda belirsizse (yalnızca "başvurunuz alındı" maili, unvan yok)
  yalnızca şirket adı yeterli: `trendyolgo`, `omtera-join`
- Aynı şirkete **farklı bir rol** için ikinci kez başvurulduysa id'ye rolü
  ayırt edici ek yap (`sirket-rol2`), şirket adını tekrar kullanma yalın
  haliyle — birinci kayıtla çakışır

**Aynı şirkete aynı role tekrar mail geldiyse** (ör. ATS "başvurunuz alındı"
sonra "değerlendirmeye devam" gönderdi) bu **yeni kayıt değil**, mevcut
kaydın güncellenmesi. Önce id'yi ara, bulamazsan yeni aç.

## `channel`

Beş değer var, gönderici adresinden çıkar:

| Değer | Nereden anlaşılır |
|---|---|
| `ats` | Gönderici `config/rules.yaml` → `ats_senders` listesindeki bir alan adından (workday, lever, ashby, smartrecruiters…) |
| `linkedin` | Gönderici `linkedin.com` uzantılı, LinkedIn Easy Apply veya kaydedilen ilan akışı |
| `indeed` | Gönderici `indeed.com` |
| `aggregator` | Kariyer.net, Yenibiris gibi iş ilanı toplayıcısı üzerinden — ATS değil, LinkedIn değil |
| `direct` | Şirketin kendi İK'sından doğrudan mail, hiçbir aracı platform yok |

Emin değilsen ATS sağlayıcı listesine tekrar bak — çoğu "belirsiz" durum
aslında bilinen bir ATS'in az bilinen bir alan adı olur.

## `track`

Serbest metin, sabit bir liste değil ama konvansiyon var: tek kelime
(`Growth`, `Finance`, `Retail`) veya `Ana/İkincil` biçiminde iki alan
(`Data/Fintech`, `Growth/Product`, `Marketing/Data`). İkinci kelimeyi yalnızca
rol gerçekten iki alanı birden kapsıyorsa ekle — zorlama.

Rol ailesini burada tekrar tanımlama; `track` gruplamak için, `match.rationale`
gerekçelendirmek için var.

## `fit` (1–5)

**Elle atanır, otomatik türetilmez.** `match` segmentiyle fikren örtüşür ama
aynı şey değil — `fit` önceliklendirme formülünde (`docs/TEKNIK.md`) kullanılır,
`match` toplamı eşleşme ekseninde ayrı yaşar. Kaba karşılık:

- 🟢 Güçlü (78–100) → `fit` 4–5
- 🔵 İyi (62–77) → `fit` 3–4
- 🟡 Orta (45–61) → `fit` 2–3
- 🔴 Zayıf (0–44) → `fit` 1–2

Ama son karar burada değil — `eslestirici` puanı hesapladıktan sonra fit'i
elle ver, mekanik yuvarlama yapma. Aynı segmentte iki ilan farklı `fit`
alabilir (biri deadline'ı geçmiş ve artık önemsiz, diğeri hâlâ canlı).

## `location`

Serbest metin, gördüğün biçimlerden biri:

- `"İstanbul, Türkiye"` — yalnızca şehir/ülke biliniyorsa
- `"Maslak, İstanbul (ofis, 5 gün)"` — çalışma düzeni netse parantez içine ekle
- `"Remote"` — tamamen uzaktan, konum şartı yoksa
- `"Puffy — Dubai, on-site"` gibi taşınma gerektiren roller için şehir açıkça yazılır (lokasyon cezasının kaynağı burası)

## `contact`

Yalnızca **doğrudan bir İK kişisiyle yazışma varsa** doldurulur (68 kaydın
6'sında var — çoğu kayıtta yok, bu normal). Üçüncü kişi kuralı burada da
geçerli:

```
"contact": "İK Müdürü — ik@sirket.example"
```

Gerçek isim/e-posta asla girmez. `.example` alan adı zorunlu.

## `match` ve `gap_skills`

Bu alanları burada doldurma — `eslesme-puanlama` skill'ine (veya
`eslestirici` ajanına) geç. Bu skill yalnızca kaydın **iskeletini** kurar;
puanlama ayrı bir disiplin.

## `links_actions`

URL kuralı `mail-siniflandirma` skill'inde — tekrar yazılmıyor. Özet: yalnızca
mailde doğrulanmış link gerçek URL olur, yoksa Gmail arama derin bağlantısı.

## Kayıttan sonra doğrula

Yeni kayıt eklendikten sonra:

```bash
python3 src/match.py      # match toplamı ve segment doğru hesaplanıyor mu
python3 src/pipeline.py   # yeni kayıt rapora düşüyor mu, şema hatası var mı
```

Biri hata verirse önce şemaya bak — eksik zorunlu alan, yanlış tarih biçimi
(`YYYY-MM-DD` değilse) veya `links_actions` içinde `kind` unutulmuş olabilir.
