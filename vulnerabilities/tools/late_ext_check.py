"""Hand-check helper (Turkish): for each empty-period flag that survived the rebuttal, the lines of the extending
commit's diff that hold the old or the new date, and the publisher's amendment note at the pin that names the
extending act. Paths before the 10 November 2026 rename (kanun/<n>/...) are followed to law/<year>/<n>/..."""
import json, re, subprocess, sys
G = "gl/vulnerabilities/scripts/sources/corpus/turkey-law.git"; PIN = "9c398d4944beae7bada4325f4dea413ed98feaac"
MON = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()
def forms(d):
    y, m, dd = d.split("-"); m, dd = int(m), int(dd)
    f = [f"{dd} {MON[m-1]} {y}", f"{dd}/{m}/{y}", f"{dd:02d}/{m:02d}/{y}", f"{dd}.{m}.{y}", f"{dd:02d}.{m:02d}.{y}", d]
    if (m, dd) == (12, 31): f += [f"{y} yılı sonuna", f"{y} yılı sonu"]
    if (m, dd) == (1, 1): f += [f"{int(y)-1} yılı sonuna"]
    return f
def git(*a): return subprocess.run(["git", "-C", G, *a], capture_output=True).stdout.decode("utf-8", "replace")
paths = json.loads(git("show", f"{PIN}:data/paths.json"))["paths"]
def newpath(p):
    if p.startswith("kanun/"):
        parts = p.split("/")
        for k, v in (paths.items() if isinstance(paths, dict) else []):
            if k.rstrip("/") == "/".join(parts[:2]):
                return v.rstrip("/") + "/" + "/".join(parts[2:])
    return p
seen = set()
for x in map(json.loads, open("gl/vulnerabilities/scripts/findings/run/late_extension_triage.jsonl", encoding="utf-8")):
    surv = x.get("rebut", {}).get("survives")
    if not surv and "--all" not in sys.argv: continue
    r = x["row"]; k = (r["path"], r["old_until"], r["new_until"], r["law"])
    if k in seen: continue
    seen.add(k)
    np = newpath(r["path"])
    num = re.search(r"\d+", r["law"]).group()
    c = [l.split()[0] for l in git("log", "--format=%h %an", PIN, "--", r["path"], np).splitlines()
         if l.split(" ", 1)[1].startswith(r["law"].split(" (")[0])]
    hits = []
    for cc in c:
        d = git("diff", "-U0", "--word-diff", f"{cc}^", cc, "--", r["path"], np)
        for line in d.splitlines():
            if any(f in line for f in forms(r["old_until"]) + forms(r["new_until"])) and ("{+" in line or "[-" in line):
                hits.append(line.strip()[:400])
    text = git("show", f"{PIN}:{np}")
    notes = [l.strip()[:400] for l in text.splitlines() if num in l and ("sayılı" in l or "Kanun" in l)]
    print(f"## {'SURV' if surv else 'drop'} {r['path']} -> {np}\n   {r['old_until']} -> {r['new_until']} by {r['law']} in force {r['extended_in_force']} ({r['gap_days']} d); commits {c}")
    for h in hits[:4]: print("   DIFF", h)
    if not hits: print("      (no diff line holds either date)")
    for n in notes[:4]: print("   NOTE", n)
