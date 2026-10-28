"""README, REPRODUCE.md, SOURCES.md, LICENSE, corpus.json, laws.csv, data/ and tools for the Turkey law repository
(called by build.py; every file is generated, so a rebuild keeps them current)."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
REPO_FILES = HERE / 'repo'
CACHE = HERE / '.cache'
BUILD_FILES = ('fetch.py', 'build.py', 'history.py', 'docs.py', 'check_repo.py', 'convert_doc.ps1')

CITATION = {'file': r'(kanun|osmanli|khk|cbk)/([0-9]+)/[a-z0-9~.-]+\.md',
            'cites': '([^0-9]|^){n} say\u0131l\u0131'}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _csv(rows: list[list]) -> bytes:
    out = io.StringIO()
    w = csv.writer(out, lineterminator='\n')
    for r in rows:
        w.writerow(r)
    return out.getvalue().encode('utf-8')


def source_sums() -> str:
    paths = sorted([*(CACHE / 'list').glob('*.json'), *(CACHE / 'doc').glob('*.html'), *(CACHE / 'doc').glob('*.miss'),
                    *(CACHE / 'old').glob('*.json')], key=lambda p: (p.parent.name, p.name))
    return ''.join(f'{p.parent.name}/{p.name}\t{_sha(p)}\n' for p in paths)


def previous_texts() -> list[list[str]]:
    """The 'ONCEKI METINLER' lists: earlier consolidated texts the site offers as .doc/.pdf, per act."""
    from build import iso
    rows = []
    for f in sorted((CACHE / 'old').glob('*.json'), key=lambda p: p.name):
        tertip, no = f.stem.split('.', 1)
        try:
            data = json.loads(f.read_text('utf-8'))
        except json.JSONDecodeError:
            continue
        for r in data:
            rows.append([no, tertip, r.get('mevzuatTurEnumString') or '', r.get('mevzuatNo') or '',
                         iso(r.get('kabulTarih') or ''), iso(r.get('resmiGazeteTarihi') or ''),
                         r.get('resmiGazeteSayisi') or '', r.get('pdfUrl') or '', r.get('docUrl') or ''])
    return rows


def requests_count() -> int:
    p = CACHE / 'requests.log'
    return len(p.read_text('utf-8').splitlines()) if p.exists() else 0


def render(acts, groups, issues, amend, inforce, today: str, retrieved: str, versions=(), extra=None,
           fgroups=()) -> dict[str, bytes]:
    from build import KINDS
    built = [a for a in acts if a['built']]
    by_kind = Counter(a['kind'] for a in built)
    articles = sum(a['articles'] for a in built)
    amending = {(r[4]) for r in amend if r[4]}
    prev = previous_texts()
    stats = {
        'today': today, 'retrieved': retrieved, 'acts': len(acts), 'built': len(built),
        'kanun': by_kind.get('kanun', 0), 'osmanli': by_kind.get('osmanli', 0), 'khk': by_kind.get('khk', 0), 'cbk': by_kind.get('cbk', 0),
        'articles': articles, 'commits': len(groups) + 1,
        'consolidated': (extra or {}).get('kinds', {}).get('current', 0),
        'amendment_commits': (extra or {}).get('kinds', {}).get('amendment', 0),
        'unexplained_commits': (extra or {}).get('kinds', {}).get('unexplained', 0),
        'editorial_commits': (extra or {}).get('kinds', {}).get('editorial', 0),
        'baseline_commits': (extra or {}).get('kinds', {}).get('enacted', 0) + (extra or {}).get('kinds', {}).get('consolidated', 0),
        'future_commits': len(fgroups),
        'history_laws': sum(1 for a in acts if a.get('history')), 'versions': len(versions),
        'current_only': sum(1 for a in built if not a.get('history')),
        'old_versions': sum(1 for v in versions if not v['tag'].endswith('-current')),
        'first_version': min((v['date'] for v in versions), default=''),
        'credited_files': sum(len(e['files']) - 1 for g in groups for e in g['events'] if e['kind'] == 'amendment'),
        'unexplained_files': sum(len(e['files']) - 1 for g in groups for e in g['events'] if e['kind'] == 'unexplained'),
        'notes': len(amend), 'inforce_rows': len(inforce), 'inforce_acts': len({r[0] for r in inforce}), 'amending_laws': len(amending), 'unreadable': len(issues),
        'footnotes': sum(a['footnotes'] for a in built), 'requests': requests_count(),
        'previous_text_acts': len({(r[0], r[1]) for r in prev}), 'previous_texts': len(prev),
        'oldest_enacted': min((a['enacted'] for a in built if a['enacted']), default=''),
    }

    ver = HERE / 'verification.json'
    if ver.exists():
        v = json.loads(ver.read_text('utf-8'))
        check = (f"check_repo.py on the previous identical-input build: {v['acts']} current texts read back from git, "
                 f"{v['words']} words compared with the site's HTML, {v['mismatches']} mismatches; "
                 f"{v.get('versions', 0)} earlier versions read back at their tags, {v.get('version_words', 0)} words "
                 f"compared with Word's own text of each .doc, {v.get('version_mismatches', 0)} mismatches in the characters "
                 f"({v.get('version_case_only', 0)} differ only in letter case, from Word's All caps formatting, and "
                 f"{v.get('version_spacing_only', 0)} only in where words break, from tabs Word leaves out of its HTML); "
                 f"{v['commits']} commits, {v['bad_trailers']} with unparseable trailers, {v['backwards']} backwards, "
                 f"{v['future']} after the build day on main, {v['merges']} merges; tool samples {v['tool_ok']}/{v['tool_samples']} right.")
    else:
        check = 'Not yet run for this build.'
    stats['check'] = check

    def fill(s: str) -> str:
        for k, v in stats.items():
            if isinstance(v, (str, int)):
                s = s.replace('{{' + k.upper() + '}}', str(v))
        for name in BUILD_FILES:
            s = s.replace('{{SHA_' + name.upper().replace('.', '_') + '}}', _sha(HERE / name))
        return s

    sums = source_sums()
    corpus = {
        'corpus': 'tr/national/acts',
        'name': 'T\u00fcrkiye: laws, decree-laws and presidential decrees in force (Mevzuat Bilgi Sistemi)',
        'label': 'T\u00fcrkiye',
        'language': 'tr',
        'acts': {'kanun': stats['kanun'], 'osmanli': stats['osmanli'], 'khk': stats['khk'], 'cbk': stats['cbk']},
        'history': 'in-force',
        'history_laws': 'data/history-laws.csv',
        'history_from': stats['first_version'] or retrieved,
        'record_to': retrieved,
        'checked_on': retrieved,
        'record_note': (f"{stats['history_laws']} laws have dated history from the publisher's earlier consolidated "
                        f"texts ({stats['old_versions']} earlier versions, each checked word for word against its "
                        "source document), with changes credited to amending acts dated by the publisher's in-force "
                        'tables; see data/history-laws.csv. The other acts are current-only: one version, the text '
                        f'as published on {retrieved}.'),
        'built': today,
        'baseline_trailer': 'Consolidated',
        'in_force_trailer': 'In-force',
        'has_future_branch': bool(fgroups),
        'future_branch': 'future' if fgroups else None,
        'dates': {'commit': "in-force date: the publisher's in-force table for amendments (see the Date-source "
                            'trailer); the retrieval day for current-only texts',
                  'baseline_trailer': 'Consolidated', 'other_trailers': ['Enacted', 'Published', 'Applies-from'],
                  'time': '12:00 Europe/Istanbul (UTC+3; UTC+2 with summer time before 2016-09-07)',
                  'before_1970': 'clamped to 1970-01-01'},
        'author': {'consolidated': 'Mevzuat Bilgi Sistemi (T.C. Cumhurba\u015fkanl\u0131\u011f\u0131)',
                   'amendment': 'the amending act (Kanun N, KHK N, Anayasa Mahkemesi K. Y/N)',
                   'unexplained': 'Mevzuat Bilgi Sistemi (T.C. Cumhurba\u015fkanl\u0131\u011f\u0131)'},
        'scope': {
            'trailer': 'Applies',
            'when_absent': 'not extracted for T\u00fcrkiye; transitional rules are in the text (Gecici maddeler)',
            'default_reach': {
                'rule': 'non-retroactivity of laws (kanunlar\u0131n geriye y\u00fcr\u00fcmezli\u011fi)',
                'meaning': 'a law applies from its entry into force and does not reach completed facts unless it '
                           'says so; for criminal law the more favourable law applies',
                'authority': 'Anayasa art. 38 (criminal); T\u00fcrk Ceza Kanunu art. 7; T\u00fcrk Medeni Kanunu '
                             'Y\u00fcr\u00fcrl\u00fck ve Uygulama \u015eekli Hakk\u0131nda Kanun (4722) art. 1',
                'decided_here': False,
            },
        },
        'citation': CITATION,
        'tool': 'tools/in_force_on.py',
    }
    acts_csv = _csv([['kind', 'number', 'tertip', 'title', 'enacted', 'published', 'gazette', 'articles', 'footnotes',
                      'amendment_notes', 'has_previous_texts', 'path', 'source']] +
                    [[a['kind'], a['no'], a['tertip'], a['title'], a['enacted'], a['published'], a['gazette'],
                      a['articles'], a['footnotes'], a['notes'], 'yes' if a['old'] else 'no', a['dir'] + '/', a['url']]
                     for a in acts])
    files = {
        'corpus.json': (json.dumps(corpus, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
        'README.md': fill((REPO_FILES / 'README.md').read_text('utf-8')).encode('utf-8'),
        'REPRODUCE.md': fill((REPO_FILES / 'REPRODUCE.md').read_text('utf-8')).encode('utf-8'),
        'SOURCES.md': fill((REPO_FILES / 'SOURCES.md').read_text('utf-8')).encode('utf-8'),
        'LICENSE': (REPO_FILES / 'LICENSE').read_bytes(),
        'laws.csv': acts_csv,
        'data/amendments.csv': _csv([['act', 'article', 'kind', 'date', 'amending_law', 'amending_article', 'note']]
                                    + amend),
        'data/in-force-list.csv': _csv([['act', 'amending', 'articles', 'in_force', 'in_force_as_printed']] + inforce),
        'data/previous-texts.csv': _csv([['number', 'tertip', 'by_kind', 'by_number', 'enacted', 'published',
                                          'gazette', 'pdf', 'doc']] + prev),
        'data/versions.csv': _csv([['law', 'tag', 'source', 'acts', 'in_force', 'date_source', 'date_note', 'header',
                                    'files']] + [[v['law'], v['tag'], v['base'], ' '.join(v['acts']), v['date'],
                                                  v['date_source'], v['date_note'], v['header'], v['files']]
                                                 for v in versions]),
        'data/history-laws.csv': _csv([['law', 'title', 'versions', 'first_version']] + [
            [a['dir'], a['title'], a['history'], min(v['date'] for v in versions if v['law'] == a['dir'])]
            for a in acts if a.get('history')]),
        'data/unreadable.csv': _csv([['act', 'issue']] + issues),
        'data/stats.json': (json.dumps(stats, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8'),
        'data/source-sha256.tsv': sums.encode('utf-8'),
        'tools/in_force_on.py': (REPO_FILES / 'tools' / 'in_force_on.py').read_bytes(),
    }
    for name in BUILD_FILES:
        files[f'tools/build/{name}'] = (HERE / name).read_bytes()
    for name in ('README.md', 'REPRODUCE.md', 'SOURCES.md', 'LICENSE'):
        files[f'tools/build/repo/{name}'] = (REPO_FILES / name).read_bytes()
    return files
