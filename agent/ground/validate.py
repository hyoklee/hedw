#!/usr/bin/env python3
"""Ground truth for the coherence check: NSRDB GHI and NASA POWER vs SURFRAD /
SOLRAD pyranometers at the 14 NOAA GML stations, 2019-2023.

Inputs (per station `name` in stations.csv):
  raw/ground/<name>_hourly.csv          ground hourly mean over [H:00, H+1:00) UTC
  raw/nsrdb/<name>_<year>.csv           NSRDB value at H:30 UTC (same request as HEDW-US)
  raw/nsrdb/flags/<name>_<year>_flags.csv   NSRDB fill_flag, cloud_type
  raw/power/<name>.json                 POWER hour H mean
Ground GHI = direct*cos(zen)+diffuse when both components pass QC (BSRN
practice), else the global pyranometer.

Outputs in <out_dir>: summary.json, stations.csv, episode_days.csv, fill_vs_retrieved.csv,
figures/rmse_by_station.png, figures/episode_days.png.
usage: validate.py <out_dir>
"""
import csv, json, os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "agent"))
import coherence as co  # noqa: E402
import fillflags as ff  # noqa: E402

EPISODES = ["2019-11-17", "2019-11-18", "2019-11-19", "2019-11-20", "2020-02-13", "2020-02-14"]


def load_station(name):
    g = pd.read_csv(os.path.join(ROOT, "raw/ground", f"{name}_hourly.csv"))
    g.index = pd.to_datetime(g.time_utc, utc=True)
    ground = g.ghi_comp.where(g.ghi_comp.notna(), g.ghi)
    ns = pd.concat([co.load_nsrdb(os.path.join(ROOT, "raw/nsrdb", f"{name}_{y}.csv"))[0] for y in range(2019, 2024)])
    pw, pmeta = co.load_power(os.path.join(ROOT, "raw/power", f"{name}.json"))
    fl = ff.load(name)
    j = pd.DataFrame({"ground": ground, "nsrdb": ns.GHI, "zen": ns.zen, "power": pw.ALLSKY_SFC_SW_DWN,
                      "power_clear": pw.CLRSKY_SFC_SW_DWN})
    if fl is not None:
        j["fill"] = fl["Fill Flag"]
    return j, pmeta


def stats(obs, est):
    m = np.isfinite(obs) & np.isfinite(est)
    o, e = obs[m], est[m]
    if len(o) < 50:
        return {"n": int(len(o))}
    return {"n": int(len(o)), "r": round(float(np.corrcoef(o, e)[0, 1]), 4),
            "mbe_pct": round(float(100 * (e.sum() - o.sum()) / o.sum()), 2),
            "rmse_wm2": round(float(np.sqrt(np.mean((e - o) ** 2))), 1),
            "rmse_pct": round(float(100 * np.sqrt(np.mean((e - o) ** 2)) / o.mean()), 1)}


def main(out):
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    sts = list(csv.DictReader(open(os.path.join(ROOT, "agent/ground/stations.csv"))))
    rows, ep_rows, fill_rows, per = [], [], [], {}
    for st in sts:
        name = st["name"]
        try:
            j, pm = load_station(name)
        except FileNotFoundError as e:
            per[name] = {"error": str(e)}
            continue
        day = (j.zen < 85) & j.ground.notna() & j.nsrdb.notna() & j.power.notna()
        h = j[day]
        # daily totals over hours where all three are valid; keep days with >= 6 such hours
        dd = h[["ground", "nsrdb", "power"]].resample("1D").agg(["sum", "count"])
        dsum = pd.DataFrame({k: dd[(k, "sum")] for k in ["ground", "nsrdb", "power"]})[dd[("ground", "count")] >= 6]
        rec = {"station": name, "network": st["network"], "lat": float(st["lat"]), "lon": float(st["lon"]),
               "elev_m": float(st["elev_m"]), "daylight_hours": int(day.sum()), "days": int(len(dsum)),
               "hourly": {"nsrdb": stats(h.ground.values, h.nsrdb.values), "power": stats(h.ground.values, h.power.values)},
               "daily": {"nsrdb": stats(dsum.ground.values, dsum.nsrdb.values),
                         "power": stats(dsum.ground.values, dsum.power.values)}}
        en, ep = np.abs(dsum.nsrdb - dsum.ground), np.abs(dsum.power - dsum.ground)
        rec["daily_nsrdb_closer_frac"] = round(float((en < ep).mean()), 3)
        if "fill" in h:
            filled = h.fill >= 50
            on_ep = pd.Series(h.index.strftime("%Y-%m-%d").isin(EPISODES), index=h.index)
            for lab, m in [("filled", filled), ("retrieved", ~filled),
                           ("filled_routine", filled & ~on_ep), ("filled_episode", filled & on_ep)]:
                rec[f"hourly_{lab}"] = {"nsrdb": stats(h.ground[m].values, h.nsrdb[m].values),
                                        "power": stats(h.ground[m].values, h.power[m].values)}
                fill_rows.append([name, lab, int(m.sum()), rec[f"hourly_{lab}"]["nsrdb"].get("rmse_wm2"),
                                  rec[f"hourly_{lab}"]["power"].get("rmse_wm2"),
                                  rec[f"hourly_{lab}"]["nsrdb"].get("mbe_pct"), rec[f"hourly_{lab}"]["power"].get("mbe_pct")])
        for d in EPISODES:
            x = j.loc[d]
            dl = (x.zen < 85)
            fillfrac = float((x.fill[dl] >= 50).mean()) if "fill" in x and dl.any() else None
            ep_rows.append([name, float(st["lon"]), d, round(float(x.ground[dl].sum())), round(float(x.nsrdb[dl].sum())),
                            round(float(x.power[dl].sum())), round(float(x.power_clear[dl].sum())),
                            None if fillfrac is None else round(fillfrac, 2), int(x.ground[dl].notna().sum()), int(dl.sum())])
        per[name] = rec
        rows.append(rec)

    with open(os.path.join(out, "stations.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "lat", "lon", "elev_m", "days", "nsrdb_daily_r", "power_daily_r", "nsrdb_daily_mbe_pct",
                    "power_daily_mbe_pct", "nsrdb_hourly_rmse_wm2", "power_hourly_rmse_wm2", "nsrdb_daily_rmse_pct",
                    "power_daily_rmse_pct", "daily_nsrdb_closer_frac"])
        for r in rows:
            w.writerow([r["station"], r["lat"], r["lon"], r["elev_m"], r["days"], r["daily"]["nsrdb"]["r"],
                        r["daily"]["power"]["r"], r["daily"]["nsrdb"]["mbe_pct"], r["daily"]["power"]["mbe_pct"],
                        r["hourly"]["nsrdb"]["rmse_wm2"], r["hourly"]["power"]["rmse_wm2"],
                        r["daily"]["nsrdb"]["rmse_pct"], r["daily"]["power"]["rmse_pct"], r["daily_nsrdb_closer_frac"]])
    with open(os.path.join(out, "episode_days.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "lon", "date", "ground_whm2", "nsrdb_whm2", "power_whm2", "power_clear_whm2",
                    "nsrdb_fill_frac_daylight", "ground_valid_hours", "daylight_hours"])
        w.writerows(ep_rows)
    with open(os.path.join(out, "fill_vs_retrieved.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "nsrdb_hours", "n", "nsrdb_rmse_wm2", "power_rmse_wm2", "nsrdb_mbe_pct", "power_mbe_pct"])
        w.writerows(fill_rows)

    med = lambda key, prod, f: round(float(np.median([r[key][prod][f] for r in rows])), 4)
    ep = pd.DataFrame(ep_rows, columns=["station", "lon", "date", "g", "n", "p", "c", "fill", "gv", "dl"])
    epf = ep[(ep.fill >= 0.5) & (ep.gv >= 0.8 * ep.dl)]
    epn = ep[(ep.fill < 0.5) & (ep.gv >= 0.8 * ep.dl)]
    fr = pd.DataFrame(fill_rows, columns=["station", "kind", "n", "nr", "pr", "nm", "pm"])
    for c in ["nr", "pr", "nm", "pm"]:
        fr[c] = pd.to_numeric(fr[c], errors="coerce")  # None when a group has < 50 hours
    summ = {
        "stations": len(rows), "period": "2019-2023", "daylight_definition": "zenith < 85 deg, all three series valid",
        "median_daily_r": {"nsrdb": med("daily", "nsrdb", "r"), "power": med("daily", "power", "r")},
        "median_daily_mbe_pct": {"nsrdb": med("daily", "nsrdb", "mbe_pct"), "power": med("daily", "power", "mbe_pct")},
        "median_daily_rmse_pct": {"nsrdb": med("daily", "nsrdb", "rmse_pct"), "power": med("daily", "power", "rmse_pct")},
        "median_hourly_rmse_wm2": {"nsrdb": med("hourly", "nsrdb", "rmse_wm2"), "power": med("hourly", "power", "rmse_wm2")},
        "stations_where_nsrdb_daily_rmse_lower": int(sum(r["daily"]["nsrdb"]["rmse_pct"] < r["daily"]["power"]["rmse_pct"] for r in rows)),
        "median_daily_nsrdb_closer_frac": round(float(np.median([r["daily_nsrdb_closer_frac"] for r in rows])), 3),
        "filled_hours": {"hours": int(fr[fr.kind == "filled"].n.sum()),
                         "median_nsrdb_rmse_wm2": round(float(fr[fr.kind == "filled"].nr.median()), 1),
                         "median_power_rmse_wm2_same_hours": round(float(fr[fr.kind == "filled"].pr.median()), 1)},
        "filled_routine_hours": {"hours": int(fr[fr.kind == "filled_routine"].n.sum()),
                                 "median_nsrdb_rmse_wm2": round(float(fr[fr.kind == "filled_routine"].nr.median()), 1),
                                 "median_power_rmse_wm2_same_hours": round(float(fr[fr.kind == "filled_routine"].pr.median()), 1),
                                 "median_nsrdb_mbe_pct": round(float(fr[fr.kind == "filled_routine"].nm.median()), 1)},
        "filled_episode_hours": {"hours": int(fr[fr.kind == "filled_episode"].n.sum()),
                                 "median_nsrdb_rmse_wm2": round(float(fr[fr.kind == "filled_episode"].nr.dropna().median()), 1),
                                 "median_power_rmse_wm2_same_hours": round(float(fr[fr.kind == "filled_episode"].pr.dropna().median()), 1),
                                 "median_nsrdb_mbe_pct": round(float(fr[fr.kind == "filled_episode"].nm.dropna().median()), 1)},
        "retrieved_hours": {"hours": int(fr[fr.kind == "retrieved"].n.sum()),
                            "median_nsrdb_rmse_wm2": round(float(fr[fr.kind == "retrieved"].nr.median()), 1),
                            "median_power_rmse_wm2_same_hours": round(float(fr[fr.kind == "retrieved"].pr.median()), 1)},
        "episode_days": {"station_days_filled": int(len(epf)), "station_days_not_filled": int(len(epn)),
                         "filled_median_abs_err_pct": {
                             "nsrdb": round(float(np.median(100 * np.abs(epf.n - epf.g) / epf.g)), 1) if len(epf) else None,
                             "power": round(float(np.median(100 * np.abs(epf.p - epf.g) / epf.g)), 1) if len(epf) else None},
                         "filled_stations_lon_range": [float(epf.lon.min()), float(epf.lon.max())] if len(epf) else None,
                         "not_filled_stations": sorted(set(epn.station))},
        "per_station": per,
    }
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=1)
    figures(out, rows, ep)
    print(json.dumps({k: v for k, v in summ.items() if k != "per_station"}, indent=1))


def figures(out, rows, ep):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [r["station"].split("_", 1)[1] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(x - 0.2, [r["daily"]["nsrdb"]["rmse_pct"] for r in rows], 0.4, label="NSRDB (HEDW-US source)")
    ax.bar(x + 0.2, [r["daily"]["power"]["rmse_pct"] for r in rows], 0.4, label="NASA POWER")
    ax.set_xticks(x, names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("daily RMSE vs ground (%)"); ax.legend(); ax.set_title("Daily GHI error against SURFRAD/SOLRAD, 2019-2023")
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/rmse_by_station.png"), dpi=110); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 6))
    v = ep[ep.gv >= 0.8 * ep.dl]
    f = v.fill >= 0.5
    ax.scatter(v.g[f], v.n[f], c="C3", label="NSRDB, filled day")
    ax.scatter(v.g[~f], v.n[~f], c="C0", label="NSRDB, retrieved")
    ax.scatter(v.g, v.p, marker="x", c="k", label="POWER")
    m = max(v.g.max(), v.n.max(), v.p.max()) * 1.05
    ax.plot([0, m], [0, m], "k:", lw=0.8); ax.set_xlabel("ground daily GHI (Wh/m2)"); ax.set_ylabel("product (Wh/m2)")
    ax.set_title("Gap-fill episode days (2019-11-17..20, 2020-02-13..14)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(out, "figures/episode_days.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1])
