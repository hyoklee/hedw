#!/usr/bin/env python3
"""Download CIMIS hourly solar radiation (hly-sol-rad, W/m2) for 2019-2023.

API (documented on cimis.water.ca.gov/web-api/rest-api/latest): base
https://et.water.ca.gov, key in header Ocp-Apim-Subscription-Key (the user's
key, read from ~/.config/hedw/cimis.env, never from the repo), at most 1,750
records per request -> 70-day chunks per station.
Output: raw/ground/cimis/<name>.csv with date, hour (CIMIS 0100..2400 label), value, qc.
usage: fetch_cimis.py [--stations agent/ground/cimis_selected.csv]
"""
import argparse, csv, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://et.water.ca.gov/StationWeb/GetDataByStationNumber"


def key():
    for line in open(os.path.expanduser("~/.config/hedw/cimis.env")):
        if line.startswith("CIMIS_APP_KEY="):
            return line.split("=", 1)[1].strip()


def get(params, k, tries=4):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": k, "Accept": "application/json",
                                                       "User-Agent": "hedw-cimis/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read()[:200].decode("utf-8", "replace")
            print(f"  HTTP {e.code} {params['stationNbrs']} {params['startDate']}: {msg}", flush=True)
            if e.code in (400, 404):
                return None
        except Exception as e:  # noqa: BLE001
            print(f"  error {params['stationNbrs']} {params['startDate']}: {e}", flush=True)
        time.sleep(5 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", default=os.path.join(ROOT, "agent/ground/cimis_selected.csv"))
    a = ap.parse_args()
    k = key()
    os.makedirs(os.path.join(ROOT, "raw/ground/cimis"), exist_ok=True)
    for st in csv.DictReader(open(a.stations)):
        out = os.path.join(ROOT, "raw/ground/cimis", f"{st['name']}.csv")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            print(st["name"], "skip", flush=True); continue
        t0, rows, d, fails = time.time(), [], date(2019, 1, 1), 0
        while d <= date(2023, 12, 31):
            e = min(d + timedelta(days=69), date(2023, 12, 31))
            js = get({"stationNbrs": st["code"], "startDate": d.isoformat(), "endDate": e.isoformat(),
                      "isHourly": "true", "unitOfMeasure": "M", "dataItems": "hly-sol-rad"}, k)
            if js is None:
                fails += 1
            else:
                for p in js["Data"]["Providers"]:
                    for r in p["Records"]:
                        v = r.get("HlySolRad") or {}
                        rows.append([r["Date"], r["Hour"], v.get("Value") or "", (v.get("Qc") or "").strip()])
            d = e + timedelta(days=1)
            time.sleep(1.0)
        with open(out + ".part", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "hour", "sol_rad_wm2", "qc"]); w.writerows(rows)
        os.replace(out + ".part", out)
        print(st["name"], f"{len(rows)} hourly records, {fails} failed chunk(s), {time.time()-t0:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
