#!/usr/bin/env python3
"""사이트맵 <lastmod> 용 날짜표(data/lastmod.json) 갱신.

  python3 tools/update_lastmod.py        # prepublish.sh 가 자동으로 부른다

content/cases·guides 의 각 글에 대해 git 에 마지막으로 커밋된 날(한국 시간)을 적고,
아직 커밋 안 됐거나 바뀐 글은 오늘 날짜로 적는다. CI 는 얕은 clone 이라 git 기록을 못 보므로 결과를 커밋한다.
"""
import datetime, json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data/lastmod.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(KST).strftime('%Y-%m-%d')


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True).stdout.strip()


dirty = set(git('status', '--porcelain', '--', 'content').replace('?? ', ' M ').split('\n'))
dirty = {l[3:].strip() for l in dirty if l.strip()}
old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
res = {}
for kind in ('cases', 'guides'):
    for f in sorted(os.listdir(os.path.join(ROOT, 'content', kind))):
        if not f.endswith('.md'):
            continue
        rel = f'content/{kind}/{f}'
        key = f"{'case' if kind == 'cases' else 'guide'}/{f[:-3]}"
        if rel in dirty:
            res[key] = today
            continue
        ts = git('log', '-1', '--format=%ct', '--', rel)
        res[key] = datetime.datetime.fromtimestamp(int(ts), KST).strftime('%Y-%m-%d') if ts else old.get(key, today)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'lastmod: {len(res)} pages')
