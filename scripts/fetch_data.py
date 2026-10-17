#!/usr/bin/env python3
"""Fetch monthly real-user Core Web Vitals pass rates per technology from the
HTTP Archive Tech Report API (public, no key): https://cdn.httparchive.org/v1
Data = Chrome UX Report (CrUX) field data joined with HTTP Archive (Wappalyzer)
technology detections. Writes data/raw.json."""
import json, time, urllib.parse, urllib.request, datetime, pathlib, sys
API = "https://cdn.httparchive.org/v1"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MONTHS_BACK = 14

def get(path, params=None, tries=4):
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "frameworkspeed-refresh/0.1"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {i+1} {url}: {e}", file=sys.stderr); time.sleep(3 * (i + 1))
    raise RuntimeError(f"failed: {url}")

def main():
    cats = json.loads((ROOT / "scripts/technologies.json").read_text())
    techs = [t for ts in cats.values() for t in ts]
    dates = get("dates")["dates"]  # e.g. "2026_09_01", newest first
    start = dates[min(MONTHS_BACK, len(dates) - 1)].replace("_", "-")
    rows = []
    for i in range(0, len(techs), 4):
        batch = techs[i:i + 4]
        print("fetching", batch)
        rows += get("cwv", {"technology": ",".join(batch), "geo": "ALL", "rank": "ALL", "start": start})
    out = {"source": API + "/cwv", "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "api_dates_latest": dates[0], "start": start, "categories": cats, "rows": rows}
    (ROOT / "data/raw.json").write_text(json.dumps(out))
    print(f"wrote {len(rows)} rows for {len({r['technology'] for r in rows})}/{len(techs)} technologies")
    missing = set(techs) - {r["technology"] for r in rows}
    if missing: print("no data:", sorted(missing))

if __name__ == "__main__":
    main()
