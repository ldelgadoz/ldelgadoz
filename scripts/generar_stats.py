"""Genera stats.svg con mi actividad de GitHub (sin servidores de terceros).
Lo ejecuta el workflow .github/workflows/stats.yml con el GITHUB_TOKEN."""
import json, os, urllib.request
from datetime import date, timedelta
from html import escape

USER = os.environ.get("GH_USER", "ldelgadoz")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){
      totalCount
      nodes{ languages(first:6, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name color } } } }
    }
  }
}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
u = json.load(urllib.request.urlopen(req))["data"]["user"]
cc = u["contributionsCollection"]
cal = cc["contributionCalendar"]
days = {d["date"]: d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]}

# Rachas
today = date.today()
cur = 0
d = today if days.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
while days.get(d.isoformat(), 0) > 0:
    cur += 1
    d -= timedelta(days=1)
best = run = 0
for k in sorted(days):
    run = run + 1 if days[k] > 0 else 0
    best = max(best, run)

commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
total = cal["totalContributions"]

# Contribuciones por semana (últimas 26)
weeks = [sum(x["contributionCount"] for x in w["contributionDays"]) for w in cal["weeks"]][-26:]

# Lenguajes
langs = {}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n = e["node"]
        l = langs.setdefault(n["name"], [0, n["color"] or "#8b949e"])
        l[0] += e["size"]
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:5]
tot_l = sum(v[0] for _, v in top) or 1

ACC, ACC2, BG, TXT, MUT = "#800040", "#e0307a", "#0d1117", "#e6edf3", "#8b949e"
W, H = 840, 390
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Actividad de GitHub de {escape(USER)}">',
     f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="{ACC}" stroke-width="2"/>',
     f'<style>text{{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif}}</style>']

# Tarjetas de números
def stat(x, big, label):
    o.append(f'<rect x="{x}" y="24" width="244" height="84" rx="10" fill="#161b22" stroke="#30363d"/>')
    o.append(f'<text x="{x+122}" y="68" text-anchor="middle" font-size="32" font-weight="700" fill="{ACC2}">{big}</text>')
    o.append(f'<text x="{x+122}" y="94" text-anchor="middle" font-size="13" fill="{MUT}">{escape(label)}</text>')
stat(24, commits, "commits este año")
stat(298, f"{cur} {'día' if cur == 1 else 'días'}", "racha actual")
stat(572, f"{best} {'día' if best == 1 else 'días'}", "racha más larga")

# Gráfica de barras
o.append(f'<text x="24" y="138" font-size="14" font-weight="600" fill="{TXT}">Contribuciones por semana (últimas 26)</text>')
mx = max(weeks) or 1
bw, gap, base, hmax = 24, 7.4, 280, 110
for i, v in enumerate(weeks):
    h = max(3, v / mx * hmax) if v else 3
    x = 24 + i * (bw + gap)
    fill = ACC2 if v else "#21262d"
    o.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" rx="3" fill="{fill}"><title>{v} contribuciones</title></rect>')

# Lenguajes (barra apilada + leyenda)
if top:
    o.append(f'<text x="24" y="304" font-size="14" font-weight="600" fill="{TXT}">Lenguajes más usados</text>')
    x, bw_total = 24, W - 48
    o.append(f'<clipPath id="cl"><rect x="24" y="314" width="{bw_total}" height="10" rx="5"/></clipPath><g clip-path="url(#cl)">')
    for name, (size, color) in top:
        w = size / tot_l * bw_total
        o.append(f'<rect x="{x:.1f}" y="314" width="{w:.1f}" height="10" fill="{color}"/>')
        x += w
    o.append('</g>')
    lx = 24
    for name, (size, color) in top:
        pct = size / tot_l * 100
        o.append(f'<circle cx="{lx+5}" cy="343" r="5" fill="{color}"/>')
        o.append(f'<text x="{lx+16}" y="347" font-size="12" fill="{TXT}">{escape(name)} <tspan fill="{MUT}">{pct:.0f}%</tspan></text>')
        lx += 16 + 8 * len(name) + 52
o.append(f'<text x="24" y="379" font-size="11" fill="{MUT}">{total} contribuciones en el último año · {u["repositories"]["totalCount"]} repos propios · se actualiza solo cada día</text>')
o.append('</svg>')
open("stats.svg", "w", encoding="utf-8").write("\n".join(o))
print("stats.svg generado:", commits, "commits,", cur, "racha")
