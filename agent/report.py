#!/usr/bin/env python3
"""~1 KB digest of a solar-coherence run's summary.json (for LLM agents).
usage: report.py <run_dir> [--city NAME]"""
import csv, json, os, sys


def digest(run, city=None):
    s = json.load(open(os.path.join(run, "summary.json")))
    if city:
        for r in csv.DictReader(open(os.path.join(run, "cities.csv"))):
            if r["city"].lower().replace(" ", "") == city.lower().replace(" ", ""):
                days = [d for d in csv.DictReader(open(os.path.join(run, "anomalous_days.csv"))) if d["city"] == r["city"]][:5]
                return json.dumps({"city": r, "top_anomalous_days": days}, indent=0)
        return f"no city {city!r}; names look like Missouri_KansasCity"
    d = s["distribution_all_cities"]
    out = [f"run {s['run']}: {s['cities_analysed']} cities ({s['cities_likely_in_release']} likely in HEDW-US release), {s['period_utc']}",
           f"r_hourly median {d['r_hourly']['median']} (min {d['r_hourly']['min']}); r_daily median {d['r_daily']['median']} (min {d['r_daily']['min']})",
           f"bias% median {d['bias_pct']['median']} (p05 {d['bias_pct']['p05']}, p95 {d['bias_pct']['p95']}); best lag per city-year {s['best_lag_city_years']}",
           f"physics {s['physics']}",
           f"anomalous cities {s['n_anomalous_cities']}, city-years {s['n_anomalous_city_years']}, anomalous days {s['total_anomalous_days']}"]
    for a in s["anomalous_cities"][:12]:
        out.append(f"  {a['city']}: r_daily {a['r_daily']} bias {a['bias_pct']}% days {a['anomalous_days']} "
                   f"{'; '.join(f'{y}:{v}' for y, v in a['flags_by_year'].items())} {' '.join(a['z_flags'])}")
    if len(s["anomalous_cities"]) > 12:
        out.append(f"  ... {len(s['anomalous_cities']) - 12} more in summary.json")
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    city = a[a.index("--city") + 1] if "--city" in a else None
    print(digest(a[0], city))
