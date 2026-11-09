"""게시 전 검사. 사용:
  python3 tools/check.py                 # 전체 검사 (기존 글의 [확인 필요] 등은 경고만)
  python3 tools/check.py --strict <slug> # 새로 올릴 글은 경고도 오류로 처리
먼저 build.py로 dist/를 만든 뒤 실행. 오류가 하나라도 있으면 종료 코드 1 → 게시하지 말 것."""
import os, re, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import build
from PIL import Image
ROOT = build.ROOT; ST = os.path.join(ROOT, 'static'); DIST = build.OUT
args = sys.argv[1:]; strict = set()
if '--strict' in args:
    i = args.index('--strict'); strict = set(args[i + 1:])
errs, warns = [], []
def bad(slug, msg, hard=False):
    (errs if hard or slug in strict else warns).append(f'[{slug}] {msg}')
def img_path(src): return os.path.join(ST, src.lstrip('/'))
CASES = {c['slug']: c for c in build.CASES}; GUIDES = {g['slug']: g for g in build.GUIDES}
def common(x, kind):
    s = x['slug']
    for k in ['title', 'description', 'date']:
        if not x.get(k): bad(s, f'frontmatter {k} 없음', True)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', x.get('date', '')): bad(s, f"date 형식 확인 필요: '{x.get('date')}'")
    if len(x.get('title', '')) > 60: bad(s, f"제목 {len(x['title'])}자 (60자 이하 권장)")
    d = len(x.get('description', ''))
    if not 50 <= d <= 170: bad(s, f'description {d}자 (50~170자)')
    body = x['body']
    for pat in ['[확인 필요]', '확인 필요:', '[도메인]', 'TODO', 'TBD', 'lorem']:
        if pat in body or pat in x.get('description', ''): bad(s, f"본문에 '{pat}' 남아 있음")
    if x.get('cover') and not os.path.exists(img_path(x['cover'])): bad(s, f"cover 파일 없음: {x['cover']}", True)
    lines = body.split('\n')
    for i, l in enumerate(lines):
        m = re.match(r'^!\[(.*?)\]\((.+?)\)\s*$', l)
        if m:
            if not m.group(1).strip(): bad(s, f'그림 alt 비어 있음: {m.group(2)}', True)
            if not os.path.exists(img_path(m.group(2))): bad(s, f'본문 그림 파일 없음: {m.group(2)}', True)
            if i > 0 and lines[i - 1].strip(): bad(s, f'그림 줄 앞에 빈 줄 필요: {m.group(2)}', True)
            if i + 1 < len(lines) and lines[i + 1].strip() and i + 2 < len(lines) and lines[i + 2].strip():
                bad(s, f'그림 다음 줄은 캡션 한 줄, 그 뒤는 빈 줄이어야 함: {m.group(2)}', True)
        elif '![' in l: bad(s, f'그림 문법 오류(한 줄에 ![alt](경로) 만): {l[:60]}', True)
    srcs = re.findall(r'\]\((/[^)]+)\)', body)
    if len(srcs) != len(set(srcs)): bad(s, '같은 그림이 본문에 두 번 이상 들어감', True)
    for kind2, slug2 in re.findall(r'naezipcare\.kr/(case|guide)/([a-z0-9-]+)/?', body + x.get('related_cases', '')):
        if slug2 not in (CASES if kind2 == 'case' else GUIDES): bad(s, f'없는 글로 가는 링크: /{kind2}/{slug2}/', True)
    for r in [t.strip() for t in x.get('related_cases', '').split(',') if t.strip()]:
        if r not in CASES: bad(s, f'related_cases에 없는 현장: {r}', True)
    page = os.path.join(DIST, kind, s, 'index.html')
    if not os.path.exists(page): bad(s, f'빌드 결과 없음: {kind}/{s}/ (build.py 먼저 실행)', True)
    else:
        h = open(page, encoding='utf-8').read()
        if h.count('<h1') != 1: bad(s, 'h1이 1개가 아님', True)
        if 'application/ld+json' not in h: bad(s, '구조화 데이터 없음', True)
    if not os.path.exists(os.path.join(ST, 'og', s + '.jpg')): bad(s, 'og 이미지 없음 → python3 tools/make_og.py')
for c in build.CASES:
    common(c, 'case')
    for im in c['images']:
        if not os.path.exists(img_path(im['src'])): bad(c['slug'], f"사진 파일 없음: {im['src']}", True)
        if not im.get('alt'): bad(c['slug'], f"사진 alt 없음: {im['src']}", True)
for g in build.GUIDES:
    s = g['slug']; common(g, 'guide')
    if g.get('category') not in build.GUIDE_CAT: bad(s, f"category 값 오류: {g.get('category')}", True)
    t = os.path.join(ST, 'guides', s, 'thumb.jpg')
    if not os.path.exists(t): bad(s, '썸네일 없음 → python3 tools/make_thumb.py ' + s, True)
    elif Image.open(t).size != (1080, 1080): bad(s, f'썸네일 크기 {Image.open(t).size} (1080x1080이어야 함)', True)
    tt = g.get('thumb_title', '')
    if not tt: bad(s, 'thumb_title 없음', True)
    else:
        ls = [re.sub(r'\*', '', l).strip() for l in tt.split('|')]
        if len(ls) > 3: bad(s, 'thumb_title 3줄 초과', True)
        for l in ls:
            if len(l) > 11: bad(s, f"thumb_title 한 줄이 김({len(l)}자): '{l}' → 잘림 위험", True)
    if not g.get('thumb_sub'): bad(s, 'thumb_sub 없음')
    elif len(g['thumb_sub']) > 30: bad(s, f"thumb_sub {len(g['thumb_sub'])}자 (30자 이하)", True)
    figs = re.findall(r'^!\[.*?\]\((/guides/[^)]+)\)', g['body'], re.M)
    if not figs: bad(s, '설명 그림이 본문에 없음 (규칙 14)', True)
    for f in figs:
        w, h = Image.open(img_path(f)).size
        if w != 1200: bad(s, f'설명 그림 폭 {w}px (1200px이어야 함): {f}', True)
        if not 300 <= h <= 1600: bad(s, f'설명 그림 높이 {h}px 확인: {f}')
    n = len(re.sub(r'\s', '', g['body']))
    if not 1200 <= n <= 4000: bad(s, f'본문 길이 {n}자(공백 제외) 확인')
sm = os.path.join(DIST, 'sitemap.xml')
if os.path.exists(sm):
    x = open(sm, encoding='utf-8').read()
    for s in strict:
        kind = 'guide' if s in GUIDES else 'case'
        if f'/{kind}/{s}/' not in x: errs.append(f'[{s}] sitemap에 없음 (INDEX=1 SITE_URL=... 로 빌드했는지 확인)')
for s in strict:
    if s not in CASES and s not in GUIDES: errs.append(f'[{s}] 해당 slug의 글이 없음')
for w in warns: print('경고', w)
for e in errs: print('오류', e)
print(f"\n{'통과' if not errs else '실패'}: 오류 {len(errs)}개, 경고 {len(warns)}개")
sys.exit(1 if errs else 0)
