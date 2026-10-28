"""Build the Turkey law repository from the mevzuat.gov.tr cache (fetch.py).

    python -X utf8 scripts/turkey-law/build.py ~/Documents/turkey-law --today YYYY-MM-DD [--limit N] [--workers N]

The Mevzuat Bilgi Sistemi publishes only the CURRENT consolidated text of each act (a few hundred laws also list
earlier texts as .doc/.pdf files; those are recorded in data/previous-texts.csv but not built). So:

1. Every act (Kanun, Kanun Hukmunde Kararname, Cumhurbaskanligi Kararnamesi) is one folder, `kanun/<no>/`,
   `khk/<no>/`, `cbk/<no>/`. Each article is one file (`madde-21.md`, `gecici-madde-1.md`, `ek-madde-3.md`,
   `madde-4a.md` for "Madde 4/A"), one paragraph per line. The title, numbers and preamble before the first article
   are `baslangic.md`; the publisher's footnotes are `dipnotlar.md`; `index.txt` gives the reading order. Headings
   (KISIM, BOLUM, marginal titles) that stand right before an article go on top of that article's file. Text is
   exactly as published (Turkish, Latin script); only whitespace is normalised and soft hyphens dropped.
2. Each act is one commit, `Kind: consolidated`, authored by the publisher, dated noon Turkey time (UTC+3) on the
   day the text was retrieved, which is also its `In-force:` date: the text in force on that day as the publisher
   gives it. Nobody is credited with single lines, because earlier wording is not published here. The site's
   amendment notes "(Degisik: 3/10/2001-4709/6 md.)" stay in the text and are parsed into data/amendments.csv.
3. One git fast-import stream, everything sorted, so the same cache always gives the same hashes.
"""
import argparse
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / '.cache'
SITE = 'https://www.mevzuat.gov.tr'
COMMITTER = 'Lexifina <turkey-law@lexifina.com>'
PUBLISHER = ('Mevzuat Bilgi Sistemi (T.C. Cumhurba\u015fkanl\u0131\u011f\u0131)', 'mevzuat@mevzuat-gov-tr.invalid')
KINDS = [  # (list name, folder, label, tur)
    ('Kanun', 'kanun', 'Kanun', 1),  # this list also holds the Ottoman laws still in force (tur 0): osmanli/
    ('KHK', 'khk', 'KHK', 4),
    ('CumhurbaskaniKararnameleri', 'cbk', 'CBK', 19),
]

# ---------------------------------------------------------------------------------------------------- text

WS = re.compile(r'[\s\u00a0\u2000-\u200a\u202f\u205f\u3000]+')
DROP = re.compile(r'[\u00ad\u200b\u200c\u200d\u2060\ufeff]')


def norm(s: str) -> str:
    return WS.sub(' ', DROP.sub('', s)).strip()


BLOCK = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'blockquote', 'ul', 'ol', 'dl', 'dt', 'dd',
         'center', 'pre', 'address', 'body', 'html'}
EMPH = {'b', 'strong', 'i', 'em', 'u'}
SKIP = {'style', 'script', 'head', 'title', 'xml', 'noscript'}


class Paras(HTMLParser):
    """Word HTML -> paragraphs: [{'text', 'plain' (characters outside b/i/u), 'note' (inside a footnote div)}].
    A table row is one paragraph with its cells joined by ' | '."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[dict] = []
        self.cur: list[str] = []
        self.plain = 0
        self.skip = 0
        self.emph = 0
        self.cell = 0
        self.row: list[str] | None = None
        self.divs: list[bool] = []  # per open div: is it a footnote div
        self.note = 0

    def flush(self):
        t = norm(''.join(self.cur))
        if self.row is not None and self.cell:
            if t:
                self.row[-1] = (self.row[-1] + ' ' + t).strip()
        elif t:
            self.out.append({'text': t, 'plain': self.plain, 'note': self.note > 0})
        self.cur = []
        self.plain = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == 'br':
            self.cur.append(' ')
            return
        if tag in EMPH:
            self.emph += 1
            return
        if tag == 'div':
            a = dict(attrs)
            is_note = bool(re.match(r'(ftn|edn)\d+$', a.get('id') or ''))
            self.divs.append(is_note)
            if is_note:
                self.flush()
                self.note += 1
            return
        if tag == 'tr':
            self.flush()
            self.row = []
            return
        if tag in ('td', 'th'):
            if self.row is None:
                self.flush()
                self.row = []
            self.flush()
            self.row.append('')
            self.cell += 1
            return
        if tag in BLOCK:
            self.flush()

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in EMPH:
            self.emph = max(0, self.emph - 1)
            return
        if tag == 'div':
            self.flush()
            if self.divs and self.divs.pop():
                self.note -= 1
            return
        if tag in ('td', 'th'):
            self.flush()
            self.cell = max(0, self.cell - 1)
            return
        if tag == 'tr':
            self.flush()
            cells = self.row or []
            self.row = None
            self.cell = 0
            if any(cells):
                self.out.append({'text': ' | '.join(cells), 'plain': 1, 'note': self.note > 0, 'table': True})
            return
        if tag in BLOCK:
            self.flush()

    def handle_data(self, data):
        if self.skip:
            return
        self.cur.append(data)
        if not self.emph:
            self.plain += len(data.strip())

    def close(self):
        super().close()
        if self.row is not None:
            self.handle_endtag('tr')
        self.flush()


def content(html: str) -> str:
    """The Word document the site embeds: from its <body> to </body> (the page around it is site chrome)."""
    m = re.search(r'(?is)<body[^>]*>(.*)</body>', html)
    return m.group(1) if m else html


ART = re.compile(
    r'^(?P<pre>(?:(?:Ek|EK)\s+(?:Ge\u00e7ici|GE\u00c7\u0130C\u0130)|Ge\u00e7ici|GE\u00c7\u0130C\u0130|Ek|EK|'
    r'M\u00fckerrer|M\u00dcKERRER|Muvakkat|MUVAKKAT|Zeyl|ZEYL)\s+)?'
    r'(?P<word>Madde|MADDE|Bend|BEND)\s*(?P<n>\d{1,4})(?:\s*/\s*(?P<l>[A-Za-z\u00c7\u011e\u0130\u00d6\u015e\u00dc\u00e7\u011f\u0131\u00f6\u015f\u00fc]{1,2})(?![A-Za-z\u00e7\u011f\u0131\u00f6\u015f\u00fc]))?'
    r'\s*(?:[-\u2010-\u2015\u2212.:]|\(|$)')
FOLD = str.maketrans('\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dcI', 'cgiosuCGIOSUi')


def art_name(m: re.Match) -> str:
    pre = norm(m.group('pre') or '').translate(FOLD).lower().replace(' ', '-')
    pre = {'muvakkat': 'gecici'}.get(pre, pre)  # Ottoman-era "Muvakkat" = Gecici
    word = 'bend' if m.group('word').lower() == 'bend' else 'madde'  # Ottoman-era acts number "Bend"s
    name = f"{pre + '-' if pre else ''}{word}-{int(m.group('n'))}"
    if m.group('l'):
        name += m.group('l').translate(FOLD).lower()
    return name


def heading_like(p: dict) -> bool:
    t = p['text']
    return (p['plain'] == 0 and not p.get('table') and len(t) < 200 and not t.startswith(('(', '[', '\u201c', '"'))
            and not ART.match(t))


def upper(p: dict) -> bool:
    return p['text'] == p['text'].upper()


APPX = re.compile('\u0130\u015eLENEMEYEN|G\u00d6STER\u0130R (L\u0130STE|TABLO|CETVEL)|Y\u00dcR\u00dcRL\u00dc\u011eE G\u0130R\u0130\u015e|'
                  'DE\u011e\u0130\u015e\u0130KL\u0130K GET\u0130REN MEVZUAT')
NOTE = re.compile(
    r'\((?P<label>[^():]{1,80}?)\s*:\s*(?P<date>\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})\s*[-\u2010-\u2015\u2212]\s*'
    r'(?P<law>(?:KHK\s*[-/]?\s*|CBK\s*[-/]?\s*)?\d{1,5})\s*/\s*(?P<art>[0-9]+(?:\s*/\s*[0-9A-Za-z\u00c7\u011e\u0130\u00d6\u015e\u00dc]+)?)\s*md\.?\s*\)')


def iso(d: str) -> str:
    m = re.fullmatch(r'\s*(\d{1,2})\s*[./]\s*(\d{1,2})\s*[./]\s*(\d{4})\s*', d or '')
    # Ottoman-era dates are printed in the Rumi or Hijri calendar (year 1288-1341): not converted, left blank
    if not m or int(m.group(3)) < 1800:
        return ''
    return f'{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'


def build_act(act: dict) -> dict:
    p = CACHE / 'doc' / f"{act['tur']}.{act['tertip']}.{act['no']}.html"
    if not p.exists():
        return {'files': {}, 'inforce': [], 'issues': [[act['dir'], 'not fetched: ' + (
            p.with_suffix('.miss').read_text('utf-8').strip() if p.with_suffix('.miss').exists() else 'missing')]],
            'amend': []}
    parser = Paras()
    parser.feed(content(p.read_text('utf-8')))
    parser.close()
    paras = [x for x in parser.out if not x['note']]
    notes = [x['text'] for x in parser.out if x['note']]
    issues: list[list[str]] = []
    # the publisher's appendices after the act: provisions of amending acts that could not be worked into the text
    # ("... KANUNA ISLENEMEYEN HUKUMLER") and the list of when each amending act entered into force ("... YURURLUGE
    # GIRIS TARIHINI GOSTERIR LISTE"). They are cut off first, so their quoted articles do not become articles.
    appendix: list[tuple[int, str]] = []
    i = 0
    while i < len(paras):
        x = paras[i]
        if heading_like(x) and x['text'] == x['text'].upper() and APPX.search(x['text']):
            j = i
            while (j - 1 >= 0 and i - (j - 1) <= 2 and heading_like(paras[j - 1]) and upper(paras[j - 1])
                   and (not appendix or j - 1 > appendix[-1][0])):
                j -= 1
            k = i
            while k + 1 < len(paras) and heading_like(paras[k + 1]) and upper(paras[k + 1]) and \
                    APPX.search(paras[k + 1]['text']):
                k += 1
            group = ' '.join(p['text'] for p in paras[j:k + 1])
            appendix.append((j, 'islenemeyen-hukumler' if '\u0130\u015eLENEMEYEN' in group else 'yururluk-listesi'))
            i = k + 1
            continue
        i += 1
    cut = appendix[0][0] if appendix else len(paras)
    tail = paras[cut:]
    paras = paras[:cut]
    # article starts, ignoring anything inside an open quotation (an amending act quoting another act's articles)
    starts: list[tuple[int, str]] = []
    depth = 0
    for i, x in enumerate(paras):
        t = x['text']
        m = ART.match(t) if not x.get('table') else None
        if m and depth <= 0:
            starts.append((i, art_name(m)))
            depth = 0
        depth += t.count('\u201c') - t.count('\u201d')
    files: dict[str, list[str]] = {}
    order: list[str] = []
    if not starts:
        if paras:
            files['metin.md'] = [x['text'] for x in paras]
            order.append('metin.md')
        issues.append([act['dir'], 'no article headings found; whole text in metin.md'])
    else:
        # pull heading-like paragraphs that stand right before an article into that article
        bounds = []
        prev_start = -1
        for k, (i, name) in enumerate(starts):
            j = i
            limit = prev_start + 1 if k else 0
            while j - 1 >= limit and heading_like(paras[j - 1]) and i - (j - 1) <= 6:
                if k == 0 and ':' in paras[j - 1]['text']:
                    break
                j -= 1
            bounds.append((j, name))
            prev_start = i
        front = paras[:bounds[0][0]]
        if front:
            files['baslangic.md'] = [x['text'] for x in front]
            order.append('baslangic.md')
        seen: dict[str, int] = {}
        for k, (j, name) in enumerate(bounds):
            end = bounds[k + 1][0] if k + 1 < len(bounds) else len(paras)
            if name in seen:
                seen[name] += 1
                name = f'{name}~{seen[name]}'
            else:
                seen[name] = 1
            files[f'{name}.md'] = [x['text'] for x in paras[j:end]]
            order.append(f'{name}.md')
    inforce = []
    seen_app: dict[str, int] = {}
    for k, (j, name) in enumerate(appendix):
        end = appendix[k + 1][0] if k + 1 < len(appendix) else cut + len(tail)
        part = tail[j - cut:end - cut]
        seen_app[name] = seen_app.get(name, 0) + 1
        fn = f'{name}.md' if seen_app[name] == 1 else f'{name}~{seen_app[name]}.md'
        files[fn] = [x['text'] for x in part]
        order.append(fn)
        if name == 'yururluk-listesi':
            for x in part:
                cells = x['text'].split(' | ') if x.get('table') else []
                if len(cells) >= 3 and re.search(r'\d{4}', cells[-1]) and not re.search('Y\u00fcr\u00fcrl\u00fc\u011fe Giri\u015f', cells[-1], re.I):
                    inforce.append([act['dir'], cells[0], ' | '.join(cells[1:-1]), iso(cells[-1]), cells[-1]])
    if notes:
        files['dipnotlar.md'] = notes
        order.append('dipnotlar.md')
    amend = []
    for fn in order:
        if fn == 'dipnotlar.md' or fn.startswith(('yururluk-listesi', 'islenemeyen-hukumler')):
            continue
        for line in files[fn]:
            for m in NOTE.finditer(line):
                law = re.sub(r'\s+', '', m.group('law'))
                amend.append([act['dir'], fn[:-3], norm(m.group('label')), iso(m.group('date')), law,
                              re.sub(r'\s+', '', m.group('art')), m.group(0)])
    out = {f"{act['dir']}/{fn}": '\n'.join(lines) + '\n' for fn, lines in files.items()}
    if out:
        out[f"{act['dir']}/index.txt"] = '\n'.join(order) + '\n'
    return {'files': out, 'issues': issues, 'amend': amend, 'inforce': inforce,
            'articles': sum(1 for f in order if 'madde-' in f or f.startswith('bend-')),
            'footnotes': len(notes)}


# ---------------------------------------------------------------------------------------------------- acts

def load_acts(limit: int | None) -> list[dict]:
    acts = []
    for list_name, folder, label, tur in KINDS:
        f = CACHE / 'list' / f'{list_name}.json'
        if not f.exists():
            sys.exit(f'missing {f}; run fetch.py')
        for r in json.loads(f.read_text('utf-8')):
            t = int(r['mevzuatTur'])
            if t == 0 and tur == 1:
                kind, lab = 'osmanli', 'Osmanli Kanunu'
            else:
                assert t == tur, r
                kind, lab = folder, label
            acts.append({'kind': kind, 'label': lab, 'tur': t, 'no': str(r['mevzuatNo']).strip(),
                         'enacted_printed': norm(r.get('kabulTarih') or ''),
                         'published_printed': norm(r.get('resmiGazeteTarihi') or ''),
                         'tertip': str(r['mevzuatTertip']).strip(), 'title': norm(r.get('mevAdi') or ''),
                         'enacted': iso(r.get('kabulTarih') or ''), 'published': iso(r.get('resmiGazeteTarihi') or ''),
                         'gazette': norm(str(r.get('resmiGazeteSayisi') or '')),
                         'mukerrer': (r.get('mukerrer') or '').upper() == 'EVET', 'old': bool(r.get('hasOldLaw')),
                         'url': f"{SITE}/mevzuat?MevzuatNo={r['mevzuatNo']}&MevzuatTur={tur}&MevzuatTertip={r['mevzuatTertip']}"})
    # folder per act: <kind>/<no>; a number used in two Dustur tertips gets -t<tertip> on the older one(s)
    by = {}
    for a in acts:
        by.setdefault((a['kind'], a['no']), []).append(a)
    for (kind, no), group in by.items():
        group.sort(key=lambda a: -int(a['tertip']))
        for k, a in enumerate(group):
            a['dir'] = f'{kind}/{no}' if k == 0 else f"{kind}/{no}-t{a['tertip']}"
    acts.sort(key=lambda a: (['kanun', 'osmanli', 'khk', 'cbk'].index(a['kind']), int(re.sub(r'\D', '', a['no']) or 0), a['dir']))
    return acts[:limit] if limit else acts


# ---------------------------------------------------------------------------------------------------- git

def git_date(day: str) -> str:
    """Noon in Turkey. Turkey has kept UTC+3 all year since 2016-09-07; every commit here is dated after that."""
    d = datetime.strptime(day, '%Y-%m-%d')
    assert d >= datetime(2016, 9, 7), day
    ts = int(datetime(d.year, d.month, d.day, 9, 0, tzinfo=timezone.utc).timestamp())
    return f'{ts} +0300'


def message(act: dict, day: str, built: dict) -> str:
    kind_name = {'kanun': 'Kanun', 'osmanli': 'Osmanl\u0131 Kanunu', 'khk': 'Kanun H\u00fckm\u00fcnde Kararname',
                 'cbk': 'Cumhurba\u015fkanl\u0131\u011f\u0131 Kararnamesi'}[act['kind']]
    head = f"{act['label']} {act['no']}{'' if act['dir'].endswith(act['no']) else ' (Tertip ' + act['tertip'] + ')'}: "
    title = act['title']
    subject = head + title
    if len(subject) > 72:
        subject = subject[:69].rstrip() + '...'
    n = len(built['amend'])
    body = [f"The current text of {kind_name} No. {act['no']}, {title}, as the Mevzuat Bilgi Sistemi",
            f'(www.mevzuat.gov.tr) published it on {day}.',
            '',
            'The source keeps only the current consolidated text, so this commit holds the whole act and no line is',
            'credited to an amending law. The publisher\'s amendment notes stay in the text '
            f'({n} notes such as "(De\u011fi\u015fik: <date>-<law>/<article> md.)"),',
            'listed in data/amendments.csv' + (f"; its footnotes are in {act['dir']}/dipnotlar.md." if built.get('footnotes') else '.')]
    tr = ['Kind: consolidated', f'In-force: {day}', f'Consolidated: {day}', f"Law: {title}",
          f"Law-number: {act['no']}", f"Law-kind: {act['kind']}", f"Tertip: {act['tertip']}"]
    if act['enacted']:
        tr.append(f"Enacted: {act['enacted']}")
    elif act['enacted_printed']:
        tr.append(f"Enacted-as-printed: {act['enacted_printed']}")
    if act['published']:
        tr.append(f"Published: {act['published']}")
    elif act['published_printed']:
        tr.append(f"Published-as-printed: {act['published_printed']}")
    if act['gazette']:
        tr.append(f"Gazette: Resmi Gazete {act['gazette']}{' (Mukerrer)' if act['mukerrer'] else ''}")
    tr.append(f"Source: {act['url']}")
    return '\n'.join([subject, '', *body, '', *tr]) + '\n'


def fast_import(repo: Path, commits: list[tuple], docs: dict[str, bytes], today: str, retrieved: str) -> None:
    proc = subprocess.Popen(['git', '-C', str(repo), 'fast-import', '--quiet', '--done'], stdin=subprocess.PIPE)
    w = proc.stdin.write
    for act, built in commits:
        when = git_date(retrieved)
        w(b'commit refs/heads/main\n')
        w(f'author {PUBLISHER[0]} <{PUBLISHER[1]}> {when}\ncommitter {COMMITTER} {when}\n'.encode())
        m = message(act, retrieved, built).encode('utf-8')
        w(f'data {len(m)}\n'.encode() + m + b'\n')
        for path, text in sorted(built['files'].items()):
            t = text.encode('utf-8')
            w(f'M 100644 inline {path}\ndata {len(t)}\n'.encode() + t + b'\n')
        w(b'\n')
    when = git_date(retrieved)
    msg = (f'Documentation: README, REPRODUCE, SOURCES, LICENSE, corpus.json, tools and data\n\n'
           f'Built from the mevzuat.gov.tr cache retrieved on {retrieved}. No law text changes.\n\n'
           f'In-force: {retrieved}\nKind: documentation\n').encode()
    w(b'commit refs/heads/main\n')
    w(f'author {COMMITTER} {when}\ncommitter {COMMITTER} {when}\n'.encode())
    w(f'data {len(msg)}\n'.encode() + msg + b'\n')
    for path, data in sorted(docs.items()):
        w(f'M 100644 inline {path}\ndata {len(data)}\n'.encode() + data + b'\n')
    w(b'\ndone\n')
    proc.stdin.close()
    if proc.wait():
        sys.exit('git fast-import failed')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--today', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.today):
        sys.exit('--today must be YYYY-MM-DD')
    retrieved = (CACHE / 'fetched_on.txt').read_text('utf-8').strip()
    if retrieved > args.today:
        sys.exit(f'retrieval date {retrieved} is after --today {args.today}')
    acts = load_acts(args.limit)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(build_act, acts, chunksize=4))  # ordered: output does not depend on timing
    commits, issues, amend, inforce = [], [], [], []
    for act, built in zip(acts, results):
        issues += built['issues']
        amend += built['amend']
        inforce += built['inforce']
        act['articles'] = built.get('articles', 0)
        act['footnotes'] = built.get('footnotes', 0)
        act['notes'] = len(built['amend'])
        act['built'] = bool(built['files'])
        if built['files']:
            commits.append((act, built))
    print(f'{len(acts)} acts, {len(commits)} commits, {len(issues)} issues, {len(amend)} amendment notes', flush=True)

    import docs as docmod
    docs = docmod.render(acts, commits, issues, amend, inforce, args.today, retrieved)

    repo = args.repo
    remote = None
    if repo.exists() and any(repo.iterdir()):
        if not (repo / '.git').exists():
            sys.exit(f'{repo} is not empty and not a git repository; refusing')
        r = subprocess.run(['git', '-C', str(repo), 'log', '--format=%ae', 'main'], capture_output=True, text=True)
        authors = set(r.stdout.split())
        if authors - {PUBLISHER[1], 'turkey-law@lexifina.com', 'world-law@lexifina.com'}:
            sys.exit(f'{repo} holds commits by {sorted(authors)}; refusing to replace it')
        remote = subprocess.run(['git', '-C', str(repo), 'remote', 'get-url', 'origin'], capture_output=True,
                                text=True).stdout.strip() or None
        import shutil
        import stat

        def onerr(func, path, _):
            import os
            os.chmod(path, stat.S_IWRITE)
            func(path)
        for child in repo.iterdir():
            shutil.rmtree(child, onerror=onerr) if child.is_dir() else child.unlink()
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    for k, v in (('core.autocrlf', 'false'), ('core.longpaths', 'true'), ('core.quotepath', 'false')):
        subprocess.run(['git', '-C', str(repo), 'config', k, v], check=True)
    if remote:
        subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin', remote], check=True)
    fast_import(repo, commits, docs, args.today, retrieved)
    subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '-f', 'main'], check=True)
    head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    count = subprocess.run(['git', '-C', str(repo), 'rev-list', '--count', 'HEAD'], capture_output=True,
                           text=True).stdout.strip()
    print(f'built {repo}: {count} commits, head {head}', flush=True)


if __name__ == '__main__':
    main()
