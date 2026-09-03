#!/usr/bin/env python3
"""
Rapor ve eğitim verisi üreticisi.

Raporlar
--------
funnel()            Kaydedilen → başvurulan → yanıt → ileri aşama → sonuç hunisi
skill_gaps()        Çıkarımsal eksik yetkinlik analizi (red gerekçesi DEĞİL — aşağıdaki nota bak)
trend()             Haftalık başvuru hacmi ve sonuç dağılımı
track_success()     Rol/sektör bazlı ilerleme ve red oranı
channel_success()   Başvuru kanalı bazlı etkinlik
response_speed()    Şirketlerin yanıt süresi dağılımı
missed()            Kaydedilip başvurulmayan / süresi dolan fırsatlar
engagement()        Kullanım sıklığı, streak ve yaşam döngüsü aşaması
learning_plan()     Eksiklerden türeyen öncelikli eğitim planı

Eksik yetkinlik verisi hakkında
-------------------------------
Taranan 15 red e-postasının HİÇBİRİ gerekçe belirtmiyor; hepsi standart
kalıp metin. Bu yüzden "eksik yetkinlik", şirketlerin söylediği bir şey
değil, ilanın rol ailesi ile CV arasındaki farktan ÇIKARILAN bir tahmindir.
Arayüzde de bu şekilde etiketlenir.
"""

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"

ADVANCED_STAGES = ("interviewed", "interview_scheduling", "next_stage", "assessment", "offer")
INTERVIEW_STAGES = ("interviewed", "interview_scheduling")


def _load(name):
    return json.loads((D / name).read_text(encoding="utf-8"))


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


# ---------------------------------------------------------------- huni

def funnel(apps, saved):
    jobs = saved["jobs"]
    responded = [a for a in apps if _d(a.get("last_contact")) and _d(a["applied"])
                 and _d(a["last_contact"]) > _d(a["applied"])]
    advanced = [a for a in apps if a.get("stage") in ADVANCED_STAGES]
    interviewed = [a for a in apps if a.get("stage") in INTERVIEW_STAGES]
    rejected = [a for a in apps if a["status"] == "rejected"]
    offers = [a for a in apps if a.get("stage") == "offer"]

    total = len(apps)
    steps = [
        {"key": "saved", "label": "Kaydedilen ilan", "value": len(jobs),
         "note": "LinkedIn hatırlatması gelenler — alt sınır, tamamı değil", "partial": True},
        {"key": "applied", "label": "Başvurulan", "value": total,
         "note": "Kaydedilenlerin dışındaki doğrudan başvurular dahil"},
        {"key": "responded", "label": "Yanıt alınan", "value": len(responded),
         "note": "Otomatik onay dışında bir dönüş gelenler"},
        {"key": "advanced", "label": "İleri aşamaya geçen", "value": len(advanced),
         "note": "Test, sonraki aşama veya mülakat"},
        {"key": "interviewed", "label": "Mülakata giren", "value": len(interviewed),
         "note": "Görüşme yapılan veya planlanan"},
        {"key": "offer", "label": "Teklif", "value": len(offers), "note": "Henüz yok"},
    ]
    for i, s in enumerate(steps):
        s["pct_of_applied"] = round(100 * s["value"] / total, 1) if i >= 1 else None
        # Kaydedilen ilan sayısı yalnızca alt sınır olduğu için ondan sonraki
        # adıma dönüşüm oranı hesaplanmaz — yanıltıcı olurdu.
        prev = steps[i - 1] if i else None
        s["conv_from_prev"] = (round(100 * s["value"] / prev["value"], 1)
                               if prev and prev["value"] and not prev.get("partial") else None)

    return {
        "steps": steps,
        "rejected": len(rejected),
        "reject_rate": round(100 * len(rejected) / total, 1),
        "pending": total - len(rejected) - len(offers),
        "caveat": "'Görüntülenen ilan' verisi yok — LinkedIn bunu e-postayla bildirmiyor. "
                  "Huni, kaydedilen ilan hatırlatmalarından başlıyor.",
    }


# ---------------------------------------------------------------- eksik yetkinlik

def skill_gaps(apps, catalog):
    total_c = Counter()
    reject_c = Counter()
    open_c = Counter()
    by_skill_apps = defaultdict(list)

    for a in apps:
        for s in a.get("gap_skills", []):
            total_c[s] += 1
            by_skill_apps[s].append({"id": a["id"], "company": a["company"], "role": a["role"],
                                     "status": a["status"], "match_score": a.get("match_score")})
            if a["status"] == "rejected":
                reject_c[s] += 1
            else:
                open_c[s] += 1

    rows = []
    for skill, n in total_c.most_common():
        meta = catalog["skills"].get(skill, {})
        # Öncelik: redlerde görülmesi, açık süreçleri etkilemesi ve kapanması gereken seviye farkı
        level_gap = max(0, meta.get("target_level", 0) - meta.get("cv_level", 0))
        priority = reject_c[skill] * 3 + open_c[skill] * 1 + level_gap * 2
        rows.append({
            "skill": skill,
            "name": meta.get("name", skill),
            "why": meta.get("why", ""),
            "effort": meta.get("effort"),
            "caveat": meta.get("caveat"),
            "cv_level": meta.get("cv_level"),
            "target_level": meta.get("target_level"),
            "total": n, "rejected": reject_c[skill], "open": open_c[skill],
            "priority": priority,
            "resources": meta.get("resources", []),
            "applications": sorted(by_skill_apps[skill],
                                   key=lambda x: -(x["match_score"] or 0))[:6],
        })
    rows.sort(key=lambda r: (-r["priority"], -r["total"]))
    return {
        "rows": rows,
        "basis": "ÇIKARIM — taranan 15 red e-postasının hiçbiri gerekçe belirtmiyor. "
                 "Eksikler, ilanın rol ailesi ile CV arasındaki farktan türetildi.",
    }


# ---------------------------------------------------------------- trend

def trend(apps):
    weeks = defaultdict(lambda: {"applied": 0, "rejected": 0, "advanced": 0})
    start = date(2026, 8, 1)
    labels = ["1–7 Ağu", "8–14 Ağu", "15–21 Ağu", "22–28 Ağu", "29 Ağu–1 Eyl"]
    for a in apps:
        i = min((_d(a["applied"]) - start).days // 7, 4)
        weeks[i]["applied"] += 1
        if a["status"] == "rejected":
            weeks[i]["rejected"] += 1
        if a.get("stage") in ADVANCED_STAGES:
            weeks[i]["advanced"] += 1
    return [{"label": labels[i], **weeks[i]} for i in range(5)]


# ---------------------------------------------------------------- rol / kanal başarısı

def _group_success(apps, key, min_n=2):
    g = defaultdict(list)
    for a in apps:
        g[a.get(key) or "—"].append(a)
    rows = []
    for name, items in g.items():
        if len(items) < min_n:
            continue
        adv = [x for x in items if x.get("stage") in ADVANCED_STAGES]
        rej = [x for x in items if x["status"] == "rejected"]
        ms = [x["match_score"] for x in items if x.get("match_score") is not None]
        rows.append({
            "name": name, "count": len(items),
            "advanced": len(adv), "rejected": len(rej),
            "advance_rate": round(100 * len(adv) / len(items), 1),
            "reject_rate": round(100 * len(rej) / len(items), 1),
            "avg_match": round(sum(ms) / len(ms)) if ms else None,
        })
    rows.sort(key=lambda r: (-r["advance_rate"], -r["count"]))
    return rows


def track_success(apps):
    return _group_success(apps, "track", min_n=2)


def channel_success(apps):
    return _group_success(apps, "channel", min_n=1)


# ---------------------------------------------------------------- yanıt hızı

def response_speed(apps):
    buckets = [("0-3 gün", 0, 3), ("4-7 gün", 4, 7), ("8-14 gün", 8, 14),
               ("15-21 gün", 15, 21), ("22+ gün", 22, 9999)]
    out = [{"label": b[0], "value": 0} for b in buckets]
    days = []
    for a in apps:
        ap, lc = _d(a["applied"]), _d(a.get("last_contact"))
        if not (ap and lc and lc > ap):
            continue
        n = (lc - ap).days
        days.append(n)
        for i, (_, lo, hi) in enumerate(buckets):
            if lo <= n <= hi:
                out[i]["value"] += 1
                break
    days.sort()
    median = days[len(days) // 2] if days else None
    return {"buckets": out, "median_days": median, "responded": len(days),
            "silent": len(apps) - len(days)}


# ---------------------------------------------------------------- kaçırılanlar

def missed(saved):
    jobs = saved["jobs"]
    not_applied = [j for j in jobs if not j["applied"]]
    expired = [j for j in not_applied if j["expired"]]
    strong = [j for j in not_applied if j["match_estimate"] >= 75]
    return {
        "saved_total": len(jobs),
        "applied": sum(1 for j in jobs if j["applied"]),
        "not_applied": len(not_applied),
        "expired": expired,
        "strong_missed": sorted(strong, key=lambda j: -j["match_estimate"]),
        "all_open": sorted([j for j in not_applied if not j["expired"]],
                           key=lambda j: -j["match_estimate"]),
    }


# ---------------------------------------------------------------- kullanım / streak

def engagement(eng, apps, today):
    days = sorted(_d(x) for x in eng["report_days"])
    if not days:
        return {}
    # güncel streak: bugünden veya dünden geriye kesintisiz
    cur = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        cur += 1
        cursor -= timedelta(days=1)
    # en uzun streak
    longest = run = 1
    for i in range(1, len(days)):
        run = run + 1 if (days[i] - days[i - 1]).days == 1 else 1
        longest = max(longest, run)

    start = _d(eng["tracking_started"])
    span = (today - start).days + 1
    last7 = [d for d in days if (today - d).days < 7]

    return {
        "tracking_started": eng["tracking_started"],
        "days_tracked": span,
        "reports_sent": len(days),
        "coverage": round(100 * len(days) / span, 1),
        "current_streak": cur,
        "longest_streak": longest,
        "missed_days": eng["missed_days"],
        "reports_last_7d": len(last7),
        "feedback_replies": eng["feedback_replies"],
        "calendar": [{"date": (start + timedelta(days=i)).isoformat(),
                      "active": (start + timedelta(days=i)) in days}
                     for i in range(span)],
    }


def lifecycle_stage(journey, eng_stats, apps, profile_exists):
    n = len(apps)
    streak = eng_stats.get("current_streak", 0)
    fb = eng_stats.get("feedback_replies", 0)
    last7 = eng_stats.get("reports_last_7d", 0)
    reports = eng_stats.get("reports_sent", 0)

    if not profile_exists:
        key = "newcomer"
    elif n == 0:
        key = "activated"
    elif n < 10:
        key = "applying"
    elif streak >= 7 and fb >= 1:
        key = "habit"
    elif last7 >= 4:
        key = "engaged"
    elif reports >= 1:
        key = "tracking"
    else:
        key = "applying"

    stages = journey["stages"]
    cur = next(s for s in stages if s["key"] == key)
    nxt = next((s for s in stages if s["order"] == cur["order"] + 1), None)

    blockers = []
    if key == "engaged":
        if streak < 7:
            blockers.append(f"Kesintisiz streak {streak}/7 gün")
        if fb < 1:
            blockers.append("Henüz hiçbir rapora geri bildirim yazılmadı (0/1)")
    return {"current": cur, "next": nxt, "blockers": blockers,
            "all": [{"key": s["key"], "label": s["label"], "order": s["order"]} for s in stages],
            "nudges": journey["page_nudges"]}


# ---------------------------------------------------------------- eğitim planı

def learning_plan(gaps, catalog):
    """Eksiklerden türeyen, öncelik sıralı eğitim planı. Eğitim sayfası ve
    başvuru detayındaki kurs kartı aynı bu çıktıyı kullanır."""
    plan = []
    for i, row in enumerate(gaps["rows"]):
        plan.append({
            "rank": i + 1,
            "skill": row["skill"], "name": row["name"], "why": row["why"],
            "effort": row["effort"], "caveat": row["caveat"],
            "cv_level": row["cv_level"], "target_level": row["target_level"],
            "affects_total": row["total"], "affects_open": row["open"],
            "seen_in_rejections": row["rejected"],
            "priority": row["priority"],
            "resources": row["resources"],
            "applications": row["applications"],
        })
    return plan


def build_all(today=None):
    today = today or date.today()
    apps_raw = _load("applications.json")
    catalog = _load("skills_catalog.json")
    saved = _load("saved_jobs.json")
    eng = _load("engagement.json")
    journey = _load("journey.json")
    profile = _load("profile.json")

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from match import enrich_with_match
    apps = enrich_with_match(apps_raw["applications"])
    for a in apps:
        mr = a.get("match_result") or {}
        a["match_score"] = mr.get("score")
        a["match_segment_key"] = mr.get("segment_key")

    gaps = skill_gaps(apps, catalog)
    eng_stats = engagement(eng, apps, today)
    return {
        "funnel": funnel(apps, saved),
        "skill_gaps": gaps,
        "trend": trend(apps),
        "track_success": track_success(apps),
        "channel_success": channel_success(apps),
        "response_speed": response_speed(apps),
        "missed": missed(saved),
        "engagement": eng_stats,
        "lifecycle": lifecycle_stage(journey, eng_stats, apps, bool(profile)),
        "learning_plan": learning_plan(gaps, catalog),
    }


if __name__ == "__main__":
    import sys
    t = datetime.strptime(sys.argv[1], "%Y-%m-%d").date() if len(sys.argv) > 1 else date.today()
    r = build_all(t)

    print("HUNİ")
    for s in r["funnel"]["steps"]:
        c = f" · önceki adımdan %{s['conv_from_prev']}" if s["conv_from_prev"] is not None else ""
        print(f"  {s['label']:<22} {s['value']:>3}{c}")
    print(f"  ! {r['funnel']['caveat']}")

    print("\nEKSİK YETKİNLİKLER (öncelik sırası)")
    for g in r["learning_plan"][:6]:
        print(f"  {g['rank']}. {g['name']:<28} {g['affects_total']:>2} başvuru "
              f"({g['seen_in_rejections']} red) · öncelik {g['priority']}")

    print("\nKULLANIM")
    e = r["engagement"]
    print(f"  {e['reports_sent']}/{e['days_tracked']} gün (%{e['coverage']}) · "
          f"streak {e['current_streak']} (en uzun {e['longest_streak']}) · "
          f"geri bildirim {e['feedback_replies']}")

    print(f"\nAŞAMA: {r['lifecycle']['current']['label']} → {r['lifecycle']['next']['label']}")
    for b in r["lifecycle"]["blockers"]:
        print(f"  eksik: {b}")

    print("\nROL BAZLI BAŞARI (ilk 5)")
    for t_ in r["track_success"][:5]:
        print(f"  {t_['name']:<22} {t_['count']:>2} başvuru · ilerleme %{t_['advance_rate']}")

    print("\nKAÇIRILANLAR")
    m = r["missed"]
    print(f"  {m['not_applied']}/{m['saved_total']} kaydedilen ilana başvurulmamış, "
          f"{len(m['expired'])} tanesinin süresi dolmuş")
    for j in m["strong_missed"]:
        print(f"    [{j['match_estimate']}] {j['company']} — {j['role'][:48]}"
              f"{' (SÜRESİ DOLDU)' if j['expired'] else ''}")
