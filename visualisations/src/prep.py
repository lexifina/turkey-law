"""Compute every number for the 20 charts into <build>/data.json.

    python prep.py <build-dir>

Reads <build>/log.tsv (from make.py) and the tables extracted into <build>/repo/ (data/ and law/1982/2709/).
Every rule that reads a category out of a title is in this file.
"""
import bisect, collections, csv, difflib, glob, io, json, os, re, statistics, sys
from datetime import date, timedelta

B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '.build')
R = os.path.join(B, 'repo')
D_ = os.path.join(R, 'data')
csv.field_size_limit(10 ** 9)
OUT, PROFILE = {}, {}
C = collections.Counter


def rd(path):
    with open(os.path.join(D_, path), encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def up(s):  # Turkish upper case
    return s.replace('i', 'İ').replace('ı', 'I').upper()


def low(s):  # Turkish lower case
    return s.replace('İ', 'i').replace('I', 'ı').lower()


def ws(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def dmy(s):
    """dd.mm.yyyy or dd/mm/yyyy -> date; Rumi years 1336-1345 (used until 1925) -> +584; 01.01.0001 -> None"""
    m = re.match(r'^\s*(\d{1,2})[./](\d{1,2})[./](\d{4})', s or '')
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 1000:
        return None
    if 1330 <= y <= 1345:
        y += 584
    if not 1 <= mo <= 12 or not 1 <= d <= 31:
        return None
    try:
        return date(y, mo, d)
    except ValueError:
        return date(y, mo, min(d, 28))


ISO = lambda s: date.fromisoformat(s[:10])

# ------------------------------------------------------------------ the git log (one line per commit)
LOG = []
with open(os.path.join(B, 'log.tsv'), encoding='utf-8') as fh:
    for line in fh:
        f = line.rstrip('\n').split('\t')
        if len(f) < 7:
            continue
        LOG.append({'h': f[0], 'an': f[1], 'ad': f[2], 's': f[3], 'kind': f[4], 'inf': f[5], 'path': f[6]})
print('commits', len(LOG))

# ------------------------------------------------------------------ the index of every law (data/m4-all/)
raw = []
for f in sorted(glob.glob(os.path.join(D_, 'm4-all', 'law-index-*.csv'))):
    with open(f, encoding='utf-8') as fh:
        raw += list(csv.DictReader(fh))
LAWS, seen = [], set()
for x in raw:
    t = ws(x['kanunBasligi'])
    key = (x['mevzuatTertip'], x['kanunNo'], x['resmiGazeteTarih'], t)
    if key in seen:
        continue
    seen.add(key)
    LAWS.append({'tertip': x['mevzuatTertip'], 'no': x['kanunNo'].strip(), 'd': dmy(x['resmiGazeteTarih']), 'title': t,
                 'U': up(t).replace('´', "'").replace('’', "'"), 'tag': ws(x['digerKanunlar']), 'inforce': x['yururlulukDurumu'] == '1',
                 'ilga': x['ilgaTuru'].strip(), 'ilga_no': x['ilgaEdenKanunNo'].strip(), 'ilga_d': dmy(x['ilgaEdenKanunTarih']),
                 'muk': x['mukerrer'].startswith('EVET'), 'unpub': 'Yayımlanmadan' in x['aciklama']})
PROFILE['law_index_rows'] = len(raw)
PROFILE['law_index'] = len(LAWS)
PROFILE['law_dupes'] = len(raw) - len(LAWS)
PROFILE['laws_in_force'] = sum(1 for l in LAWS if l['inforce'])
VETO = [l for l in LAWS if l['tag'] == 'VETO']
DATED = [l for l in LAWS if l['d'] and l['tag'] != 'VETO' and l['d'].year >= 1920]
LAST_LAW = max(l['d'] for l in DATED)
print('laws', len(raw), len(LAWS), 'dated 1920+', len(DATED), 'veto', len(VETO), 'last', LAST_LAW)

AGREE = r'\b(ANLAŞMA|ANDLAŞMA|ANTLAŞMA|SÖZLEŞME|MUKAVELE|MUAHEDE|İTİLAFNAME|PROTOKOL|MUTABAKAT|KONVANSİYON|NOTA\b|NOTALAR|MEKTUP|DEKLARASYON|ŞARTI\b|ŞARTNAME|STATÜ|AHİTNAME|BEYANNAME|MİSAK|PAKT|TAHKİMNAME|SENEDİ)'
APPROVE = r'ONAYLANMASI|UYGUN BULUN|KATILMA|TASDİK|ONANMASI|ONAYLANDIĞI|İMZASINA SALAHİYET|İMZALANMASINA|ONAMA|MERİYET|İLTİHAK|AKİT VE İMZA'


def law_cat(l):
    """one category per law, from its title (rules below) and the index's own tag (digerKanunlar)"""
    t = l['U']
    if (re.search(AGREE, t) and re.search(APPROVE, t)) or (l['tag'] == 'ANLAŞMA' and re.search(AGREE + '|' + APPROVE, t)) \
            or re.search(r'ONAYLANMASININ UYGUN BULUNDU|KATILMAMIZIN UYGUN BULUNDU|KATILMASININ UYGUN BULUNDU', t):  # the formula for approving a treaty
        return 'treaty'
    if l['tag'] == 'BÜTÇE' or re.search(r'BÜTÇE|KESİN ?HESAP|HESABI KATİ|HESABI KAT\'İ|HESABI KATI|M[UÜ]VAZENE|MÜNAKALE|TAHSİSAT|EK ÖDENEK|ÖDENEK VERİLMESİ|ÖDENEK KONULMASI|ÖDENEK AKTARILMASI|FEVKALADE ÖDENEK|MALİ YILI|BİLANÇO|AVANS KANUNU|\bİKRAZ|İSTİKRAZ', t):
        return 'budget'
    if re.search(r'KANUN HÜKMÜNDE KARARNAME', t) and re.search(r'KABUL', t):
        return 'khk'
    if re.search(r'\bBAZI KANUN|\bÇEŞİTLİ KANUN', t):
        return 'omnibus'
    if l['tag'] in ('ÖZEL', 'GENEL AF') or re.search(r'VATANİ HİZMET|\bAF KANUNU|AFFI UMUMİ|\bAFFINA\b|\bAFFI HAKKINDA|AFLARINA', t):
        return 'special'
    if re.search(r'DEĞİŞİKLİK|DEĞİŞTİRİL|TADİL|MUADDİL|MÜZEYYEL|ZEYL|EK MADDE|MADDE EKLEN|MADDELER EKLEN|FIKRA EKLEN|BENT EKLEN|YÜRÜRLÜKTEN KALDIRIL|KALDIRILMASI|İLGASI|ERTELENMESİ|TEFSİR|UZATILMASI|\bEK KANUN|\bEKLENMESİ', t):
        return 'amend'
    return 'new'


for l in DATED:
    l['cat'] = law_cat(l)
CATS = ['treaty', 'budget', 'amend', 'omnibus', 'khk', 'special', 'new']

# c01: laws per year, 1920 to now
yc = C(l['d'].year for l in DATED)
c01 = [{'y': y, 'n': yc[y], 'treaty': sum(1 for l in DATED if l['d'].year == y and l['cat'] == 'treaty')} for y in range(1920, LAST_LAW.year + 1)]
OUT['c01'] = {'rows': c01, 'last': LAST_LAW.isoformat(), 'n': len(DATED), 'veto': len(VETO),
              'undated': sum(1 for l in LAWS if not l['d'] and l['tag'] != 'VETO'), 'unpub': sum(1 for l in LAWS if not l['d'] and l['tag'] != 'VETO' and l['unpub']), 'pre1920': sum(1 for l in LAWS if l['d'] and l['d'].year < 1920 and l['tag'] != 'VETO'),
              't4': [min(l['d'].year for l in DATED if l['tertip'] == '4'), sum(1 for l in DATED if l['tertip'] == '4' and l['d'].year <= 1961)]}
u3 = sorted(int(l['no']) for l in LAWS if l['tertip'] == '3' and not l['d'] and l['tag'] != 'VETO' and l['no'].isdigit())
d3n = {int(l['no']): l['d'] for l in DATED if l['tertip'] == '3' and l['no'].isdigit()}
lo3 = max(n for n in d3n if n < u3[0]); hi3 = min(n for n in d3n if n > u3[-1])
OUT['c01']['undated3'] = [len(u3), u3[0], u3[-1], lo3, d3n[lo3].isoformat(), hi3, d3n[hi3].isoformat()]
print('c01', [(r['y'], r['n']) for r in c01[::8]], OUT['c01']['undated'], OUT['c01']['pre1920'])

# c02: what the laws were, by decade
c02 = collections.defaultdict(C)
for l in DATED:
    c02[(l['d'].year // 10) * 10][l['cat']] += 1
OUT['c02'] = [{'d': d, **c02[d]} for d in sorted(c02)]
tagcheck = C((l['tag'] or '-', l['cat']) for l in DATED)
print('c02', [(r['d'], {k: r.get(k, 0) for k in CATS}) for r in OUT['c02']])
print('   tag x cat', sorted(tagcheck.items(), key=lambda x: -x[1])[:24])

# ------------------------------------------------------------------ Assembly terms (from the index of plenary minutes)
MIN = []
for f in glob.glob(os.path.join(D_, 'minutes-*.csv')):
    with open(f, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if not re.match(r'^\d{4}-\d\d-\d\d$', r.get('sitting_date', '')):
                continue
            MIN.append({'term': int(r['term']), 'd': ISO(r['sitting_date']), 'closed': r.get('sitting_kind') == 'closed-published-index' or 'Kapalı' in r.get('source_chamber', ''),
                        'no': r.get('sitting_number', ''), 'f': os.path.basename(f)})
bt = collections.defaultdict(list)
for m in MIN:
    bt[m['term']].append(m['d'])
dropped = []
for t, ds in bt.items():  # a sitting dated years away from the rest of its term is a typo in the source
    md = sorted(ds)[len(ds) // 2]
    for m in [m for m in MIN if m['term'] == t and abs((m['d'] - md).days) > 6 * 365]:
        dropped.append(m); MIN.remove(m)
dk = C((m['term'], m['d'], m['closed'], m['no']) for m in MIN)
MIN_DUPES = sum(v - 1 for v in dk.values() if v > 1)
TERMS = {}
for m in MIN:
    a, z = TERMS.get(m['term'], (m['d'], m['d']))
    TERMS[m['term']] = (min(a, m['d']), max(z, m['d']))
print('terms', sorted((t, a.isoformat(), z.isoformat()) for t, (a, z) in TERMS.items()), 'dropped', [(m['term'], m['d'].isoformat()) for m in dropped])


def term_of(d):
    best = None
    for t, (a, z) in sorted(TERMS.items()):
        if a <= d:
            best = t
    return best


# c03: omnibus laws by term (17-28), and the acts each amending instrument reached (amendment notes)
c03 = []
for t in sorted(TERMS):
    if t < 17:
        continue
    a = TERMS[t][0]
    nxt = min([TERMS[u][0] for u in TERMS if u > t] or [date(2100, 1, 1)])
    ls = [l for l in DATED if a <= l['d'] < nxt]
    dom = [l for l in ls if l['cat'] not in ('treaty', 'budget')]
    c03.append({'t': t, 'a': a.isoformat(), 'z': TERMS[t][1].isoformat(), 'all': len(ls), 'dom': len(dom), 'omni': sum(1 for l in dom if l['cat'] == 'omnibus'),
                'treaty': sum(1 for l in ls if l['cat'] == 'treaty'), 'khk': sum(1 for l in dom if l['cat'] == 'khk')})
AM = rd('amendments.csv')
PROFILE['amend_notes'] = len(AM)


def mode(xs):
    return C(xs).most_common(1)[0][0] if xs else ''


def amender(s):
    s = s.strip()
    m = re.match(r'^KHK\W*(\d+)$', s, re.I)
    if m:
        return ('KHK', int(m.group(1)))
    m = re.match(r'^(\d+)$', s)
    return ('Kanun', int(m.group(1))) if m else None


reach, notes_by, dates_by = collections.defaultdict(set), C(), collections.defaultdict(list)
for r in AM:
    k = amender(r['amending_law'])
    if not k:
        continue
    reach[k].add(r['act']); notes_by[k] += 1
    if r['date']:
        dates_by[k].append(r['date'])
first_by = {k: mode(v) for k, v in dates_by.items()}  # the date most of its notes print (a few notes carry a typo)
by_no = collections.defaultdict(list)
for l in DATED:
    if l['no'].isdigit():
        by_no[int(l['no'])].append(l)


def law_title(no, year=None):
    c = by_no.get(no, [])
    if year:
        c = sorted(c, key=lambda l: abs(l['d'].year - year))
    return c[0]['title'] if c else ''


# titles of decree-laws, from the gazette index and the decree-law folder's commits
KHK_T = {}
for c in LOG:
    m = re.match(r'^KHK (\d+): (.+)$', c['s'])
    if m and c['an'].startswith('Mevzuat Bilgi Sistemi'):
        KHK_T.setdefault(int(m.group(1)), m.group(2).rstrip('. '))
top = sorted(reach, key=lambda k: (-len(reach[k]), -notes_by[k]))[:14]
OUT['c03'] = {'terms': c03, 'reach': [{'k': k[0], 'no': k[1], 'acts': len(reach[k]), 'notes': notes_by[k], 'd': first_by.get(k, ''),
                                       'title': law_title(k[1], int(first_by[k][:4]) if first_by.get(k) else None) if k[0] == 'Kanun' else ''} for k in top],
              'amenders': len(reach)}
print('c03', [(r['t'], r['dom'], r['omni'], r['all']) for r in c03])
print('   reach', [(r['k'], r['no'], r['acts'], r['notes'], r['d'], r['title'][:70]) for r in OUT['c03']['reach']])

# c04: vetoes: law numbers the index marks VETO (never published), dated by the published number just below
PRES = [('gursel', '1961-10-26', '1966-03-28'), ('sunay', '1966-03-28', '1973-03-28'), ('koruturk', '1973-04-06', '1980-04-06'),
        ('evren', '1982-11-09', '1989-11-09'), ('ozal', '1989-11-09', '1993-04-17'), ('demirel', '1993-05-16', '2000-05-16'),
        ('sezer', '2000-05-16', '2007-08-28'), ('gul', '2007-08-28', '2014-08-28'), ('erdogan', '2014-08-28', '2099-01-01')]
pub = {}
for l in DATED:
    if l['tertip'] == '5' and l['no'].isdigit():
        n = int(l['no'])
        if n not in pub or l['d'] < pub[n]['d']:
            pub[n] = l
nums = sorted(pub)
nt = lambda s: re.sub(r'[^A-ZÇĞİÖŞÜ0-9 ]', '', s).replace('  ', ' ').strip()
c04 = []
for v in VETO:
    n = int(v['no']); i = bisect.bisect_left(nums, n)
    lo = pub[nums[i - 1]] if i > 0 else None
    d = lo['d']
    p = next((k for k, a0, z0 in PRES if a0 <= d.isoformat() < z0), None)
    rep = None
    for m in nums[i:i + 600]:
        if (pub[m]['d'] - d).days > 3 * 365:
            break
        if difflib.SequenceMatcher(None, nt(v['U']), nt(pub[m]['U'])).ratio() > 0.9:
            rep = m; break
    c04.append({'no': n, 'd': d.isoformat(), 'p': p, 'title': v['title'], 'rep': rep, 'rep_d': pub[rep]['d'].isoformat() if rep else None,
                'lo': nums[i - 1], 'hi': nums[i] if i < len(nums) else None})
c04.sort(key=lambda r: r['no'])
OUT['c04'] = {'rows': c04, 'pres': [[k, a0, z0] for k, a0, z0 in PRES]}
print('c04', C(r['p'] for r in c04), sum(1 for r in c04 if r['rep']))

# c05: plenary sittings per year; the closed sessions (gizli celse) the index lists
c05y = collections.defaultdict(C)
for m in MIN:
    c05y[m['d'].year]['closed' if m['closed'] else 'open'] += 1
OUT['c05'] = {'years': [{'y': y, 'open': c05y[y]['open'], 'closed': c05y[y]['closed']} for y in sorted(c05y)],
              'terms': [[t, a.isoformat(), z.isoformat(), sum(1 for m in MIN if m['term'] == t and not m['closed']), sum(1 for m in MIN if m['term'] == t and m['closed'])]
                        for t, (a, z) in sorted(TERMS.items())],
              'n': len(MIN), 'dropped': len(dropped), 'dupes': MIN_DUPES,
              'closed_sameday': sum(1 for m in MIN if m['closed'] and any(o['term'] == m['term'] and o['d'] == m['d'] and not o['closed'] for o in MIN if o['d'] == m['d']))}
print('c05', OUT['c05']['terms'][:3], OUT['c05']['closed_sameday'])

# ------------------------------------------------------------------ the Resmî Gazete daily index (data/rg-*.csv, data/rg-index/)


def read_multi(path):
    """a csv file that may contain a second header row part-way through (rg-2023.csv joins two formats)"""
    with open(path, encoding='utf-8', newline='') as fh:
        head = None
        for row in csv.reader(fh):
            if not row:
                continue
            if head is None or (row[0] in ('date', 'issue') and 'title' in row):
                head = row; continue
            yield dict(zip(head, row))


def rg_items():
    files = [f for f in sorted(glob.glob(os.path.join(D_, 'rg-*.csv'))) if 'rg-issues' not in f]
    files += sorted(glob.glob(os.path.join(D_, 'rg-index', 'm8-years-2of8', 'rg-20??-??.csv')))
    files += sorted(glob.glob(os.path.join(D_, 'rg-index', 'm8-years-5of8', 'rg-20??.csv')))
    seen = set()
    for f in files:
        for r in read_multi(f):
            d = r.get('date', '')
            if not re.match(r'^\d{4}-\d\d-\d\d$', d):
                continue
            t = ws(re.sub(r'^[\s—–-]+', '', r.get('title', '')))
            key = (d, re.sub(r'[^0-9a-zçğıöşüâîû]', '', low(t))[:200])
            if key in seen:  # the same item listed by two sources (or twice in one)
                continue
            seen.add(key)
            yield {'d': d, 'y': int(d[:4]), 'sec': re.sub(r'\s+', '', r.get('section', '')).upper(), 'h': ws(up(r.get('heading', ''))), 't': t, 'f': os.path.basename(f)}


RG = [i for i in rg_items() if 'İLÂN' not in i['sec'] and 'İLAN' not in i['sec']]
print('rg items', len(RG))
for i in RG:
    m = re.match(r'^KHK/(\d+)\s+(.+)$', i['t'])
    if m:
        KHK_T.setdefault(int(m.group(1)), m.group(2))


def rg_type(i):
    h, t, tl, y = i['h'], i['t'], low(i['t']), i['y']
    cbno = re.search(r'karar sayısı\s*:\s*\d+', tl)
    if 'KANUN HÜKMÜNDE KARARNAME' in h or (re.search(r'kanun hükmünde kararname\s*$', tl) and not re.search(r'kanun\s*$', tl)):
        return 'khk'
    if 'CUMHURBAŞKANLIĞI KARARNAME' in h or h in ('KARARNAMESİ', 'KARARNAMELERİ') or re.search(r'cumhurbaşkanlığı kararnamesi\s*(\(|$)', tl):
        return 'cbk'
    if 'BAKANLAR' in h:
        return 'bkk'
    if cbno and y >= 2018:
        return 'cbkarar'
    if 'CUMHURBAŞKANI KARAR' in h or (y >= 2018 and h in ('KARARLARI', 'KARARI')):
        return 'cbkarar'
    if 'YÖNETMEL' in h.replace(' ', '') or (not h and re.search(r'yönetmeliği?\s*$|yönetmelik\s*$', tl)):
        return 'univ' if UNIV(t) else 'reg'
    if 'TEBLİĞ' in h or 'TEBL' in h:
        return 'teblig'
    if 'ANDLAŞMA' in h or 'SÖZLEŞME' in h or 'ANLAŞMA' in h:
        return 'treaty'
    if re.search(r'ATAMA|VEKÂLET|VEKALET|SEÇME|GÖREVLENDİRME|BAKAN ATANMASI', h):
        return 'appoint'
    if 'YARGI' in i['sec'] or re.search(r'MAHKEME|YARGITAY|DANIŞTAY|SEÇİM KURULU|HÂKİMLER|HAKİMLER|SAYIŞTAY', h):
        return 'court'
    if 'YASAMA' in i['sec'] or re.search(r'^KANUN', h):
        return 'tbmm' if re.search(r'TBMM|MECLİS', h) else 'law'
    if re.match(r'^\d{4}/\d{2,6}\s', t) and y <= 2018:
        return 'bkk'
    if re.search(r'yönetmeliği?\s*$|yönetmelik\s*$', tl):
        return 'univ' if UNIV(t) else 'reg'
    if re.search(r'tebliğ', tl):
        return 'teblig'
    return 'other'


UNIV = lambda t: bool(re.search(r'üniversitesi|yüksek teknoloji enstitüsü', low(t)))
for i in RG:
    i['ty'] = rg_type(i)
RGY = sorted(set(i['y'] for i in RG))
RGLAST = max(i['d'] for i in RG)
c13 = collections.defaultdict(C)
for i in RG:
    c13[i['y']][i['ty']] += 1
OUT['c13'] = {'years': RGY, 'rows': {y: dict(c13[y]) for y in RGY}, 'last': RGLAST, 'days': {y: len(set(i['d'] for i in RG if i['y'] == y)) for y in RGY}}
PROFILE['rg_items'] = len(RG)
PROFILE['rg_days'] = len(set(i['d'] for i in RG))
print('c13', {y: dict(c13[y]) for y in (2016, 2021, 2025)})
for r in OUT['c03']['reach']:
    if r['k'] == 'KHK':
        r['title'] = KHK_T.get(r['no'], '')
print('   other samples', [i['t'][:60] for i in RG if i['ty'] == 'other' and i['y'] in (2003, 2015, 2024)][:12])

# c14: urgent expropriation (acele kamulaştırma) decisions, by what they are for
EXP = [('energy', r'enerji nakil|iletim hat|dağıtım hat|trafo|transformatör|\bkv\b|teiaş|tedaş|elektrik (iletim|dağıtım|üretim)|\bhes\b|\bres\b|\bges\b|\bjes\b|\bdges\b|santral|rüzgar|güneş enerji|jeotermal|hidroelektrik|enerji (üretim|tesis|projesi)|elektrik enerjisi|epdk|enerji piyasası|\benh\b|\bbrş\b'),
       ('mining', r'ruhsat|maden ve petrol işleri|kömür işletmeleri|\btki\b|cevher|maden \(|maden işletme|maden üretim|linyit|mermer|kireçtaşı|agrega|kalker'),
       ('oilgas', r'doğal ?gaz|boru hat|botaş|tpao|\blng\b|tanap|petrol(?! işleri)'),
       ('transport', r'otoyol|karayol|demiryol|rayl|metro|havaliman|liman|köprü|tünel|\byol\b|yolu\b|ulaşım|kavşak|viyadük|tramvay|hızlı tren|otogar'),
       ('water', r'baraj|sulama|gölet|içme ?suyu|atıksu|arıtma|isale|taşkın|ıslah|\bsu\b|dsi|devlet su işleri'),
       ('urban', r'kentsel dönüşüm|afet|deprem|riskli alan|rezerv yapı|konut|toki|gecekondu|yenileme alanı|toplu konut'),
       ]
c14 = collections.defaultdict(C)
c14ex = collections.defaultdict(list)
for i in RG:
    tl = low(i['t'])
    if not re.search(r'acele\s+kamulaştır', tl) or i['ty'] in ('law', 'court', 'teblig', 'reg', 'univ'):
        continue
    k = next((k for k, rx in EXP if re.search(rx, tl)), 'other')
    c14[i['y']][k] += 1
    if len(c14ex[k]) < 6:
        c14ex[k].append(i['t'][:110])
OUT['c14'] = {'years': RGY, 'rows': {y: dict(c14[y]) for y in RGY},
              'dec': {y: c13[y]['bkk'] + c13[y]['cbkarar'] for y in RGY}}
print('c14', {y: dict(c14[y]) for y in RGY})
for k, v in c14ex.items():
    print('   ', k, v[:3])

# c15: universities' share of the regulations in the gazette
c15 = []
for y in RGY:
    regs = [i for i in RG if i['y'] == y and i['ty'] in ('reg', 'univ')]
    un = [i for i in regs if i['ty'] == 'univ']
    c15.append({'y': y, 'all': len(regs), 'univ': len(un), 'centre': sum(1 for i in un if re.search(r'uygulama ve araştırma merkezi', low(i['t'])))})
OUT['c15'] = c15
print('c15', [(r['y'], r['all'], r['univ'], r['centre']) for r in c15])

# ------------------------------------------------------------------ decisions of the Assembly (parliament-decision/ and the gazette index)
PD = {}
for c in LOG:
    m = re.match(r'^parliament-decision/(\d{4})/(\d+)', c['path'])
    if m and not re.match(r'^TBMM decision \d+', c['s']):
        PD.setdefault(int(m.group(2)), {'no': int(m.group(2)), 'd': c['inf'] or c['ad'], 't': c['s'], 'src': 'repo'})
for i in RG:
    if (i['ty'] == 'tbmm' or re.search(r'TBMM|MECLİS', i['h'])):
        m = re.match(r'^((?:\d\s?){2,4})\s+(\D.*)$', i['t'])
        if m and int(m.group(1).replace(' ', '')) not in PD:
            no = int(m.group(1).replace(' ', ''))
            PD[no] = {'no': no, 'd': i['d'], 't': m.group(2), 'src': 'rg'}
PROFILE['tbmm_decisions_titled'] = len(PD)
PROFILE['tbmm_decisions'] = len(set(int(re.match(r'^parliament-decision/\d{4}/(\d+)', c['path']).group(1)) for c in LOG if re.match(r'^parliament-decision/\d{4}/\d+', c['path'])))

# c06: the state of emergency (olağanüstü hal) and martial law decisions
WORDNUM = {'bir': 1, 'iki': 2, 'üç': 3, 'dört': 4, 'beş': 5, 'altı': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9, 'on': 10, 'on bir': 11, 'on iki': 12, 'on üç': 13}


def provinces(t):
    """the number of provinces under the regime after the decision, when its title says it"""
    u = up(t)
    if 'ÜLKE GENELİNDE' in u or ('OLAĞANÜSTÜ HALİN UZATILMASINA DAİR KARAR' in u and len(u) < 60):
        return 81
    m = re.search(r'\(?(\d+)\)?\s*İLDE\s*(?:4 AY SÜRE İLE\s*)?(?:YENİDEN\s*)?UZATILMA?SINA', u)
    if m:
        return int(m.group(1))
    m = re.search(r'DAHA EVVEL\s*\(?(\d+)\)?\s*İLDE UZATILAN OLAĞANÜSTÜ HALİN YENİDEN', u)
    if m:
        return int(m.group(1))
    m = re.match(r'^(.*?)\s*İLLERİNDE', u)
    if m and ',' in m.group(1):
        return len([p for p in re.split(r',| VE ', m.group(1)) if p.strip()])
    if re.search(r'\bİLİNDE OLAĞANÜSTÜ HAL İLANINA', u):
        return 1
    return None


c06 = []
for no, p in sorted(PD.items()):
    u = up(p['t'])
    if 'OLAĞANÜSTÜ HAL' not in u:
        continue
    months = 4 if re.search(r'4 AY|DÖRT AY', u) else 3 if re.search(r'ÜÇ AY|3 AY', u) else None
    kind = 'declare' if re.search(r'İLANINA|İLAN EDİLMESİNE', u) and 'KALDIRIL' not in u else 'lift' if re.search(r'KALDIRILMASINA', u) else 'extend'
    c06.append({'no': no, 'd': p['d'], 'n': provinces(p['t']), 'kind': kind, 'months': months, 't': p['t'], 'src': p['src']})
# a province declared the same day as an extension elsewhere is added to it (1993: 9 + Bitlis)
byd = collections.defaultdict(list)
for r in c06:
    byd[r['d']].append(r)
for d, rs in byd.items():
    if len(rs) == 2 and all(r['n'] for r in rs):
        tot = sum(r['n'] for r in rs)
        for r in rs:
            r['n_total'] = tot
OUT['c06'] = c06
print('c06', [(r['d'], r['no'], r['n'], r.get('n_total'), r['kind'], r['months']) for r in c06])

# c07: authorisations to send the armed forces abroad (Constitution art. 92)
MISSION = [('lebanon', r'LÜBNAN|UNIFIL|1701 \(2006\)'), ('somalia', r'2713 \(2023\)|SOMALİ İLE ÜLKEMİZ|SOMALİ.NİN DENİZ YETKİ'), ('aden', r'KORSANLIK|ADEN KÖRFEZİ|DENİZ HAYDUTLUĞU'),
           ('afghanistan', r'AFGANİSTAN'), ('africa', r'ORTA AFRİKA|\bMALİ VE\b|\bMALİ\b.*CUMHURİYET'), ('libya', r'LİBYA'), ('azerbaijan', r'AZERBAYCAN'),
           ('qatar', r'KATAR'), ('gulf', r'KÖRFEZ KRİZİ'), ('iraq_syria', r'IRAK VE SURİYE|AYRILIKÇI HAREKETLER'), ('iraq', r'IRAK'), ('syria', r'SURİYE')]
c07 = []
for no, p in sorted(PD.items()):
    u = up(p['t'])
    if 'SİLAHLI KUVVET' not in u or ('GÖNDERİL' not in u and 'GÖREVLENDİR' not in u and 'İŞTİRAK' not in u and 'BULUNMASI' not in u and 'İZİN' not in u):
        continue
    k = next((k for k, rx in MISSION if re.search(rx, u)), None)
    if k is None and int(p['d'][:4]) <= 1991:
        k = 'gulf'
    ref = [int(x) for x in re.findall(r'(\d{3,4}) SAYILI (?:TÜRKİYE BÜYÜK MİLLET MECLİSİ )?KARAR', u)]
    yrs = re.search(r'\b(BİR|İKİ|ÜÇ|\d+) YIL', u)
    mos = re.search(r'\b(ALTI|DOKUZ|ON İKİ|ON SEKİZ|YİRMİ DÖRT|\d+) AY\b', u)
    W = {'BİR': 1, 'İKİ': 2, 'ÜÇ': 3, 'ALTI': 6, 'DOKUZ': 9, 'ON İKİ': 12, 'ON SEKİZ': 18, 'YİRMİ DÖRT': 24}
    months = (W.get(mos.group(1)) or int(mos.group(1))) if mos else ((W.get(yrs.group(1)) or int(yrs.group(1))) * 12 if yrs else None)
    c07.append({'no': no, 'd': p['d'], 'k': k, 'ref': ref, 'months': months, 't': p['t'], 'src': p['src']})
# a decision that names no country takes the mission of the decision it extends, or of a later decision extending it
bn = {r['no']: r for r in c07}
for _ in range(3):
    for r in c07:
        if r['k'] is None:
            r['k'] = next((bn[x]['k'] for x in r['ref'] if x in bn and bn[x]['k']), None)
        if r['k'] is None:
            later = [o for o in c07 if r['no'] in o['ref'] and o['k']]
            if later:
                r['k'] = later[0]['k']
for r in c07:
    if r['k'] is None:
        r['k'] = 'unnamed'
OUT['c07'] = c07
print('c07', C(r['k'] for r in c07), [(r['d'], r['no'], r['k'], r['months']) for r in c07 if r['k'] in ('unnamed', 'gulf', 'libya', 'somalia')])

# ------------------------------------------------------------------ amendment notes (data/amendments.csv)
# c08: notes by year and by kind of amending act
c08 = collections.defaultdict(C)
for r in AM:
    k = amender(r['amending_law'])
    if not k or not r['date']:
        continue
    c08[int(r['date'][:4])][k[0]] += 1
yr0 = 1980
OUT['c08'] = {'rows': [{'y': y, 'law': c08[y]['Kanun'], 'khk': c08[y]['KHK']} for y in range(yr0, max(c08) + 1)],
              'before': sum(sum(c08[y].values()) for y in c08 if y < yr0), 'n': sum(sum(v.values()) for v in c08.values()),
              'acts': len(set(r['act'] for r in AM)),
              'year_acts': {y: len(set(r['act'] for r in AM if r['date'][:4] == str(y))) for y in (2008, 2011, 2018)},
              'khk703': [len(reach[('KHK', 703)]), notes_by[('KHK', 703)]], 'k5728': [len(reach[('Kanun', 5728)]), notes_by[('Kanun', 5728)]],
              'khk2011': sum(1 for r in AM if r['date'][:4] == '2011' and amender(r['amending_law']) and amender(r['amending_law'])[0] == 'KHK'),
              'khk_acts2011': len(set(amender(r['amending_law'])[1] for r in AM if r['date'][:4] == '2011' and amender(r['amending_law']) and amender(r['amending_law'])[0] == 'KHK'))}
print('c08', OUT['c08']['khk703'], OUT['c08']['k5728'], OUT['c08']['year_acts'], OUT['c08']['khk2011'], OUT['c08']['khk_acts2011'], OUT['c08']['before'])

PATHS = json.load(open(os.path.join(D_, 'paths.json'), encoding='utf-8'))['paths']


def act_title(act):
    kind, _, no = act.partition('/')
    p = PATHS.get(act, '')
    y = int(p.split('/')[1]) if p.count('/') >= 2 and p.split('/')[1].isdigit() else None
    if kind == 'kanun' and no.isdigit():
        cands = [l for l in LAWS if l['no'] == no and l['d'] and l['tag'] != 'VETO']
        if cands:
            cands.sort(key=lambda l: (not l['inforce'], abs(l['d'].year - y) if y else 0))
            return cands[0]['title'], cands[0]['d'].isoformat()
    for c in LOG:
        if c['path'].startswith(p + '/') and c['s'] and not c['s'].startswith(('KHK', 'Kanun')):
            return c['s'], (str(y) if y else '')
    return act, (str(y) if y else '')


# c09: the most-amended acts, notes per year
nb_act = C(r['act'] for r in AM)
top25 = [a for a, _ in nb_act.most_common(25)]
c09 = []
for a in top25:
    by = C(int(r['date'][:4]) for r in AM if r['act'] == a and r['date'])
    t, d = act_title(a)
    c09.append({'act': a, 'n': nb_act[a], 'title': t, 'd': d, 'by': {str(y): n for y, n in by.items()}, 'inforce': True})
OUT['c09'] = c09
print('c09', [(r['act'], r['n'], r['title'][:50], r['d']) for r in c09])

# c10: the Constitution of 1982, article by article
CDIR = os.path.join(R, 'law', '1982', '2709')
ORD = ['BİRİNCİ', 'İKİNCİ', 'ÜÇÜNCÜ', 'DÖRDÜNCÜ', 'BEŞİNCİ', 'ALTINCI', 'YEDİNCİ']
arts = []
for f in os.listdir(CDIR):
    m = re.match(r'^(gecici-)?madde-(\d+)\.md$', f)
    if not m:
        continue
    txt = open(os.path.join(CDIR, f), encoding='utf-8').read()
    lines = [x.strip() for x in txt.split('\n') if x.strip()]
    mi = next((i for i, x in enumerate(lines) if re.match(r'^(Geçici )?Madde \d+', x, re.I)), 0)
    arts.append({'id': f[:-3], 'no': int(m.group(2)), 'tmp': bool(m.group(1)), 'lines': lines, 'mi': mi,
                 'repealed': bool(re.match(r'^(Geçici )?Madde \d+\s*[–-]\s*\(Mülga', lines[mi] if lines else '', re.I))})
# the printed order: articles 1-174, the provisional articles, then 175-177; a heading at the end of a file belongs to the next one
arts.sort(key=lambda a: (0 if not a['tmp'] and a['no'] <= 174 else 1 if a['tmp'] else 2, a['no']))
ISPART = lambda x: re.match(r'^(' + '|'.join(ORD) + r') KISIM$', x)
NOFN = lambda x: re.sub(r'\s*\[\d+\]', '', x).strip()
carry = []
for a in arts:
    head = carry + a['lines'][:a['mi']]
    carry = []
    # headings printed after an article's text (no closing punctuation) belong to the next article
    i = len(a['lines'])
    while i - 1 > a['mi'] and not re.search(r'[.;,)]$', NOFN(a['lines'][i - 1])):
        i -= 1
    carry = a['lines'][i:]
    part = next((x for x in head if ISPART(x)), None)
    a['part'] = part
    a['part_name'] = head[head.index(part) + 1] if part and head.index(part) + 1 < len(head) else None
    a['title'] = re.sub(r'[:\s]+$', '', NOFN(head[-1])) if head else ''
    del a['lines'], a['mi']
cons = [r for r in AM if r['act'] == 'kanun/2709']
for a in arts:
    a['notes'] = sorted([[r['date'], r['amending_law'], r['kind']] for r in cons if r['article'] == a['id']])
parts, cur = [], None
for a in arts:
    if a['part']:
        cur = {'p': a['part'], 'name': a['part_name'], 'arts': []}; parts.append(cur)
    cur['arts'].append(a['id'])
OUT['c10'] = {'arts': [{k: a[k] for k in ('id', 'no', 'tmp', 'title', 'repealed', 'notes')} for a in arts], 'parts': parts,
              'acts': C(r['amending_law'] for r in cons).most_common(), 'act_dates': {k: mode([r['date'] for r in cons if r['amending_law'] == k]) for k in set(r['amending_law'] for r in cons)},
              'baslangic': [[r['date'], r['amending_law'], r['kind']] for r in cons if r['article'] == 'baslangic']}
print('c10', len(arts), [(p['p'], p['name'], p['arts'][0], p['arts'][-1], len(p['arts'])) for p in parts],
      sum(1 for a in arts if a['notes'] and not a['tmp']), sum(1 for a in arts if a['notes']), sum(1 for a in arts if a['repealed']), OUT['c10']['baslangic'],
      C(r['article'] for r in cons if not re.match(r'^(gecici-)?madde-\d+$', r['article'])))

# c11: when amendments take effect, from the publisher's in-force tables (data/in-force-list.csv)
IFL = rd('in-force-list.csv')
PROFILE['inforce_rows'] = len(IFL)
c11 = collections.defaultdict(C)
for r in IFL:
    a = r['amending'].strip()
    if not re.fullmatch(r'\d{3,4}', a) or not r['in_force']:
        continue
    n = int(a)
    if n not in pub:
        continue
    p, f = pub[n]['d'], ISO(r['in_force'])
    dd = (f - p).days
    if p.year < 1985 or abs(dd) > 3 * 366:  # outside this window the number may belong to an older series of laws
        continue
    c11[p.year]['same' if dd == 0 else 'later' if dd > 0 else 'before'] += 1
OUT['c11'] = [{'y': y, **c11[y]} for y in sorted(c11)]
print('c11', [(r['y'], r) for r in OUT['c11'][-6:]])

# c12: how laws end, by decade of publication
c12 = collections.defaultdict(C)
for l in DATED:
    k = 'inforce' if l['inforce'] else 'bylaw' if l['ilga'] == '1' else 'bykhk' if l['ilga'] == '4' else 'lapsed'
    c12[(l['d'].year // 10) * 10][k] += 1
rep_by = C((l['ilga'], l['ilga_no'], l['ilga_d'].year if l['ilga_d'] else None) for l in DATED if l['ilga'] in ('1', '4') and not l['inforce'])
khk_y = C(l['ilga_d'].year for l in DATED if l['ilga'] == '4' and not l['inforce'] and l['ilga_d'])
OUT['c12'] = {'rows': [{'d': d, **c12[d]} for d in sorted(c12)],
              'top': [[k[0], k[1], k[2], n, law_title(int(k[1]), k[2]) if k[0] == '1' and k[1].isdigit() else KHK_T.get(int(k[1]), '') if k[1].isdigit() else ''] for k, n in rep_by.most_common(8)],
              'khk_years': sorted(khk_y.items())}
print('c12', OUT['c12']['rows'], OUT['c12']['top'][:5], OUT['c12']['khk_years'])

# c16: international agreements approved by law, by the other party (title words; rules below)
STATES = [('KKTC', r'KUZEY KIBRIS|KIBRIS TÜRK'), ('CY', r'KIBRIS CUMHURİYETİ'),
          ('US', r'AMERİKA BİRLEŞİK DEVLET|BİRLEŞİK AMERİKA|\bABD\b|AMERİKAN HÜKÜMET|AMERİKA MÜTTEHİT|MÜTTEHİT AMERİKA|AMERİKA HÜKÜMET'),
          ('AZ', r'AZERBAYCAN'), ('DD', r'DEMOKRATİK ALMAN'), ('DE', r'ALMANYA|\bALMAN\b'),
          ('SU', r'SOVYET|\bSSCB\b|ŞÛRALAR CUMHURİYETLERİ|ŞURALAR CUMHURİYETLERİ|ŞÜRALAR CUMHURİYETLERİ|FEDERATİF ŞÜRALAR|FEDERATİF ŞURALAR|RUS SOSYALİST'), ('BY', r'BELARUS|BEYAZ ?RUSYA'),
          ('RU', r'(?<!BEYAZ )RUSYA'), ('GB', r'İNGİLTERE|BİRLEŞİK KI?RALLIK|BÜYÜK BRİTANYA|İNGİLİZ'), ('IE', r'(?<!KUZEY )İRLANDA'), ('FR', r'FRANSA|FRANSIZ'),
          ('IT', r'İTALYA'), ('ES', r'İSPANYA'), ('PT', r'PORTEKİZ'), ('NL', r'HOLLANDA|NEDERLAND|FELEMENK'), ('BE', r'BELÇİKA'), ('LU', r'LÜKSEMBURG'), ('CH', r'İSVİÇRE'),
          ('AT', r'AVUSTURYA'), ('SE', r'İSVEÇ'), ('NO', r'NORVEÇ'), ('DK', r'DANİMARKA'), ('FI', r'FİNLANDİY[AE]'), ('IS', r'İZLANDA'), ('PL', r'POLONYA|LEHİSTAN'),
          ('CS', r'ÇEKOSLOVAK'), ('CZ', r'\bÇEK CUMHURİYETİ|\bÇEKYA'), ('SK', r'SLOVAK'), ('HU', r'MACAR'), ('RO', r'ROMANYA|ROMEN'), ('BG', r'BULGAR'),
          ('GR', r'YUNAN'), ('AL', r'ARNAVUT'), ('YU', r'YUGOSLAV|SIRP.?HIRVAT'), ('MK', r'MAKEDONYA'), ('RS', r'SIRBİSTAN|SIRP'), ('ME', r'KARADAĞ'), ('BA', r'BOSNA'),
          ('HR', r'HIRVAT'), ('SI', r'SLOVENYA'), ('XK', r'KOSOVA'), ('MD', r'MOLDOVA'), ('UA', r'UKRAYNA'), ('LT', r'LİTVANYA'), ('LV', r'LETONYA'),
          ('EE', r'ESTONYA'), ('MT', r'MALTA'), ('GE', r'GÜRCİSTAN'), ('AM', r'ERMENİSTAN'), ('KZ', r'KAZAKİSTAN|KAZAK\b'), ('KG', r'KIRGIZ'), ('UZ', r'ÖZBEK'),
          ('TM', r'TÜRKMENİSTAN'), ('TJ', r'TACİKİSTAN'), ('MN', r'MOĞOLİSTAN'), ('AF', r'AFGAN'), ('PK', r'PAKİSTAN'), ('IN', r'HİNDİSTAN'), ('BD', r'BANGLADEŞ'),
          ('LK', r'SRİ LANKA|SEYLAN'), ('NP', r'NEPAL'), ('CN', r'\bÇİN\b'), ('JP', r'JAPON'), ('KP', r'KORE DEMOKRATİK|KUZEY KORE'), ('KR', r'KORE'),
          ('VN', r'VİETNAM'), ('TH', r'TAYLAND'), ('MY', r'MALEZYA'), ('SG', r'SİNGAPUR'), ('ID', r'ENDONEZYA'), ('PH', r'FİLİPİN'), ('BN', r'BRUNEY'),
          ('KH', r'KAMBOÇYA'), ('LA', r'\bLAOS'), ('MM', r'MYANMAR|BURMA'), ('AU', r'AVUSTRALYA'), ('NZ', r'YENİ ZELANDA'), ('CA', r'KANADA'), ('MX', r'MEKSİKA'),
          ('CU', r'KÜBA'), ('BR', r'BREZİLYA'), ('AR', r'ARJANTİN'), ('CL', r'ŞİLİ'), ('CO', r'KOLOMBİYA'), ('VE', r'VENEZUELA'), ('PE', r'\bPERU'),
          ('EC', r'EKVADOR'), ('UY', r'URUGUAY'), ('PY', r'PARAGUAY'), ('BO', r'BOLİVYA'), ('PA', r'PANAMA'), ('CR', r'KOSTA RİKA'), ('GT', r'GUATEMALA'),
          ('DO', r'DOMİNİK'), ('HN', r'HONDURAS'), ('SV', r'EL SALVADOR'), ('NI', r'NİKARAGUA'), ('JM', r'JAMAİKA'), ('HT', r'HAİTİ'), ('TT', r'TRİNİDAD'),
          ('IR', r'\bİRAN|ACEMİSTAN'), ('IQ', r'\bIRAK'), ('SY', r'SURİYE'), ('LB', r'LÜBNAN'), ('IL', r'İSRAİL'), ('PS', r'FİLİSTİN'), ('JO', r'ÜRDÜN|ERDÜN'),
          ('SA', r'SUUDİ|HİCAZ|NECİT|NECİD'), ('KW', r'KUVEYT'), ('QA', r'KATAR'), ('AE', r'BİRLEŞİK ARAP EMİRLİK'), ('BH', r'BAHREYN'), ('OM', r'\bUMMAN|\bOMAN\b'), ('YE', r'YEMEN'),
          ('EG', r'MISIR|BİRLEŞİK ARAP CUMHURİYETİ'), ('LY', r'LİBYA'), ('TN', r'TUNUS'), ('DZ', r'CEZAYİR'), ('MA', r'\bFAS\b'), ('MR', r'MORİTANYA'),
          ('SS', r'GÜNEY SUDAN'), ('SD', r'\bSUDAN'), ('ET', r'ETİYOPYA|HABEŞ'), ('SO', r'SOMALİ'), ('DJ', r'CİBUTİ'), ('ER', r'ERİTRE'), ('KE', r'KENYA'), ('TZ', r'TANZANYA'),
          ('UG', r'UGANDA'), ('RW', r'RUANDA'), ('NG', r'NİJERYA'), ('NE', r'\bNİJER\b'), ('GH', r'\bGANA'), ('SN', r'SENEGAL'), ('ML', r'MALİ CUMHURİYETİ'),
          ('BF', r'BURKİNA'), ('CI', r'FİLDİŞİ'), ('GQ', r'EKVATOR GİNE'), ('GW', r'GİNE.?BİSSAU'), ('GN', r'\bGİNE\b'), ('SL', r'SİERRA'),
          ('LR', r'LİBERYA'), ('GM', r'GAMBİYA'), ('TG', r'\bTOGO'), ('BJ', r'BENİN'), ('CM', r'KAMERUN'), ('TD', r'\bÇAD\b'), ('GA', r'GABON'), ('CG', r'KONGO'),
          ('AO', r'ANGOLA'), ('ZM', r'ZAMBİYA'), ('ZW', r'ZİMBABVE'), ('MZ', r'MOZAMBİK'), ('MW', r'MALAVİ'), ('MG', r'MADAGASKAR'), ('NA', r'NAMİBYA'),
          ('ZA', r'GÜNEY AFRİKA'), ('BW', r'BOTSVANA'), ('MU', r'MORİTYUS'), ('SC', r'SEYŞEL'), ('KM', r'KOMOR'), ('MV', r'MALDİV'), ('VA', r'VATİKAN|PAPALIK'),
          ('MC', r'MONAKO'), ('SM', r'SAN MARİNO'), ('LI', r'LİHTENŞTAYN'), ('AD', r'ANDORRA'), ('FJ', r'FİJİ'), ('PG', r'PAPUA')]
c16, c16n, unmatched = collections.defaultdict(C), C(), []
ERA = lambda y: 'e1' if y < 1960 else 'e2' if y < 1980 else 'e3' if y < 2000 else 'e4'
for l in DATED:
    if l['cat'] != 'treaty':
        continue
    t = re.sub(r'TÜRKİYE CUMHURİYETİ|TÜRKİYE BÜYÜK MİLLET MECLİSİ|\bTÜRKİYE\b|TÜRK HÜKÜMETİ', ' ', l['U'])
    hits = []
    for k, rx in STATES:
        if re.search(rx, t):
            hits.append(k)
            t = re.sub(rx, ' ', t)  # so KUZEY KIBRIS is not counted again as KIBRIS, BEYAZ RUSYA not as RUSYA
    if 'GB' in hits and 'IE' in hits:
        hits.remove('IE')
    if len(set(hits)) > 3 or not hits:
        k = 'multi'
        c16['multi'][ERA(l['d'].year)] += 1; c16n['multi'] += 1
        if not hits and len(unmatched) < 400:
            unmatched.append(l['U'][:100])
    else:
        for k in set(hits):
            c16[k][ERA(l['d'].year)] += 1; c16n[k] += 1
OUT['c16'] = {'rows': [{'k': k, 'n': n, 'by': dict(c16[k])} for k, n in c16n.most_common()], 'laws': sum(1 for l in DATED if l['cat'] == 'treaty')}
print('c16', c16n.most_common(30), OUT['c16']['laws'])
print('   multi samples', [u for u in unmatched if re.search(r' İLE | ARASINDA', u)][:25])

# c17: what metropolitan councils decide (titled decisions of Bursa, Mersin and Tekirdağ)
LOC = [('property', r'taşınmaz|satış|satılması|kiralan|kiraya|kiralama|tahsis|devir|devri|takas|irtifak|kamulaştır|bağış|hibe|trampa|ecrimisil|işletme hakkı|mülkiyet'),
       ('zoning', r'\bimar\b|plan\w*|\bnip\b|\buip\b|ölçekli|parselasyon|\bada\b|parsel|koruma amaçlı|yer seçimi'),
       ('budget', r'bütçe|ödenek|aktarım|borçlanma|kredi|faaliyet raporu|denetim komisyon|kesin hesap|\bmali\b|harcama|gelir'),
       ('fees', r'ücret|tarife|fiyat|bilet|abonman'),
       ('transport', r'ulaşım|toplu taşıma|trafik|otopark|durak|raylı|metro|taksi|servis|\bhat\b|güzergah|\byol\b|cadde|sokak|kavşak|ukome'),
       ('naming', r'\bisim|adının verilmesi|ad verilmesi|adı verilmesi|isimlendirme|isim verilmesi'),
       ('org', r'şirket|personel|kadro|sözleşmeli|işçi|memur|meclis üye|komisyon|encümen|yönetmelik|yönerge|görev, yetki|teşkilat|daire başkanlığı|genel kurul|temsil|yetki verilmesi|maaş|mesai|vize'),
       ('social', r'sosyal|yardım|engelli|şehit|gazi|öğrenci|kreş|aşevi|spor|kültür|eğitim|sağlık|kadın|çocuk|yaşlı|kardeş şehir|protokol|ödül')]
c17 = collections.defaultdict(C)
c17ex = collections.defaultdict(list)
for c in LOG:
    m = re.match(r'^local/(bursa|mersin|tekirdag)/buyuksehir', c['path'])
    if not m:
        continue
    s = c['s']
    if re.search(r'council decision \d|official text|as enacted|Karar No', s):
        continue
    t = low(re.sub(r'^\d+\s*-\s*MEC\.KAR\.\s*', '', s))
    k = next((k for k, rx in LOC if re.search(rx, t)), 'other')
    c17[m.group(1)][k] += 1
    c17[m.group(1)]['_years_' + (c['inf'] or c['ad'])[:4]] += 1
    if len(c17ex[(m.group(1), k)]) < 4:
        c17ex[(m.group(1), k)].append(s[:80])
OUT['c17'] = {k: dict(v) for k, v in c17.items()}
OUT['c17_total'] = {k: sum(1 for c in LOG if c['path'].startswith('local/%s/buyuksehir' % k)) for k in ('bursa', 'mersin', 'tekirdag', 'ankara')}
print('c17', OUT['c17'], OUT['c17_total'])
for k, v in sorted(c17ex.items()):
    if k[1] in ('other', 'zoning', 'property'):
        print('   ', k, v)

# ------------------------------------------------------------------ the Constitutional Court
# c18: decisions recorded as changing a law in force (the publisher's in-force tables)
c18 = {}
for r in IFL:
    a = ws(r['amending'])
    if not re.search(r'Anayasa Mah', a):
        continue
    k = re.search(r'K(?:arar)?\.?\s*(?:No\.?)?\s*:*\s*(\d{4})\s*/\s*(\d+)', a)
    d = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', a)
    key = (k.group(1) + '/' + k.group(2)) if k else a
    dd = date(int(d.group(3)), int(d.group(2)), int(d.group(1))) if d else None
    e = c18.setdefault(key, {'k': key, 'd': dd.isoformat() if dd else None, 'y': dd.year if dd else int(k.group(1)) if k else None, 'acts': set(), 'rows': 0, 'deferred': False, 'inf': []})
    e['acts'].add(r['act']); e['rows'] += 1
    if re.search(r'(ay|yıl) sonra', low(r['in_force_as_printed'])):
        e['deferred'] = True
    if r['in_force']:
        e['inf'].append(r['in_force'])
for e in c18.values():
    e['acts'] = sorted(e['acts'])
    e['lag'] = (ISO(min(e['inf'])) - ISO(e['d'])).days if e['inf'] and e['d'] else None
acts18 = C(a for e in c18.values() for a in e['acts'])
OUT['c18'] = {'dec': [{'k': e['k'], 'd': e['d'], 'y': e['y'], 'n': len(e['acts']), 'def': e['deferred'], 'lag': e['lag']} for e in c18.values()],
              'acts': [[a, n, *act_title(a)] for a, n in acts18.most_common(12)], 'rows': sum(e['rows'] for e in c18.values())}
print('c18', len(c18), C(e['y'] for e in c18.values()), sum(1 for e in c18.values() if e['deferred']), OUT['c18']['acts'][:6])

# c19, c20: individual applications (data/aym-individual-<year>.csv)
IND = []
for f in sorted(glob.glob(os.path.join(D_, 'aym-individual-*.csv'))):
    with open(f, encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            app = (r.get('application_number') or r.get('application_no') or '').strip()
            oc = (r.get('outcome') or r.get('result') or '').strip()
            unit = (r.get('deciding_unit') or r.get('decision_making_unit') or '').strip()
            if r.get('metadata_json'):
                try:
                    mj = json.loads(r['metadata_json'])
                    oc = oc or (mj.get('kararTuruBasvuruSonucuLabel') or '').strip()
                    unit = unit or (mj.get('kararVerenBirimLabel') or '').strip()
                except ValueError:
                    pass
            IND.append({'app': app, 'd': r.get('decision_date', ''), 'oc': oc, 'unit': unit})
OC = {'Esas (İhlal)': 'viol', 'Esas (İhlal Olmadığı)': 'noviol', 'Kabul Edilemezlik vd.': 'inadm'}
c19 = collections.defaultdict(C)
c20 = collections.defaultdict(list)
maxno = collections.defaultdict(int)
for r in IND:
    if not r['d']:
        continue
    y = int(r['d'][:4])
    c19[y][OC.get(r['oc'], 'unknown')] += 1
    m = re.match(r'^(\d{4})/(\d+)', r['app'])
    if m:
        c20[y].append(y - int(m.group(1)))
        maxno[int(m.group(1))] = max(maxno[int(m.group(1))], int(m.group(2)))
OUT['c19'] = [{'y': y, **c19[y]} for y in sorted(c19)]
OUT['c20'] = [{'y': y, 'n': len(v), 'b': [sum(1 for x in v if x <= 1), sum(1 for x in v if x == 2), sum(1 for x in v if x == 3), sum(1 for x in v if x == 4), sum(1 for x in v if x >= 5)],
               'med': statistics.median(v), 'mean': round(sum(v) / len(v), 2)} for y, v in sorted(c20.items())]
OUT['c20_maxno'] = sorted(maxno.items())
PROFILE['aym_individual'] = len(IND)
print('c19', OUT['c19'])
print('c20', [(r['y'], r['n'], r['b'], r['med']) for r in OUT['c20']])

# ------------------------------------------------------------------ profile
PROFILE.update({
    'commits': len(LOG), 'head': os.environ.get('HEAD_SHA', ''), 'built': date.today().isoformat(),
    'last_commit_date': max(c['ad'] for c in LOG), 'minutes': len(MIN), 'terms': len(TERMS),
    'rg_first': min(i['d'] for i in RG), 'rg_last': RGLAST, 'law_last': LAST_LAW.isoformat(),
    'constitution_files': len(arts),
    'councils': sum(OUT['c17_total'].values()),
})
json.dump({'charts': OUT, 'profile': PROFILE}, open(os.path.join(B, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), default=list)
print('profile', PROFILE)
