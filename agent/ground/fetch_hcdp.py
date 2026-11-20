#!/usr/bin/env python3
"""Fetch Hawaii Mesonet incoming shortwave (SWin_1_Avg, W/m2, 5-min) from the
HCDP API (https://api.hcdp.ikewai.org, spec: github.com/hcdp/hcdp_api_docs).

Token: HCDP_TOKEN in ~/.config/hedw/hcdp.env (outside the repo; requested by the
user through the HCDP API access form). Requests are one station-month each,
1 s apart. Output: raw/ground/hcdp/<station_id>.csv (timestamp UTC, value).
usage: fetch_hcdp.py <station_id>[,<station_id>...] <start YYYY-MM> <end YYYY-MM>
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = "https://api.hcdp.ikewai.org/mesonet/db/measurements"


def token():
    for line in open(os.path.expanduser("~/.config/hedw/hcdp.env")):
        if line.startswith("HCDP_TOKEN="):
            return line.split("=", 1)[1].strip()
    sys.exit("HCDP_TOKEN missing")


def months(a, b):
    y, m = map(int, a.split("-")); y1, m1 = map(int, b.split("-"))
    while (y, m) <= (y1, m1):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def get(params, tok):
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {tok}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print("  retry", attempt, type(e).__name__, flush=True); time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed " + str(params))


def main(ids, a, b):
    tok = token()
    os.makedirs(os.path.join(ROOT, "raw/ground/hcdp"), exist_ok=True)
    for sid in ids.split(","):
        rows = []
        for y, m in months(a, b):
            ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
            d = get({"station_ids": sid, "var_ids": "SWin_1_Avg", "row_mode": "array", "reverse": "true",
                     "start_date": f"{y}-{m:02d}-01T00:00:00Z", "end_date": f"{ny}-{nm:02d}-01T00:00:00Z",
                     "limit": 50000}, tok)
            # the API's index lists station_id first, but rows carry the timestamp first; detect by content
            for r in d["data"]:
                ts = r[0] if "T" in str(r[0]) else r[1]
                if ts < f"{ny}-{nm:02d}-01":
                    rows.append((ts, r[3]))
            print(f"{sid} {y}-{m:02d}: {len(d['data'])}", flush=True)
            time.sleep(1)
        rows = sorted(set(rows))
        with open(os.path.join(ROOT, "raw/ground/hcdp", f"{sid}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["timestamp_utc", "swin_wm2"]); w.writerows(rows)
        print(sid, "rows", len(rows))


if __name__ == "__main__":
    main(*sys.argv[1:4])
