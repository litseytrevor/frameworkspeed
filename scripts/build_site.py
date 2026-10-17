#!/usr/bin/env python3
"""Compute leaderboard from data/raw.json and generate the static site in site/."""
import json, pathlib, re, html, datetime, shutil
ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MIN_ORIGINS = 1000  # minimum mobile origins tested to be ranked
COMPARISONS = [("Next.js", "Astro"), ("WordPress", "Shopify"), ("Vercel", "Netlify"), ("React", "Vue.js"), ("Wix", "Squarespace")]
SITE_NAME = "FrameworkSpeed"
BASE_URL = "https://litseytrevor.github.io/frameworkspeed/"

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def pct(g, t): return round(100 * g / t, 1) if t else None
def mlabel(d): return datetime.date.fromisoformat(d).strftime("%b %Y")
def esc(s): return html.escape(str(s))

def load():
    raw = json.loads((ROOT / "data/raw.json").read_text())
    cat_of = {t: c for c, ts in raw["categories"].items() for t in ts}
    series = {}
    for r in raw["rows"]:
        v = {x["name"]: x for x in r["vitals"]}
        o = v.get("overall")
        if not o: continue
        rec = {"date": r["date"],
               "mobile": pct(o["mobile"]["good_number"], o["mobile"]["tested"]), "mobile_n": o["mobile"]["tested"],
               "desktop": pct(o["desktop"]["good_number"], o["desktop"]["tested"]), "desktop_n": o["desktop"]["tested"]}
        for m in ("LCP", "INP", "CLS"):
            if m in v: rec[m] = pct(v[m]["mobile"]["good_number"], v[m]["mobile"]["tested"])
        series.setdefault(r["technology"], []).append(rec)
    for t in series: series[t].sort(key=lambda x: x["date"])
    return raw, cat_of, series

def compute(raw, cat_of, series):
    latest = max(r["date"] for s in series.values() for r in s)
    board = []
    for t, s in series.items():
        cur = s[-1]
        if cur["date"] != latest or cur["mobile"] is None: continue
        prev = s[-2] if len(s) > 1 else None
        yr = next((x for x in s if x["date"][:7] == f"{int(latest[:4])-1}{latest[4:7]}"), None)
        board.append({"tech": t, "slug": slug(t), "category": cat_of.get(t, "Other"), **cur,
                      "mom": round(cur["mobile"] - prev["mobile"], 1) if prev and prev["mobile"] is not None else None,
                      "yoy": round(cur["mobile"] - yr["mobile"], 1) if yr and yr["mobile"] is not None else None,
                      "ranked": cur["mobile_n"] >= MIN_ORIGINS})
    board.sort(key=lambda x: -x["mobile"])
    r = 0
    for b in board:
        if b["ranked"]: r += 1; b["rank"] = r
        else: b["rank"] = None
    board.sort(key=lambda x: (not x["ranked"], -x["mobile"]))
    return latest, board

CSS = """*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#111;background:#fafafa}
a{color:#0b57d0;text-decoration:none}a:hover{text-decoration:underline}
header,main,footer{max-width:960px;margin:0 auto;padding:0 20px}
header{display:flex;align-items:center;justify-content:space-between;padding-top:18px;padding-bottom:18px;border-bottom:1px solid #e5e5e5}
.logo{font-weight:800;font-size:20px;color:#111;letter-spacing:-.02em}.logo span{color:#0a8f4a}
nav a{margin-left:18px;color:#444;font-size:15px}
h1{font-size:32px;letter-spacing:-.02em;margin:32px 0 6px}h2{font-size:22px;margin:36px 0 10px}
.sub{color:#555;margin:0 0 20px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e5e5;border-radius:8px;overflow:hidden;font-size:15px}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #eee}th{background:#f4f4f4;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#555}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{display:inline-block;height:8px;background:#0a8f4a;border-radius:4px;vertical-align:middle;margin-right:8px}
.up{color:#0a8f4a}.down{color:#c5221f}.muted{color:#888}
.cat{font-size:12px;color:#666;background:#f0f0f0;padding:2px 7px;border-radius:10px;white-space:nowrap}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:18px 0}
.card{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:14px 16px}.card b{font-size:26px;display:block}
.box{background:#fff;border:1px solid #e5e5e5;border-radius:8px;padding:20px;margin:24px 0}
.signup input{padding:10px;border:1px solid #ccc;border-radius:6px;width:260px;font-size:15px}
.signup button,.btn{padding:10px 16px;border:0;border-radius:6px;background:#111;color:#fff;font-size:15px;cursor:pointer}
footer{color:#777;font-size:13px;padding-top:30px;padding-bottom:40px;border-top:1px solid #e5e5e5;margin-top:48px}
svg text{font:12px system-ui,sans-serif;fill:#666}
.filters a{margin-right:10px;font-size:14px}"""

def page(title, body, desc="", depth=0, path=""):
    p = "../" * depth
    canon = BASE_URL + ("" if path == "index.html" else path)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canon}"><meta property="og:title" content="{esc(title)}"><meta property="og:url" content="{canon}"><link rel="stylesheet" href="{p}style.css"></head><body>
<header><a class="logo" href="{p}index.html">Framework<span>Speed</span></a><nav><a href="{p}index.html">Leaderboard</a><a href="{p}compare/index.html">Compare</a><a href="{p}about.html">Methodology</a><a href="{p}sponsor.html">Sponsor</a></nav></header>
<main>{body}</main>
<footer>Data: <a href="https://httparchive.org/reports/cwv-tech">HTTP Archive Core Web Vitals Technology Report</a> (Chrome UX Report real-user data + HTTP Archive technology detection). Updated monthly. {SITE_NAME} is an independent project.</footer></body></html>"""

def delta(v):
    if v is None: return '<span class="muted">–</span>'
    c = "up" if v > 0 else "down" if v < 0 else "muted"
    return f'<span class="{c}">{"+" if v > 0 else ""}{v:.1f}</span>'

def chart(lines, w=900, h=300):
    """lines: [(label,color,[(date,val)])] -> inline SVG"""
    pts = [v for _, _, s in lines for _, v in s if v is not None]
    if not pts: return ""
    lo, hi = max(0, int(min(pts) // 10 * 10)), min(100, int(-(-max(pts) // 10) * 10))
    if hi == lo: hi = lo + 10
    dates = sorted({d for _, _, s in lines for d, _ in s})
    L, R, T, B = 44, 20, 16, 40
    X = lambda i: L + (w - L - R) * i / max(1, len(dates) - 1)
    Y = lambda v: T + (h - T - B) * (1 - (v - lo) / (hi - lo))
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Core Web Vitals pass rate over time">']
    for g in range(lo, hi + 1, 10):
        o.append(f'<line x1="{L}" x2="{w-R}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="#eee"/><text x="{L-8}" y="{Y(g)+4:.1f}" text-anchor="end">{g}%</text>')
    for i, d in enumerate(dates):
        if i % 2 == 0 or i == len(dates) - 1:
            o.append(f'<text x="{X(i):.1f}" y="{h-14}" text-anchor="middle">{datetime.date.fromisoformat(d).strftime("%b %y")}</text>')
    for label, color, s in lines:
        m = dict(s); p = [(X(i), Y(m[d])) for i, d in enumerate(dates) if m.get(d) is not None]
        o.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in p)}"/>')
        for x, y in p: o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
    o.append("</svg>")
    leg = " ".join(f'<span style="margin-right:16px"><span style="display:inline-block;width:12px;height:12px;background:{c};border-radius:2px;vertical-align:-1px"></span> {esc(l)}</span>' for l, c, _ in lines)
    return "".join(o) + f'<div style="font-size:14px;margin-top:4px">{leg}</div>'

SIGNUP = """<div class="box signup"><!-- PLACEHOLDER: newsletter form not connected to any provider yet --><h2 style="margin-top:0">Get the monthly leaderboard</h2><p class="sub">One email a month when new CrUX data lands: who moved, who slipped, and why. No spam.</p>
<form onsubmit="alert('Newsletter coming soon. This is a placeholder.');return false"><input type="email" placeholder="you@example.com" required> <button>Subscribe</button></form><p class="muted" style="font-size:13px;margin-bottom:0">Placeholder: the newsletter is not live yet; nothing is submitted.</p></div>"""

def main():
    raw, cat_of, series = load()
    latest, board = compute(raw, cat_of, series)
    L = mlabel(latest)
    if SITE.exists(): shutil.rmtree(SITE)
    (SITE / "tech").mkdir(parents=True); (SITE / "compare").mkdir()
    (SITE / "style.css").write_text(CSS)
    ranked = [b for b in board if b["ranked"]]
    movers = sorted([b for b in ranked if b["mom"] is not None], key=lambda b: -abs(b["mom"]))[:6]
    # JSON export
    (ROOT / "data/leaderboard.json").write_text(json.dumps({"month": latest, "min_origins": MIN_ORIGINS, "board": board}, indent=1))

    # home
    cats = sorted({b["category"] for b in ranked})
    rows = []
    for b in board:
        rk = b["rank"] if b["rank"] else '<span class="muted" title="fewer than %d origins">–</span>' % MIN_ORIGINS
        rows.append(f'<tr data-cat="{esc(b["category"])}"><td class="n">{rk}</td><td><a href="tech/{b["slug"]}.html">{esc(b["tech"])}</a></td><td><span class="cat">{esc(b["category"])}</span></td>'
                    f'<td><span class="bar" style="width:{b["mobile"]*1.2:.0f}px"></span>{b["mobile"]:.1f}%</td><td class="n">{delta(b["mom"])}</td><td class="n">{delta(b["yoy"])}</td>'
                    f'<td class="n">{b["desktop"]:.1f}%</td><td class="n">{b["mobile_n"]:,}</td></tr>')
    mv = "".join(f'<div class="card"><a href="tech/{b["slug"]}.html">{esc(b["tech"])}</a><b class="{"up" if b["mom"]>0 else "down"}">{"+" if b["mom"]>0 else ""}{b["mom"]:.1f} pts</b><span class="muted">now {b["mobile"]:.1f}% mobile</span></div>' for b in movers)
    flt = '<div class="filters">Filter: <a href="#" data-f="">All</a>' + "".join(f'<a href="#" data-f="{esc(c)}">{esc(c)}</a>' for c in cats) + "</div>"
    js = """<script>document.querySelectorAll('.filters a').forEach(a=>a.onclick=e=>{e.preventDefault();const f=a.dataset.f;document.querySelectorAll('tbody tr').forEach(r=>r.style.display=!f||r.dataset.cat===f?'':'none')})</script>"""
    body = f"""<h1>Which web stacks are actually fast?</h1><p class="sub">Share of real-world origins passing all three Core Web Vitals (LCP, INP, CLS) on mobile, by technology. Data month: <b>{L}</b>. Source: Chrome UX Report via HTTP Archive.</p>
<h2>Biggest movers this month</h2><div class="cards">{mv}</div>
<h2>Leaderboard: {L}</h2>{flt}<p class="muted" style="font-size:13px">Ranked by mobile pass rate; technologies with fewer than {MIN_ORIGINS:,} mobile origins are shown unranked. Δ = percentage-point change in mobile pass rate.</p>
<table><thead><tr><th class="n">#</th><th>Technology</th><th>Type</th><th>Mobile pass rate</th><th class="n">Δ MoM</th><th class="n">Δ YoY</th><th class="n">Desktop</th><th class="n">Mobile origins</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
{SIGNUP}{js}"""
    (SITE / "index.html").write_text(page(f"{SITE_NAME}: Core Web Vitals leaderboard for web frameworks, hosts and CMSs ({L})", body, f"Monthly real-user Core Web Vitals pass rates for {len(board)} web technologies. Data month {L}.", 0, "index.html"))

    # tech pages
    for b in board:
        s = series[b["tech"]]
        c = chart([("Mobile", "#0a8f4a", [(x["date"], x["mobile"]) for x in s]), ("Desktop", "#0b57d0", [(x["date"], x["desktop"]) for x in s])])
        trs = "".join(f'<tr><td>{mlabel(x["date"])}</td><td class="n">{x["mobile"]:.1f}%</td><td class="n">{x["desktop"]:.1f}%</td><td class="n">{x.get("LCP","–")}%</td><td class="n">{x.get("INP","–")}%</td><td class="n">{x.get("CLS","–")}%</td><td class="n">{x["mobile_n"]:,}</td></tr>' for x in reversed(s))
        peers = [p for p in ranked if p["category"] == b["category"] and p["tech"] != b["tech"]][:6]
        pl = ", ".join(f'<a href="{p["slug"]}.html">{esc(p["tech"])}</a> ({p["mobile"]:.1f}%)' for p in peers)
        rk = f'#{b["rank"]} of {len(ranked)}' if b["rank"] else "Unranked (small sample)"
        body = f"""<h1>{esc(b["tech"])} Core Web Vitals</h1><p class="sub"><span class="cat">{esc(b["category"])}</span> &nbsp;Real-user pass rate, data through {L}.</p>
<div class="cards"><div class="card">Mobile pass rate<b>{b["mobile"]:.1f}%</b>{delta(b["mom"])} pts vs last month</div><div class="card">Desktop pass rate<b>{b["desktop"]:.1f}%</b></div><div class="card">Leaderboard rank<b>{rk}</b></div><div class="card">Mobile origins measured<b>{b["mobile_n"]:,}</b></div></div>
<div class="box">{c}</div><h2>Similar technologies</h2><p>{pl or "–"}</p>
<h2>Monthly data</h2><p class="muted" style="font-size:13px">LCP/INP/CLS columns are the share of mobile origins with a "good" score for each metric.</p>
<table><thead><tr><th>Month</th><th class="n">Mobile</th><th class="n">Desktop</th><th class="n">LCP</th><th class="n">INP</th><th class="n">CLS</th><th class="n">Mobile origins</th></tr></thead><tbody>{trs}</tbody></table>{SIGNUP}"""
        (SITE / "tech" / f'{b["slug"]}.html').write_text(page(f'{b["tech"]} Core Web Vitals pass rate ({L}) | {SITE_NAME}', body, f'{b["tech"]}: {b["mobile"]:.1f}% of origins pass Core Web Vitals on mobile ({L}).', 1, f'tech/{b["slug"]}.html'))

    # comparisons
    bym = {b["tech"]: b for b in board}
    links = []
    for a, z in COMPARISONS:
        if a not in bym or z not in bym: continue
        A, Z = bym[a], bym[z]
        c = chart([(a + " (mobile)", "#0a8f4a", [(x["date"], x["mobile"]) for x in series[a]]), (z + " (mobile)", "#e8710a", [(x["date"], x["mobile"]) for x in series[z]])])
        def row(lbl, k, suf="%"):
            va, vz = A.get(k), Z.get(k)
            return f'<tr><td>{lbl}</td><td class="n">{va}{suf}</td><td class="n">{vz}{suf}</td></tr>'
        win = a if A["mobile"] > Z["mobile"] else z
        gap = abs(A["mobile"] - Z["mobile"])
        fn = f"{slug(a)}-vs-{slug(z)}.html"
        body = f"""<h1>{esc(a)} vs {esc(z)}: real-world speed</h1><p class="sub">In {L}, {win} sites passed Core Web Vitals on mobile {gap:.1f} percentage points more often ({A["mobile"]:.1f}% vs {Z["mobile"]:.1f}%).</p>
<div class="box">{c}</div><table><thead><tr><th>{L}</th><th class="n">{esc(a)}</th><th class="n">{esc(z)}</th></tr></thead><tbody>
{row("Mobile pass rate (all 3 CWV)","mobile")}{row("Desktop pass rate","desktop")}{row("Good LCP (mobile)","LCP")}{row("Good INP (mobile)","INP")}{row("Good CLS (mobile)","CLS")}
<tr><td>Change vs last month (pts)</td><td class="n">{delta(A["mom"])}</td><td class="n">{delta(Z["mom"])}</td></tr><tr><td>Change vs a year ago (pts)</td><td class="n">{delta(A["yoy"])}</td><td class="n">{delta(Z["yoy"])}</td></tr>
<tr><td>Mobile origins measured</td><td class="n">{A["mobile_n"]:,}</td><td class="n">{Z["mobile_n"]:,}</td></tr></tbody></table>
<p class="muted" style="font-size:14px">Correlation, not causation: pass rates reflect the kinds of sites built with each technology (audience, devices, content, hosting), not only the technology itself. See <a href="../about.html">methodology</a>.</p>{SIGNUP}"""
        (SITE / "compare" / fn).write_text(page(f"{a} vs {z} Core Web Vitals ({L}) | {SITE_NAME}", body, f"{a} vs {z} real-user Core Web Vitals pass rates, {L}.", 1, "compare/" + fn))
        links.append(f'<li><a href="{fn}">{esc(a)} vs {esc(z)}</a>: {A["mobile"]:.1f}% vs {Z["mobile"]:.1f}% mobile</li>')
    (SITE / "compare" / "index.html").write_text(page(f"Comparisons | {SITE_NAME}", f"<h1>Head-to-head comparisons</h1><p class='sub'>Data month {L}.</p><ul>{''.join(links)}</ul>", "", 1, "compare/index.html"))

    # about
    about = f"""<h1>Methodology</h1>
<p><b>Data source.</b> All figures come from the <a href="https://httparchive.org/reports/cwv-tech">HTTP Archive Core Web Vitals Technology Report</a>, fetched from its public API (<code>https://cdn.httparchive.org/v1/cwv</code>, no key required). That report joins real-user measurements from Google's <a href="https://developer.chrome.com/docs/crux">Chrome UX Report (CrUX)</a> with technology detections from HTTP Archive's monthly crawl (Wappalyzer-based). API code: <a href="https://github.com/HTTPArchive/tech-report-apis">HTTPArchive/tech-report-apis</a>.</p>
<p><b>Metric.</b> "Pass rate" = share of origins detected using a technology whose 75th-percentile real-user LCP, INP and CLS are all "good" (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1). Geography: all; rank: all origins. The leaderboard ranks by mobile pass rate; desktop is shown alongside.</p>
<p><b>Minimum sample.</b> Technologies with fewer than {MIN_ORIGINS:,} mobile origins in the latest month appear unranked.</p>
<p><b>Changes.</b> Δ MoM and Δ YoY are percentage-point differences in mobile pass rate versus the previous month and the same month a year earlier.</p>
<p><b>Caveats.</b> This is correlation, not causation. Who uses a technology (large e-commerce vs small blogs), their audiences' devices and networks, and detection accuracy all affect the numbers. CrUX only includes origins with enough Chrome traffic. A month's data is published by HTTP Archive after the month's crawl completes.</p>
<p><b>Freshness.</b> Data month shown: {L}. Last fetched: {raw["fetched_at"][:10]} (UTC).</p>
<p><b>License/credit.</b> Data courtesy of HTTP Archive and the Chrome UX Report. {SITE_NAME} is independent and not affiliated with Google or HTTP Archive.</p>"""
    (SITE / "about.html").write_text(page(f"Methodology | {SITE_NAME}", about, "How FrameworkSpeed calculates its leaderboard.", 0, "about.html"))
    sponsor = """<h1>Sponsor FrameworkSpeed</h1><p class="sub">Reach web developers who care about performance: framework authors, frontend engineers, agencies and performance consultants.</p>
<div class="box"><h2 style="margin-top:0">Placements (coming soon)</h2><ul><li>Monthly newsletter sponsor (one per issue)</li><li>Site-wide sponsor slot on the leaderboard and technology pages</li><li>"Verified fast" showcase listings for templates, themes and agencies</li></ul>
<p>Rates and audience stats will be published once the newsletter launches.</p><!-- PLACEHOLDER: replace sponsor@example.com with a real contact address --><p><a class="btn" href="mailto:sponsor@example.com">Get in touch (placeholder address)</a></p></div>"""
    (SITE / "sponsor.html").write_text(page(f"Sponsor | {SITE_NAME}", sponsor, "Sponsorship options.", 0, "sponsor.html"))
    # sitemap
    urls = ["index.html", "about.html", "sponsor.html", "compare/index.html"] + [f"tech/{b['slug']}.html" for b in board] + [f"compare/{slug(a)}-vs-{slug(z)}.html" for a, z in COMPARISONS]
    (SITE / "sitemap.txt").write_text("\n".join(BASE_URL + ("" if u == "index.html" else u) for u in urls))
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.txt\n")
    (SITE / ".nojekyll").write_text("")
    print(f"built {len(urls)} pages, data month {latest}, {len(ranked)} ranked / {len(board)} total")

if __name__ == "__main__":
    main()
