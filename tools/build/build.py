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
from collections import Counter
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
        self.rows: list[list[str]] = []  # open table rows, innermost last (Word nests tables in cells)
        self.divs: list[bool] = []  # per open div: is it a footnote div
        self.note = 0

    def flush(self):
        t = norm(''.join(self.cur))
        if self.rows and self.cell:
            if t:
                row = self.rows[-1]
                if not row:
                    row.append('')
                row[-1] = (row[-1] + ' ' + t).strip()
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
            if self.rows:  # a table inside a cell: what the outer row holds so far comes first
                self.emit_row(self.rows[-1])
                self.rows[-1].clear()
            self.rows.append([])
            return
        if tag in ('td', 'th'):
            if not self.rows:
                self.flush()
                self.rows.append([])
            self.flush()
            self.rows[-1].append('')
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
            if self.rows:
                self.emit_row(self.rows.pop())
            return
        if tag in BLOCK:
            self.flush()

    def emit_row(self, cells: list[str]):
        if any(cells):
            self.out.append({'text': ' | '.join(c for c in cells), 'plain': 1, 'note': self.note > 0, 'table': True})

    def handle_data(self, data):
        if self.skip:
            return
        self.cur.append(data)
        if not self.emph:
            self.plain += len(data.strip())

    def close(self):
        super().close()
        while self.rows:
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


LIST_ITEM = re.compile(r'^(?:\(\d+\)|\d+[.)\-]|[a-z\u00e7\u011f\u0131\u00f6\u015f\u00fc]{1,2}\)|[IVX]+[.)-]\s*\()')


def heading_like(p: dict) -> bool:
    """A section heading or marginal article title: short, no closing punctuation, not a list item. Decided on the
    text only (older Word files do not mark headings bold)."""
    t = re.sub(r'\s*(\[\d+\]|\(\d\))$', '', p['text'])
    if t.endswith(':') and len(t) < 60:
        t = t[:-1]
    return (not p.get('table') and 0 < len(t) < 150 and not t.endswith(('.', ';', ':', ',')) and
            not t.startswith(('(', '[', '\u201c', '"', '\u2018', "'")) and not LIST_ITEM.match(t) and not ART.match(t)
            and re.search(r'[A-Za-z\u00c7\u011e\u0130\u00d6\u015e\u00dc\u00e7\u011f\u0131\u00f6\u015f\u00fc]', t) is not None)


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


HEADER = re.compile(r'(ilk hali|de\u011fi\u015fik hali|de\u011fi\u015fik \u015fekli)\s*$', re.I)


def build_act(act: dict) -> dict:
    p = CACHE / 'doc' / f"{act['tur']}.{act['tertip']}.{act['no']}.html"
    if not p.exists():
        return {'files': {}, 'inforce': [], 'issues': [[act['dir'], 'not fetched: ' + (
            p.with_suffix('.miss').read_text('utf-8').strip() if p.with_suffix('.miss').exists() else 'missing')]],
            'amend': []}
    return parse_html(p.read_text('utf-8'), act['dir'])


def parse_html(html: str, act_dir: str) -> dict:
    """One act's Word HTML -> files. An earlier text's first line names its version ("Kanunun ilk hali", "6525
    sayili Kanun ile degisik hali"); it is returned as `header` and kept out of the files."""
    act = {'dir': act_dir}
    parser = Paras()
    parser.feed(content(html))
    parser.close()
    paras = [x for x in parser.out if not x['note']]
    notes = [x['text'] for x in parser.out if x['note']]
    issues: list[list[str]] = []
    header = ''
    for k in range(min(3, len(paras))):
        if HEADER.search(paras[k]['text']) and len(paras[k]['text']) < 160:
            header = ' '.join(x['text'] for x in paras[:k + 1])
            del paras[:k + 1]
            break
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
    return {'files': out, 'issues': issues, 'amend': amend, 'inforce': inforce, 'header': header, 'order': order,
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

def _last_sunday(year: int, month: int) -> datetime:
    d = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    d = d.fromordinal(d.toordinal() - 1)
    return d.fromordinal(d.toordinal() - (d.weekday() + 1) % 7)


def tz_hours(day: datetime) -> int:
    """Turkey's offset at noon on `day`. UTC+3 all year since 2016-09-07. Before: UTC+2, with summer time (UTC+3)
    from the last Sunday of March to the last Sunday of October, and the three moved changes of 2011 (start 28
    March), 2014 (start 31 March) and 2015 (end 8 November). Rules before 1986 differed from year to year; the same
    EU-style rule is used for them, and the date in the In-force trailer is the one that counts."""
    if day >= datetime(2016, 9, 7):
        return 3
    start, end = _last_sunday(day.year, 3), _last_sunday(day.year, 10)
    start = {2011: datetime(2011, 3, 28), 2014: datetime(2014, 3, 31)}.get(day.year, start)
    end = {2015: datetime(2015, 11, 8)}.get(day.year, end)
    return 3 if start <= day < end else 2


def git_date(day: str, seq: int = 0) -> str:
    """Noon in Turkey on `day`. Git cannot take dates before 1970: those are 1970-01-01 plus `seq` seconds, and the
    real date is in the In-force trailer."""
    d = datetime.strptime(day, '%Y-%m-%d')
    if d.year < 1970:
        return f'{seq} +0200'
    h = tz_hours(d)
    ts = int(datetime(d.year, d.month, d.day, 12 - h, 0, tzinfo=timezone.utc).timestamp())
    return f'{ts} +0{h}00'


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
            'The source keeps only the current consolidated text of this act, so this commit holds the whole act and',
            'no line is credited to an amending law. The publisher\'s amendment notes stay in the text '
            f'({n} notes such as "(De\u011fi\u015fik: <date>-<law>/<article> md.)"),',
            'listed in data/amendments.csv' + (f"; its footnotes are in {act['dir']}/dipnotlar.md." if built.get('footnotes') else '.')]
    tr = ['Kind: consolidated', f'In-force: {day}', f'Consolidated: {day}', f"Law: {title}"] + law_trailers(act)
    return '\n'.join([subject, '', *body, '', *tr]) + '\n'


def law_trailers(act: dict) -> list[str]:
    tr = [f"Law-number: {act['no']}", f"Law-kind: {act['kind']}", f"Tertip: {act['tertip']}"]
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
    return tr


def short(s: str, n: int = 72) -> str:
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def group_message(g: dict, acts_by_dir: dict, titles: dict) -> tuple[str, str, str]:
    """(author name, author email, message) for one commit."""
    import history
    evs = g['events']
    e0 = evs[0]
    day = g['date']
    laws = sorted({e['law'] for e in evs}, key=lambda d: acts_by_dir[d]['order'])
    if e0['kind'] == 'current':
        act = acts_by_dir[e0['law']]
        return PUBLISHER[0], PUBLISHER[1], message(act, day, e0['built'])
    if e0['kind'] in ('enacted', 'consolidated'):
        act = acts_by_dir[e0['law']]
        v = e0['version']
        if e0['kind'] == 'enacted':
            name, email = history.act_name(act['no'], titles), history.act_email(act['no'])
            subject = short(f"{act['label']} {act['no']}: as enacted ({act['title']})")
            body = [f"{act['title']}, as first published, from the publisher's earlier text \"{v['parsed']['header']}\".",
                    'Dated by its Resmi Gazete date (no in-force table row names the act itself).']
        else:
            name, email = PUBLISHER
            by = ', '.join(history.act_name(a, titles) for a in v['acts']) or 'unknown acts'
            subject = short(f"{act['label']} {act['no']}: earliest available text, as amended by {by}")
            body = [f"The earliest text of {act['title']} that the publisher keeps (\"{v['parsed']['header']}\"),",
                    f'as amended by {by}. Earlier wording is not available, so nothing in it is credited to a law.']
        tr = [f"Kind: {e0['kind']}", f'In-force: {day}', f"Date-source: {v['date_source']}", f"Law: {act['title']}"]
        tr += [f'Consolidated-by: {a}' for a in v['acts']]
        tr += [f"Version: {e0['tag']}", f"Source-text: {v['base']}.doc"] + law_trailers(act)
        return name, email, '\n'.join([subject, '', *body, '', *tr]) + '\n'
    affecting = sorted(p for e in evs for p in e['files'] if not p.endswith('/index.txt'))
    tags = [e['tag'] for e in evs if e.get('tag')]
    law_names = [f"{acts_by_dir[d]['label']} {acts_by_dir[d]['no']}" for d in laws]
    if e0['kind'] == 'amendment':
        x = e0['act']
        name, email = history.act_name(x, titles), history.act_email(x)
        subject = short(f"{name}: in force {day}, {len(affecting)} provision(s) of {', '.join(law_names)}")
        body = [f'{name} takes effect on {day}, by the publisher\'s in-force table, in: {", ".join(law_names)}.',
                'Each change is credited to it because a new amendment note in the provision names it, or the',
                'in-force table lists the provision for it (see Evidence).']
        tr = ['Kind: amendment', f'In-force: {day}', f'Amending-act: {x}']
        tr += [f'Applies-from: {p}: {d}' for e in evs for p, d in sorted(e.get('applies', {}).items())]
        tr += [f"Date-source: {s}" for s in sorted({e['date_source'] for e in evs})]
        tr += [f'Affecting: {p}' for p in affecting]
        tr += [f"Evidence: {p}: {e['evidence'][p]}" for e in evs for p in sorted(e.get('evidence', {}))]
        tr += [f'Version: {t}' for t in tags]
        return name, email, '\n'.join([subject, '', *body, '', *tr]) + '\n'
    name, email = PUBLISHER
    if e0['kind'] == 'unexplained':
        subject = short(f"Unexplained changes on {day}: {len(affecting)} provision(s) of {', '.join(law_names)}")
        body = ['Changes between two of the publisher\'s texts that cannot be credited to exactly one act with an',
                'in-force date. They are labelled, not credited; Candidate names the acts that might explain them.']
        tr = ['Kind: unexplained', f'In-force: {day}']
        tr += [f'Candidate: {c}' for c in sorted({c for e in evs for v in e['candidates'].values() for c in v})]
        tr += [f'Affecting: {p}' for p in affecting]
        tr += [f"Reason: {p}: {e['reasons'][p]}" for e in evs for p in sorted(e['reasons'])]
        tr += [f'Version: {t}' for t in tags]
        return name, email, '\n'.join([subject, '', *body, '', *tr]) + '\n'
    subject = short(f"Publisher's apparatus on {day}: {', '.join(law_names)}")
    body = ['Changes to the publisher\'s own apparatus between two of its texts: footnotes, the in-force list,',
            'provisions not worked into the text, footnote numbers, and the file order. No law text changes.']
    tr = ['Kind: editorial', f'In-force: {day}'] + [f'Affecting: {p}' for p in affecting] + [f'Version: {t}' for t in tags]
    return name, email, '\n'.join([subject, '', *body, '', *tr]) + '\n'


def plan(events: list[dict]) -> list[dict]:
    """Group events into commits: one per amending act per in-force day (across laws), one per baseline or current
    text, and one unexplained and one editorial commit per day. A law's own events keep their order; if merging
    across laws would break that on some day, that day's commits are made per law instead."""
    by_day: dict[str, list[dict]] = {}
    for e in events:
        by_day.setdefault(e['date'], []).append(e)
    out = []
    for day in sorted(by_day):
        evs = by_day[day]
        # a law with two version steps on this day keeps its steps in separate commits (each version's tag must
        # point at exactly that version); other laws' events still merge across laws
        steps: dict[str, set] = {}
        for e in evs:
            steps.setdefault(e['law'], set()).add(e['seq'][0])
        multi = {law for law, s in steps.items() if len(s) > 1}
        for merged in (True, False):
            def key(e):
                base = {'enacted': ('0', e['law']), 'consolidated': ('0', e['law']), 'current': ('0', e['law']),
                        'amendment': ('1', e['act']), 'unexplained': ('2',), 'editorial': ('3',)}[e['kind']]
                if not merged or e['law'] in multi:
                    return base + (e['law'], f"{e['seq'][0]:04d}")
                return base
            groups: dict[tuple, list[dict]] = {}
            per_law: dict[str, list[tuple]] = {}
            for e in evs:
                groups.setdefault(key(e), []).append(e)
                seq = per_law.setdefault(e['law'], [])
                if not seq or seq[-1] != key(e):
                    seq.append(key(e))
            if any(len(s) != len(set(s)) for s in per_law.values()):
                continue  # a law would return to a group it left
            edges = {k: set() for k in groups}
            indeg = {k: 0 for k in groups}
            for s in per_law.values():
                for a, b in zip(s, s[1:]):
                    if b not in edges[a]:
                        edges[a].add(b)
                        indeg[b] += 1
            ready = sorted(k for k in groups if indeg[k] == 0)
            order = []
            while ready:
                k = ready.pop(0)
                order.append(k)
                for b in sorted(edges[k]):
                    indeg[b] -= 1
                    if indeg[b] == 0:
                        ready.append(b)
                        ready.sort()
            if len(order) != len(groups):
                continue
            out += [{'date': day, 'events': groups[k]} for k in order]
            break
        else:
            raise SystemExit(f'cannot order the commits of {day}')
    return out


def fast_import(repo: Path, groups: list[dict], future: list[dict], docs: dict[str, bytes], retrieved: str,
                acts_by_dir: dict, titles: dict) -> dict:
    proc = subprocess.Popen(['git', '-C', str(repo), 'fast-import', '--quiet', '--done'], stdin=subprocess.PIPE)
    w = proc.stdin.write
    mark = 0
    last_mark: dict[str, int] = {}
    tags: dict[str, int] = {}
    state: dict[str, str] = {}

    def commit(ref: str, g: dict, parent: int | None) -> int | None:
        nonlocal mark
        files = {}
        for e in g['events']:
            files.update(e['files'])
        changed = {p: t for p, t in files.items() if state.get(p) != t}
        if not changed:
            return None
        mark += 1
        name, email, msg = group_message(g, acts_by_dir, titles)
        when = git_date(g['date'], mark)
        w(f'commit {ref}\nmark :{mark}\n'.encode())
        w(f'author {name} <{email}> {when}\ncommitter {COMMITTER} {when}\n'.encode('utf-8'))
        m = msg.encode('utf-8')
        w(f'data {len(m)}\n'.encode() + m + b'\n')
        if parent:
            w(f'from :{parent}\n'.encode())
        for path, text in sorted(changed.items()):
            if text is None:
                w(f'D {path}\n'.encode())
            else:
                t = text.encode('utf-8')
                w(f'M 100644 inline {path}\ndata {len(t)}\n'.encode() + t + b'\n')
            state[path] = text
        w(b'\n')
        return mark

    for g in groups:
        m = commit('refs/heads/main', g, None)
        for e in g['events']:
            if m:
                last_mark[e['law']] = m
            if e.get('tag'):
                tags[e['tag']] = m or last_mark[e['law']]
    when = git_date(retrieved, mark + 1)
    msg = (f'Documentation: README, REPRODUCE, SOURCES, LICENSE, corpus.json, tools and data\n\n'
           f'Built from the mevzuat.gov.tr cache retrieved on {retrieved}. No law text changes.\n\n'
           f'In-force: {retrieved}\nKind: documentation\n').encode()
    mark += 1
    w(f'commit refs/heads/main\nmark :{mark}\n'.encode())
    w(f'author {COMMITTER} {when}\ncommitter {COMMITTER} {when}\n'.encode())
    w(f'data {len(msg)}\n'.encode() + msg + b'\n')
    for path, data in sorted(docs.items()):
        w(f'M 100644 inline {path}\ndata {len(data)}\n'.encode() + data + b'\n')
    w(b'\n')
    main_tip = mark
    parent = main_tip
    future_tags = {}
    for g in future:
        m = commit('refs/heads/future', g, parent)
        if m:
            parent = m
            for e in g['events']:
                future_tags[e['law']] = m
    for t, m in sorted(tags.items()):
        w(f'reset refs/tags/{t}\nfrom :{m}\n\n'.encode())
    w(b'done\n')
    proc.stdin.close()
    if proc.wait():
        sys.exit('git fast-import failed')
    return {'tags': len(tags), 'future_commits': len([g for g in future]), 'future_laws': sorted(future_tags)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--today', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--no-history', action='store_true', help='current text only (the first published build)')
    args = ap.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.today):
        sys.exit('--today must be YYYY-MM-DD')
    retrieved = (CACHE / 'fetched_on.txt').read_text('utf-8').strip()
    if retrieved > args.today:
        sys.exit(f'retrieval date {retrieved} is after --today {args.today}')
    acts = load_acts(args.limit)
    for k, a in enumerate(acts):
        a['order'] = k
    acts_by_dir = {a['dir']: a for a in acts}
    titles = {a['no']: a['title'] for a in acts if a['kind'] == 'kanun' and a['tertip'] == '5'}
    titles.update({a['no']: a['title'] for a in acts if a['kind'] == 'kanun' and a['no'] not in titles})
    from concurrent.futures import ProcessPoolExecutor
    from functools import partial
    import history
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(build_act, acts, chunksize=4))  # ordered: output does not depend on timing
        hist_acts = [(a, r) for a, r in zip(acts, results) if a['old'] and r['files'] and not args.no_history]
        hist = list(pool.map(partial(history.law_history, retrieved=retrieved, titles=titles),
                             [a for a, _ in hist_acts], [r for _, r in hist_acts], chunksize=2))
    hist_by = {a['dir']: h for (a, _), h in zip(hist_acts, hist)}
    events, issues, amend, inforce, versions = [], [], [], [], []
    for act, built in zip(acts, results):
        issues += built['issues']
        amend += built['amend']
        inforce += built['inforce']
        act['articles'] = built.get('articles', 0)
        act['footnotes'] = built.get('footnotes', 0)
        act['notes'] = len(built['amend'])
        act['built'] = bool(built['files'])
        h = hist_by.get(act['dir'])
        if h:
            issues += h['issues']
        if h and h['events']:
            act['history'] = len(h['versions'])
            events += h['events']
            versions += h['versions']
        elif built['files']:
            act['history'] = 0
            events.append({'law': act['dir'], 'date': retrieved, 'kind': 'current', 'act': '', 'seq': (0, 0, ''),
                           'files': built['files'], 'built': built})
    main_events = [e for e in events if not e.get('future') and not (e.get('noop') and not e['files'])]
    future_events = [e for e in events if e.get('future')]
    groups = plan(main_events)
    fgroups = plan(future_events)
    print(f'{len(acts)} acts, {sum(1 for a in acts if a.get("history"))} with history, {len(versions)} versions, '
          f'{len(groups)} law commits, {len(fgroups)} future commits, {len(issues)} issues', flush=True)
    stats_extra = {'kinds': Counter(g['events'][0]['kind'] for g in groups),
                   'future_kinds': Counter(g['events'][0]['kind'] for g in fgroups)}

    import docs as docmod
    docs = docmod.render(acts, groups, issues, amend, inforce, args.today, retrieved, versions=versions,
                         extra=stats_extra, fgroups=fgroups)

    repo = args.repo
    remote = None
    if repo.exists() and any(repo.iterdir()):
        if not (repo / '.git').exists():
            sys.exit(f'{repo} is not empty and not a git repository; refusing')
        r = subprocess.run(['git', '-C', str(repo), 'log', '--all', '--format=%ae'], capture_output=True, text=True)
        authors = {a for a in r.stdout.split() if not a.endswith('@mevzuat-gov-tr.invalid')}
        if authors - {'turkey-law@lexifina.com', 'world-law@lexifina.com'}:
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
    res = fast_import(repo, groups, fgroups, docs, retrieved, acts_by_dir, titles)
    subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '-f', 'main'], check=True)
    head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    count = subprocess.run(['git', '-C', str(repo), 'rev-list', '--count', 'HEAD'], capture_output=True,
                           text=True).stdout.strip()
    print(f'built {repo}: {count} commits on main, {res["tags"]} tags, future commits {res["future_commits"]}, '
          f'head {head}', flush=True)


if __name__ == '__main__':
    main()
