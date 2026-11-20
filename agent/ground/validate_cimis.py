#!/usr/bin/env python3
"""Ground truth for the flagged California cities: CIMIS hourly solar radiation
vs NSRDB (the HEDW-US source) and NASA POWER, 2019-2023.

CIMIS hourly records: Date + Hour '0100'..'2400' (Pacific Standard Time, no DST,
per CIMIS docs; checked here by lag scan), HlySolRad W/m2 with a QC code.
Kept: QC ' ' (passed) or 'Y' (moderate outlier); dropped: everything else
(M missing, R far out, N/S/Q not collected, P/H estimated or historical).

Compares (a) products at the station coordinates vs the station and
(b) each flagged city's own products (city coordinates = the HEDW-US request)
vs its nearest station. Uses compare()/products() from validate_local.py.
usage: validate_cimis.py <out_dir>
"""
import csv, json, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "agent/ground"))
sys.path.insert(0, os.path.join(ROOT, "agent"))
import validate_local as vl  # noqa: E402


def load_cimis(name, conv=("PST", "end")):
    d = pd.read_csv(os.path.join(ROOT, "raw/ground/cimis", f"{name}.csv"), dtype={"hour": str, "qc": str})
    d["qc"] = d.qc.fillna("").str.strip()
    v = pd.to_numeric(d.sol_rad_wm2, errors="coerce").where(d.qc.isin(["", "Y"]))
    v = v.where((v >= 0) & (v < 1500))
    h = d.hour.astype(int) // 100                     # 1..24
    t = pd.to_datetime(d.date) + pd.to_timedelta(h, unit="h")   # label time
    if conv[1] == "end":
        t = t - pd.Timedelta(hours=1)                 # start of the averaged hour
    if conv[0] == "PST":
        idx = pd.DatetimeIndex(t + pd.Timedelta(hours=8)).tz_localize("UTC")
    else:
        idx = pd.DatetimeIndex(t).tz_localize("America/Los_Angeles", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    s = pd.Series(v.values, index=idx)
    return s[s.index.notna()].groupby(level=0).mean(), int(d.qc.isin(["", "Y"]).sum()), int(len(d))


def lag_scan(name, pw):
    out = {}
    for conv in [("PST", "end"), ("PST", "start"), ("local", "end")]:
        g, _, _ = load_cimis(name, conv)
        j = pd.DataFrame({"g": g, "p": pw.ALLSKY_SFC_SW_DWN}).dropna()
        out["/".join(conv)] = {season: {str(L): round(vl.corr(x.g.values, x.p.shift(L).values), 4) for L in (-1, 0, 1)}
                               for season, x in [("winter", j[j.index.month.isin([12, 1, 2])]),
                                                 ("summer", j[j.index.month.isin([6, 7, 8])])]}
    best = max(out, key=lambda k: out[k]["winter"]["0"] + out[k]["summer"]["0"])
    return best, out


def main(out):
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    sts = list(csv.DictReader(open(os.path.join(ROOT, "agent/ground/cimis_selected.csv"))))
    fmap = json.load(open(os.path.join(ROOT, "agent/ground/cimis_flagged_map.json")))
    summ = {"stations": {}, "flagged_cities": {}}
    votes, ground = {}, {}
    for st in sts:
        ns, pw = vl.products(st["name"])
        best, scan = lag_scan(st["name"], pw)
        votes[best] = votes.get(best, 0) + 1
        summ["stations"][st["name"]] = {"code": st["code"], "lat": float(st["lat"]), "lon": float(st["lon"]),
                                        "time_best": best, "time_scan_r": scan}
    conv = tuple(max(votes, key=votes.get).split("/"))
    summ["time_convention"] = {"chosen": "/".join(conv), "votes": votes}
    for st in sts:
        g, nkept, nall = load_cimis(st["name"], conv)
        ground[st["code"]] = g
        ns, pw = vl.products(st["name"])
        summ["stations"][st["name"]].update(vl.compare(g, ns, pw, st["name"]))
        summ["stations"][st["name"]]["qc_kept_frac"] = round(nkept / nall, 4)
    for city, m in fmap.items():
        ns, pw = vl.products(city)
        r = vl.compare(ground[m["station"]], ns, pw, f"{city} products vs CIMIS #{m['station']} {m['name']} ({m['km']} km)")
        r.update(station=m["station"], station_name=m["name"], distance_km=m["km"])
        summ["flagged_cities"][city] = r
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=1)

    with open(os.path.join(out, "stations.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["series", "days", "nsrdb_daily_r", "power_daily_r", "nsrdb_daily_mbe_pct", "power_daily_mbe_pct",
                    "nsrdb_daily_rmse_pct", "power_daily_rmse_pct", "daily_nsrdb_closer_frac",
                    "nsrdb_mbe_jja_pct", "power_mbe_jja_pct"])
        rows = [(k, v) for k, v in summ["stations"].items()] + [(f"{k} vs #{v['station']} ({v['distance_km']} km)", v)
                                                              for k, v in summ["flagged_cities"].items()]
        for k, v in rows:
            mb = v["monthly_bias_vs_ground"]
            jja = lambda key: round(float(np.mean([mb[m][key] for m in (6, 7, 8) if m in mb])), 1)
            w.writerow([k, v["days"], v["daily"]["nsrdb"]["r"], v["daily"]["power"]["r"], v["daily"]["nsrdb"]["mbe_pct"],
                        v["daily"]["power"]["mbe_pct"], v["daily"]["nsrdb"]["rmse_pct"], v["daily"]["power"]["rmse_pct"],
                        v["daily_nsrdb_closer_frac"], jja("nsrdb_mbe_pct"), jja("power_mbe_pct")])
    figures(out, summ)
    print(json.dumps(summ["time_convention"]))
    for k, v in rows:
        mb = v["monthly_bias_vs_ground"]
        print(f"{k:58s} r N/P {v['daily']['nsrdb']['r']}/{v['daily']['power']['r']}  MBE% N/P {v['daily']['nsrdb']['mbe_pct']:6}/{v['daily']['power']['mbe_pct']:6}"
              f"  JJA N/P {np.mean([mb[m]['nsrdb_mbe_pct'] for m in (6,7,8)]):5.1f}/{np.mean([mb[m]['power_mbe_pct'] for m in (6,7,8)]):5.1f}"
              f"  RMSE% N/P {v['daily']['nsrdb']['rmse_pct']}/{v['daily']['power']['rmse_pct']}")


def figures(out, s):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(s["stations"])
    fig, axes = plt.subplots(3, 3, figsize=(13, 9), sharex=True, sharey=True)
    for ax, n in zip(axes.flat, names):
        mb = s["stations"][n]["monthly_bias_vs_ground"]
        ms = sorted(int(m) for m in mb)
        ax.plot(ms, [mb[m]["nsrdb_mbe_pct"] for m in ms], "o-", ms=3, label="NSRDB (HEDW-US source)")
        ax.plot(ms, [mb[m]["power_mbe_pct"] for m in ms], "s-", ms=3, label="NASA POWER")
        ax.axhline(0, color="k", lw=0.6); ax.set_title(n.replace("CIMIS_", "#"), fontsize=9)
    axes[0, 0].legend(fontsize=7); axes[1, 0].set_ylabel("monthly bias vs CIMIS (%)")
    for ax in axes[-1]:
        ax.set_xlabel("month"); ax.set_xticks(range(1, 13))
    fig.suptitle("NSRDB and POWER vs CIMIS pyranometers near the flagged California cities, 2019-2023")
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/monthly_bias_vs_cimis.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])
