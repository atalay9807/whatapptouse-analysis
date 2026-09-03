# Otomasyonun İşleyişi

## Günlük Routine

**Trigger:** `trig_01UdkGdW5SJxvPVB2X3ZSgYJ` — "Günlük İş Takip Raporu (09:00)"
**Cron:** `0 6 * * *` (UTC) = her gün 09:00 Europe/Istanbul
**Bildirim:** push açık, e-posta kapalı

Her sabah şu adımları izler:

1. **Tara** — Gmail'de son 24 saatin iş temalı e-postalarını arar
   (`config/rules.yaml` → `scan.daily_query`).
2. **Sınıflandır** — her e-postayı `status_rules` sırasına göre etiketler:
   teklif → mülakat daveti → aksiyon gerekli → red → incelemede.
   `noise_senders` listesindekiler yalnızca sayılır.
3. **Güncelle** — `data/applications.json` içindeki ilgili kaydın `stage`,
   `status`, `last_contact`, `deadline` ve `next_step` alanlarını tazeler;
   yeni başvuru varsa kayıt ekler.
4. **Raporla** — `atalay.denizer0@gmail.com` adresine kısa HTML özet gönderir.
   Konu: `📋 Günlük İş Takip Raporu — <tarih>`.
5. **Hatırlat** — deadline'ı yaklaşan/geçen ve sessizleşen süreçler için
   `reminders` kurallarını uygular.

Kritik bir gelişme yoksa e-posta bunu açıkça söyler ve açık aksiyonları
tekrar hatırlatır — sessiz kalmaz.

## Haftalık geri bildirim

Pazartesi günleri rapor `--weekly` bölümünü içerir: dört soru sorulur ve
yanıtlar bir sonraki taramada `fit` puanlarına yansıtılır. Bu, sistemin tek
yönlü bir bildirim akışı değil, karşılıklı bir döngü olmasını sağlar.

## Bakım

**Yeni başvuru elle eklemek:** `data/applications.json` içindeki
`applications` dizisine bir kayıt ekle. Zorunlu alanlar: `id`, `company`,
`role`, `channel`, `applied`, `last_contact`, `stage`, `status`, `track`,
`fit`. Opsiyonel: `deadline`, `contact`, `next_step`, `links`, `notes`.

**Puanlamayı değiştirmek:** `config/rules.yaml` → `scoring` bölümü referans
dokümandır; gerçek ağırlıklar `src/pipeline.py` başındaki `STAGE_WEIGHT`,
`FIT_MULTIPLIER`, `STALE_DAYS` sabitlerindedir. İkisini birlikte güncelle.

**Routine'i düzenlemek:** prompt'u değiştirmek için `update_trigger` kullan —
sil ve yeniden oluşturma, çalışma geçmişi kaybolur.

**Tam yeniden inşa:** `config/rules.yaml` → `scan.backfill_queries` içindeki
dört sorgu son 30 günü sıfırdan tarar. Ayda bir çalıştırmak, kaçan
başvuruları yakalar.

## Bilinen sınırlar

- LinkedIn "Easy Apply" başvuruları çoğu zaman yalnızca şirketin ATS'inden
  onay maili üretir; LinkedIn'in kendi başvuru kaydı e-postaya düşmez.
  Bu yüzden `applied` tarihi bazen ATS onay tarihidir, gerçek başvuru
  tarihinden 0–2 gün sonrasıdır.
- `fit` puanı otomatik hesaplanmaz; elle atanır ve haftalık geri bildirimle
  güncellenir.
- Gmail araması İngilizce ve Türkçe anahtar kelimelere dayanır; başka dilde
  gelen e-postalar gürültüye düşebilir.
