"""Write this repository's own WATCHING.md, FRESHNESS.md and monitoring/README.md (Turkish) and their .en.md copies.

    python monitoring/make_pages.py [--ref origin/main] [--today YYYY-MM-DD] [--github lexifina/turkey-law] [--log-ref origin/status]

Everything is read from git. Each commit's Source trailer names the official source it came from (commits without one
are placed by their folder), and its In-force trailer (or author date) is the day the text applies or the decision was
given. In this repository a commit's committer date is that same day, not the day it was published, so the day each
commit reached `main` comes from the landing log, monitoring/landed.tsv: one row per push (when, before, after).
--github REPO adds GitHub's own push log of REPO's main (`gh api repos/REPO/activity`, needs the gh CLI and read access),
and every run adds a row for the ref it reads, so a fork that runs this every 6 hours keeps its own log.
--log-ref reads the log from another branch first (the fork workflow keeps it on `status`).
global-law's row for this corpus is read from global-law's data/freshness.tsv (skipped when offline).
Standard library only.
"""
import argparse, collections, csv, datetime as dt, io, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument('--ref', default=None)
ap.add_argument('--today', default=None)
ap.add_argument('--github', default=None, help='owner/repo whose push log (GitHub activity API) to add to monitoring/landed.tsv')
ap.add_argument('--log-ref', default=None, help='branch to read monitoring/landed.tsv from before the working tree (e.g. origin/status)')
a = ap.parse_args()
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def git(*args, ok=False, data=None):
    r = subprocess.run(['git', '-C', ROOT, *args], capture_output=True, input=data)
    if r.returncode and not ok:
        raise subprocess.CalledProcessError(r.returncode, args, r.stdout, r.stderr)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else ''


ref = a.ref or ('origin/main' if subprocess.run(['git', '-C', ROOT, 'rev-parse', '-q', '--verify', 'origin/main'], capture_output=True).returncode == 0 else 'HEAD')
head = git('rev-parse', ref).strip()
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = dt.date.fromisoformat(a.today) if a.today else NOW.date()
GL = 'https://github.com/lexifina/global-law/blob/main'
GLT = 'https://github.com/lexifina/global-law/tree/main'
REPO = 'lexifina/turkey-law'
CORPUS = 'turkey/national/acts'

# ------------------------------------------------------------------ sources
# (domain, key, Turkish name, English name, (what is read: Turkish, English), level, address shown)
SRC = [
    ('mevzuat.gov.tr', 'mbs', 'Mevzuat Bilgi Sistemi (T.C. Cumhurbaşkanlığı)', 'Mevzuat Bilgi Sistemi (the Presidency\'s legislation database)',
     ('her mevzuat türünün arama tablosu (MevzuatDatatable), her düzenlemenin metin sayfası ve kanunların önceki metinleri',
      'the search table of each type of act (MevzuatDatatable), each act\'s text page and the earlier texts of laws'), 'national', 'https://www.mevzuat.gov.tr'),
    ('resmigazete.gov.tr', 'rg', 'Resmî Gazete', 'Resmî Gazete (Official Gazette)',
     ('her günün sayı fihristi (eskiler/YYYY/MM/YYYYMMDD.htm)', 'each day\'s issue index (eskiler/YYYY/MM/YYYYMMDD.htm)'), 'national', 'https://www.resmigazete.gov.tr'),
    ('tbmm.gov.tr', 'tbmm', 'Türkiye Büyük Millet Meclisi', 'Grand National Assembly (TBMM)',
     ('Meclis kararları listesi ve karar metinleri', 'the list of Assembly decisions and their texts'), 'national', 'https://www.tbmm.gov.tr'),
    ('anayasa.gov.tr', 'aym', 'Anayasa Mahkemesi', 'Constitutional Court (Anayasa Mahkemesi)',
     ('karar bilgi bankalarının arama API\'si (norm denetimi, bireysel başvuru, siyasi parti, Yüce Divan, yasama dokunulmazlığı)',
      'the decision databases\' search API (norm review, individual applications, political parties, Yüce Divan, immunity)'), 'courts', 'https://normkararlarbilgibankasi.anayasa.gov.tr'),
    ('uyusmazlik.gov.tr', 'um', 'Uyuşmazlık Mahkemesi', 'Court of Jurisdictional Disputes (Uyuşmazlık Mahkemesi)',
     ('karar arama sayfası ve karar PDF\'leri', 'the decision search and the decisions\' PDFs'), 'courts', 'https://kararlar.uyusmazlik.gov.tr'),
    ('rekabet.gov.tr', 'rk', 'Rekabet Kurumu', 'Competition Authority (Rekabet Kurumu)',
     ('kararlar listesi (/tr/Kararlar) ve her kararın sayfası', 'the decisions list (/tr/Kararlar) and each decision\'s page'), 'courts', 'https://www.rekabet.gov.tr'),
    ('sigortatahkim.org', 'stk', 'Sigorta Tahkim Komisyonu', 'Insurance Arbitration Commission (Sigorta Tahkim Komisyonu)',
     ('Hakem Karar Dergisi sayıları', 'the issues of the arbitral awards journal (Hakem Karar Dergisi)'), 'courts', 'https://www.sigortatahkim.org'),
    ('rtuk.gov.tr', 'rtuk', 'Radyo ve Televizyon Üst Kurulu', 'Radio and Television Supreme Council (RTÜK)',
     ('Üst Kurul kararları', 'the Council\'s decisions'), 'records', 'https://www.rtuk.gov.tr'),
    ('ysk.gov.tr', 'ysk', 'Yüksek Seçim Kurulu', 'Supreme Election Council (YSK)',
     ('kararların tam listesi (doc/karar/kararlar.txt) ve karar PDF\'leri', 'the full list of decisions (doc/karar/kararlar.txt) and their PDFs'), 'records', 'https://www.ysk.gov.tr'),
    ('sayistay.gov.tr', 'say', 'Sayıştay', 'Court of Accounts (Sayıştay)',
     ('Genel Kurul, Temyiz Kurulu ve daire kararları listeleri', 'the lists of decisions of the General Assembly, the Appeals Board and the chambers'), 'records', 'https://www.sayistay.gov.tr'),
    ('ankara.bel.tr', 'abb', 'Ankara Büyükşehir Belediyesi', 'Ankara Metropolitan Municipality',
     ('Meclis kararları listesi (/meclis/kararlar) ve karar dosyaları', 'the council decisions list (/meclis/kararlar) and the decision files'), 'local', 'https://www.ankara.bel.tr'),
    ('bursa.bel.tr', 'bbb', 'Bursa Büyükşehir Belediyesi', 'Bursa Metropolitan Municipality',
     ('Meclis kararları ve karar PDF\'leri', 'the council decisions and their PDFs'), 'local', 'https://www.bursa.bel.tr'),
]
SHORT = {'mbs': 'Mevzuat Bilgi Sistemi', 'rg': 'Resmî Gazete', 'tbmm': 'TBMM', 'aym': 'Anayasa Mahkemesi', 'um': 'Uyuşmazlık Mahkemesi',
         'rk': 'Rekabet Kurumu', 'stk': 'Sigorta Tahkim Komisyonu', 'rtuk': 'RTÜK', 'ysk': 'YSK', 'say': 'Sayıştay',
         'abb': 'Ankara Büyükşehir', 'bbb': 'Bursa Büyükşehir'}
# commits with no Source trailer: the folder of their first file says where they came from
FOLDER_SRC = {'kanun': 'mbs', 'khk': 'mbs', 'cbk': 'mbs', 'osmanli': 'mbs', 'law': 'mbs', 'decree-law': 'mbs', 'presidential-decree': 'mbs',
              'ottoman': 'mbs', 'bylaw': 'mbs', 'regulation': 'mbs', 'presidential-circular': 'mbs', 'communique': 'mbs', 'presidential-decision': 'mbs',
              'parliament-decision': 'tbmm', 'election': 'ysk', 'audit': 'say'}
THRESH = {'national': 7, 'local': 30, 'courts': 30, 'records': 30}
NOTES = {}
PAUSED = {}  # source key -> (Turkish, English) reason, when a source is deliberately not re-read
NOT_WATCHED = [
    ('Yargıtay karar arama (karararama.yargitay.gov.tr)', 'Yargıtay decision search (karararama.yargitay.gov.tr)',
     'bağlantı zaman aşımına uğradı (2026-11-13)', 'the connection timed out (2026-11-13)'),
    ('Danıştay karar arama ve UYAP Emsal', 'Danıştay decision search and UYAP Emsal',
     'her aramada reCAPTCHA isteniyor', 'every search asks for a reCAPTCHA'),
    ('Kamu Denetçiliği Kurumu kararları (kararlar.ombudsman.gov.tr)', 'Ombudsman decisions (kararlar.ombudsman.gov.tr)',
     'bağlantıyı reddetti (2026-11-13)', 'refused the connection (2026-11-13)'),
]
NON_RECORD_KINDS = {'documentation', 'layout', 'metadata'}


def src_of(url):
    host = re.sub(r'^https?://', '', url.strip()).split('/')[0].lower()
    for dom, *rest in SRC:
        if host == dom or host.endswith('.' + dom):
            return rest[0]
    return None


def x(k):
    return next(s for s in SRC if s[1] == k)


# ------------------------------------------------------------------ the landing log
LOG = os.path.join(HERE, 'landed.tsv')
LOG_FIELDS = ['when', 'before', 'after', 'how']


def read_log():
    text = ''
    if a.log_ref:
        text = git('show', f'{a.log_ref}:monitoring/landed.tsv', ok=True)
    if not text and os.path.exists(LOG):
        with open(LOG, encoding='utf-8') as f:
            text = f.read()
    return [r for r in csv.DictReader(io.StringIO(text), delimiter='\t') if r.get('after')]


def github_log(repo):
    try:
        out = subprocess.run(['gh', 'api', '--paginate', f'repos/{repo}/activity?ref=refs/heads/main&per_page=100',
                              '-q', '.[] | [.timestamp, .before, .after, .activity_type] | @tsv'],
                             capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        print('GitHub push log not read:', e, file=sys.stderr)
        return []
    if out.returncode:
        print('GitHub push log not read:', out.stderr.decode('utf-8', 'replace').strip()[:200], file=sys.stderr)
        return []
    rows = []
    for line in out.stdout.decode('utf-8').splitlines():
        when, before, after, kind = (line.split('\t') + ['', '', '', ''])[:4]
        if after and not after.startswith('0000000'):
            rows.append({'when': when, 'before': before, 'after': after, 'how': f'github {kind}'})
    return rows


log = read_log()
if a.github:
    known = {r['after'] for r in log}
    log += [r for r in github_log(a.github) if r['after'] not in known]
log.sort(key=lambda r: r['when'])
exists = set()
if log:
    out = git('cat-file', '--batch-check', data=''.join(f"{s}^{{commit}}\n" for r in log for s in (r['before'], r['after']) if s).encode())
    exists = {line.split()[0] for line in out.splitlines() if not line.endswith('missing')}
if not any(r['after'] == head for r in log):
    base = next((r['after'] for r in reversed(log) if r['after'] in exists and
                 subprocess.run(['git', '-C', ROOT, 'merge-base', '--is-ancestor', r['after'], head], capture_output=True).returncode == 0), '')
    log.append({'when': NOW.strftime('%Y-%m-%dT%H:%M:%SZ'), 'before': base, 'after': head, 'how': 'seen by make_pages.py'})
    exists.add(head)
landed = {}
for r in log:
    if r['after'] not in exists:
        continue
    rng = [r['after']] + (['^' + r['before']] if r['before'] in exists else [])
    for h in git('rev-list', *rng).split():
        landed.setdefault(h, r['when'])

# ------------------------------------------------------------------ read git
SEP = '\x1f'
fmt = SEP.join(['%H', '%aI', '%cI', '%(trailers:key=Kind,valueonly,separator=%x1e)', '%(trailers:key=Source,valueonly,separator=%x1e)',
                '%(trailers:key=In-force,valueonly,separator=%x1e)', '%s'])
S = {k: {'n': 0, 'newest': None, 'future': 0, 'last': None, 'pages': collections.Counter(), 'folders': collections.Counter()} for _, k, *_ in SRC}
commits = []
cur = None
for line in git('log', ref, '--format=@@' + fmt, '--name-only', '--no-renames').split('\n'):
    if line.startswith('@@'):
        h, ad, cd, kind, srcs, inforce, subj = line[2:].split(SEP)
        cur = {'h': h, 'ad': ad[:10], 'cd': cd, 'kind': kind.strip(), 'src': [s.strip() for s in srcs.split('\x1e') if s.strip()],
               'inforce': inforce.split('\x1e')[0].strip(), 'files': []}
        commits.append(cur)
    elif line.strip() and cur is not None:
        cur['files'].append(line.strip())


def folder(f):
    p = f.split('/')
    depth = {'case-law': 2, 'decision': 2, 'local': 3, 'election': 2, 'audit': 2, 'data': 1}.get(p[0], 1)
    if p[0] == 'case-law' and len(p) > 3 and p[1] == 'constitutional-court':
        depth = 3
    return '/'.join(p[:depth]) + '/' if len(p) > depth else (p[0] + '/' if len(p) > 1 else p[0])


for c in commits:
    k = next((src_of(s) for s in c['src'] if src_of(s)), None)
    if not k and c['files']:
        k = FOLDER_SRC.get(c['files'][0].split('/')[0])
    c['source'] = k
    w = landed.get(c['h'])
    c['landed'] = dt.datetime.fromisoformat(w.replace('Z', '+00:00')) if w else dt.datetime.fromisoformat(c['cd']).astimezone(dt.timezone.utc)
    if not k:
        continue
    s = S[k]
    s['n'] += 1
    if c['kind'] not in NON_RECORD_KINDS:
        try:
            d = dt.date.fromisoformat(c['inforce'][:10]) if re.match(r'\d{4}-\d\d-\d\d', c['inforce']) else dt.date.fromisoformat(c['ad'])
        except ValueError:
            d = dt.date.fromisoformat(c['ad'])
        if d > TODAY:
            s['future'] += 1
        elif not s['newest'] or d > s['newest']:
            s['newest'] = d
    ld = c['landed'].date()
    if not s['last'] or ld > s['last']:
        s['last'] = ld
    for u in c['src']:
        if src_of(u) == k:
            s['pages'][u] += 1
    for f in c['files'][:1]:
        if not f.startswith(('README', 'LICENSE', 'PLAN', 'FRESHNESS', 'WATCHING', 'monitoring/')):
            s['folders'][folder(f)] += 1
unlogged = sum(1 for c in commits if c['h'] not in landed)


# index tables in data/: the Resmî Gazete daily index and the Constitutional Court's individual-application index
def tables(pattern):
    rx = re.compile(pattern)
    names = [p for p in git('ls-tree', '-r', '--name-only', ref, 'data/').splitlines() if rx.search(p)]
    if not names:
        return {}
    res, pos = {}, 0
    raw = subprocess.run(['git', '-C', ROOT, 'cat-file', '--batch'], input=''.join(f'{ref}:{n}\n' for n in names).encode('utf-8'), capture_output=True).stdout
    for n in names:
        e = raw.index(b'\n', pos)
        size = int(raw[pos:e].split()[2])
        res[n] = list(csv.DictReader(io.StringIO(raw[e + 1:e + 1 + size].decode('utf-8-sig', 'replace'))))
        pos = e + 1 + size + 1
    return res


def day(v):
    m = re.search(r'(\d{4})-(\d\d)-(\d\d)|(\d\d)[./](\d\d)[./](\d{4})', v or '')
    if not m:
        return None
    try:
        return dt.date(int(m[1]), int(m[2]), int(m[3])) if m[1] else dt.date(int(m[6]), int(m[5]), int(m[4]))
    except ValueError:
        return None


rg_days = {d for rows in tables(r'^data/(rg-index/.*/)?rg-[^/]*\.csv$|^data/rg-index/[^/]+/issues\.csv$').values()
           for r in rows if r.get('issue') and (d := day(r.get('date'))) and d.year >= 2001 and d <= TODAY}
aym_rows = [r for rows in tables(r'^data/aym-individual-\d{4}\.csv$').values() for r in rows]
aym_days = [d for r in aym_rows if (d := day(r.get('decision_date'))) and d <= TODAY]
if rg_days and (not S['rg']['newest'] or max(rg_days) > S['rg']['newest']):
    S['rg']['newest'] = max(rg_days)
if aym_days and (not S['aym']['newest'] or max(aym_days) > S['aym']['newest']):
    S['aym']['newest'] = max(aym_days)

# global-law's row for this corpus
gl = None
try:
    with urllib.request.urlopen('https://raw.githubusercontent.com/lexifina/global-law/main/data/freshness.tsv', timeout=30) as resp:
        for r in csv.DictReader(io.StringIO(resp.read().decode('utf-8')), delimiter='\t'):
            if r['path'] == CORPUS:
                gl = r
except Exception as e:
    print('global-law freshness not read:', e, file=sys.stderr)
behind = None
if gl and gl.get('pinned') and subprocess.run(['git', '-C', ROOT, 'cat-file', '-e', gl['pinned'] + '^{commit}'], capture_output=True).returncode == 0:
    behind = int(git('rev-list', '--count', f'{gl["pinned"]}..{ref}').strip())


# ------------------------------------------------------------------ helpers
def d_tr(d): return f'{d.day:02d}.{d.month:02d}.{d.year}' if d else '–'
def d_en(d): return d.isoformat() if d else '–'
def num(n, lang): return f'{n:,}'.replace(',', '.' if lang == 'tr' else ',')


def status(k, s, lang):
    tr = lang == 'tr'
    if k in PAUSED: return 'duraklatıldı' if tr else 'paused'
    if not s['last']: return 'hiç okunmadı' if tr else 'never read'
    ok = (TODAY - s['last']).days <= THRESH[x(k)[5]]
    return ('güncel' if ok else 'gecikmiş') if tr else ('current' if ok else 'stale')


def name(k, lang): return x(k)[2] if lang == 'tr' else x(k)[3]
def link(k): return x(k)[6]
def what(k, lang): return x(k)[4][0 if lang == 'tr' else 1]


def folders(k):
    f = S[k]['folders']
    return ', '.join(f'`{p}`' for p, _ in f.most_common(4)) + (' …' if len(f) > 4 else '')


ORDER = [s[1] for s in SRC if S[s[1]]['n']]
def other(lang, base): return f'[English]({base}.en.md)' if lang == 'tr' else f'[Türkçe]({base}.md)'


last_commit = git('log', '-1', '--format=%H%x1f%s', ref).strip().split('\x1f')
last_landed = next(c['landed'] for c in commits if c['h'] == last_commit[0])


def window(days):
    cut = NOW - dt.timedelta(days=days)
    cnt = collections.Counter()
    for c in commits:
        if c['landed'] >= cut:
            cnt[c['source'] or ('docs' if c['kind'] in NON_RECORD_KINDS or not c['kind'] else 'other')] += 1
    return cnt


LOG_NOTE = {
    'tr': 'Bu depoda bir commit\'in tarihi, metnin yürürlüğe girdiği ya da kararın verildiği gündür; yayımlandığı gün değildir. Her commit\'in `main` dalına ulaştığı gün [`monitoring/landed.tsv`](monitoring/landed.tsv) dosyasındaki iniş kaydından gelir (GitHub\'ın push kaydı ve `make_pages.py`\'nin her çalışması).',
    'en': 'In this repository a commit\'s date is the day its text took effect or the decision was given, not the day it was published. The day each commit reached `main` comes from the landing log, [`monitoring/landed.tsv`](monitoring/landed.tsv) (GitHub\'s push log and every run of `make_pages.py`).',
}


# ------------------------------------------------------------------ WATCHING
def watching(lang):
    tr = lang == 'tr'
    D = d_tr if tr else d_en
    o = ['# Kaynakların izlenmesi: Türkiye için neler izleniyor' if tr else '# Watching the sources: what is watched for Türkiye', '', other(lang, 'WATCHING'), '']
    o.append((f'global-law\'un her ülkenin kaynaklarını nasıl izlediği (değişiklik dedektörleri, günlük yoklama, bir isabetin ne anlama geldiği): [global-law WATCHING.md]({GL}/WATCHING.md). '
              'Bu sayfa aynı şeyin yalnızca Türkiye için olanıdır: bu deponun metin aldığı her resmî kaynak, yeni bir şey olup olmadığını görmek için onda neyin okunduğu ve en son ne zaman okunduğu.')
             if tr else
             (f'How global-law watches every country\'s sources (change detectors, the daily poll, what a hit means): [global-law WATCHING.md]({GL}/WATCHING.md). '
              'This page is the same thing for Türkiye only: every official source this repository takes text from, what is read on it to see whether anything is new, and when it was last read.'))
    o.append('')
    o.append((f'{D(TODAY)} tarihinde git geçmişinden (`{head[:10]}`) oluşturuldu: her commit kaynağını `Source:` satırında adlandırır ve "en son okunma", bu deponun o kaynaktan en son bir şey yayımladığı gündür. ' + LOG_NOTE['tr'])
             if tr else
             (f'Built on {D(TODAY)} from the git history (`{head[:10]}`): each commit names its source in its `Source:` line, and "last read" is the day this repository last published something from that source. ' + LOG_NOTE['en']))
    o.append('')
    o.append('| Kaynak | Neler okunuyor | Klasörler | Commit | En son okunma | Durum |' if tr else '| Source | What is read | Folders | Commits | Last read | State |')
    o.append('| --- | --- | --- | ---: | --- | --- |')
    for k in ORDER:
        s = S[k]
        o.append(f'| [{name(k, lang)}]({link(k)}) | {what(k, lang)} | {folders(k)} | {num(s["n"], lang)} | {D(s["last"])} | {status(k, s, lang)} |')
    o.append('')
    if tr:
        o.append(f'Ayrıca [`data/`](data/) klasöründe Resmî Gazete\'nin günlük fihristi ({num(len(rg_days), lang)} gün, {D(min(rg_days)) if rg_days else "–"} ile {D(max(rg_days)) if rg_days else "–"} arası) ve Anayasa Mahkemesinin bireysel başvuru kararları dizini ({num(len(aym_rows), lang)} satır, en yenisi {D(max(aym_days)) if aym_days else "–"}) bulunur; her satır resmî adresini taşır.')
    else:
        o.append(f'In addition, [`data/`](data/) holds the Resmî Gazete\'s daily index ({num(len(rg_days), lang)} days, {D(min(rg_days)) if rg_days else "–"} to {D(max(rg_days)) if rg_days else "–"}) and the Constitutional Court\'s index of individual-application decisions ({num(len(aym_rows), lang)} rows, the newest {D(max(aym_days)) if aym_days else "–"}); every row carries its official address.')
    o.append('')
    o.append('## İzlenmeyenler' if tr else '## Not watched')
    o.append('')
    for ntr, nen, wtr, wen in NOT_WATCHED:
        o.append(f'- **{ntr if tr else nen}**: {wtr if tr else wen}.')
    o.append('')
    o.append(('Bunlar aşılmaz: engel kalkana kadar bu kaynaklardan hiçbir şey alınmaz (bkz. [PLAN.md](PLAN.md)).') if tr else
             ('These are never worked around: nothing is taken from these sources until the block is gone (see [PLAN.md](PLAN.md)).'))
    o.append('')
    o.append('## Nasıl izleniyor' if tr else '## How it is watched')
    o.append('')
    if tr:
        o += ['- **Türkiye için henüz otomatik günlük izleme yok.** global-law\'un değişiklik dedektörleri hazır, ancak açılmadı. Her kaynak, bu depodaki şeridi çalıştığında yeniden okunur; yukarıdaki tarih bunun en son ne zaman olduğunu gösterir.',
              '- **Görgü kuralları.** Her kaynak robots.txt dosyasına uyularak ve istekler arasında beklenerek okunur; metin her zaman resmî kaynaktan gelir, hiçbir zaman bir dedektörden gelmez.',
              '- **Bir isabet.** Bir kaynak yeni bir şey yayımladığında, bu, yürürlüğe girdiği ya da verildiği günle tarihlenmiş yeni bir commit olur; global-law onu bir sonraki geçişinde alır ([monitoring/](monitoring/)).']
    else:
        o += ['- **There is no automatic daily watch for Türkiye yet.** global-law\'s change detectors are built but not switched on. Each source is re-read when its lane in this repository runs, and the date above shows when that last happened.',
              '- **Manners.** Every source is read within its robots.txt, with pauses between requests; text always comes from the official source, never from a detector.',
              '- **A hit.** When a source publishes something new, it becomes a new commit dated the day it applies or was given; global-law picks it up on its next pass ([monitoring/](monitoring/README.en.md)).']
    o.append('')
    o.append(('Yalnızca resmî yayın (Resmî Gazete, mahkemelerin ve kurumların kendi siteleri) hukuken bağlayıcıdır.') if tr else
             ('Only the official publication (the Resmî Gazete, the courts\' and bodies\' own sites) has legal force.'))
    o.append('')
    return '\n'.join(o)


# ------------------------------------------------------------------ FRESHNESS
def freshness(lang):
    tr = lang == 'tr'
    D = d_tr if tr else d_en
    o = ['# Güncellik: bugün de doğru mu?' if tr else '# Freshness: is it true right now?', '', other(lang, 'FRESHNESS'), '']
    o.append((f'global-law\'un her derlemin güncelliğini nasıl ölçtüğü (durumlar, 7 ve 30 günlük eşikler, `freshness.py` aracı): [global-law FRESHNESS.md]({GL}/FRESHNESS.md). '
              'Burada aynı ölçü Türkiye için, kaynak kaynak verilir.') if tr else
             (f'How global-law measures freshness for every corpus (the statuses, the 7- and 30-day thresholds, the `freshness.py` tool): [global-law FRESHNESS.md]({GL}/FRESHNESS.md). '
              'Here is the same measure for Türkiye, source by source.'))
    o.append('')
    o.append('## global-law onu nasıl görüyor' if tr else '## How global-law sees it')
    o.append('')
    if gl:
        lv = dt.date.fromisoformat(gl['last_verified']) if gl.get('last_verified') else None
        o.append('| Derlem | Durum | Son denetim | Yöntem | global-law\'daki commit | Buradaki daha yeni commit |' if tr else '| Corpus | Status | Last checked | Method | Commit pinned in global-law | Newer commits here |')
        o.append('| --- | --- | --- | --- | --- | ---: |')
        o.append(f'| `{CORPUS}` | `{gl["status"]}` | {D(lv)} | `{gl["method"]}` | `{gl["pinned"][:10]}` | {num(behind, lang) if behind is not None else "–"} |')
        o.append('')
        o.append((f'`{gl["status"]}`: ulusal mevzuat için eşik, son denetimden bu yana 7 gündür. global-law sabitlenmiş commit\'ten daha yeni olanları bir sonraki geçişinde alır; o zamana kadar onları burada okuyun.') if tr else
                 (f'`{gl["status"]}`: the threshold for national law is 7 days since the last check. global-law takes commits newer than the pinned one on its next pass; until then, read them here.'))
    else:
        o.append(f'global-law\'un satırı bu sayfa oluşturulurken okunamadı; bkz. [data/freshness.tsv]({GL}/data/freshness.tsv).' if tr else
                 f'global-law\'s row could not be read when this page was built; see [data/freshness.tsv]({GL}/data/freshness.tsv).')
    o.append('')
    o.append('## Kaynak kaynak' if tr else '## Source by source')
    o.append('')
    o.append(('"En yeni kayıt", gelecekte olmayan en geç yürürlük ya da karar günüdür (Resmî Gazete için fihristteki en son sayı); "en son okunma", bu deponun kaynaktan en son bir şey yayımladığı gündür. Eşik: ulusal mevzuat için 7 gün, mahkeme ve kurul kararları, yerel düzenlemeler ve diğer kayıtlar için 30 gün.') if tr else
             ('"Newest record" is the latest day of effect or decision that is not in the future (for the Resmî Gazete, the last issue in the index); "last read" is the day this repository last published something from the source. Threshold: 7 days for national law, 30 for court and board decisions, local acts and other records.'))
    o.append('')
    o.append('| Kaynak | Commit | En yeni kayıt | En son okunma | Geçen gün | Durum | Not |' if tr else '| Source | Commits | Newest record | Last read | Days since | State | Note |')
    o.append('| --- | ---: | --- | --- | ---: | --- | --- |')
    for k in ORDER:
        s = S[k]
        age = (TODAY - s['last']).days if s['last'] else None
        note = PAUSED[k][0 if tr else 1] if k in PAUSED else (NOTES[k][0 if tr else 1] if k in NOTES else '')
        if s['future']:
            note = (note + '; ' if note else '') + (f'{num(s["future"], lang)} tanesi gelecekte yürürlüğe giriyor' if tr else f'{num(s["future"], lang)} dated in the future')
        o.append(f'| {name(k, lang)} | {num(s["n"], lang)} | {D(s["newest"])} | {D(s["last"])} | {age if age is not None else "–"} | {status(k, s, lang)} | {note} |')
    o.append('')
    if unlogged:
        o.append((f'{num(unlogged, lang)} commit iniş kaydında yok; onlar için commit tarihi kullanıldı.') if tr else
                 (f'{num(unlogged, lang)} commits are not in the landing log; their commit date was used.'))
        o.append('')
    o.append('## Kendiniz denetleyin' if tr else '## Check it yourself')
    o.append('')
    o.append('```')
    o.append('git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- law/    ' + ('# yayımlanan son kanun commit\'i ve yürürlük günü' if tr else '# the last law commit published, and the day it applies'))
    o.append('git log -1 --format="%h %(trailers:key=In-force,valueonly,separator=) %s" -- case-law/constitutional-court/norm/    ' + ('# Anayasa Mahkemesinin yayımlanan son norm denetimi kararı' if tr else '# the last norm-review decision published'))
    o.append('tail -n 3 monitoring/landed.tsv    ' + ('# main dalına son push\'lar' if tr else '# the last pushes to main'))
    o.append('```')
    o.append('')
    o.append(('İlgilendiğiniz tarih son denetimden sonraysa metni resmî kaynakla karşılaştırın. Yalnızca resmî yayın hukuken bağlayıcıdır.') if tr else
             ('When the date you care about is after the last check, confirm the text against the official source. Only the official publication has legal force.'))
    o.append('')
    return '\n'.join(o)


# ------------------------------------------------------------------ monitoring
def monitoring(lang):
    tr = lang == 'tr'
    D = d_tr if tr else d_en
    w1, w7, w30 = window(1), window(7), window(30)

    def wtxt(c):
        def label(k):
            if k == 'docs': return 'belge' if tr else 'documentation'
            if k == 'other': return 'diğer' if tr else 'other'
            return SHORT[k]
        return '; '.join(f'{label(k)} {num(n, lang)}' for k, n in c.most_common()) or ('hiçbiri' if tr else 'none')
    o = ['# İzleme: Türkiye kaydı ayak uyduruyor mu?' if tr else '# Monitoring: does Türkiye keep up?', '', other(lang, 'README'), '']
    o.append((f'global-law\'un tüm derlemleri nasıl izlediği (15 dakikada bir geçiş, her commit\'in denetimi, herkese açık bir durum): [global-law monitoring/]({GLT}/monitoring). '
              'Bu sayfa yalnızca bu deponun durumudur.') if tr else
             (f'How global-law monitors every corpus (a pass every 15 minutes, a check of every commit, a public status): [global-law monitoring/]({GLT}/monitoring). '
              'This page is the state of this repository alone.'))
    o.append('')
    o.append(f'**{"Durum" if tr else "Status"} {D(TODAY)}**')
    o.append('')
    o.append('| | |')
    o.append('| --- | --- |')
    o.append(f'| {"Son commit" if tr else "Last commit"} | {("main dalına ulaştı" if tr else "reached main")} {last_landed.strftime("%Y-%m-%d %H:%M")} UTC: {last_commit[1][:120]}{"…" if len(last_commit[1]) > 120 else ""} |')
    o.append(f'| {"Son 24 saat" if tr else "Last 24 hours"} | {wtxt(w1)} |')
    o.append(f'| {"Son 7 gün" if tr else "Last 7 days"} | {wtxt(w7)} |')
    o.append(f'| {"Son 30 gün" if tr else "Last 30 days"} | {wtxt(w30)} |')
    if gl:
        pin = f'`{gl["pinned"][:10]}` commit\'ine sabitli' if tr else f'pinned at `{gl["pinned"][:10]}`'
        more = (f', burada {num(behind, lang)} daha yeni commit' if tr else f', {num(behind, lang)} newer commits here') if behind else ''
        o.append(f'| global-law | `{CORPUS}` `{gl["status"]}`, {pin}{more} |')
    for k, (rtr, ren) in PAUSED.items():
        o.append(f'| {name(k, lang)} | {"duraklatıldı: " + rtr if tr else "paused: " + ren} |')
    stale = [name(k, lang) for k in ORDER if status(k, S[k], lang) in ('gecikmiş', 'stale')]
    page = 'FRESHNESS.md' if tr else 'FRESHNESS.en.md'
    o.append(f'| {"Gecikmiş kaynaklar" if tr else "Stale sources"} | {", ".join(stale) if stale else ("yok" if tr else "none")} ([{page}](../{page})) |')
    o.append('')
    o.append('Zamanlar her commit\'in `main` dalına ulaştığı andır ([`landed.tsv`](landed.tsv)); commit tarihleri yürürlük ya da karar günleridir.' if tr else
             'Times are when each commit reached `main` ([`landed.tsv`](landed.tsv)); commit dates are the days of effect or decision.')
    o.append('')
    o.append('## Yeni değişiklikler nasıl gelir' if tr else '## How new changes arrive')
    o.append('')
    if tr:
        o += ['1. Her kaynağın şeridi yeni metinlerin listesini okur (bkz. [WATCHING.md](../WATCHING.md)) ve her değişikliği, yürürlüğe girdiği ya da verildiği günle tarihlenmiş bir commit olarak yayımlar.',
              '2. Yayımlanmadan önce her commit bu deponun denetimlerinden geçer: metin kaynakla, tarihler yayıncının kendi tarihleriyle karşılaştırılır (bkz. [REPRODUCE.md](../REPRODUCE.md)).',
              f'3. global-law her 15 dakikada bir yeni commit\'leri denetler ve `{CORPUS}` üzerindeki işaretçisini ilerletir (bkz. [global-law monitoring/]({GLT}/monitoring)).']
    else:
        o += ['1. Each source\'s lane reads its list of new texts (see [WATCHING.en.md](../WATCHING.en.md)) and publishes each change as a commit dated the day it took effect or was given.',
              '2. Before publishing, every commit goes through this repository\'s checks: the text against the source, the dates against the publisher\'s own (see [REPRODUCE.md](../REPRODUCE.md)).',
              f'3. Every 15 minutes global-law checks new commits and moves its pin on `{CORPUS}` (see [global-law monitoring/]({GLT}/monitoring)).']
    o.append('')
    o.append('## Kendiniz denetleyin' if tr else '## Check it yourself')
    o.append('')
    o.append('```')
    o.append('git fetch && git log -1 --format="%h %s" origin/main')
    o.append('python monitoring/make_pages.py --github lexifina/turkey-law    ' + ('# bu üç sayfayı GitHub\'ın push kaydıyla yeniden oluştur' if tr else '# rebuild these three pages with GitHub\'s push log'))
    o.append('python monitoring/make_plan.py                                  ' + ('# PLAN.md\'yi yeniden say' if tr else '# count PLAN.md again'))
    o.append('```')
    o.append('')
    o.append('## Kendiniz izleyin: bir fork ve GitHub Actions' if tr else '## Watch it yourself: a fork and GitHub Actions')
    o.append('')
    if tr:
        o += ['Herkes bu depoyu fork\'layabilir ve kendi kopyasını bize ihtiyaç duymadan güncel tutabilir. GitHub Actions herkese açık depolar için ücretsizdir.',
              '',
              f'1. Fork\'layın: <https://github.com/{REPO}/fork>.',
              '2. Fork\'ta [`monitoring/fork-workflow.yml`](fork-workflow.yml) dosyasını `.github/workflows/refresh.yml` olarak kopyalayın ve `main` dalına commit edin.',
              f'3. Fork\'un **Actions** sekmesinde iş akışlarını etkinleştirin (GitHub fork\'larda bunları varsayılan olarak kapatır) ve **Refresh from {REPO}** iş akışını bir kez çalıştırın.',
              '',
              'İş akışı her 6 saatte bir bu deponun yeni commit\'lerini fork\'unuzun `main` dalına alır (GitHub\'ın kendi "Sync fork" özelliğiyle; böylece `main` bu depo artı sizin iş akışı dosyanızdır), kopyanız için WATCHING, FRESHNESS ve bu sayfayı yeniden oluşturur, iniş kaydını (`landed.tsv`) her çalışmada büyütür, bunları bir `status` dalına yayımlar ve FRESHNESS\'ı çalışma özetinde gösterir. Bir çalışma birkaç dakika sürer. İş akışı resmî kaynakları okumaz: bu deponun ne kadar güncel olduğunu denetler.']
    else:
        o += ['Anyone can fork this repository and keep their copy current without us. GitHub Actions is free for public repositories.',
              '',
              f'1. Fork it: <https://github.com/{REPO}/fork>.',
              '2. In the fork, copy [`monitoring/fork-workflow.yml`](fork-workflow.yml) to `.github/workflows/refresh.yml` and commit it to `main`.',
              f'3. On the fork\'s **Actions** tab, enable workflows (GitHub turns them off in forks by default) and run **Refresh from {REPO}** once.',
              '',
              'Every 6 hours the workflow takes the new commits from this repository into your fork\'s `main` (through GitHub\'s own "Sync fork", so your `main` is this repository plus your workflow file), rebuilds WATCHING, FRESHNESS and this page for your copy, grows the landing log (`landed.tsv`) by one row a run, publishes them to a `status` branch and shows FRESHNESS in the run summary. A run takes a few minutes. The workflow does not read the official sources: it checks how current this repository is.']
    o.append('')
    return '\n'.join(o)


def write(path, text):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('wrote', path)


with open(LOG, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\t'.join(LOG_FIELDS) + '\n')
    for r in log:
        f.write('\t'.join(r.get(k, '') for k in LOG_FIELDS) + '\n')
print('wrote monitoring/landed.tsv')
write('WATCHING.md', watching('tr')); write('WATCHING.en.md', watching('en'))
write('FRESHNESS.md', freshness('tr')); write('FRESHNESS.en.md', freshness('en'))
write('monitoring/README.md', monitoring('tr')); write('monitoring/README.en.md', monitoring('en'))
