# FrameworkSpeed (local prototype)
Monthly real-user Core Web Vitals leaderboard for web frameworks, hosts and CMSs.

- Data: HTTP Archive Tech Report API, public, no key: `https://cdn.httparchive.org/v1/cwv?technology=A,B&geo=ALL&rank=ALL&start=YYYY-MM-DD`
  (`/v1/dates` lists available months; `/v1/technologies?onlyname` lists valid names). CrUX field data + HTTP Archive tech detection.
- `scripts/technologies.json`: tracked technologies by category (62).
- `scripts/fetch_data.py`: writes `data/raw.json` (latest + ~14 prior months).
- `scripts/build_site.py`: computes leaderboard (`data/leaderboard.json`) and writes static site to `site/`.
- `scripts/refresh.sh`: fetch + build (run monthly, e.g. GitHub Actions cron).
- Preview: `cd site && python3 -m http.server 8000`.

## Deployment
Live: https://litseytrevor.github.io/frameworkspeed/ (GitHub Pages, source = GitHub Actions).
`.github/workflows/refresh-and-deploy.yml` runs on the 15th of each month (14:00 UTC), on manual dispatch, and on pushes to scripts/workflow:
fetches data, commits `data/` if changed, builds `site/`, deploys via actions/deploy-pages.

## Placeholders (not live yet)
- Newsletter signup form (no provider connected; nothing is submitted).
- Sponsor contact `sponsor@example.com` on sponsor.html.
