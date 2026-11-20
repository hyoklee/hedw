#!/usr/bin/env python3
"""Merge per-city coherence shards (JSONL) into one run: flags, robust z across
cities, CSV tables, figures and summary.json.

usage: aggregate.py <run_dir>     (reads <run_dir>/shards/*.jsonl)
Thresholds are those of wiki/concept-solar-coherence.md.
"""
import csv, glob, json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 7 targets with no county mapping in the authors' xlsx -> cannot be in the 141 release
NOT_IN_RELEASE = {"California_GardenGrove", "California_Oceanside", "Mississippi_Jackson",
                  "California_SantaRosa", "California_RanchoCucamonga", "Missouri_Springfield",
                  "Florida_PembrokePines"}
THR = {"r_daily_min": 0.85, "bias_pct_abs_max": 15.0, "lag_ok": [0], "lag_tolerated": [-1, 1],
       "physics_viol_frac_max": 0.005, "robust_z_abs_max": 3.0}
ZMETRICS = ["r_hourly", "r_daily", "bias_pct", "rmse_hourly_wm2", "anomalous_days"]


def robust_z(x):
    x = np.asarray(x, float)
    med = np.nanmedian(x)
    mad = 1.4826 * np.nanmedian(np.abs(x - med))
    return (x - med) / (mad if mad > 0 else 1e-9)


def city_year_flags(m):
    f = []
    if m["best_lag_h"] not in THR["lag_ok"] + THR["lag_tolerated"]:
        f.append(f"lag={m['best_lag_h']}h")
    if not (m["r_daily"] >= THR["r_daily_min"]):
        f.append(f"r_daily={m['r_daily']:.3f}")
    if abs(m["bias_pct"]) > THR["bias_pct_abs_max"]:
        f.append(f"bias={m['bias_pct']:+.1f}%")
    if m["physics_viol_frac"] > THR["physics_viol_frac_max"]:
        f.append(f"physics={100*m['physics_viol_frac']:.2f}%")
    if m["nsrdb_missing"] or m["power_missing"]:
        f.append(f"missing nsrdb={m['nsrdb_missing']} power={m['power_missing']}")
    return f


def main(run):
    recs = []
    for p in sorted(glob.glob(os.path.join(run, "shards", "*.jsonl"))):
        recs += [json.loads(l) for l in open(p) if l.strip()]
    errs = [r for r in recs if "error" in r]
    recs = sorted([r for r in recs if "error" not in r], key=lambda r: r["city"])
    coords = {r["name"]: r for r in csv.DictReader(open(os.path.join(ROOT, "raw/upstream/hedw-code/target_cities.csv")))}
    for r in recs:
        r["in_release"] = "no" if r["city"] in NOT_IN_RELEASE else "likely"
        r["lat"], r["lon"], r["ba"] = float(coords[r["city"]]["lat"]), float(coords[r["city"]]["lon"]), coords[r["city"]]["ba"]
        r["grid_offset_km"] = round(float(111.2 * np.hypot(r["nsrdb_lat"] - r["lat"],
                                    (r["nsrdb_lon"] - r["lon"]) * np.cos(np.radians(r["lat"])))), 2)

    # city-level robust z on the 5-year metrics
    for k in ZMETRICS:
        vals = [r["all"][k] if k in r["all"] else r[k] for r in recs]
        for r, z in zip(recs, robust_z(vals)):
            r.setdefault("z", {})[k] = round(float(z), 2)
    for r in recs:
        r["flags_by_year"] = {y: city_year_flags(m) for y, m in r["years"].items()}
        r["flags_by_year"] = {y: f for y, f in r["flags_by_year"].items() if f}
        # one-sided for correlation (low is bad) and error/count metrics (high is bad); bias two-sided
        bad = lambda k, v: abs(v) > THR["robust_z_abs_max"] and not (
            (k.startswith("r_") and v > 0) or (k in ("rmse_hourly_wm2", "anomalous_days") and v < 0))
        r["z_flags"] = [f"z({k})={v:+.1f}" for k, v in r["z"].items() if bad(k, v)]
        r["anomalous"] = bool(r["flags_by_year"] or r["z_flags"])

    # tables
    cols = ["city", "in_release", "ba", "lat", "lon", "grid_offset_km", "r_hourly", "r_daily", "best_lag_h",
            "bias_pct", "rmse_hourly_wm2", "mae_hourly_wm2", "night_nonzero_frac", "flat_hours",
            "over_clearsky_days_frac", "anomalous_days", "anomalous_days_low", "anomalous_days_high", "anomalous", "flags"]
    with open(os.path.join(run, "cities.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in recs:
            a = r["all"]
            flags = "; ".join([f"{y}: {', '.join(v)}" for y, v in r["flags_by_year"].items()] + r["z_flags"])
            w.writerow([r["city"], r["in_release"], r["ba"], r["lat"], r["lon"], r["grid_offset_km"],
                        round(a["r_hourly"], 4), round(a["r_daily"], 4), a["best_lag_h"], round(a["bias_pct"], 2),
                        round(a["rmse_hourly_wm2"], 1), round(a["mae_hourly_wm2"], 1), round(a["night_nonzero_frac"], 5),
                        a["flat_hours"], round(a["over_clearsky_days_frac"], 4), r["anomalous_days"],
                        r["anomalous_days_low"], r["anomalous_days_high"], int(r["anomalous"]), flags])
    with open(os.path.join(run, "city_years.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["city", "year", "r_hourly", "r_daily", "best_lag_h", "bias_pct", "rmse_hourly_wm2", "physics_viol_frac", "flags"])
        for r in recs:
            for y, m in r["years"].items():
                w.writerow([r["city"], y, round(m["r_hourly"], 4), round(m["r_daily"], 4), m["best_lag_h"],
                            round(m["bias_pct"], 2), round(m["rmse_hourly_wm2"], 1), round(m["physics_viol_frac"], 5),
                            ", ".join(r["flags_by_year"].get(y, []))])
    with open(os.path.join(run, "anomalous_days.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["city", "date", "nsrdb_whm2", "power_whm2", "power_clear_whm2", "z"])
        for r in recs:
            for d in r["anomalous_day_list"]:
                w.writerow([r["city"], d["date"], d["nsrdb_whm2"], d["power_whm2"], d["power_clear_whm2"], d["z"]])

    # summary
    A = lambda k: np.array([r["all"][k] for r in recs], float)
    rel = [r for r in recs if r["in_release"] != "no"]
    lags = {}
    for r in recs:
        for m in r["years"].values():
            lags[str(m["best_lag_h"])] = lags.get(str(m["best_lag_h"]), 0) + 1
    q = lambda x: {"min": round(float(np.min(x)), 4), "p05": round(float(np.percentile(x, 5)), 4),
                   "median": round(float(np.median(x)), 4), "p95": round(float(np.percentile(x, 95)), 4),
                   "max": round(float(np.max(x)), 4)}
    worst = sorted(recs, key=lambda r: r["all"]["r_daily"])[:10]
    summ = {
        "run": os.path.basename(os.path.abspath(run)),
        "period_utc": "2019-01-01T00/2023-12-31T23",
        "comparison": "NSRDB GOES aggregated v4.0.0 GHI (hourly, value at HH:30 UTC) vs NASA POWER hourly ALLSKY_SFC_SW_DWN (mean over HH:00-HH+1:00 UTC, CERES SYN1deg)",
        "cities_analysed": len(recs), "cities_failed": [e["city"] + ": " + e["error"] for e in errs],
        "cities_likely_in_release": len(rel), "cities_not_in_release": sorted(NOT_IN_RELEASE & {r["city"] for r in recs}),
        "thresholds": THR,
        "distribution_all_cities": {k: q(A(k)) for k in ["r_hourly", "r_daily", "bias_pct", "rmse_hourly_wm2", "mae_hourly_wm2"]},
        "best_lag_city_years": lags,
        "physics": {"cities_with_night_ghi": sum(r["all"]["night_nonzero_frac"] > 0 for r in recs),
                    "max_night_ghi_wm2": max(r["all"]["night_max_wm2"] for r in recs),
                    "cities_with_negative_ghi": sum(r["all"]["negative_hours"] > 0 for r in recs),
                    "cities_with_flat_runs": sum(r["all"]["flat_hours"] > 0 for r in recs),
                    "missing_nsrdb_hours": int(sum(r["all"]["nsrdb_missing"] for r in recs)),
                    "missing_power_hours": int(sum(r["all"]["power_missing"] for r in recs))},
        "anomalous_cities": [{"city": r["city"], "in_release": r["in_release"], "r_daily": round(r["all"]["r_daily"], 4),
                              "bias_pct": round(r["all"]["bias_pct"], 2), "anomalous_days": r["anomalous_days"],
                              "flags_by_year": r["flags_by_year"], "z_flags": r["z_flags"]} for r in recs if r["anomalous"]],
        "n_anomalous_cities": sum(r["anomalous"] for r in recs),
        "n_anomalous_city_years": sum(len(r["flags_by_year"]) for r in recs),
        "lowest_r_daily": [{"city": r["city"], "r_daily": round(r["all"]["r_daily"], 4), "bias_pct": round(r["all"]["bias_pct"], 2)} for r in worst],
        "total_anomalous_days": int(sum(r["anomalous_days"] for r in recs)),
        "correlation_bias_vs_lat": round(float(np.corrcoef(A("bias_pct"), [r["lat"] for r in recs])[0, 1]), 3),
        "detector_elapsed_ms_total": round(sum(r["elapsed_ms"] for r in recs), 1),
    }
    json.dump(summ, open(os.path.join(run, "summary.json"), "w"), indent=1)
    figures(run, recs)
    print(f"{len(recs)} cities, {summ['n_anomalous_cities']} anomalous, {len(errs)} failed -> {run}/summary.json")


def figures(run, recs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fd = os.path.join(run, "figures"); os.makedirs(fd, exist_ok=True)
    lat = np.array([r["lat"] for r in recs]); lon = np.array([r["lon"] for r in recs])
    for key, lab, cmap in [("r_daily", "daily r (NSRDB vs POWER)", "viridis"), ("bias_pct", "bias % (NSRDB/POWER - 1)", "coolwarm")]:
        v = np.array([r["all"][key] for r in recs])
        fig, ax = plt.subplots(figsize=(9, 5))
        kw = {"vmin": -15, "vmax": 15} if key == "bias_pct" else {}
        sc = ax.scatter(lon, lat, c=v, cmap=cmap, s=40, edgecolor="k", lw=0.3, **kw)
        an = np.array([r["anomalous"] for r in recs])
        ax.scatter(lon[an], lat[an], s=140, facecolor="none", edgecolor="red", lw=1.2, label="flagged")
        plt.colorbar(sc, label=lab); ax.set_xlabel("lon"); ax.set_ylabel("lat"); ax.legend(loc="lower left")
        ax.set_title(f"{lab}, 2019-2023, {len(recs)} cities")
        fig.tight_layout(); fig.savefig(os.path.join(fd, f"map_{key}.png"), dpi=110); plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].hist([r["all"]["r_daily"] for r in recs], 30); ax[0].set_xlabel("daily r")
    ax[1].hist([r["all"]["bias_pct"] for r in recs], 30); ax[1].set_xlabel("bias %")
    L = [int(k) for k in recs[0]["all"]["r_by_lag"]]
    for r in recs:
        ax[2].plot(L, [r["all"]["r_by_lag"][str(l)] for l in L], color="0.6", lw=0.5)
    ax[2].set_xlabel("POWER shift (h)"); ax[2].set_ylabel("hourly r")
    fig.tight_layout(); fig.savefig(os.path.join(fd, "distributions.png"), dpi=110); plt.close(fig)
    # monthly bias heatmap for the 25 lowest-r cities
    worst = sorted(recs, key=lambda r: r["all"]["r_daily"])[:25]
    months = sorted(worst[0]["monthly_bias_pct"])
    M = np.array([[r["monthly_bias_pct"].get(m, np.nan) for m in months] for r in worst])
    fig, ax = plt.subplots(figsize=(13, 7))
    im = ax.imshow(M, aspect="auto", cmap="coolwarm", vmin=-40, vmax=40)
    ax.set_yticks(range(len(worst)), [r["city"] for r in worst], fontsize=7)
    ax.set_xticks(range(0, len(months), 6), months[::6], fontsize=7)
    plt.colorbar(im, label="monthly bias %"); ax.set_title("Monthly NSRDB/POWER bias, 25 lowest daily-r cities")
    fig.tight_layout(); fig.savefig(os.path.join(fd, "monthly_bias_worst25.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])
