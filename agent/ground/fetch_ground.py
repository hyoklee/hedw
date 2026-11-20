#!/usr/bin/env python3
"""Download NOAA GML SURFRAD / SOLRAD 1-min radiation for 2019-2023 and reduce
it to hourly means while streaming (the ~9 GB of daily files are not kept).

Output: raw/ground/<name>_hourly.csv with columns
  time_utc (start of hour), ghi (mean of QC-0 global minutes, W/m2),
  ghi_comp (mean of direct*cos(zen)+diffuse, QC-0 components), n_ghi, n_comp, zen
An hour needs >= 45 valid minutes, else the value is empty. The hourly mean
over [H:00, H+1:00) matches NASA POWER's hour H.

Column layout (README_SURFRAD / README_SOLRAD): year jday month day hour min dt zen,
then value+QC pairs. SURFRAD: global, upwelling, direct-normal, diffuse.
SOLRAD: global, direct-normal, diffuse. Missing = -9999.9.

usage: fetch_ground.py [--stations agent/ground/stations.csv] [--workers 8] [--only CODE]
"""
import argparse, csv, io, math, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://gml.noaa.gov/aftp/data/radiation"
COLS = {"surfrad": (8, 12, 14), "solrad": (8, 10, 12)}  # global, direct, diffuse value columns


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "hedw-ground/1.0"}),
                                        timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return b"ERROR"


def day_hourly(text, net):
    g, dn, df = COLS[net]
    rows = [l.split() for l in text.splitlines()[2:]]
    rows = [r for r in rows if len(r) > df + 1]
    if not rows:
        return []
    a = np.array([[float(r[4]), float(r[7]), float(r[g]), float(r[g + 1]), float(r[dn]), float(r[dn + 1]),
                   float(r[df]), float(r[df + 1])] for r in rows])
    hour, zen = a[:, 0].astype(int), a[:, 1]
    glob_ok = (a[:, 3] == 0) & (a[:, 2] > -9000)
    comp_ok = (a[:, 5] == 0) & (a[:, 7] == 0) & (a[:, 4] > -9000) & (a[:, 6] > -9000)
    comp = a[:, 4] * np.clip(np.cos(np.radians(zen)), 0, None) + a[:, 6]
    out = []
    for h in range(24):
        m = hour == h
        ng, nc = int((m & glob_ok).sum()), int((m & comp_ok).sum())
        out.append((h, float(a[m & glob_ok, 2].mean()) if ng >= 45 else None,
                    float(comp[m & comp_ok].mean()) if nc >= 45 else None, ng, nc,
                    float(zen[m].mean()) if m.any() else None))
    return out


def station(st, workers):
    out = os.path.join(ROOT, "raw/ground", f"{st['name']}_hourly.csv")
    days = [date(2019, 1, 1) + timedelta(d) for d in range((date(2024, 1, 1) - date(2019, 1, 1)).days)]
    kept = []
    if os.path.exists(out) and os.path.getsize(out) > 0:
        # Re-run: keep existing rows, fetch only the days that have none
        # (download errors last time; true 404s are cheap to re-ask).
        kept = list(csv.reader(open(out)))[1:]
        have = {r[0][:10] for r in kept}
        days = [d for d in days if d.isoformat() not in have]
        if not days:
            return st["name"], "skip"

    def one(d):
        yy, jd = d.year, d.timetuple().tm_yday
        url = f"{BASE}/{st['dir']}/{yy}/{st['code']}{yy % 100:02d}{jd:03d}.dat"
        b = get(url)
        if b is None:
            return d, "missing", []
        if b == b"ERROR":
            return d, "error", []
        try:
            return d, "ok", day_hourly(b.decode("ascii", "replace"), st["network"])
        except Exception as e:  # noqa: BLE001
            return d, f"parse:{e}", []

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(one, days))
    status = {}
    tmp = out + ".part"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "ghi", "ghi_comp", "n_ghi", "n_comp", "zen"])
        new = []
        for d, s, hours in res:
            status[s.split(":")[0]] = status.get(s.split(":")[0], 0) + 1
            for h, gv, cv, ng, nc, z in hours:
                new.append([f"{d.isoformat()}T{h:02d}:00Z", "" if gv is None else f"{gv:.2f}",
                            "" if cv is None else f"{cv:.2f}", ng, nc, "" if z is None else f"{z:.2f}"])
        w.writerows(sorted(kept + new, key=lambda r: r[0]))
    os.replace(tmp, out)
    return st["name"], f"{len(days)} day(s) requested: {status} in {time.time() - t0:.0f} s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default=os.path.join(ROOT, "agent/ground/stations.csv"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--only")
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "raw/ground"), exist_ok=True)
    for st in csv.DictReader(open(a.stations)):
        if a.only and st["code"] != a.only:
            continue
        print(time.strftime("%H:%M:%S"), *station(st, a.workers), flush=True)


if __name__ == "__main__":
    sys.exit(main())
