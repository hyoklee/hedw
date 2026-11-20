#!/usr/bin/env python3
"""NSRDB gap-filling vs the coherence anomalies.

Reads raw/nsrdb/flags/<city>_<year>_flags.csv (ghi, clearsky_ghi, cloud_type,
fill_flag; same request as HEDW-US otherwise) and a coherence run, and writes
<run>/fillflags.json and <run>/fillflag_days.csv.

Fill Flag in the hourly GOES v4 product takes values 0..100 in steps of ~7
(0, 7, 14, ..., 100). We read it as the percentage of the hour's sub-hourly
samples that NSRDB gap-filled (inference, not documented in the file header,
whose legend lists the 30-min codes 1-5: Missing Image, Low Irradiance,
Exceeds Clearsky, Missing Cloud Properties, Rayleigh Violation).
A "filled day" here: >= 50 % of daylight hours (clearsky_ghi > 200 W/m2) have fill_flag >= 50.

usage: fillflags.py <run_dir>
"""
import csv, glob, json, os, sys, collections
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(city):
    parts = []
    for y in range(2019, 2024):
        f = os.path.join(ROOT, "raw/nsrdb/flags", f"{city}_{y}_flags.csv")
        if not os.path.exists(f):
            return None
        d = pd.read_csv(f, skiprows=2)
        d.index = pd.to_datetime(dict(year=d.Year, month=d.Month, day=d.Day, hour=d.Hour), utc=True)
        parts.append(d)
    return pd.concat(parts)


def main(run):
    cities = [r for r in csv.DictReader(open(os.path.join(run, "cities.csv")))]
    anom = collections.defaultdict(set)
    for r in csv.DictReader(open(os.path.join(run, "anomalous_days.csv"))):
        anom[r["city"]].add(r["date"])
    per_city, date_count, rows = {}, collections.Counter(), []
    tot_anom = tot_anom_filled = tot_days = tot_filled = 0
    for c in cities:
        name = c["city"]
        d = load(name)
        if d is None:
            continue
        day = d["Clearsky GHI"] > 200   # exclude low-sun hours (often flagged "Low Irradiance")
        ff = d["Fill Flag"]
        g = pd.DataFrame({"day": day, "filled": day & (ff >= 50), "full": day & (ff >= 100)})
        daily = g.resample("1D").sum()
        filled_day = daily.filled >= 0.5 * daily.day.clip(lower=1)
        fdates = {str(t.date()) for t in daily.index[filled_day]}
        for t in fdates:
            date_count[t] += 1
        a = anom.get(name, set())
        hit = a & fdates
        per_city[name] = {"daylight_hours": int(day.sum()),
                          "daylight_hours_fill_ge50": int(g.filled.sum()),
                          "daylight_hours_fill_100": int(g.full.sum()),
                          "frac_daylight_fill_ge50": round(float(g.filled.sum() / max(1, day.sum())), 5),
                          "filled_days": len(fdates),
                          "top_anomalous_days_listed": len(a), "of_which_filled": len(hit),
                          "anomalous": c["anomalous"] == "1"}
        tot_days += len(daily); tot_filled += len(fdates)
        tot_anom += len(a); tot_anom_filled += len(hit)
        for t in sorted(hit):
            rows.append([name, t])
    fr = np.array([v["frac_daylight_fill_ge50"] for v in per_city.values()])
    an = np.array([v["anomalous"] for v in per_city.values()])
    res = {
        "cities": len(per_city),
        "frac_daylight_hours_fill_ge50": {"median": round(float(np.median(fr)), 5), "max": round(float(fr.max()), 5),
                                          "min": round(float(fr.min()), 5),
                                          "city_max": max(per_city, key=lambda k: per_city[k]["frac_daylight_fill_ge50"])},
        "base_rate_filled_days": round(tot_filled / max(1, tot_days), 5),
        "top_anomalous_days_listed": tot_anom, "top_anomalous_days_filled": tot_anom_filled,
        "frac_top_anomalous_days_filled": round(tot_anom_filled / max(1, tot_anom), 4),
        "frac_fill_anomalous_cities_median": round(float(np.median(fr[an])), 5) if an.any() else None,
        "frac_fill_other_cities_median": round(float(np.median(fr[~an])), 5) if (~an).any() else None,
        "dates_most_cities_filled": date_count.most_common(10),
        "per_city": per_city,
    }
    json.dump(res, open(os.path.join(run, "fillflags.json"), "w"), indent=1)
    with open(os.path.join(run, "fillflag_days.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["city", "date_anomalous_and_filled"]); w.writerows(rows)
    print(json.dumps({k: v for k, v in res.items() if k != "per_city"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
