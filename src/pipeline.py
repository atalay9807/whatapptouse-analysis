#!/usr/bin/env python3
"""
İş başvurusu takip pipeline'ı.

data/applications.json'u okur, her başvuruyu önceliklendirir, hatırlatmaları
üretir ve rapor çıktısı verir (Markdown / düz metin / CSV).

Kullanım:
    python3 src/pipeline.py                    # bugünün günlük raporu (Markdown)
    python3 src/pipeline.py --format text      # e-postaya uygun düz metin
    python3 src/pipeline.py --format csv       # tabloyu CSV olarak
    python3 src/pipeline.py --weekly           # haftalık özet + geri bildirim soruları
    python3 src/pipeline.py --today 2026-09-05 # tarihi sabitle (test için)
"""

import argparse
import csv
import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match import enrich_with_match, segment_summary, load_profile  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "applications.json"

STAGE_WEIGHT = {
    "offer": 100,
    "interview_scheduling": 88,
    "assessment": 85,
    "next_stage": 82,
    "interviewed": 78,
    "application_incomplete": 70,
    "in_process": 60,
    "under_review": 35,
    "talent_pool": 20,
    "closed": 0,
}

FIT_MULTIPLIER = 4
STALE_DAYS = 12
DEAD_DAYS = 21

BAND_LABEL = {
    "critical": "🔴 KRİTİK",
    "high": "🟠 YÜKSEK",
    "normal": "🟡 NORMAL",
    "low": "⚪ DÜŞÜK",
    "archive": "⚫ KAPANDI",
}


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def days_between(later, earlier):
    return (later - earlier).days if later and earlier else None


def deadline_bonus(days_left):
    """Deadline'a kalan güne göre aciliyet puanı."""
    if days_left is None:
        return 0
    if days_left < 0:
        return 40          # geçmiş deadline en yüksek aciliyet
    if days_left <= 1:
        return 35
    if days_left <= 3:
        return 25
    if days_left <= 7:
        return 15
    if days_left <= 14:
        return 8
    return 0


def score(app, today):
    """0-140 arası öncelik puanı."""
    if app["status"] == "rejected":
        return 0
    total = STAGE_WEIGHT.get(app.get("stage"), 30)
    total += app.get("fit", 3) * FIT_MULTIPLIER

    dl = parse_date(app.get("deadline"))
    total += deadline_bonus(days_between(dl, today))

    # Uzun sessizlik puanı düşürür (süreç muhtemelen ölmüş)
    silence = days_between(today, parse_date(app.get("last_contact")))
    if silence is not None:
        if silence > DEAD_DAYS:
            total -= 20
        elif silence > STALE_DAYS:
            total -= 8
    return max(total, 0)


def band(app, today, points):
    if app["status"] == "rejected":
        return "archive"
    dl = parse_date(app.get("deadline"))
    left = days_between(dl, today)
    if app["status"] == "action_required" and (left is None or left <= 3):
        return "critical"
    if points >= 100:
        return "critical"
    if points >= 75:
        return "high"
    if points >= 45:
        return "normal"
    return "low"


def reminders_for(app, today):
    """Bu başvuru için bugün üretilecek hatırlatmalar."""
    out = []
    dl = parse_date(app.get("deadline"))
    left = days_between(dl, today)
    if left is not None:
        if left < 0:
            out.append(f"⏳ Deadline {abs(left)} gün önce doldu ({app['deadline']}) — uzatma iste ya da kapat.")
        elif left == 0:
            out.append(f"🔥 Deadline BUGÜN ({app['deadline']}).")
        elif left <= 2:
            out.append(f"⏰ Deadline {left} gün sonra ({app['deadline']}).")
        elif left <= 7:
            out.append(f"📅 Deadline {left} gün sonra ({app['deadline']}).")

    silence = days_between(today, parse_date(app.get("last_contact")))
    if app["status"] not in ("rejected", "action_required") and silence is not None:
        if app.get("stage") == "interviewed" and silence >= 5:
            out.append(f"✉️ Mülakattan {silence} gün geçti — nazik takip maili at.")
        elif silence >= DEAD_DAYS:
            out.append(f"💤 {silence} gündür sessiz — kapanmış say, listeden düşür.")
        elif silence >= STALE_DAYS:
            out.append(f"✉️ {silence} gündür sessiz — takip maili zamanı.")
    return out


def enrich(data, today):
    enrich_with_match(data["applications"])
    apps = []
    for app in data["applications"]:
        item = dict(app)
        item["score"] = score(app, today)
        item["band"] = band(app, today, item["score"])
        item["reminders"] = reminders_for(app, today)
        item["days_silent"] = days_between(today, parse_date(app.get("last_contact")))
        item["days_to_deadline"] = days_between(parse_date(app.get("deadline")), today)
        mr = app.get("match_result") or {}
        item["match_score"] = mr.get("score")
        item["match_segment"] = mr.get("segment")
        item["match_segment_key"] = mr.get("segment_key")
        item["match_rationale"] = mr.get("rationale")
        item["match_weakest"] = mr.get("weakest")
        apps.append(item)
    apps.sort(key=lambda a: (-a["score"], a["company"]))
    return apps


def focus_list(apps):
    """Aktif ve eşleşmesi güçlü olanlar — enerjinin gitmesi gereken yer."""
    return [a for a in apps
            if a["status"] != "rejected" and a.get("match_segment_key") in ("strong", "good")]


def wasted_effort(apps):
    """Zayıf/orta eşleşmeye harcanan başvurular."""
    return [a for a in apps if a.get("match_segment_key") in ("fair", "weak")]


def funnel(apps):
    active = [a for a in apps if a["status"] != "rejected"]
    rejected = [a for a in apps if a["status"] == "rejected"]
    interviews = [a for a in active if a.get("stage") in
                  ("interviewed", "interview_scheduling", "next_stage", "assessment")]
    stale = [a for a in active if (a["days_silent"] or 0) >= STALE_DAYS]
    total = len(apps)
    return {
        "total": total,
        "active": len(active),
        "rejected": len(rejected),
        "interviews": len(interviews),
        "stale": len(stale),
        "response_rate": round(100 * len([a for a in apps if (a["days_silent"] or 99) < 99
                                          and a["status"] != "awaiting_response"]) / total, 1) if total else 0,
        "interview_rate": round(100 * len(interviews) / total, 1) if total else 0,
        "rejection_rate": round(100 * len(rejected) / total, 1) if total else 0,
    }


# ---------------------------------------------------------------- çıktı formatları

def render_markdown(apps, stats, data, today, weekly=False):
    L = []
    L.append(f"# 📋 İş Başvuru Takip Raporu — {today.strftime('%d.%m.%Y')}")
    L.append("")
    L.append(f"**Tarama penceresi:** {data['meta']['scan_window']['from']} → {data['meta']['scan_window']['to']}  ")
    L.append(f"**Hesap:** {data['meta']['email']}")
    L.append("")
    L.append("## Özet")
    L.append("")
    L.append("| Metrik | Değer |")
    L.append("|---|---:|")
    L.append(f"| Toplam başvuru | {stats['total']} |")
    L.append(f"| Aktif süreç | {stats['active']} |")
    L.append(f"| Mülakat/değerlendirme aşaması | {stats['interviews']} |")
    L.append(f"| Olumsuz sonuçlanan | {stats['rejected']} |")
    L.append(f"| Sessizleşen (12+ gün) | {stats['stale']} |")
    L.append(f"| Mülakata dönüşüm | %{stats['interview_rate']} |")
    L.append(f"| Red oranı | %{stats['rejection_rate']} |")
    L.append("")

    # Bugünün hatırlatmaları
    todo = [(a, r) for a in apps for r in a["reminders"]]
    if todo:
        L.append("## ⏰ Bugünün Hatırlatmaları")
        L.append("")
        for a, r in todo[:15]:
            L.append(f"- **{a['company']} — {a['role']}**: {r}")
        L.append("")

    # Eşleşme segmentasyonu
    segs = segment_summary(apps)
    L.append("## 🎯 CV Eşleşme Segmentasyonu")
    L.append("")
    L.append("| Segment | Başvuru | İleri aşamaya geçen | Red |")
    L.append("|---|---:|---:|---:|")
    for k in ("strong", "good", "fair", "weak"):
        s_ = segs[k]
        L.append(f"| {s_['label']} | {s_['count']} | %{s_['advance_rate']} | %{s_['reject_rate']} |")
    L.append("")
    waste = wasted_effort(apps)
    if waste:
        L.append(f"> Başvuruların **{len(waste)}'i (%{round(100*len(waste)/len(apps))})** "
                 f"orta veya zayıf eşleşmeye gitmiş. Bu enerji güçlü eşleşmelere kaydırılabilir.")
        L.append("")

    focus = sorted(focus_list(apps), key=lambda a: -a["match_score"])[:12]
    if focus:
        L.append("### Odaklanılacak açık süreçler (eşleşmesi en güçlü 12)")
        L.append("")
        L.append("| Eşleşme | Şirket | Pozisyon | Aşama | Neden uyuyor |")
        L.append("|---:|---|---|---|---|")
        for a in focus:
            why = (a.get("match_rationale") or "").replace("|", "/")
            if len(why) > 88:
                why = why[:85] + "…"
            L.append(f"| {a['match_score']} | {a['company']} | {a['role']} | {a['stage']} | {why} |")
        L.append("")

    # Öncelik tabloları
    for key in ("critical", "high", "normal", "low"):
        rows = [a for a in apps if a["band"] == key]
        if not rows:
            continue
        L.append(f"## {BAND_LABEL[key]} ({len(rows)})")
        L.append("")
        L.append("| Şirket | Pozisyon | Aşama | Deadline | Sessiz | Aciliyet | Eşleşme | Sonraki adım |")
        L.append("|---|---|---|---|---:|---:|---:|---|")
        for a in rows:
            dl = a.get("deadline") or "—"
            silent = f"{a['days_silent']}g" if a["days_silent"] is not None else "—"
            nxt = (a.get("next_step") or "—").replace("|", "/")
            if len(nxt) > 80:
                nxt = nxt[:77] + "…"
            ms = f"{a['match_score']}" if a.get("match_score") is not None else "—"
            L.append(f"| {a['company']} | {a['role']} | {a['stage']} | {dl} | {silent} | "
                     f"{a['score']} | {ms} | {nxt} |")
        L.append("")

    rejected = [a for a in apps if a["status"] == "rejected"]
    if rejected:
        L.append(f"## {BAND_LABEL['archive']} ({len(rejected)})")
        L.append("")
        L.append("| Şirket | Pozisyon | Başvuru | Sonuç tarihi | Süre |")
        L.append("|---|---|---|---|---:|")
        for a in rejected:
            d = days_between(parse_date(a["last_contact"]), parse_date(a["applied"]))
            L.append(f"| {a['company']} | {a['role']} | {a['applied']} | {a['last_contact']} | {d}g |")
        L.append("")

    if data.get("recruiter_outreach"):
        L.append("## 📨 Yanıtlanmamış Recruiter Mesajları")
        L.append("")
        L.append("| Tarih | Kimden | Konu | Kanal |")
        L.append("|---|---|---|---|")
        for r in data["recruiter_outreach"]:
            L.append(f"| {r['date']} | {r['from']} | {r['topic']} | {r['channel']} |")
        L.append("")

    if weekly:
        L.append("## 💬 Senden Beklenen Geri Bildirim")
        L.append("")
        L.append("1. Bu hafta hangi **3 role** odaklanmak istiyorsun?")
        L.append("2. Sessizleşen süreçlerden hangilerini **kapatalım**?")
        L.append("3. Hedef sektör/rol/lokasyon tercihin değişti mi?")
        L.append("4. Maaş beklentin güncellenmeli mi?")
        L.append("")
        L.append("> Yanıtını bu rapora cevap olarak yaz; bir sonraki taramada dikkate alınacak.")
        L.append("")
    return "\n".join(L)


def render_text(apps, stats, today):
    """E-posta gövdesine uygun kısa düz metin."""
    L = [f"İş Takip Raporu — {today.strftime('%d.%m.%Y')}", ""]
    crit = [a for a in apps if a["band"] == "critical"]
    if crit:
        L.append("KRİTİK / BUGÜN AKSİYON:")
        for a in crit:
            L.append(f"- {a['company']} ({a['role']}): {a.get('next_step','—')}")
            for r in a["reminders"]:
                L.append(f"    {r}")
        L.append("")
    high = [a for a in apps if a["band"] == "high"]
    if high:
        L.append("AKTİF SÜREÇLER:")
        for a in high:
            L.append(f"- {a['company']} ({a['role']}) — {a['stage']}")
        L.append("")
    focus = sorted(focus_list(apps), key=lambda a: -a["match_score"])[:5]
    if focus:
        L.append("EŞLEŞMESİ EN GÜÇLÜ AÇIK SÜREÇLER:")
        for a in focus:
            L.append(f"- [{a['match_score']}] {a['company']} — {a['role']}")
        L.append("")
    L.append(f"ÖZET: {stats['active']} aktif / {stats['interviews']} mülakat aşaması / "
             f"{stats['stale']} sessiz / {stats['rejected']} olumsuz (toplam {stats['total']})")
    return "\n".join(L)


def render_csv(apps):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["oncelik", "aciliyet_puani", "eslesme_puani", "eslesme_segmenti", "sirket",
                "pozisyon", "asama", "durum", "kanal", "basvuru", "son_temas", "sessiz_gun",
                "deadline", "en_zayif_boyut", "eslesme_gerekcesi", "sonraki_adim"])
    for a in apps:
        w.writerow([BAND_LABEL[a["band"]], a["score"], a.get("match_score", ""),
                    a.get("match_segment", ""), a["company"], a["role"], a["stage"],
                    a["status"], a.get("channel", ""), a.get("applied", ""),
                    a.get("last_contact", ""), a["days_silent"] if a["days_silent"] is not None else "",
                    a.get("deadline") or "", a.get("match_weakest", ""),
                    a.get("match_rationale", ""), a.get("next_step", "")])
    return buf.getvalue()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--format", choices=["markdown", "text", "csv", "json"], default="markdown")
    p.add_argument("--weekly", action="store_true", help="haftalık geri bildirim bölümünü ekle")
    p.add_argument("--today", help="YYYY-MM-DD (test için tarihi sabitler)")
    p.add_argument("--out", help="çıktı dosyası (varsayılan: stdout)")
    args = p.parse_args()

    today = parse_date(args.today) if args.today else date.today()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    apps = enrich(data, today)
    stats = funnel(apps)

    if args.format == "markdown":
        out = render_markdown(apps, stats, data, today, weekly=args.weekly)
    elif args.format == "text":
        out = render_text(apps, stats, today)
    elif args.format == "csv":
        out = render_csv(apps)
    else:
        out = json.dumps({"generated": today.isoformat(), "stats": stats, "applications": apps},
                         ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"Yazıldı: {args.out}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
