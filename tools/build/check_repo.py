"""Check the Turkey law repository against the source HTML.

    python -X utf8 scripts/turkey-law/check_repo.py ~/Documents/turkey-law [--no-record]

1. Words: for every act, the files read back from git (main, in index.txt order) give exactly the words of the HTML
   the site served, in order. The source side is extracted independently of build.py: drop <script>/<style>/<head>,
   turn block tags into spaces, strip all other tags, unescape, then split on whitespace. ' | ' cell separators are
   ignored on both sides.
2. Trailers: every commit's message parses with `git interpret-trailers --parse`, and has In-force.
3. History: no merges; In-force dates never go backwards and are not after the build day.
4. Tool: tools/in_force_on.py prints the file for sample articles, and refuses a date before the record.
Writes scripts/turkey-law/verification.json (read by docs.py into REPRODUCE.md) unless --no-record.
"""
import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / '.cache'
BLOCKS = r'p|div|li|h[1-6]|table|tr|td|th|br|blockquote|ul|ol|dl|dt|dd|center|pre|address|body|html'
DROP = re.compile(r'[\u00ad\u200b\u200c\u200d\u2060\ufeff]')


def source_words(html: str) -> list[str]:
    m = re.search(r'(?is)<body[^>]*>(.*)</body>', html)
    h = m.group(1) if m else html
    h = re.sub(r'(?is)<(script|style|head|title|xml|noscript)\b.*?</\1\s*>', ' ', h)
    h = re.sub(r'(?is)<!--.*?-->', ' ', h)
    h = re.sub(rf'(?is)</?(?:{BLOCKS})\b[^>]*>', ' ', h)
    h = re.sub(r'(?s)<[^>]*>', '', h)
    return [w for w in DROP.sub('', unescape(h)).split() if w != '|']


MARKS = re.compile(r'\[\d+\]')
CTRL = re.compile(r'[\x00-\x1f\x7f]')


def fold(text: str) -> str:
    """Letter case folded, with the four Turkish i's as one letter."""
    return text.lower().replace('\u0131', 'i').replace('i\u0307', 'i')


def word_words(text: str) -> list[str]:
    """Words of Word's own plain text (Range.Text): control characters (paragraph and cell marks, the footnote
    reference character) are spaces; footnote markers are not compared on either side."""
    text = text.replace('\x1f', '').replace('\x1e', '-')  # Word's optional hyphen; non-breaking hyphen
    # a Symbol-font character is U+F0xx in Word's text and its font code 0xxx in Word's HTML (and on the site)
    text = re.sub('[\uf000-\uf0ff]', lambda m: chr(ord(m.group()) - 0xf000), text)
    return [w for w in MARKS.sub(' ', CTRL.sub(' ', DROP.sub('', text))).split() if w != '|']


def git(repo: Path, *a: str) -> str:
    return subprocess.run(['git', '-C', str(repo), '-c', 'core.quotepath=false', *a], capture_output=True,
                          text=True, encoding='utf-8', check=True).stdout


class Blobs:
    def __init__(self, repo: Path):
        self.p = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)

    def get(self, spec: str) -> str | None:
        self.p.stdin.write(spec.encode('utf-8') + b'\n')
        self.p.stdin.flush()
        head = self.p.stdout.readline().split()
        if head[-1] == b'missing':
            return None
        data = self.p.stdout.read(int(head[2]))
        self.p.stdout.read(1)
        return data.decode('utf-8')


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    record = '--no-record' not in sys.argv
    sys.path.insert(0, str(HERE))
    import build
    acts = build.load_acts(None)
    blobs = Blobs(repo)
    mism, words, checked, missing = [], 0, 0, 0
    has_future = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '-q', 'future'],
                                capture_output=True).returncode == 0
    future_laws = set()
    if has_future:
        for path in git(repo, 'log', '--format=', '--name-only', 'main..future').split():
            future_laws.add('/'.join(path.split('/')[:2]))
    for a in acts:
        src = CACHE / 'doc' / f"{a['tur']}.{a['tertip']}.{a['no']}.html"
        ref = 'future' if a['dir'] in future_laws else 'main'
        idx = blobs.get(f"{ref}:{a['dir']}/index.txt")
        if not src.exists():
            if idx is not None:
                mism.append([a['dir'], 'in git but no source'])
            missing += 1
            continue
        if idx is None:
            mism.append([a['dir'], 'source exists but act not in git'])
            continue
        mine = []
        for fn in idx.split():
            mine += blobs.get(f"{ref}:{a['dir']}/{fn}").split()
        mine = [w for w in mine if w != '|']
        theirs = source_words(src.read_text('utf-8'))
        checked += 1
        words += len(theirs)
        if mine != theirs:
            k = next((i for i, (x, y) in enumerate(zip(mine, theirs)) if x != y), min(len(mine), len(theirs)))
            mism.append([a['dir'], f"word {k}: git {' '.join(mine[k:k + 8])!r} vs source {' '.join(theirs[k:k + 8])!r}"
                                   f" ({len(mine)} vs {len(theirs)} words)"])
    print(f'words: {checked} acts, {words} words, {len(mism)} mismatches, {missing} not fetched; '
          f'{len(future_laws)} read from the future branch')
    for m in mism[:20]:
        print('  ', *m)

    # every earlier version, at its tag, against Word's own text of the source .doc
    import csv
    vmism, vwords, vchecked, spaced, case_only = [], 0, 0, 0, 0
    vrows = list(csv.DictReader(git(repo, 'show', 'main:data/versions.csv').splitlines()))
    for v in vrows:
        if v['source'] == 'current':
            continue
        base = CACHE / 'oldhtml' / v['source']
        body = (base.parent / (base.name + '.content.txt')).read_text('utf-8')
        notes = (base.parent / (base.name + '.footnotes.txt')).read_text('utf-8')
        theirs = word_words(body) + word_words(notes)
        head = v['header'].split()
        if head and theirs[:len(head)] == [w for w in head]:
            theirs = theirs[len(head):]
        tag = f"refs/tags/{v['tag']}"
        idx = blobs.get(f"{tag}:{v['law']}/index.txt")
        if idx is None:
            vmism.append([v['tag'], 'no index at tag'])
            continue
        mine = []
        for fn in idx.split():
            mine += MARKS.sub(' ', blobs.get(f"{tag}:{v['law']}/{fn}")).split()
        mine = [w for w in mine if w != '|']
        vchecked += 1
        vwords += len(theirs)
        if mine != theirs:
            spaced += 1
        if ''.join(mine) != ''.join(theirs) and fold(''.join(mine)) == fold(''.join(theirs)):
            case_only += 1
        elif ''.join(mine) != ''.join(theirs):
            k = next((i for i, (x, y) in enumerate(zip(mine, theirs)) if x != y), min(len(mine), len(theirs)))
            vmism.append([v['tag'], f"word {k}: git {' '.join(mine[k:k + 8])!r} vs Word {' '.join(theirs[k:k + 8])!r}"
                                    f" ({len(mine)} vs {len(theirs)} words)"])
    print(f'versions: {vchecked} earlier versions, {vwords} words, {len(vmism)} mismatches in the characters; '
          f'{spaced - case_only - len(vmism)} differ only in where words break (a tab or space Word drops from its '
          f'HTML); {case_only} only in letter case (Word "All caps" formatting: the HTML keeps the stored letters)')
    for m in vmism[:25]:
        print('  ', *m)
    mism += vmism

    # trailers and dates
    log = git(repo, 'log', '--reverse', '--first-parent', '--format=%H%x1f%B%x1e', 'main').split('\x1e')
    bad, last, back = 0, '', 0
    built_day = json.loads(git(repo, 'show', 'main:corpus.json'))['built']
    future = 0
    for entry in log:
        entry = entry.strip('\n')
        if not entry:
            continue
        h, msg = entry.split('\x1f', 1)
        parsed = subprocess.run(['git', 'interpret-trailers', '--parse'], input=msg, capture_output=True, text=True,
                                encoding='utf-8').stdout
        tr = dict(l.split(': ', 1) for l in parsed.splitlines() if ': ' in l)
        d = tr.get('In-force', '')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d):
            bad += 1
            continue
        if d < last:
            back += 1
        if d > built_day:
            future += 1
        last = d
    merges = int(git(repo, 'rev-list', '--merges', '--count', 'main').strip())
    commits = int(git(repo, 'rev-list', '--count', 'main').strip())
    print(f'history: {commits} commits, {bad} without a parseable In-force, {back} backwards, {future} after '
          f'{built_day}, {merges} merges')

    # the on-date tool
    retrieved = (CACHE / 'fetched_on.txt').read_text('utf-8').strip()
    samples = [('kanun/2709', 'madde-21'), ('kanun/2709', 'gecici-madde-21'), ('kanun/5237', 'madde-7'),
               ('kanun/4721', 'madde-1'), ('kanun/6098', 'madde-1'), ('kanun/5846', 'madde-31'), ('cbk/1', 'madde-1'),
               ('khk/375', 'madde-1')]
    ok = 0
    for law, art in samples:
        want = blobs.get(f'main:{law}/{art}.md')
        r = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', retrieved, law, art], cwd=repo,
                           capture_output=True, text=True, encoding='utf-8')
        early = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', '1900-01-01', law, art],
                               cwd=repo, capture_output=True, text=True, encoding='utf-8')
        good = want is not None and r.stdout == want and early.returncode != 0
        ok += good
        if not good:
            print('   tool mismatch', law, art, (r.stdout or r.stderr)[:120])
    # earlier versions: on a version's in-force date the tool must give the article as tagged, unless a later
    # commit of the same law is dated that same day (two versions or steps on one day)
    picked = [v for v in vrows if v['source'] != 'current'][::max(1, vchecked // 40 or 1)][:40]
    for v in picked:
        tag = f"refs/tags/{v['tag']}"
        idx = blobs.get(f"{tag}:{v['law']}/index.txt") or ''
        arts = [n for n in idx.split() if n.startswith(('madde-', 'gecici-madde-', 'ek-madde-'))]
        if not arts:
            continue
        art = arts[len(arts) // 2][:-3]
        later = git(repo, 'log', '--format=%(trailers:key=In-force,valueonly,separator=)', f'{tag}..main', '--',
                    v['law']).split()
        if v['in_force'] in later or v['in_force'] < '1970-01-01':
            continue
        want = blobs.get(f"{tag}:{v['law']}/{art}.md")
        r = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', v['in_force'], v['law'], art],
                           cwd=repo, capture_output=True, text=True, encoding='utf-8')
        samples.append((v['law'], art))
        good = r.stdout == want
        ok += good
        if not good:
            print('   tool mismatch at version', v['tag'], art, (r.stdout or r.stderr)[:120])
    print(f'tool: {ok}/{len(samples)} samples right')
    fails = len(mism) + bad + back + future + merges + (len(samples) - ok)
    if record:
        (HERE / 'verification.json').write_text(json.dumps({
            'acts': checked, 'words': words, 'mismatches': len(mism) - len(vmism), 'versions': vchecked,
            'version_words': vwords, 'version_mismatches': len(vmism), 'version_spacing_only': spaced - case_only - len(vmism), 'version_case_only': case_only, 'commits': commits, 'bad_trailers': bad,
            'backwards': back, 'future': future, 'merges': merges, 'tool_samples': len(samples), 'tool_ok': ok},
            indent=1, sort_keys=True) + '\n', 'utf-8')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
