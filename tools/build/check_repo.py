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
    for a in acts:
        src = CACHE / 'doc' / f"{a['tur']}.{a['tertip']}.{a['no']}.html"
        idx = blobs.get(f"main:{a['dir']}/index.txt")
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
            mine += blobs.get(f"main:{a['dir']}/{fn}").split()
        mine = [w for w in mine if w != '|']
        theirs = source_words(src.read_text('utf-8'))
        checked += 1
        words += len(theirs)
        if mine != theirs:
            k = next((i for i, (x, y) in enumerate(zip(mine, theirs)) if x != y), min(len(mine), len(theirs)))
            mism.append([a['dir'], f"word {k}: git {' '.join(mine[k:k + 8])!r} vs source {' '.join(theirs[k:k + 8])!r}"
                                   f" ({len(mine)} vs {len(theirs)} words)"])
    print(f'words: {checked} acts, {words} words, {len(mism)} mismatches, {missing} not fetched')
    for m in mism[:20]:
        print('  ', *m)

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
        early = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', '2000-01-01', law, art],
                               cwd=repo, capture_output=True, text=True, encoding='utf-8')
        good = want is not None and r.stdout == want and early.returncode != 0
        ok += good
        if not good:
            print('   tool mismatch', law, art, (r.stdout or r.stderr)[:120])
    print(f'tool: {ok}/{len(samples)} samples right')
    fails = len(mism) + bad + back + future + merges + (len(samples) - ok)
    if record:
        (HERE / 'verification.json').write_text(json.dumps({
            'acts': checked, 'words': words, 'mismatches': len(mism), 'commits': commits, 'bad_trailers': bad,
            'backwards': back, 'future': future, 'merges': merges, 'tool_samples': len(samples), 'tool_ok': ok},
            indent=1, sort_keys=True) + '\n', 'utf-8')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
