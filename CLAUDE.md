# Gauge — proje talimatları

## Proje nedir

İş başvurusu takip ve CV eşleştirme sistemi. Gmail'i tarar, başvuruları tek
yerde toplar, her ilanı CV'ye göre puanlar, eksik yetkinlikleri çıkarır ve
günlük hatırlatma üretir. 30 günlük gerçek bir iş arama sürecinin verisi
(68 başvuru) üzerine kuruldu.

**İki işi birden görüyor:** hem sahibinin günlük kullandığı bir araç, hem de
işverene gösterilen bir portföy projesi. İkinci rol yüzünden depo herkese açık,
demo verisi anonim ve README işverene hitap ediyor.

## Hedef kullanıcı

Aynı anda çok sayıda başvuru yapan, hangisinin nerede olduğunu takip edemeyen
iş arayan biri. Teknik değil — arayüz açıklama gerektirmemeli. Sorduğu üç soru:

1. **Bugün ne yapmalıyım?** → aciliyet ekseni
2. **Enerjimi nereye harcamalıyım?** → eşleşme ekseni
3. **Neyi öğrenmem gerekiyor?** → eksik yetkinlik analizi

## Çalışma tarzı

- **Önce plan, sonra kod.** Birden fazla dosyaya dokunacak işlerde önce ne
  yapılacağını söyle, onay al. Tek satırlık düzeltmede plan yapma.
- **Küçük adımlar.** Bir turda bir konu bitir; yarım bırakılmış üç iş yerine
  bitmiş bir iş yeğdir.
- **Kısa yaz.** Yapılan işi anlat, süreci anlatma. Seçenek listesi dökme,
  önerini söyle.
- **Doğrula, iddia etme.** "Çalışıyor" demeden önce çalıştır. Renk eklerken
  kontrast ölç, göz kararı yapma. Ekran çıktısını görmeden "düzeldi" deme.
- **Sormadan yapma:** veri dosyalarını toplu silme/yeniden yazma, `main`'e push,
  depo adı veya görünürlük değişikliği, dışarıya bir şey yayınlama.
- **Sorman gerekmeyen:** kod düzeltme, şablon değişikliği, rapor yeniden üretme,
  geliştirme dalına commit.

## Dil ve üslup

Çıktı dili **Türkçe** — kod yorumları, değişken adları, commit mesajları,
arayüz metinleri dahil. Yalnızca yerleşik teknik terimler İngilizce kalır
(`match`, `pipeline`, `commit`, `deadline`).

Kullanıcıya **"sen"** diye hitap edilir. Ton: doğrudan, abartısız, kesin.
Övgü ve dolgu cümlesi yok. Kötü haber varsa önce o söylenir.

---

## En kritik kural: ölçülemeyen şey uydurulmaz

Bu proje, ölçemediği şeyleri açıkça söylediği için güvenilir. Üç sınır arayüzün
her yerinde etiketlidir ve **kaldırılmaz, yumuşatılmaz:**

| Sınır | Neden | Nasıl gösterilir |
|---|---|---|
| **Red gerekçeleri bilinmiyor** | 15 red e-postasının hiçbiri sebep belirtmiyor | Eksik yetkinlikler "ÇIKARIM" diye etiketlenir |
| **Görüntülenen ilan verisi yok** | LinkedIn e-postayla bildirmiyor | Huninin ilk adımı taralı çubukla "alt sınır"; ondan sonraki dönüşüm **hesaplanmaz** |
| **Kurs kayıtları simülasyon** | Gerçek kurs API'si bağlı değil | Üç yerde belirtilir: sayfa bandı, liste etiketi, tıklama bildirimi |

Bağlı iki kural:

- **URL uydurulmaz.** Yalnızca e-postada doğrulanmış bağlantılar gerçek URL
  olarak girer. Doğrulanmamışsa Gmail arama derin bağlantısı üretilir.
- **Üçüncü kişilerin adı/e-postası depoya girmez.** İK çalışanları rol
  etiketiyle temsil edilir (`İK Müdürü — ik@x.example`). `.example` alan adı
  RFC 2606 gereği hiçbir zaman gerçek olamaz.

---

## Genel çalışma akışı

Günlük Routine her sabah 09:00'da (TSİ): **tara → sınıflandır → veriyi güncelle
→ puanla → hatırlat → raporla.** Pazartesileri rapora geri bildirim soruları
eklenir. Her adımın ayrıntısı `mail-siniflandirma` ve `rapor-formati`
skill'lerinde.

## Veri katmanı

`data/` altındaki JSON dosyaları **tek doğruluk kaynağıdır.** Kod bunları okur,
koda asla sabit veri gömülmez.

| Dosya | İçerik |
|---|---|
| `applications.json` | 68 başvuru + `recruiter_outreach` |
| `profile.json` | CV'den türetilmiş profil — eşleşmenin referansı |
| `skills_catalog.json` | Beceri → kaynak eşlemesi. **Eğitim sayfası ve başvuru detayındaki kurs kartı buradan beslenir**, ikisi asla ayrışmaz |
| `journey.json` | Yaşam döngüsü aşamaları, sayfa yönlendirmeleri, şablon değişkenleri |
| `engagement.json` | Gerçek rapor gönderim günleri (streak hesabı) |
| `saved_jobs.json` | Kaydedilip başvurulmayan ilanlar (huninin üstü) |

**Başvuru kaydının şeması** — zorunlu alanlar:

```json
{
  "id": "sirket-rol",          "company": "…",     "role": "…",
  "channel": "ats|linkedin|direct|aggregator|indeed",
  "applied": "YYYY-MM-DD",     "last_contact": "YYYY-MM-DD",
  "stage": "offer|interview_scheduling|assessment|next_stage|interviewed|application_incomplete|in_process|under_review|talent_pool|closed",
  "status": "action_required|in_progress|awaiting_response|stale|rejected",
  "track": "…",                "fit": 1-5,
  "deadline": "YYYY-MM-DD|null",
  "next_step": "…",            "notes": "…",
  "match": { "role_family": 0-35, "seniority": 0-25, "skills": 0-25,
             "domain": 0-15, "location_mod": <=0, "rationale": "tek cümle" },
  "gap_skills": ["sql", "…"],
  "links_actions": [{ "label": "…", "url": "…", "kind": "mailto|gmail|ext" }]
}
```

Tarihler daima `YYYY-MM-DD`. Bilinmeyen alan `null` ya da `"—"`, **asla tahmin
edilmiş bir değer değil.**

## Puanlama — iki eksen karıştırılmaz

**Aciliyet** "bugün ne yapmalıyım", **eşleşme** "enerjimi nereye harcamalıyım"
sorusunu yanıtlar. Zayıf eşleşmeli bir ilanın deadline'ı da acil olabilir;
arayüz ikisini ayrı kolonda gösterir, karar kullanıcıya bırakılır.

```
aciliyet = aşama_ağırlığı + (uyum × 4) + deadline_aciliyeti − sessizlik_cezası
eşleşme  = rol_ailesi(35) + kıdem(25) + beceri_örtüşmesi(25) + sektör(15) − lokasyon_cezası
```

Eşleşme segmentleri: 🟢 Güçlü 78–100 · 🔵 İyi 62–77 · 🟡 Orta 45–61 · 🔴 Zayıf 0–44

Rubrikler, eşikler ve hatırlatma kuralları **skill'lerde** (aşağıda). Gerçek
sabitler `src/pipeline.py` ve `src/match.py` başındadır; `config/rules.yaml`
referans dokümandır. **Üçü birlikte güncellenir.**

## Kullanılabilir araçlar

| Araç | Ne için | Sınır |
|---|---|---|
| **Gmail MCP** | E-posta tarama, thread okuma, taslak | Yalnızca Claude Code oturumunda; yayınlanan sayfadan erişilemez |
| **Google Drive MCP** | CV ve doküman okuma | — |
| **GitHub MCP** | Depo, Actions, PR | Pages ayarı ve depo adı değiştirilemez — kullanıcı yapar |
| **`sample` yeteneği** | Yayınlanan sayfada CV analizi | Yalnızca claude.ai'de; Pages sürümünde çalışmaz |
| **Routine** | Günlük 09:00 tarama | `update_trigger` ile düzenlenir, **silinip yeniden kurulmaz** (geçmiş kaybolur) |
| **Playwright** | Arayüz doğrulama, ekran görüntüsü | Chromium: `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` |

Ortam kısıtı: **egress proxy** yalnızca paket kayıtlarına ve `github.com`'a
izin veriyor. `github.io`, YouTube ve rastgele siteler açılamaz — doğrulama
gerekiyorsa kullanıcıdan istenir.

## Hata davranışları

- **Veri eksikse uydurma.** Alan `null` bırakılır, arayüzde `—` gösterilir.
- **Kaynak erişilemiyorsa söyle.** "Test edemedim" demek, test edilmiş gibi
  davranmaktan iyidir.
- **Doğrulama başarısızsa rapor et.** Testi geçmiş gibi gösterme; çıktıyı ver.
- **Yanlış pozitifi ayır.** Otomatik denetim uyarı verdiğinde önce gerçek mi
  diye bak; değilse neden yanlış pozitif olduğunu yaz.
- **Türetilmiş dosya bozulduysa** elle düzeltme — kaynağı düzelt, yeniden üret.

## Çıktı şablonları

**Günlük rapor** — konu `📋 Günlük İş Takip Raporu — <tarih>`; sıra: bugün
kapatılacaklar → son 24 saat → öncelik tablosu → hatırlatmalar → bildirim adedi.
Kritik gelişme yoksa bunu açıkça yaz, **sessiz kalma.**

**Commit mesajı** — Türkçe, ilk satır ≤72 karakter, gövde *ne yapıldığını değil
neden yapıldığını* anlatır. Model adı ve oturum kimliği gövdeye yazılmaz.

Rapor gövdesinin tam yapısı ve takip maili şablonları `rapor-formati`
skill'indedir.

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
edilir. **`reports/pano.html`, `site/app.html` ve `site/_artifact.html`
türetilmiş dosyalardır** — elle düzenlenmez, şablon değiştirilip yeniden
üretilir.

Arayüz değiştiğinde sırayla: `build_dashboard.py` → `site/app.html`'e kopyala →
ekran görüntülerini yenile → `site/img`'i eşitle.

## Tasarım sistemi

Üç renk üç ayrı iş yapar, birbirine karışmaz: **indigo** marka ve hacim ·
**mor rampa** (`--m1`…`--m4`, sıralı) yalnızca eşleşme kalitesi ·
**kırmızı/kehribar/yeşil** boru hattı durumu.

Tipografi: Newsreader (başlık) + Archivo (gövde) + IBM Plex Mono (veri).
Logo: iki dairenin kesişimi. İki tema da orta tonda — ne beyaz kâğıt ne siyah
ekran; yapı gölgeyle değil ince çizgiyle kurulur.

**Renk eklerken kontrast ölçülür, göz kararı yapılmaz.** Metin 4.5:1, grafik
dolgusu 3:1; her iki temada ayrı ayrı. Rampalar açıklık bakımından monotonik.
Ölçüm: `dataviz` skill'indeki `validate_palette.js`. Palet değerleri
`docs/TEKNIK.md`'de.

## Depo

- Geliştirme dalı: `claude/linkedin-job-tracking-automation-6xiogy`
- `main`'e `--no-ff` ile merge; `site/**` değişince Pages otomatik dağıtır
- `site/_artifact.html` türetilmiştir, `.gitignore`'dadır

## Açık maddeler

- ⬜ **İlan metninin otomatik çekilip beceri çıkarımı** — `match` boyutları ve
  `gap_skills` şu an elle atanıyor. Projenin en zayıf halkası; ajan işi.
- ⬜ Kullanıcı başına çoklu profil desteği
- ⬜ Kalıcı veritabanı ve oturum yönetimi

## Proje skill'leri

`.claude/skills/` altında üç skill var. Her oturumda yüklenmiyorlar — Claude
işe göre kendisi çekiyor, bu yüzden ayrıntı burada değil onlarda durur.

| Skill | Ne zaman devreye girer |
|---|---|
| `eslesme-puanlama` | Bir ilanı CV'ye karşı puanlarken, `match` objesine veya `gap_skills`'e dokunulan her işte. Dört boyutun rubrikleri, segmentler, gerekçe yazımı. |
| `mail-siniflandirma` | Günlük Gmail taramasında, bir mailin hangi kategoriye girdiğini belirlerken. Sorgular, gürültü listesi, sınıflandırma sırası, kayıt güncelleme. |
| `rapor-formati` | Rapor üretirken, hatırlatma çıkarırken, takip maili taslarken. Aciliyet ağırlıkları, eşikler, e-posta yapısı, pazartesi geri bildirim bloğu. |

Skill'lerdeki sayısal değerler koddaki sabitlerle **doğrulanmıştır**. Sabiti
değiştirirsen skill'i de güncelle, yoksa ikisi ayrışır.

## Referans

- `docs/TEKNIK.md` — formüller, bakım notları, tasarım kararları
- `docs/otomasyon.md` — günlük Routine'in işleyişi
- `docs/kaynak-claude-code-kursu.md` — ajan/skill mimarisi için izlenen kurs
