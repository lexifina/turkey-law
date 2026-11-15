"""Measure what textscan.limits() still misses in Turkish: every "kadar/dek/değin" with a past date (before the pin's
date) up to 60 characters before it, in the texts at the pin, that limits() does not return. Prints counts by form
and by law/other, and samples.   python -X utf8 measure_missed.py"""
import collections, json, random, re, subprocess, sys
sys.path.insert(0, "gl/vulnerabilities/scripts")
from ingest import textscan
G = "gl/vulnerabilities/scripts/sources/corpus/turkey-law.git"; PIN = "9c398d4944beae7bada4325f4dea413ed98feaac"
TODAY = "2026-11-15"
cfg = json.load(open("config.json", encoding="utf-8"))
NOT_LAW = tuple(cfg["not_law"])
MON = "ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık"
DATE = re.compile(rf"(?i)(?P<num>\b\d{{1,2}}\s?[./]\s?\d{{1,2}}\s?[./]\s?(?P<y1>\d{{4}}))|(?P<txt>\b\d{{1,2}}\s+(?:{MON})\s+(?P<y2>\d{{4}}))"
                  rf"|(?P<iso>\b(?P<y4>\d{{4}})-\d{{2}}-\d{{2}})|(?P<year>\b(?P<y3>(?:18|19|20)\d{{2}})\b)")
END = re.compile(r"(?i)\b(?:kadar|dek|değin)\b")
files = [l for l in subprocess.run(["git", "-C", G, "ls-tree", "-r", "--name-only", PIN], capture_output=True)
         .stdout.decode("utf-8").splitlines() if l.endswith((".md", ".txt"))]
cat = subprocess.Popen(["git", "-C", G, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
def read(p):
    cat.stdin.write(f"{PIN}:{p}\n".encode()); cat.stdin.flush()
    h = cat.stdout.readline().split()
    if len(h) < 3: return ""
    d = cat.stdout.read(int(h[2])); cat.stdout.read(1)
    return d.decode("utf-8", "replace")
def form(between, kind):
    b = re.sub(r"\s+", " ", between.strip().lower())
    WD = r"(pazartesi|salı|çarşamba|perşembe|cuma|cumartesi|pazar)"
    if kind == "year":
        if re.match(r"^yılı(nın)? sonuna", b): return "R year: yılı sonuna"
        if re.match(r"^(yılı(nın)? )?(\w+ )?ayı(nın)? sonuna", b): return "M year + month: '2020 yılı Haziran ayı sonuna'"
        if re.match(r"^mali yılı(nın)? sonuna", b): return "M fiscal year: '1953 mali yılı sonuna'"
        if re.match(r"^yılına$", b): return "Y year only: '2020 yılına kadar'"
        return "N year, other wording"
    if re.match(r"^(tarihine|tarihi|gününe|günü)?$", b) or re.match(r"^['’]?\w{0,4}( tarihine)?$", b): return "R date + tarihine"
    if re.search(r"bu tarih(ler)?(in)? d[aâ]h", b): return "M date + '(bu tarih dahil)'"
    if re.search(r"mesai", b): return "M date + end of office hours ('günü mesai bitimine kadar')"
    if re.search(rf"^{WD}", b) and re.search(r"saat|sonuna", b): return "M date + weekday before 'günü saat/sonuna' ('Salı günü saat 24.00'a kadar')"
    if re.search(r"saat", b): return "M date + time of day, other form"
    if re.search(r"(gün|tarih)(ü|i)? (sonuna|bitimine)", b): return "M date + 'günü sonuna kadar'"
    if re.match(rf"^(tarihli )?{WD} gün(üne|ü)$", b): return "M date + weekday ('Cuma gününe kadar')"
    if re.match(r"^['’]?\w{0,4} (dek|değin)$", b) or re.match(r"^ ?['’]?\w{1,4}$", b): return "M date + suffix after a space ('8/4/1971 e dek')"
    if re.match(r"^(tarihinden|['’]?(den|dan|ten|tan))", b): return "N start date ('tarihinden ... kadar')"
    return "N date, other wording"
cnt = collections.Counter(); samples = collections.defaultdict(list); total = 0
for i, p in enumerate(files):
    t = read(p)
    if "kadar" not in t and "dek" not in t and "değin" not in t: continue
    kind = "other" if p.startswith(NOT_LAW) else "law"
    for e in END.finditer(t):
        win = t[max(0, e.start() - 60):e.start()]
        ds = list(DATE.finditer(win))
        if not ds: continue
        d = ds[-1]
        y = int(d.group("y1") or d.group("y2") or d.group("y4") or d.group("y3"))
        k = "year" if d.group("year") else "date"
        if y > int(TODAY[:4]) or y < 1800: continue
        if k == "date":
            if d.group("num"):
                parts = re.split(r"\s?[./]\s?", d.group("num"))
                try: iso = f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
                except Exception: continue
            else: iso = f"{y:04d}-12-31"
            if iso >= TODAY: continue
        elif y >= int(TODAY[:4]): continue
        between = win[d.end():]
        if len(between) > 45: continue
        a = max(0, e.start() - 60) + d.start()
        w0 = max(0, a - 30); win2 = t[w0:e.end() + 2]
        read_ = any(w0 + m.start() <= a + 2 and w0 + m.end() >= e.start() for m in textscan.LIMIT_POST.finditer(win2))
        total += 1
        f = form(between, k)
        cnt[(read_, kind, f)] += 1
        if not read_ and len(samples[f]) < 4000: samples[f].append((kind, p, t[max(0, e.start() - 90):e.end()].replace("\n", " ")))
    if i % 20000 == 0: print(i, "files", file=sys.stderr)
print("total past-date 'kadar' phrases:", total)
for (r, kind, f), n in sorted(cnt.items(), key=lambda x: (-x[0][0], x[0][1], -x[1])):
    print(f"{'READ  ' if r else 'MISSED'} {kind:5} {n:7}  {f}")
random.seed(1)
for f, s in samples.items():
    print("\n##", f)
    for k, p, c in random.sample([x for x in s if x[0] == "law"], min(8, len([x for x in s if x[0] == "law"]))): print("  ", p, "|", c[-170:])
