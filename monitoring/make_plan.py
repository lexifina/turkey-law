"""Write PLAN.md: every part this repository is meant to hold, and how far each one is.

    python monitoring/make_plan.py [--ref origin/main] [--summary]

Progress is counted from the tree of the ref (git ls-tree and the index tables in data/), never typed in by hand:
a record is one folder `<kind>/.../<year>/<number>/` (the first four-digit year in its path, then one more folder),
so a law, a decision or a council resolution counts once however many files it has. Index tables (the Resmî Gazete
daily index, the Constitutional Court's individual-application index, the law index) count their rows.
Targets are the official counts read from each source on 2026-11-13 (see PARTS); a part with no count yet has no target.
Progress of a part is held/target (at most 100%); the weighted total is the sum of weight x progress over all parts,
divided by the sum of all weights. --summary prints the counts the READMEs quote instead of writing PLAN.md.
Standard library only.
"""
import argparse, collections, csv, datetime as dt, io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
YEAR = re.compile(r'1[5-9]\d\d|20\d\d')
UNIVERSITY = re.compile(r'universite|enstitu|yuksekokul|yuksek-okul|akademi')
GOVERNMENT = ('council-of-ministers', 'presidency')
DATE = re.compile(r'(\d{4})-(\d\d)-(\d\d)|(\d\d)[./](\d\d)[./](\d{4})')


def git(*args, data=None):
    return subprocess.run(['git', '-C', ROOT, *args], check=True, capture_output=True, input=data).stdout


def default_ref():
    ok = subprocess.run(['git', '-C', ROOT, 'rev-parse', '-q', '--verify', 'origin/main'], capture_output=True).returncode == 0
    return 'origin/main' if ok else 'HEAD'


def day(s):
    m = DATE.search(s or '')
    if not m:
        return None
    try:
        return dt.date(int(m[1]), int(m[2]), int(m[3])) if m[1] else dt.date(int(m[6]), int(m[5]), int(m[4]))
    except ValueError:
        return None


class Census:
    """Records and index tables at one ref."""

    def __init__(self, ref):
        self.ref = ref
        self.head = git('rev-parse', ref).decode().strip()
        self.paths = git('ls-tree', '-r', '--name-only', '-z', ref).decode('utf-8').split('\0')
        self.records = collections.defaultdict(set)      # top-level folder -> record folders
        for p in self.paths:
            s = p.split('/')
            if len(s) < 3 or s[0] in ('data', 'tools', 'monitoring', 'visualisations', 'vulnerabilities'):
                continue
            i = next((i for i in range(1, len(s) - 1) if YEAR.fullmatch(s[i])), None)
            if i is not None:
                self.records[s[0]].add('/'.join(s[:i + 2]))
        self._csv = {}

    def all_records(self):
        return set().union(*self.records.values()) if self.records else set()

    def under(self, prefix, exclude=None):
        top = prefix.split('/')[0]
        return {r for r in self.records.get(top, ()) if r.startswith(prefix) and not (exclude and exclude(r))}

    def regulations(self, kind):
        def k(r):
            issuer = r.split('/')[1]
            if issuer in GOVERNMENT:
                return 'government'
            return 'university' if UNIVERSITY.search(issuer) else 'institution'
        return {r for r in self.records.get('regulation', ()) if k(r) == kind}

    def tables(self, pattern):
        """Rows of every CSV under data/ whose path matches the regex, read at the ref."""
        rx = re.compile(pattern)
        names = [p for p in self.paths if p.startswith('data/') and p.endswith('.csv') and rx.search(p)]
        todo = [n for n in names if n not in self._csv]
        if todo:
            out = git('cat-file', '--batch', data=''.join(f'{self.ref}:{n}\n' for n in todo).encode('utf-8'))
            pos = 0
            for n in todo:
                header_end = out.index(b'\n', pos)
                size = int(out[pos:header_end].split()[2])
                body = out[header_end + 1:header_end + 1 + size].decode('utf-8-sig', 'replace')
                pos = header_end + 1 + size + 1
                self._csv[n] = list(csv.DictReader(io.StringIO(body)))
        return {n: self._csv[n] for n in names}

    # ---- counters used by the plan and the READMEs
    def repealed_laws(self):
        rows = [r for t in self.tables(r'^data/law8/mulga-and-new\.csv$').values() for r in t]
        return {r['path'].strip('/') for r in rows if r.get('status') == 'repealed'} & self.records.get('law', set())

    def rg_days(self):
        days = set()
        for name, rows in self.tables(r'^data/(rg-index/.*/)?rg-[^/]*\.csv$|^data/rg-index/[^/]+/issues\.csv$').items():
            for r in rows:
                if r.get('issue') and r.get('date') and (r.get('status') or 'ok') not in ('missing', 'not-issued'):
                    d = day(r['date'])
                    if d and d.year >= 2001:
                        days.add(d)
        return days

    def rg_items(self):
        urls = set()
        for name, rows in self.tables(r'^data/(rg-index/.*/)?rg-[^/]*\.csv$').items():
            for r in rows:
                if r.get('title') and r.get('url'):
                    urls.add(r['url'])
        return urls

    def aym_individual(self):
        rows = [r for t in self.tables(r'^data/aym-individual-\d{4}\.csv$').values() for r in t]
        keys = set()
        for r in rows:
            k = next((r.get(c) for c in ('application_number', 'application_no', 'id', 'source_id', 'decision_id') if r.get(c)), None)
            keys.add(k or repr(sorted(r.items())))
        return keys

    def law_index(self):
        rows = [r for t in self.tables(r'^data/m4-all/law-index-\d+\.csv$').values() for r in t]
        return {(r.get('mevzuatTuru'), r.get('mevzuatTertip'), r.get('kanunNo'), r.get('rowNum')) for r in rows}

    def uyusmazlik_listed(self):
        rows = [r for t in self.tables(r'^data/ledger-m31-uyusmazlik\.csv$').values() for r in t]
        return {(r.get('esas_no'), r.get('decision_no')) for r in rows}

    def history_laws(self):
        return [r for t in self.tables(r'^data/history-laws\.csv$').values() for r in t]


# --------------------------------------------------------------------------- the plan
# (section, part, will be in, weight, target, target note, how, counter, fixed status)
# Targets: law8-sources.md (official counts read from each source on 2026-11-13); "~" marks an estimate.
TODAY = dt.datetime.now(dt.timezone.utc).date()
RG_DAYS = (TODAY - dt.date(2001, 1, 1)).days + 1

def parts(c):
    law = c.records.get('law', set())
    rep = c.repealed_laws()
    ccourt = 'case-law/constitutional-court/'
    return [
        ('Primary legislation (Mevzuat Bilgi Sistemi)', None),
        ('Laws in force (Kanunlar), with the Constitution', 'law/<year>/<number>/', 20, 917, 'laws in force', 'mevzuat.gov.tr; current text checked word for word against the site', len(law - rep), None),
        ('Earlier consolidated texts of laws ("Önceki metinler")', 'the history of law/<year>/<number>/', 4, 280, 'laws with earlier texts', 'mevzuat.gov.tr .doc files, read through Microsoft Word and checked word for word', len(c.history_laws()), None),
        ('Repealed laws (mülga kanunlar)', 'law/<year>/<number>/, labelled repealed', 2, 185, 'repealed laws', 'mevzuat.gov.tr MulgaKanun', len(rep), None),
        ('Ottoman-era laws still in force', 'ottoman/<year>/<number>/', 0.5, 9, 'laws', 'mevzuat.gov.tr', len(c.under('ottoman/')), None),
        ('Decree-laws (KHK)', 'decree-law/<year>/<number>/', 2, 63, 'decree-laws', 'mevzuat.gov.tr', len(c.under('decree-law/')), None),
        ('Presidential decrees (CBK), in force and amending or repealed ones', 'presidential-decree/<year>/<number>/', 4, 203, 'decrees in the official list', 'mevzuat.gov.tr; the 170 not in force from the list\'s PDFs', len(c.under('presidential-decree/')), None),
        ('By-laws (tüzükler)', 'bylaw/<year>/<number>/', 1, 107, 'by-laws', 'mevzuat.gov.tr', len(c.under('bylaw/')), None),
        ('Index of every law ever passed, with its Resmî Gazete issue and repeal', 'data/m4-all/', 2, 15623, 'laws in the official index', 'mevzuat.gov.tr law index (MevzuatFihristDatatable)', len(c.law_index()), None),
        ('Secondary legislation', None),
        ('Presidential and Council of Ministers regulations', 'regulation/presidency/, regulation/council-of-ministers/', 4, 327, 'regulations', 'mevzuat.gov.tr', len(c.regulations('government')), None),
        ('Regulations of ministries, agencies and other bodies (kurum ve kuruluş yönetmelikleri)', 'regulation/<issuer>/<year>/<number>/', 7, 3662, 'regulations', 'mevzuat.gov.tr', len(c.regulations('institution')), None),
        ('University regulations', 'regulation/<university>/<year>/<number>/', 2, 5046, 'regulations', 'mevzuat.gov.tr', len(c.regulations('university')), None),
        ('Communiqués (tebliğler)', 'communique/<issuer>/<year>/<number>/', 7, 4482, 'communiqués', 'mevzuat.gov.tr', len(c.under('communique/')), None),
        ('Presidential decisions (CB kararları, since 2018)', 'presidential-decision/<year>/<number>/', 4, 4374, 'decisions', 'mevzuat.gov.tr PDFs; expropriation parcel lists as links only', len(c.under('presidential-decision/')), None),
        ('Presidential circulars (CB genelgeleri)', 'presidential-circular/<year>/<number>/', 1, 158, 'circulars', 'mevzuat.gov.tr PDFs', len(c.under('presidential-circular/')), None),
        ('Council of Ministers decisions before 2018 (BKK)', 'council-of-ministers-decision/<year>/<number>/', 2, None, 'about 25,000 (estimate)', 'Resmî Gazete items, from the daily index', len(c.under('council-of-ministers-decision/')), None),
        ('Case law', None),
        ('Constitutional Court: norm review (Norm Denetimi)', ccourt + 'norm/<year>/<number>/', 6, 5620, 'decisions', 'the Court\'s decisions database (normkararlarbilgibankasi.anayasa.gov.tr)', len(c.under(ccourt + 'norm/')), None),
        ('Constitutional Court: individual applications (index; text where the Court anonymises)', 'data/aym-individual-<year>.csv', 4, 18003, 'decisions', 'kararlarbilgibankasi.anayasa.gov.tr; applicants\' names as published, text only with initials', len(c.aym_individual()), None),
        ('Constitutional Court: political parties, Yüce Divan, immunity', ccourt + 'party/, supreme-criminal/, immunity/', 0.5, 1993, 'decisions', 'the same database', len(c.under(ccourt + 'party/') | c.under(ccourt + 'supreme-criminal/') | c.under(ccourt + 'immunity/')), None),
        ('Uyuşmazlık Mahkemesi (jurisdiction conflicts)', 'case-law/uyusmazlik/<year>/<number>/', 2, len(c.uyusmazlik_listed()) or None, 'decisions the court lists' if c.uyusmazlik_listed() else 'being counted', 'kararlar.uyusmazlik.gov.tr; the list is data/ledger-m31-uyusmazlik.csv', len(c.under('case-law/uyusmazlik/')), None),
        ('Unification decisions of the Yargıtay and the Danıştay (İBK)', 'case-law/yargitay/ibk/, case-law/danistay/ibk/', 3, None, 'about 1,500 (estimate)', 'Resmî Gazete, judicial section', len(c.under('case-law/yargitay/') | c.under('case-law/danistay/')), None),
        ('Competition Authority (Rekabet Kurulu)', 'decision/rekabet/<year>/<number>/', 2, 10476, 'decisions', 'rekabet.gov.tr decisions list', len(c.under('decision/rekabet/')), None),
        ('Other boards: insurance arbitration, broadcasting (RTÜK), BDDK, SPK, EPDK, GİB, KVKK, BTK', 'decision/<body>/, case-law/sigorta-tahkim/, norm/<issuer>/', 4, None, 'about 45,000 (estimate)', 'each body\'s own site; sanctions on individuals as metadata and link', len(c.under('decision/', exclude=lambda r: r.startswith('decision/rekabet/')) | c.under('case-law/sigorta-tahkim/') | c.under('norm/')), None),
        ('Local law', None),
        ('Ankara Metropolitan Council decisions', 'local/ankara/buyuksehir/<year>/<number>/', 3, None, 'about 24,000 (estimate)', 'ankara.bel.tr council decisions, 2012 on', len(c.under('local/ankara/')), None),
        ('Other metropolitan councils (İstanbul, İzmir, Bursa and 27 more)', 'local/<province>/buyuksehir/<year>/<number>/', 4, None, 'being counted', 'each council\'s site; İstanbul\'s register not found yet', len(c.under('local/', exclude=lambda r: r.startswith('local/ankara/'))), None),
        ('District and town councils, provincial councils, governors\' orders', 'local/<province>/<body>/<year>/<number>/', 2, None, 'about 1,390 councils', 'municipal sites and e-Devlet\'s council-decision services', 0, None),
        ('Elections, audit and oversight', None),
        ('Supreme Election Council (YSK): decisions, principle decisions, rules', 'election/ysk/', 1, 1778, 'decisions and rules', 'ysk.gov.tr indexes (kararlar.txt)', len(c.under('election/')), None),
        ('Court of Accounts (Sayıştay): judgments and audit reports', 'audit/sayistay/', 1.5, None, 'about 15,000 (estimate)', 'sayistay.gov.tr', len(c.under('audit/')), None),
        ('Ombudsman (KDK) decisions and reports', 'ombudsman/', 0.5, None, 'about 10,000 (estimate)', 'kararlar.ombudsman.gov.tr refused connections on 2026-11-13', len(c.under('ombudsman/')), 'blocked'),
        ('Parliament and the Resmî Gazete', None),
        ('Decisions of the Grand National Assembly (TBMM kararları)', 'parliament-decision/<year>/<number>/', 0.5, None, 'about 1,500 (estimate)', 'tbmm.gov.tr', len(c.under('parliament-decision/')), None),
        ('Bills and committee reports, labelled not law', 'bill/<term>/<number>/', 2, None, 'about 30,000 (estimate)', 'tbmm.gov.tr', len(c.under('bill/')), None),
        ('Resmî Gazete daily index since 2001 (every issue\'s sections and items)', 'data/rg-<year>.csv', 3, RG_DAYS, 'days since 2001-01-01', 'resmigazete.gov.tr daily index pages', len(c.rg_days()), None),
        ('Treaties', 'treaty/<year>/<number>/', 2, None, 'about 5,000 (estimate)', 'Resmî Gazete, with the approving law', len(c.under('treaty/')), None),
        ('Blocked or out of scope', None),
        ('All decisions of the Yargıtay, the Danıştay and the regional and first-instance courts', 'none', 0, None, 'millions', 'Yargıtay\'s search timed out; the Danıştay and UYAP Emsal need a reCAPTCHA on every search; never worked around', 0, 'blocked'),
        ('Notices in the Resmî Gazete (ilanlar) and on ilan.gov.tr', 'none', 0, None, '–', 'court and enforcement notices name private persons', 0, 'not planned'),
    ]


def pct(h, t):
    return min(h / t, 1.0) if t else 0.0


def fmt(n):
    return f'{n:,}'


def status(held, target, fixed):
    if fixed:
        return fixed
    if target and held >= target * 0.995:
        return 'done'
    return 'collecting' if held else 'planned'


def write_plan(c):
    rows = parts(c)
    real = [r for r in rows if r[1] is not None]
    total_w = sum(r[2] for r in real)
    score = sum(r[2] * pct(r[6], r[3]) for r in real) / total_w
    o = ['# The plan: every source a Turkish lawyer or citizen needs', '',
         'This is the plan for this repository, part by part, with what is published so far. The aim is everything a Turkish lawyer or citizen needs, in one dated git history: every act with its versions, secondary legislation, case law, local law, the Resmî Gazete and the legislative history behind each act.', '',
         f'**{score * 100:.1f}%** of the plan is published, weighted by how binding each source is and how often it is used. Targets are the official counts read from each source on 2026-11-13; parts whose count is only an estimate have no target yet and count 0. Counted from `{c.head[:10]}` on {TODAY.isoformat()} by [`monitoring/make_plan.py`](monitoring/make_plan.py).', '',
         '| Part | Will be in | Weight | Progress | How | Status |', '| --- | --- | ---: | --- | --- | --- |']
    for r in rows:
        if r[1] is None:
            o.append(f'| **{r[0]}** | | | | | |')
            continue
        name, where, w, target, note, how, held, fixed = r
        if target:
            prog = f'{fmt(held)} of {fmt(target)} {note} · {pct(held, target) * 100:.1f}%'
        elif fixed:
            prog = note
        else:
            prog = f'{fmt(held)} held; target {note}'
        wtxt = f'{w / total_w * 100:.1f}%' if w else '–'
        o.append(f'| {name} | {where} | {wtxt} | {prog} | {how} | {status(held, target, fixed)} |')
    o += ['', 'Progress counts what is on `main`: a record is one folder `<kind>/.../<year>/<number>/`, and index tables count their rows. '
          'Targets: mevzuat.gov.tr\'s own search table for each type of act (2026-11-13), its law index (15,623 laws of every tertip), '
          'the Constitutional Court\'s database (5,620 norm-review decisions, 18,003 individual applications, 1,993 other decisions), '
          'the Competition Authority\'s list (10,476 decisions) and YSK\'s indexes (982 decisions, 787 principle decisions, 9 rules). '
          'The Resmî Gazete is published every day, so its target is the number of days since 2001-01-01. '
          'Parts with an estimate are being counted.', '']
    with open(os.path.join(ROOT, 'PLAN.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(o))
    print(f'wrote PLAN.md ({score * 100:.1f}%)')


def summary(c):
    """The counts the READMEs quote."""
    rep = c.repealed_laws()
    law = c.records.get('law', set())
    out = collections.OrderedDict()
    out['records'] = len(c.all_records())
    out['laws in force'] = len(law - rep)
    out['repealed laws'] = len(rep)
    out['laws with history'] = len(c.history_laws())
    for k in ('ottoman/', 'decree-law/', 'presidential-decree/', 'presidential-circular/', 'bylaw/', 'parliament-decision/'):
        out[k] = len(c.under(k))
    for k in ('government', 'institution', 'university'):
        out['regulation ' + k] = len(c.regulations(k))
        out['regulation ' + k + ' issuers'] = len({r.split('/')[1] for r in c.regulations(k)})
    for k in ('case-law/constitutional-court/norm/', 'case-law/constitutional-court/party/', 'case-law/constitutional-court/immunity/',
              'case-law/constitutional-court/supreme-criminal/', 'case-law/uyusmazlik/', 'case-law/sigorta-tahkim/',
              'decision/rekabet/', 'decision/rtuk/', 'election/ysk/', 'audit/sayistay/', 'local/ankara/', 'local/bursa/'):
        out[k] = len(c.under(k))
    out['local bodies'] = len({'/'.join(r.split('/')[:3]) for r in c.records.get('local', ())})
    out['aym individual index'] = len(c.aym_individual())
    days = c.rg_days()
    out['rg days'] = len(days)
    out['rg first'] = min(days).isoformat() if days else ''
    out['rg last'] = max(days).isoformat() if days else ''
    out['rg items'] = len(c.rg_items())
    out['law index'] = len(c.law_index())
    out['top-level'] = {k: len(v) for k, v in sorted(c.records.items())}
    for k, v in out.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default=None)
    ap.add_argument('--summary', action='store_true')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    census = Census(a.ref or default_ref())
    summary(census) if a.summary else write_plan(census)
