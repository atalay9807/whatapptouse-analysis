#!/usr/bin/env python3
"""HTML panoyu data/applications.json'dan üretir (template + veri enjeksiyonu)."""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import enrich, funnel, parse_date, DATA  # noqa: E402
from match import segment_summary, load_profile  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "dashboard.template.html"


def weekly_volume(apps):
    buckets = [("1–7 Ağu", 0), ("8–14 Ağu", 0), ("15–21 Ağu", 0),
               ("22–28 Ağu", 0), ("29 Ağu–1 Eyl", 0)]
    counts = [0] * 5
    start = date(2026, 8, 1)
    for a in apps:
        idx = min((parse_date(a["applied"]) - start).days // 7, 4)
        counts[idx] += 1
    return [{"label": b[0], "value": c} for b, c in zip(buckets, counts)]


def pipeline_states(apps):
    """Boru hattı durum dağılımı — status paletiyle eşlenir."""
    action = [a for a in apps if a["status"] == "action_required"]
    active = [a for a in apps if a["status"] in ("in_progress", "awaiting_response")]
    stale = [a for a in apps if a["status"] == "stale"]
    rejected = [a for a in apps if a["status"] == "rejected"]
    return [
        {"label": "Aksiyon gerekli", "value": len(action), "tone": "critical", "icon": "!"},
        {"label": "Aktif / yanıt bekleniyor", "value": len(active), "tone": "good", "icon": "→"},
        {"label": "Sessizleşen (12+ gün)", "value": len(stale), "tone": "warning", "icon": "~"},
        {"label": "Olumsuz sonuçlanan", "value": len(rejected), "tone": "archive", "icon": "×"},
    ]


def main():
    today = parse_date(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    apps = enrich(data, today)
    payload = {
        "generated": today.isoformat(),
        "meta": data["meta"],
        "stats": funnel(apps),
        "weekly": weekly_volume(data["applications"]),
        "states": pipeline_states(apps),
        "profile": load_profile(),
        "segments": segment_summary(apps),
        "applications": [
            dict({k: a.get(k) for k in ("id", "company", "role", "stage", "status", "band", "score",
                                        "channel", "track", "location", "applied", "last_contact",
                                        "deadline", "days_silent", "days_to_deadline", "next_step",
                                        "reminders", "match_score", "match_segment",
                                        "match_segment_key", "match_rationale", "match_weakest")},
                 links_actions=a.get("links_actions", []),
                 match_breakdown=(a.get("match_result") or {}).get("breakdown", []))
            for a in apps
        ],
        "outreach": data.get("recruiter_outreach", []),
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(payload, ensure_ascii=False))
    out = ROOT / "reports" / "pano.html"
    out.write_text(html, encoding="utf-8")
    print(f"Yazıldı: {out}")


if __name__ == "__main__":
    main()
