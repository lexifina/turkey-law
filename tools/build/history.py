"""History for the laws that have earlier consolidated texts ("Onceki metinler") on mevzuat.gov.tr.

Each earlier text (a Word file, converted by convert_doc.ps1) is one version of the law, keyed by the act whose
changes it includes. Versions run in date order, then the current text. Between two versions every changed file is
credited to one act, or labelled:

- the act is taken from the amendment notes that newly appear in the file ("(Degisik: 20/2/2014-6525/48 md.)",
  "(Iptal: Anayasa Mahkemesinin ... K.: 2013/43 ...)"); if none appear, from the version's own act(s) when the
  publisher's in-force table lists this article for that act;
- the date is that act's entry-into-force date in the publisher's in-force table ("... YURURLUGE GIRIS TARIHINI
  GOSTERIR LISTE"), for this article if the table gives several; a version whose act is not in the table is dated by
  the act's Resmi Gazete date (`Date-source: published`);
- a change with no candidate, several candidates, no usable date, or a date outside the two versions' dates is
  labelled `Kind: unexplained` (author: the publisher) with `Candidate:` trailers, and is never credited;
- changes to the publisher's apparatus (footnotes, the in-force list, provisions not worked in, footnote numbers)
  are `Kind: editorial` (author: the publisher).
A change dated after the retrieval day (only possible between the last version and the current text) goes on the
`future` branch.
"""
import json
import re
from collections import Counter
from pathlib import Path

import build
from build import CACHE, iso, norm

HTML = CACHE / 'oldhtml'
APPARATUS = ('dipnotlar.md', 'yururluk-listesi', 'islenemeyen-hukumler')
MARK = re.compile(r'\[\d+\]')
DATE = r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})'
AYM = re.compile(r'K\.?\s*:?\s*(?:(\d{4})\s*/\s*)?(\d+)')
AYM_NOTE = re.compile(r'Anayasa\s+Mahkemesi\S*\s+(?:' + DATE + r'\s+tarihli\s+ve\s+)?E\.?\s*:?\s*\d{4}\s*/\s*\d+\s*[,;]?\s*'
                      r'K\.?\s*:?\s*(?:(\d{4})\s*/\s*)?(\d+)')
LETTERS = 'A-Za-z\u00c7\u011e\u0130\u00d6\u015e\u00dc\u00e7\u011f\u0131\u00f6\u015f\u00fc'


CANON_DROP = re.compile(r'\s+|_{3,}|\[\d+\]')
CANON_MAP = str.maketrans({'\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-', '\u2015': '-',
                           '\u2212': '-', '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'"})


def canon(text: str | None) -> str:
    """Text with the publisher's typography removed: whitespace, dash and quote variants, footnote markers and
    underscore rules. Two texts with the same canon differ only in typesetting."""
    return CANON_DROP.sub('', (text or '').translate(CANON_MAP))


def canon_lines(text: str | None) -> Counter:
    return Counter(c for c in (canon(l) for l in (text or '').split('\n')) if c)


def apparatus(fn: str) -> bool:
    return fn.startswith(APPARATUS) or fn == 'index.txt'


# ---------------------------------------------------------------------------------------------------- act keys

def key_from_note(law: str) -> str:
    s = re.sub(r'\s+', '', law)
    m = re.fullmatch(r'(KHK|CBK)[-/]?(\d+)', s)
    if m:
        return f'{m.group(1)}-{int(m.group(2))}'
    return str(int(s)) if s.isdigit() else ''


def key_from_cell(text: str) -> str:
    t = norm(MARK.sub('', text))
    if re.fullmatch(r'\d+', t):
        return str(int(t))
    m = re.match(r'^KHK\s*[-/\u2013]?\s*(\d+)', t)
    if m:
        return f'KHK-{int(m.group(1))}'
    if re.match(r'^Anayasa\s+Mah', t):
        m = AYM.search(t)
        if m:
            year = m.group(1)
            if not year:
                d = re.search(DATE, t)
                year = d.group(3) if d else ''
            return f'AYM-{year}/{int(m.group(2))}' if year else ''
        return ''
    m = re.match(r'^(\d+)\s+numaral\u0131\s+Cumhurba', t)
    if m:
        return f'CBK-{int(m.group(1))}'
    m = re.match(r'^(\d+)\s+say\u0131l\u0131', t, re.I)
    if m:
        return str(int(m.group(1)))
    m = re.search(r'\)\s*(\d+)$', t)
    if m:
        return str(int(m.group(1)))
    return ''


def key_from_row(r: dict) -> str:
    kind, no = r.get('mevzuatTurEnumString') or '', str(r.get('mevzuatNo') or '').strip()
    if kind in ('Kanunlar', 'M\u00fclga Kanun') and no.isdigit():
        return str(int(no))
    if 'Kararname' in kind or kind == 'M\u00fclga KHK':
        return f'KHK-{int(no)}' if no.isdigit() else ''
    if kind == 'Anayasa Mahkemesi':
        m = re.fullmatch(r'(\d{4})/?(\d+)', no)
        return f'AYM-{m.group(1)}/{int(m.group(2))}' if m else ''
    return f"{re.sub(r'[^A-Za-z]', '', kind.translate(build.FOLD)).upper()}-{no}" if no else ''


def act_name(key: str, titles: dict) -> str:
    if key.isdigit():
        t = titles.get(key)
        return f'Kanun {key}' + (f' ({t[:60]})' if t else '')
    if key.startswith('KHK-'):
        return f'KHK {key[4:]}'
    if key.startswith('CBK-'):
        return f'Cumhurba\u015fkanl\u0131\u011f\u0131 Kararnamesi {key[4:]}'
    if key.startswith('AYM-'):
        return f'Anayasa Mahkemesi K. {key[4:]}'
    return key


def act_email(key: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', ('kanun-' + key if key.isdigit() else key).lower()).strip('-') + '@mevzuat-gov-tr.invalid'


def note_keys(text: str) -> Counter:
    c = Counter()
    for m in build.NOTE.finditer(text):
        k = key_from_note(m.group('law'))
        if k:
            c[k] += 1
    for m in AYM_NOTE.finditer(text):
        year = m.group(4) or m.group(3)
        if year:
            c[f'AYM-{year}/{int(m.group(5))}'] += 1
    return c


def note_text(text: str, key: str) -> str:
    for m in build.NOTE.finditer(text):
        if key_from_note(m.group('law')) == key:
            return m.group(0)
    for m in AYM_NOTE.finditer(text):
        year = m.group(4) or m.group(3)
        if year and f'AYM-{year}/{int(m.group(5))}' == key:
            return m.group(0)
    return ''


# ---------------------------------------------------------------------------------------------------- in-force table

def cell_date(text: str) -> tuple[str, str]:
    """(in-force date, applies-from date) from an in-force-table cell. Only a cell that ENDS with a date gives one
    ("1/1/2008 tarihinden gecerli olmak uzere 8/5/2008" -> 2008-05-08, applies from 2008-01-01); a cell such as
    "... takip eden butce yili basinda" gives none."""
    t = MARK.sub('', norm(text)).strip().rstrip(')').strip()
    m = re.search(DATE + r'$', t)
    if not m:
        return '', ''
    d = iso(m.group(0))
    first = re.search(DATE, t)
    applies = iso(first.group(0)) if ('ge\u00e7erli' in t and first and first.start() < m.start()) else ''
    return d, applies


def refs(text: str) -> set[str]:
    out = set()
    for tok in re.split(r',|;|\s+ve\s+|\s+ile\s+', norm(MARK.sub('', text))):
        tok = tok.strip()
        if '\u0130\u015flenemeyen' in tok or '\u0130\u015eLENEMEYEN' in tok:
            out.add('islenemeyen-hukumler')
            continue
        m = re.match(r'^(?:(Ek\s+Ge\u00e7ici|Ge\u00e7ici|Ek|M\u00fckerrer)\s+)?(?:Madde(?:si|ler|leri|nin)?\s*)?(\d{1,4})'
                     rf'(?:\s*/\s*([{LETTERS}])(?![{LETTERS}]))?', tok, re.I)
        if not m:
            continue
        pre = norm(m.group(1) or '').translate(build.FOLD).lower().replace(' ', '-')
        name = f"{pre + '-' if pre else ''}madde-{int(m.group(2))}"
        if m.group(3):
            name += m.group(3).translate(build.FOLD).lower()
        out.add(name)
    return out


def table(parsed: list[dict]) -> dict[str, list[dict]]:
    """act key -> rows {articles (file stems), date, applies, raw}, from the newest text that lists the act."""
    out: dict[str, list[dict]] = {}
    for p in parsed:  # newest first
        rows: dict[str, list[dict]] = {}
        for _, amending, arts, _, printed in p['inforce']:
            k = key_from_cell(amending)
            if not k:
                continue
            d, applies = cell_date(printed)
            rows.setdefault(k, []).append({'articles': refs(arts), 'date': d, 'applies': applies,
                                           'raw': f'{norm(amending)} | {norm(arts)} | {norm(printed)}'})
        for k, v in rows.items():
            out.setdefault(k, v)
    return out


def table_date(tab: dict, key: str, stem: str | None) -> tuple[str, str, str]:
    """(date, applies, evidence) for act `key` and file stem, or ('', '', why)."""
    rows = tab.get(key) or []
    dates = sorted({r['date'] for r in rows if r['date']})
    if not rows:
        return '', '', 'act not in the in-force table'
    if len(dates) == 1 and all(r['date'] for r in rows):
        r = next(r for r in rows if r['date'])
        return dates[0], r['applies'], r['raw']
    if stem:
        hit = [r for r in rows if stem in r['articles'] and r['date']]
        if len({r['date'] for r in hit}) == 1:
            return hit[0]['date'], hit[0]['applies'], hit[0]['raw']
    return '', '', f'in-force table gives {len(dates)} dates for this act'


# ---------------------------------------------------------------------------------------------------- versions

def versions_for(act: dict) -> list[dict]:
    f = CACHE / 'old' / f"{act['tertip']}.{act['no']}.json"
    if not f.exists():
        return []
    rows = json.loads(f.read_text('utf-8'))
    by: dict[str, dict] = {}
    for r in rows:
        if not r.get('docUrl'):
            continue
        base = r['docUrl'].rsplit('/', 1)[1][:-4]
        v = by.setdefault(base, {'base': base, 'rows': [], 'sort': r.get('kabulTarihDosyaPath') or ''})
        v['rows'].append(r)
    return sorted(by.values(), key=lambda v: (v['sort'], v['base']))


def law_history(act: dict, current: dict, retrieved: str, titles: dict) -> dict:
    """Versions and events for one law. `current` is build_act()'s result for the current text."""
    vs = versions_for(act)
    issues, parsed = [], []
    for v in vs:
        h = HTML / f"{v['base']}.htm"
        if not h.exists():
            why = (HTML / f"{v['base']}.fail").read_text('utf-8').strip() if (HTML / f"{v['base']}.fail").exists() \
                else 'not converted'
            issues.append([act['dir'], f"earlier text {v['base']}.doc unreadable: {why}"])
            continue
        p = build.parse_html(h.read_text('utf-8'), act['dir'])
        v['parsed'] = p
        v['acts'] = sorted({k for k in (key_from_row(r) for r in v['rows']) if k})
        parsed.append(v)
    if not parsed:
        return {'events': [], 'versions': [], 'issues': issues}
    tab = table([current] + [v['parsed'] for v in reversed(parsed)])
    own = act['no'] if act['kind'] == 'kanun' else ''
    # version dates
    last = ''
    for v in parsed:
        ds, src = [], ''
        for k in v['acts']:
            d = max((r['date'] for r in tab.get(k, []) if r['date']), default='')
            if d:
                ds.append(d)
        if ds:
            v['date'], src = max(ds), 'in-force-table'
        else:
            pub = max((iso(r.get('resmiGazeteTarihi') or '') for r in v['rows']), default='')
            v['date'], src = pub, 'published'
        if not v['date']:
            v['date'], src = last or retrieved, 'previous-version'
        if v['date'] < last:
            v['date_note'] = f"{src} date {v['date']} is before the previous version's; moved to {last}"
            v['date'], src = last, 'previous-version'
        if v['date'] > retrieved:
            v['date_note'] = f"{src} date {v['date']} is after the retrieval day; moved to {retrieved}"
            v['date'], src = retrieved, 'retrieval'
        v['date_source'] = src
        v['own'] = bool(own) and v['acts'] == [own]
        last = v['date']
    cur = {'base': 'current', 'acts': [], 'date': retrieved, 'date_source': 'retrieval', 'parsed': current,
           'rows': [], 'own': False}
    chain = parsed + [cur]
    events = []
    # baseline
    b = chain[0]
    events.append({'law': act['dir'], 'date': b['date'], 'role': 0, 'kind': 'enacted' if b['own'] else 'consolidated',
                   'act': own if b['own'] else '', 'files': dict(b['parsed']['files']), 'seq': (0, 0, ''),
                   'version': light(b), 'date_source': b['date_source'], 'tag': tag_name(act, b, 0),
                   'order': b['parsed']['order']})
    for i in range(len(chain) - 1):
        events += transition(act, chain[i], chain[i + 1], i + 1, tab, retrieved, titles)
    # the index file: each event writes the law's index for the files present after it
    present: dict[str, str] = {}
    for e in events:
        prev_order = list(present_order(act, present))
        for path, text in e['files'].items():
            if path.endswith('/index.txt'):
                continue
            if text is None:
                present.pop(path, None)
            else:
                present[path] = text
        nxt = e.get('order') or prev_order
        e['files'] = {p: t for p, t in e['files'].items() if not p.endswith('/index.txt')}
        names = merge_order(nxt, prev_order)
        idx = '\n'.join(n for n in names if f"{act['dir']}/{n}" in present) + '\n'
        e['files'][f"{act['dir']}/index.txt"] = idx
        present[f"{act['dir']}/index.txt"] = idx
    vers = [{'law': act['dir'], 'tag': tag_name(act, v, k), 'base': v['base'], 'acts': v['acts'], 'date': v['date'],
             'date_source': v['date_source'], 'date_note': v.get('date_note', ''), 'header': v['parsed']['header'],
             'files': len(v['parsed']['files'])} for k, v in enumerate(chain)]
    return {'events': events, 'versions': vers, 'issues': issues, 'table': tab}


def light(v: dict) -> dict:
    return {'base': v['base'], 'acts': v['acts'], 'date_source': v['date_source'], 'parsed': {'header': v['parsed']['header']}}


def present_order(act: dict, present: dict) -> list[str]:
    idx = present.get(f"{act['dir']}/index.txt")
    return [n for n in idx.split('\n') if n] if idx else []


def merge_order(nxt: list[str], prev: list[str]) -> list[str]:
    out = list(nxt)
    seen = set(out)
    for k, n in enumerate(prev):
        if n in seen:
            continue
        # after its predecessor in the previous order, if that is placed
        pos = 0
        for p in reversed(prev[:k]):
            if p in seen:
                pos = out.index(p) + 1
                break
        out.insert(pos, n)
        seen.add(n)
    return out


def tag_name(act: dict, v: dict, k: int) -> str:
    if v['base'] == 'current':
        return f"{act['dir']}/v{k:02d}-current"
    who = 'ilk-hali' if v.get('own') else '-'.join(re.sub(r'[^A-Za-z0-9]+', '-', a) for a in v['acts']) or 'x'
    return f"{act['dir']}/v{k:02d}-{who.lower()}"


def transition(act, a, b, k, tab, retrieved, titles) -> list[dict]:
    fa, fb = a['parsed']['files'], b['parsed']['files']
    d0, d1 = a['date'], b['date']
    pre = f"{act['dir']}/"
    credited: dict[tuple, dict] = {}
    unexplained, editorial, future = {}, {}, {}
    reasons, cands = {}, {}
    changed = [p for p in sorted(set(fa) | set(fb)) if fa.get(p) != fb.get(p) and not p.endswith('/index.txt')]
    # lines that only moved from one file to another (a heading the publisher set before another article)
    removed, added = Counter(), Counter()
    for path in changed:
        if not apparatus(path[len(pre):]):
            removed += canon_lines(fa.get(path)) - canon_lines(fb.get(path))
            added += canon_lines(fb.get(path)) - canon_lines(fa.get(path))
    for path in changed:
        old, new = fa.get(path), fb.get(path)
        stem = path[len(pre):-3]
        rm, ad = canon_lines(old) - canon_lines(new), canon_lines(new) - canon_lines(old)
        if apparatus(path[len(pre):]) or canon(old) == canon(new) or (
                not (rm - added) and not (ad - removed)):
            editorial[path] = new
            continue
        newkeys = note_keys(new or '') - note_keys(old or '')
        evidence = ''
        if newkeys:
            cand = sorted(newkeys)
            evidence = 'note'
        else:
            cand = sorted(x for x in b['acts'] if stem in {s for r in tab.get(x, []) for s in r['articles']})
            evidence = 'in-force table lists the article'
        if len(cand) != 1:
            unexplained[path] = new
            reasons[path] = ('no amendment note or in-force-table row explains it' if not cand
                             else f'{len(cand)} acts could explain it')
            cands[path] = cand or list(b['acts'])
            continue
        x = cand[0]
        d, applies, why = table_date(tab, x, stem)
        src = 'in-force-table'
        if not d and x in b['acts'] and b['date_source'] == 'published':
            d, src, why = b['date'], 'published', 'version dated by the act\'s Resmi Gazete date'
        if not d:
            unexplained[path] = new
            reasons[path] = f'credited by {evidence} to {x}, but no in-force date: {why}'
            cands[path] = [x]
            continue
        if d > retrieved and b['base'] == 'current':
            future.setdefault((d, x), {})[path] = (new, evidence, why, applies)
            continue
        if not d0 <= d <= d1:
            unexplained[path] = new
            reasons[path] = f'{x} is in force {d} by the table, outside this version step ({d0} to {d1})'
            cands[path] = [x]
            continue
        ev = (note_text(new or '', x) if evidence == 'note' else f'in-force table row "{why}"')
        credited.setdefault((d, x), {})[path] = (new, ev, why, applies, src)
    out = []
    order = b['parsed']['order']
    for (d, x), files in sorted(credited.items()):
        out.append({'law': act['dir'], 'date': d, 'role': 1, 'kind': 'amendment', 'act': x, 'seq': (k, 1, x),
                    'files': {p: v[0] for p, v in files.items()}, 'evidence': {p: v[1] for p, v in files.items()},
                    'applies': {p: v[3] for p, v in files.items() if v[3]},
                    'date_source': sorted({v[4] for v in files.values()})[0], 'order': order})
    if unexplained:
        out.append({'law': act['dir'], 'date': d1, 'role': 2, 'kind': 'unexplained', 'act': '', 'seq': (k, 2, ''),
                    'files': unexplained, 'reasons': reasons, 'candidates': cands, 'order': order})
    if editorial or not out:
        out.append({'law': act['dir'], 'date': d1, 'role': 3, 'kind': 'editorial', 'act': '', 'seq': (k, 3, ''),
                    'files': editorial, 'order': order, 'noop': not editorial})
    out[-1]['tag'] = tag_name(act, b, k)
    out[-1]['version'] = light(b)
    for (d, x), files in sorted(future.items()):
        out.append({'law': act['dir'], 'date': d, 'role': 1, 'kind': 'amendment', 'act': x, 'seq': (k + 1, 1, x),
                    'files': {p: v[0] for p, v in files.items()}, 'evidence': {p: v[1] for p, v in files.items()},
                    'applies': {p: v[3] for p, v in files.items() if v[3]}, 'date_source': 'in-force-table',
                    'order': order, 'future': True})
    return out
