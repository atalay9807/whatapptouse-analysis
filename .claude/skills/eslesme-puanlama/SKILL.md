---
name: eslesme-puanlama
description: Bir iş ilanını Trace'in CV profiline karşı dört boyutta puanlar (rol ailesi 35 + kıdem 25 + beceri örtüşmesi 25 + sektör 15 − lokasyon cezası) ve dört segmentten birine yerleştirir. Yeni bir başvuru eklenirken, mevcut bir başvurunun match alanı doldurulurken veya güncellenirken, "bu ilan bana uyar mı", "kaç puan verir", "hangi segmentte" türünden sorularda, ilan metni değerlendirilirken ve gap_skills atanırken bu skill'i kullan. Puanları elle uydurma — rubrik burada. data/applications.json içindeki match objesine dokunulan her işte gerekli.
---

# Eşleşme puanlama

Trace'in iki ekseninden biri: **eşleşme**, "enerjimi nereye harcamalıyım"
sorusunu yanıtlar. Aciliyet ekseniyle karıştırılmaz — zayıf eşleşmeli bir
ilanın deadline'ı da acil olabilir.

Referans profil `data/profile.json` içindedir. Puanlarken oradan oku; bu
dosyadaki özet değişebilir, `profile.json` doğruluk kaynağıdır.

**Profilin özeti:** 2 yıl profesyonel deneyim, Growth Strategy Specialist.
Güçlü: growth analitiği (lifecycle, churn, CRM, kohort), FP&A (bütçe, forecast,
P&L), ticari strateji (fiyatlandırma, esneklik). Araçlar: Excel 5/5, Tableau 5/5,
Sheets+Apps Script 4/5, SQL 3/5, Power BI 3/5, Mixpanel 3/5. Sektör: q-commerce,
e-ticaret, teslimat. Açıklar: Python yok, ekip yönetimi yok, mühendislik lisansı.

---

## Dört boyut

Toplam ham puan 100; lokasyon cezası bundan düşülür. Her boyutu ayrı ayrı
gerekçelendir — tek bir "hissiyat" puanı verme.

### Rol ailesi — 0-35

Rolün, profilin çekirdek iş ailelerine yakınlığı. En belirleyici boyut bu,
çünkü bir insan yanlış aileye başvurduğunda diğer üç boyut kurtaramıyor.

| Puan | Ne | Örnek |
|---|---|---|
| 33–35 | Çekirdek ailenin tam karşılığı: strategic finance + analytics, ticari analist, FP&A, financial analyst, founder's associate, pricing | Strategic Finance and Analytics Specialist (35), Ticari Analist (34), CFO Office Executive (33) |
| 29–32 | Çekirdeğe komşu: BI analyst, data analyst, growth marketer, analitik pazarlama, CX analyst | Pricing Continuous Improvement (32), BI Analyst (31), Growth Marketer (30) |
| 24–28 | Kısmi örtüşme: growth PM, süreç mükemmelliği, tedarik zinciri analisti, data operations, kurucu ekip | Growth Product Manager (28), Data Operations Fellow (26), Kurucu ekip (24) |
| 18–23 | Zayıf: teknik product owner, BT/altyapı BA, müşteri çözümleri, trade marketing, rol belirsiz | BT altyapı BA (20), rol belirtilmemiş (18) |
| 10–17 | Analitik dışı: satış/BD, müşteri başarısı, influencer marketing, saatlik AI eğitim gig'i | Data Analyst (AI training) (14), yetenek havuzu (12) |
| 0–9 | Hiç kesişmiyor | International Ice-Cream Taster (2) |

**Rol belirsizse** (ilanda unvan yok, yalnızca şirket biliniyor) 18 civarı ver ve
`rationale`'da belirsizliği yaz. Tahminle yukarı çekme.

### Kıdem — 0-25

İlanın kıdem bandı ile 2 yıllık Specialist seviyesinin uyumu. Bu boyut,
verinin gösterdiği en pahalı hatayı yakalıyor: **15 redden 7'sinde eksik olan
şey ekip yönetimiydi**, yani sorun beceri değil kıdem bandıydı.

| Puan | Band |
|---|---|
| 25 | Analyst, Specialist, Associate, Junior, Intern — profilin bandı |
| 23 | Management Trainee / Graduate program (bandın bir tık altı ama marka değeri var) |
| 20–22 | Senior Specialist, Senior Analyst, Executive (hafif esneme) |
| 15–18 | Product Manager, Product Owner (ürün sahipliği deneyimi yok) |
| 13 | Manager (ekip yönetimi deneyimi yok — esneme) |
| 5–8 | Senior Manager, Lead, Head, Director, Regional Lead (ciddi esneme) |

### Beceri örtüşmesi — 0-25

İlanın beklediği araç setinin CV ile kesişimi. Pratikte 16–23 aralığında
yoğunlaşıyor; uçlara ancak gerçekten uç durumlarda gidilir.

- **21–23** — Excel/Tableau/kohort/P&L merkezli; CV'nin güçlü olduğu şeyler
- **18–20** — SQL veya Power BI orta düzeyde bekleniyor (CV 3/5, yetiyor ama sınırda)
- **14–17** — Python, ileri istatistik, dbt veya veri mühendisliği bekleniyor
- **10–13** — Alanın kendi araç seti CV'de hiç yok (satış CRM'i, tasarım, saha)
- **0–9** — Teknik kesişim yok

### Sektör yakınlığı — 0-15

| Puan | Sektör |
|---|---|
| 13–15 | q-commerce, teslimat, online marketplace, e-ticaret |
| 11–12 | fintech, bankacılık, ödeme, yatırım platformu |
| 9–10 | perakende, FMCG, seyahat, oyun, telco |
| 7–8 | endüstriyel, lojistik, ilaç, ajans |
| 4–6 | otelcilik, akademik yayıncılık, lüks perakende |
| 0–3 | tamamen ilgisiz |

### Lokasyon cezası — ≤0

Toplamdan düşülür. Veride üç değer kullanılıyor:

- **0** — İstanbul ofis, İstanbul hibrit, Türkiye'den uzaktan
- **−8** — Uzaktan ama AB/İngiltere merkezli (çalışma izni belirsiz)
- **−12** — Taşınma zorunlu (ör. Dubai ofis)
- **−20** — Sahip olunmayan bir dil şart (ör. anadil Arapça)

---

## Segmentler

```
eşleşme = rol_ailesi + kıdem + beceri + sektör + lokasyon_cezası
```

🟢 **Güçlü 78–100** — öncelikli kovala, takip maili at
🔵 **İyi 62–77** — sağlam aday, süreci canlı tut
🟡 **Orta 45–61** — kısmi uyum, zaman kalırsa
🔴 **Zayıf 0–44** — düşük getiri, kapatmayı değerlendir

**Aritmetiği elle yapma.** Dört boyutu `data/applications.json` içindeki `match`
objesine yaz, sonra `python3 src/match.py` çalıştır. Segment eşikleri ve
toplama `src/match.py` içindedir; burada tekrar tanımlanmaz ki ikisi ayrışmasın.

## Gerekçe yazımı

Her `match` objesi bir `rationale` taşır: **tek cümle**, puanın neden o
değerde olduğunu söyler. İyi gerekçe hem güçlü hem zayıf tarafı adlandırır.

İyi: *"Ticari analist = ticari strateji + P&L + fiyatlandırma deneyiminin tam
karşılığı."*
İyi: *"Growth işi birebir ama 'Manager/Senior Manager' kıdemi 2 yılın üstünde."*
Kötü: *"İyi bir eşleşme."* — hangi boyut yüzünden olduğunu söylemiyor.

## gap_skills

İlanın beklediği ama CV'de zayıf/olmayan yetkinlikler. `data/skills_catalog.json`
içindeki anahtarlardan seçilir — yeni anahtar uydurma, gerekiyorsa kataloğa
önce ekle.

**Bunlar çıkarımdır, red gerekçesi değildir.** Taranan 15 red e-postasının
hiçbiri sebep belirtmiyor. Arayüz bu ayrımı her yerde etiketliyor; puanlama
yaparken de aynı dili koru: "bu ilan X bekliyordu, CV'de yok" de,
"X yüzünden reddedildi" deme.

## Sık yapılan hatalar

- **Marka değerini rol ailesine yazmak.** Amazon'un Content Acquisition Manager
  ilanı prestijli olabilir ama rol ailesi 12'dir. Prestij puanı diye bir boyut yok.
- **Kıdemi yumuşatmak.** "Manager ama belki alırlar" diye 13'ü 20'ye çekmek,
  verinin gösterdiği en pahalı hatayı gizler.
- **Sektörü rol ailesiyle karıştırmak.** TrendyolGo'da rol belirsizdir (24) ama
  sektör birebir (15). İkisi ayrı satırdır.
- **Lokasyon cezasını unutmak.** Uzaktan EU rolleri puanı hak ettiğinden yüksek
  gösterir; 17 başvuruda −8 uygulanmış.
