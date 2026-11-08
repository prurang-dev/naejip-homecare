#!/usr/bin/env python3
"""의존성 없는 정적 사이트 빌더.

  python3 build.py                 # dist/ 에 사이트 생성
  BASE=/repo/ python3 build.py     # GitHub Pages 프로젝트 주소용
  SITE_URL=https://xxx.kr INDEX=1 python3 build.py   # 정식 도메인 + 검색 노출 허용

콘텐츠: content/cases/*.md (현장) · content/guides/*.md (설비 상식) · 업체 정보: data/business.json · 이미지/영상: static/
"""
import html, json, os, re, shutil, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist')
BASE = os.environ.get('BASE', '/')
if not BASE.endswith('/'):
    BASE += '/'
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')
INDEX = os.environ.get('INDEX') == '1'   # 도메인 확정 전까지는 검색 노출 차지

B = json.load(open(os.path.join(ROOT, 'data/business.json'), encoding='utf-8'))
RV = json.load(open(os.path.join(ROOT, 'data/reviews.json'), encoding='utf-8'))
TEL = re.sub(r'[^0-9]', '', B['phone'])
SMS = re.sub(r'[^0-9]', '', B['sms'])

SERVICE = {'leak': '누수 탐지·공사', 'drain': '하수구·배관', 'inspect': '배관 점검'}
AREA = {'pyeongtaek': '평택', 'cheonan': '천안', 'cheonan-seobuk': '천안', 'suwon': '수원',
        'yongin': '용인', 'osan': '오산', 'hwaseong': '화성', 'seoul-gangnam': '서울 강남'}


def u(path):
    """사이트 내부 경로에 BASE를 붙인다."""
    return BASE + path.lstrip('/')


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------- frontmatter / markdown ----------------
def parse_md(path):
    raw = open(path, encoding='utf-8').read()
    _, fm, body = raw.split('---', 2)
    meta, images, cur = {}, [], None
    for line in fm.strip('\n').split('\n'):
        line = re.sub(r'\s+#.*$', '', line)
        if not line.strip():
            continue
        if line.startswith('  - src:'):
            cur = {'src': line.split(':', 1)[1].strip()}
            images.append(cur)
        elif line.startswith('    alt:') and cur is not None:
            cur['alt'] = line.split(':', 1)[1].strip()
        elif re.match(r'^[a-z_]+:', line):
            k, v = line.split(':', 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            meta[k] = v
    meta['images'] = images
    meta['body'] = body.strip()
    meta['slug'] = os.path.splitext(os.path.basename(path))[0]
    return meta


def inline(s):
    s = esc(s)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def md_to_html(md):
    out = []
    for block in re.split(r'\n\s*\n', md.strip()):
        lines = block.strip().split('\n')
        first = lines[0]
        if first.startswith('## '):
            out.append(f'<h2>{inline(first[3:])}</h2>')
            if len(lines) > 1:
                out.append('<p>' + '<br>'.join(inline(l) for l in lines[1:]) + '</p>')
        elif all(l.startswith('- ') for l in lines):
            out.append('<ul>' + ''.join(f'<li>{inline(l[2:])}</li>' for l in lines) + '</ul>')
        else:
            out.append('<p>' + '<br>'.join(inline(l) for l in lines) + '</p>')
    return '\n'.join(out)


def case_date(c):
    d = c.get('date', '')
    parts = [p for p in d.split('-') if p]
    return '.'.join(parts)


def case_place(c):
    area = AREA.get(c.get('area', ''), '')
    dong = c.get('dong', '')
    return area if (not dong or dong == area) else f'{area} {dong}'


def sort_key(c):
    d = c.get('date', '')
    parts = [p for p in d.split('-') if p] + ['00', '00']
    return '-'.join(parts[:3])


CASES = sorted([parse_md(p) for p in glob.glob(os.path.join(ROOT, 'content/cases/*.md'))],
               key=sort_key, reverse=True)
BY_SLUG = {c['slug']: c for c in CASES}
GUIDES = sorted([parse_md(p) for p in glob.glob(os.path.join(ROOT, 'content/guides/*.md'))],
                key=sort_key, reverse=True)
GUIDE_CAT = {'leak': '누수', 'drain': '하수구·막힘', 'pipe': '배관', 'heating': '난방·보일러배관',
             'bath': '욕실·방수', 'season': '계절 관리', 'cost': '비용·책임'}


# ---------------- icons ----------------
def icon(name, size=22):
    paths = {
        'phone': '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
        'msg': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        'check': '<path d="M20 6 9 17l-5-5"/>',
        'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
        'pin': '<path d="M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
        'drop': '<path d="M12 3c3 4.5 6 7.8 6 11a6 6 0 0 1-12 0c0-3.2 3-6.5 6-11z"/>',
        'drain': '<circle cx="12" cy="12" r="9"/><path d="M8.5 7.5v9M12 6v12M15.5 7.5v9"/>',
        'toilet': '<path d="M6 3h6v7H6zM4 10h16a7 7 0 0 1-7 7h-2l1 4H8l1-4.4"/>',
        'ceiling': '<path d="M3 5h18M7 9v2M12 9v5M17 9v3"/><path d="M12 17c1 1.3 1.5 2.2 1.5 3a1.5 1.5 0 0 1-3 0c0-.8.5-1.7 1.5-3z"/>',
        'floor': '<path d="M3 19h18M6 15c1.2-1.5 2.4-1.5 3.6 0s2.4 1.5 3.6 0 2.4-1.5 3.6 0"/><path d="M12 4v7M9 8l3 3 3-3"/>',
        'won': '<path d="M4 7l3 10 3-8 2 0 3 8 3-10M3 11h18M3 14h18"/>',
        'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        'camera': '<path d="M4 7h3l2-3h6l2 3h3v12H4z"/><circle cx="12" cy="13" r="3.5"/>',
        'shield': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    }
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>')


# ---------------- layout ----------------
def ld_business():
    d = {
        '@context': 'https://schema.org', '@type': 'Plumber',
        'name': B['name'], 'telephone': B['phone'],
        'areaServed': [{'@type': 'City', 'name': a} for a in B['areas'] + B['areas_more']],
        'description': f"{B['region']} {'·'.join(B['areas'])} {B['tagline']}",
    }
    if SITE_URL:
        d['url'] = SITE_URL + BASE
    if not B['address'].startswith('['):
        d['address'] = B['address']
    same = [x for x in [RV.get('google_profile_url'), RV.get('naver_place_url'), B.get('naver_blog')] if x]
    if same:
        d['sameAs'] = same
    d['openingHours'] = 'Mo-Su 00:00-23:59'
    return json.dumps(d, ensure_ascii=False)


def page(title, desc, path, body, og_image=None):
    canonical = (SITE_URL + u(path)) if SITE_URL else ''
    robots = 'index,follow' if INDEX else 'noindex,nofollow'
    og_image = og_image or 'og/default.jpg'
    og = (f'<meta property="og:image" content="{esc((SITE_URL or "") + u(og_image))}">'
          '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
          f'<meta property="og:url" content="{esc(canonical)}">')
    canon = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''
    guide_nav = f'<a href="{u("guide/")}">설비 상식</a>' if GUIDES else ''
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
{canon}
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{og}
<meta property="og:site_name" content="{esc(B['name'])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="naver-site-verification" content="513c391f367bddbff12bcc71363935d685d76473">
<meta name="theme-color" content="#0B1F3A">
<link rel="icon" href="{u('favicon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{u('apple-touch-icon.png')}">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{u('assets/site.css')}">
<script type="application/ld+json">{ld_business()}</script>
</head>
<body>
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="top">
  <div class="wrap top-in">
    <a class="logo" href="{u('')}"><img class="logo-mark" src="{u('logo.svg')}" alt="" width="40" height="40"><span class="logo-text">{esc(B['name'])}<span>{esc(B['tagline'])}</span></span></a>
    <nav class="nav" aria-label="주 메뉴">
      <a href="{u('')}#symptoms">증상별 상담</a>
      <a href="{u('')}#equipment">탐지 장비</a>
      <a href="{u('case/')}">시공 사례</a>
      {guide_nav}
      <a href="{u('')}#area">출동 지역</a>
    </nav>
    <a class="top-call" href="tel:{TEL}">{icon('phone', 18)}<span>{esc(B['phone'])}</span></a>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap">
    <p class="foot-name"><img src="{u('logo.svg')}" alt="" width="28" height="28">{esc(B['name'])}</p>
    <p>{' · '.join(x for x in [('대표 ' + esc(B['owner'])) if not B['owner'].startswith('[') else '', '사업자등록번호 ' + esc(B['biz_no'])] if x)}</p>
    <p>{(esc(B['address']) + ' · ') if not B['address'].startswith('[') else ''}전화 <a href="tel:{TEL}">{esc(B['phone'])}</a></p>
    <p>출동 지역: {esc(B['region'])} ({esc(' · '.join(B['areas']))} 외 {esc(' · '.join(B['areas_more']))})</p>
    <p class="foot-small">© {esc(B['name'])}</p>
  </div>
</footer>
<div class="dock" role="region" aria-label="빠른 연락">
  <a class="dock-call" href="tel:{TEL}">{icon('phone', 20)}<span>전화 상담</span><b>{esc(B['phone'])}</b></a>
  <a class="dock-sms" href="sms:{SMS}">{icon('msg', 20)}<span>사진 문자</span></a>
</div>
</body>
</html>
'''


def call_block(title, sub):
    return f'''<div class="cta">
  <div>
    <p class="cta-title">{title}</p>
    <p class="cta-sub">{sub}</p>
  </div>
  <div class="cta-actions">
    <a class="btn btn-call btn-lg" href="tel:{TEL}">{icon('phone', 22)}<span>{esc(B['phone'])}</span></a>
    <a class="btn btn-ghost" href="sms:{SMS}">{icon('msg', 18)}<span>사진 찍어 문자 보내기</span></a>
  </div>
</div>'''


def case_card(c, small=False):
    cover = c.get('cover') or (c['images'][0]['src'] if c['images'] else '')
    return f'''<a class="case-card" href="{u('case/' + c['slug'] + '/')}">
  <span class="case-img"><img src="{u(cover)}" alt="" loading="lazy" decoding="async"></span>
  <span class="case-meta"><span class="tag">{esc(SERVICE.get(c.get('service'), ''))}</span><span>{esc(case_place(c))}</span></span>
  <span class="case-title">{esc(c['title'])}</span>
</a>'''


# ---------------- home ----------------
def home():
    trust = ['장비로 원인부터 확인', '필요한 곳만 부분 시공', '작업 사진·영상 공유']
    if B.get('arrival_minutes'):
        trust.insert(0, f"평균 {B['arrival_minutes']}분 출동")
    if B.get('warranty_months'):
        trust.append(f"시공 후 A/S {B['warranty_months']}개월")
    trust_html = ''.join(f'<li>{icon("check", 18)}<span>{esc(t)}</span></li>' for t in trust)

    hero_pics = [BY_SLUG[s] for s in [
        '2026-11-songtan-villa-floor-heating-leak', '2026-11-03-cheonan-buldang-villa-hotwater-leak',
        '2026-11-yeoksam-villa-bathroom-dye-test', '2026-10-godeok-villa-heating-thermal-check'] if s in BY_SLUG]
    hero_grid = ''.join(
        f'<a class="hp" href="{u("case/" + c["slug"] + "/")}"><img src="{u(c["cover"])}" alt="{esc(case_place(c))} 실제 현장 사진" '
        f'loading="eager" decoding="async"><span>{esc(case_place(c))}</span></a>' for c in hero_pics)

    symptoms = [
        ('ceiling', '아랫집 천장에 물이 샌다', '위층 배관·욕실 방수·유가 문제일 수 있어요'),
        ('floor', '바닥·장판 밑에서 물이 올라온다', '바닥 속 난방·온수 배관 누수 가능성'),
        ('drain', '싱크대·하수구가 막혔다', '물이 안 내려가거나 역류할 때'),
        ('toilet', '변기가 막혔다', '뚫어뻥으로 안 될 때, 넘칠 때'),
        ('won', '수도요금이 갑자기 올랐다', '보이지 않는 곳에서 새고 있을 수 있어요'),
        ('drop', '욕실 배수구 주변이 샌다', '유가 둘레·줄눈 틈으로 스며드는 경우'),
    ]
    sym_html = ''.join(f'''<a class="sym" href="tel:{TEL}">
  <span class="sym-ico">{icon(ic, 26)}</span>
  <span class="sym-t">{esc(t)}</span>
  <span class="sym-d">{esc(d)}</span>
  <span class="sym-go">{icon('phone', 15)} 바로 상담</span>
</a>''' for ic, t, d in symptoms)

    equip = [
        ('가압 테스트', '배관에 압력을 걸어 어느 배관이 새는지 숫자로 확인합니다.', '2026-11-03-cheonan-buldang-villa-hotwater-leak'),
        ('수소가스 누수탐지', '바닥 속 새는 지점을 가스 농도로 좁혀, 바닥을 손바닥만큼만 엽니다.', '2026-11-songtan-villa-floor-heating-leak'),
        ('열화상 카메라', '바닥을 뜯지 않고 난방 배관의 흐름과 이상 여부를 봅니다.', '2026-10-godeok-villa-heating-thermal-check'),
        ('관로탐지기', '도면 없는 건물에서도 하수구 배관이 지나가는 길을 찾습니다.', '2026-11-yeoksam-stairs-drain-locating'),
        ('담수·색소 테스트', '방수 문제인지 하수관 문제인지, 색으로 원인을 가립니다.', '2026-11-yeoksam-villa-bathroom-dye-test'),
    ]
    eq_html = ''.join(f'''<a class="eq" href="{u('case/' + s + '/')}">
  <span class="eq-img"><img src="{u(BY_SLUG[s]['cover'])}" alt="{esc(n)} 실제 사용 현장" loading="lazy" decoding="async"></span>
  <span class="eq-body"><span class="eq-n">{esc(n)}</span><span class="eq-d">{esc(d)}</span>
  <span class="eq-link">{esc(case_place(BY_SLUG[s]))} 현장 보기 {icon('arrow', 15)}</span></span>
</a>''' for n, d, s in equip if s in BY_SLUG)

    cases_html = ''.join(case_card(c) for c in CASES[:6])

    reviews_html = ''
    if RV.get('reviews'):
        cards = []
        for r in RV['reviews'][:6]:
            stars = '★' * int(r.get('rating', 5))
            img = f'<img src="{u(r["image"])}" alt="{esc(r.get("source", ""))} 실제 리뷰 캡처" loading="lazy">' if r.get('image') else ''
            cards.append(f'<figure class="rv"><p class="rv-stars" aria-label="별점 {len(stars)}점">{stars}</p>'
                         f'<blockquote>{esc(r.get("text", ""))}</blockquote>{img}'
                         f'<figcaption>{esc(r.get("area", ""))} · {esc(r.get("source", ""))} 리뷰</figcaption></figure>')
        links = ''.join(f'<a class="more" href="{esc(url)}">{label} 리뷰 전체 보기 {icon("arrow", 16)}</a>'
                        for label, url in [('구글', RV.get('google_review_url')), ('네이버', RV.get('naver_place_url'))] if url)
        reviews_html = f'''<section class="sec" id="reviews">
  <div class="wrap">
    <div class="sec-head"><div><p class="eyebrow">고객 리뷰</p><h2 class="h2">직접 맡겨 보신 분들의 이야기</h2></div><div>{links}</div></div>
    <div class="rv-grid">{''.join(cards)}</div>
  </div>
</section>'''

    steps = [('전화·문자 상담', '증상을 말씀해 주세요. 사진을 보내 주시면 더 정확합니다.'),
             ('방문 · 원인 확인', '장비로 새는 곳, 막힌 곳을 먼저 찾습니다.'),
             ('견적 안내 후 작업', '확인한 원인과 작업 범위를 설명드리고 시작합니다.'),
             ('결과 공유', '작업 전후 사진과 영상으로 결과를 보여드립니다.')]
    steps_html = ''.join(f'<li><span class="st-n">{i}</span><span class="st-t">{esc(t)}</span><span class="st-d">{esc(d)}</span></li>'
                         for i, (t, d) in enumerate(steps, 1))

    faqs = [
        ('어디서 새는지 모르는데 불러도 되나요?', '네. 원인을 찾는 것부터가 저희 일입니다. 가압 테스트, 가스 탐지, 열화상, 색소 테스트 등 상황에 맞는 장비로 새는 배관과 위치를 먼저 확인합니다.'),
        ('바닥을 다 뜯어야 하나요?', '대부분 아닙니다. 새는 지점을 장비로 좁힌 뒤 그 자리만 부분적으로 열어 작업하고, 연 자리는 다시 메워 복구합니다.'),
        ('아랫집에 피해가 생겼어요.', '가입하신 보험에 일상생활배상책임 특약이 있는지 확인해 보세요. 보험 처리에는 누수 원인 확인 자료가 필요한 경우가 많아, 탐지 과정을 사진과 영상으로 남겨 드립니다.'),
        ('욕실 방수를 전부 다시 해야 하나요?', '원인이 유가 둘레나 줄눈처럼 한 부분에 있다면 그 부분만 고쳐 비용을 줄일 수 있습니다. 하수관 문제라면 방수를 해도 계속 새기 때문에, 테스트로 원인을 먼저 가립니다.'),
    ]
    faq_html = ''.join(f'<details class="faq"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faqs)

    area_html = ''.join(f'<li class="chip chip-strong">{icon("pin", 16)}{esc(a)}</li>' for a in B['areas']) + \
        ''.join(f'<li class="chip">{esc(a)}</li>' for a in B['areas_more'])

    body = f'''
<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-text">
      <p class="live"><span class="dot" aria-hidden="true"></span>{esc(B['hours'])} · {esc(B['region'])} 출동</p>
      <h1>물이 새거나 막혔나요?<br><em>지금 전화 주세요.</em></h1>
      <p class="hero-sub">누수탐지 · 하수구 · 배관 공사. 장비로 원인부터 찾고, 필요한 곳만 고칩니다.</p>
      <div class="hero-cta">
        <a class="btn btn-call btn-xl" href="tel:{TEL}">{icon('phone', 26)}<span class="b-col"><small>터치하면 바로 연결</small><span>{esc(B['phone'])}</span></span></a>
        <a class="btn btn-ghost-dark" href="sms:{SMS}">{icon('msg', 18)}<span>현장 사진 찍어 문자로 상담</span></a>
      </div>
      <ul class="trust">{trust_html}</ul>
    </div>
    <div class="hero-pics" aria-label="실제 현장 사진">
      {hero_grid}
      <p class="hp-note">{icon('camera', 15)} 모두 저희가 직접 작업한 실제 현장입니다</p>
    </div>
  </div>
</section>

<section class="sec" id="symptoms">
  <div class="wrap">
    <p class="eyebrow">증상별 상담</p>
    <h2 class="h2">지금 어떤 상황인가요?</h2>
    <p class="lead">해당하는 증상을 누르면 바로 전화로 연결됩니다.</p>
    <div class="sym-grid">{sym_html}</div>
  </div>
</section>

<section class="sec sec-soft" id="equipment">
  <div class="wrap">
    <p class="eyebrow">짐작이 아니라 장비로</p>
    <h2 class="h2">원인부터 정확하게 찾습니다</h2>
    <p class="lead">원인을 모르고 뜯으면 공사가 커집니다. 상황에 맞는 장비로 새는 곳을 먼저 확인합니다.</p>
    <div class="eq-grid">{eq_html}</div>
  </div>
</section>

<section class="sec" id="cases">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="eyebrow">시공 사례</p><h2 class="h2">최근 다녀온 현장</h2></div>
      <a class="more" href="{u('case/')}">전체 {len(CASES)}건 보기 {icon('arrow', 16)}</a>
    </div>
    <div class="case-grid">{cases_html}</div>
  </div>
</section>

{guides_home()}
{reviews_html}
<section class="sec sec-soft">
  <div class="wrap">
    <p class="eyebrow">진행 과정</p>
    <h2 class="h2">전화 한 통이면 나머지는 저희가 합니다</h2>
    <ol class="steps">{steps_html}</ol>
  </div>
</section>

<section class="sec" id="area">
  <div class="wrap area">
    <div>
      <p class="eyebrow">출동 지역</p>
      <h2 class="h2">평택을 중심으로<br>{esc(B['region'])} 출동</h2>
      <p class="lead">{esc(' · '.join(B['areas']))}을 중심으로 출동합니다.</p>
      <ul class="chips">{area_html}</ul>
    </div>
    <div class="faqs">
      <p class="eyebrow">자주 묻는 질문</p>
      {faq_html}
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">{call_block('물 새는 건 기다릴수록 피해가 커집니다', f"{esc(B['hours'])} · {esc(B['region'])} 출동")}</div>
</section>
'''
    title = f"{B['name']} | {' · '.join(B['areas'])} 누수탐지 · 하수구 · 배관"
    desc = f"{B['region']} {' · '.join(B['areas'])} 누수탐지, 하수구 막힘, 배관 공사. 가압·가스·열화상 장비로 원인을 찾고 필요한 곳만 고칩니다. {B['phone']}"
    return page(title, desc, '', body, og_image='og/default.jpg')


# ---------------- case list / detail ----------------
def case_list():
    body = f'''
<section class="sec page-head">
  <div class="wrap">
    <p class="eyebrow">시공 사례</p>
    <h1 class="h1">실제 현장 {len(CASES)}건</h1>
    <p class="lead">모든 사진은 저희가 직접 작업한 현장입니다.</p>
    <div class="case-grid">{''.join(case_card(c) for c in CASES)}</div>
  </div>
</section>
<section class="sec"><div class="wrap">{call_block('비슷한 증상이 있나요?', '사진을 문자로 보내 주시면 더 빠르게 상담해 드립니다.')}</div></section>'''
    return page(f"시공 사례 | {B['name']}", f"{' · '.join(B['areas'])} 누수탐지·하수구·배관 실제 시공 사례 {len(CASES)}건", 'case/', body)


def case_page(c):
    gallery = ''.join(
        f'<figure><img src="{u(im["src"])}" alt="{esc(im.get("alt", ""))}" loading="lazy" decoding="async">'
        f'<figcaption>{esc(im.get("alt", ""))}</figcaption></figure>' for im in c['images'])
    video = ''
    if c.get('video'):
        video = (f'<figure class="vid"><video src="{u(c["video"])}" controls muted playsinline preload="metadata"></video>'
                 f'<figcaption>현장 영상</figcaption></figure>')
    related = [x for x in CASES if x['slug'] != c['slug'] and x.get('service') == c.get('service')][:3]
    if len(related) < 3:
        related += [x for x in CASES if x['slug'] != c['slug'] and x not in related][:3 - len(related)]
    cover = c.get('cover') or (c['images'][0]['src'] if c['images'] else '')
    body = f'''
<article class="sec page-head">
  <div class="wrap narrow">
    <nav class="crumb" aria-label="위치"><a href="{u('')}">홈</a> / <a href="{u('case/')}">시공 사례</a></nav>
    <p class="case-meta big"><span class="tag">{esc(SERVICE.get(c.get('service'), ''))}</span><span>{esc(case_place(c))}</span><span>{esc(c.get('building', ''))}</span><span>{esc(case_date(c))}</span></p>
    <h1 class="h1">{esc(c['title'])}</h1>
    <p class="lead">{esc(c.get('description', ''))}</p>
    <img class="cover" src="{u(cover)}" alt="{esc(c['title'])}" decoding="async">
    <div class="mini-cta"><span>같은 증상이라면 지금 바로 상담하세요</span><a class="btn btn-call" href="tel:{TEL}">{icon('phone', 18)}<span>{esc(B['phone'])}</span></a></div>
    <div class="prose">{md_to_html(c['body'])}</div>
    <h2 class="h3">현장 사진</h2>
    <div class="gallery">{video}{gallery}</div>
    {call_block('같은 증상으로 고민 중이신가요?', f"{esc(case_place(c))}을 비롯해 {esc(B['region'])} 출동")}
    <h2 class="h3">다른 현장</h2>
    <div class="case-grid three">{''.join(case_card(x) for x in related)}</div>
  </div>
</article>'''
    og = f"og/{c['slug']}.jpg" if os.path.exists(os.path.join(ROOT, 'static/og', c['slug'] + '.jpg')) else None
    return page(f"{c['title']} | {B['name']}", c.get('description', ''), f"case/{c['slug']}/", body, og_image=og)


# ---------------- guides (설비 상식) ----------------
def guide_card(g):
    return f'''<a class="guide-card" href="{u('guide/' + g['slug'] + '/')}">
  <span class="tag">{esc(GUIDE_CAT.get(g.get('category'), '설비 상식'))}</span>
  <span class="guide-title">{esc(g['title'])}</span>
  <span class="guide-desc">{esc(g.get('description', ''))}</span>
</a>'''


def guides_home():
    if not GUIDES:
        return ''
    return f'''<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="eyebrow">설비 상식</p><h2 class="h2">부르기 전에 알아 두면 좋은 것</h2></div>
      <a class="more" href="{u('guide/')}">전체 {len(GUIDES)}개 보기 {icon('arrow', 16)}</a>
    </div>
    <div class="guide-grid">{''.join(guide_card(g) for g in GUIDES[:4])}</div>
  </div>
</section>'''


def guide_list():
    body = f'''
<section class="sec page-head">
  <div class="wrap">
    <p class="eyebrow">설비 상식</p>
    <h1 class="h1">누수 · 하수구 · 배관, 알아 두면 좋은 것</h1>
    <p class="lead">현장에서 자주 받는 질문을 정리했습니다.</p>
    <div class="guide-grid">{''.join(guide_card(g) for g in GUIDES)}</div>
  </div>
</section>
<section class="sec"><div class="wrap">{call_block('직접 해결이 어렵다면', '사진을 문자로 보내 주시면 먼저 봐 드립니다.')}</div></section>'''
    return page(f"설비 상식 | {B['name']}", "누수·하수구·배관 문제를 겪을 때 알아 두면 좋은 정보", 'guide/', body)


def ld_article(g):
    d = {'@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'],
         'description': g.get('description', ''), 'inLanguage': 'ko',
         'author': {'@type': 'Organization', 'name': B['name']},
         'publisher': {'@type': 'Organization', 'name': B['name']}}
    if g.get('date'):
        d['datePublished'] = g['date']
    if SITE_URL:
        d['mainEntityOfPage'] = SITE_URL + u(f"guide/{g['slug']}/")
    return json.dumps(d, ensure_ascii=False)


def guide_page(g):
    rel_cases = [BY_SLUG[x.strip()] for x in g.get('related_cases', '').split(',') if x.strip() in BY_SLUG]
    if not rel_cases:
        rel_cases = [c for c in CASES if c.get('service') == g.get('service')][:3]
    other = [x for x in GUIDES if x['slug'] != g['slug'] and x.get('category') == g.get('category')][:3]
    if len(other) < 3:
        other += [x for x in GUIDES if x['slug'] != g['slug'] and x not in other][:3 - len(other)]
    cover = g.get('cover', '')
    cover_html = f'<img class="cover" src="{u(cover)}" alt="{esc(g["title"])}" decoding="async">' if cover else ''
    cases_html = (f'<h2 class="h3">관련 시공 사례</h2><div class="case-grid three">{"".join(case_card(c) for c in rel_cases[:3])}</div>'
                  if rel_cases else '')
    other_html = (f'<h2 class="h3">다른 설비 상식</h2><div class="guide-grid">{"".join(guide_card(x) for x in other)}</div>'
                  if other else '')
    body = f'''
<article class="sec page-head">
  <div class="wrap narrow">
    <nav class="crumb" aria-label="위치"><a href="{u('')}">홈</a> / <a href="{u('guide/')}">설비 상식</a></nav>
    <p class="case-meta big"><span class="tag">{esc(GUIDE_CAT.get(g.get('category'), '설비 상식'))}</span><span>{esc(g.get('date', ''))}</span></p>
    <h1 class="h1">{esc(g['title'])}</h1>
    <p class="lead">{esc(g.get('description', ''))}</p>
    {cover_html}
    <div class="prose">{md_to_html(g['body'])}</div>
    {call_block('혼자 해결이 어렵다면 전화 주세요', f"{esc(B['hours'])} · {esc(B['region'])} 출동")}
    {cases_html}
    {other_html}
  </div>
</article>
<script type="application/ld+json">{ld_article(g)}</script>'''
    og = f"og/{g['slug']}.jpg" if os.path.exists(os.path.join(ROOT, 'static/og', g['slug'] + '.jpg')) else None
    return page(f"{g['title']} | {B['name']}", g.get('description', ''), f"guide/{g['slug']}/", body, og_image=og)


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(content)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'static'), OUT)
    write('index.html', home())
    write('case/index.html', case_list())
    for c in CASES:
        write(f"case/{c['slug']}/index.html", case_page(c))
    if GUIDES:
        write('guide/index.html', guide_list())
        for g in GUIDES:
            write(f"guide/{g['slug']}/index.html", guide_page(g))
    write('404.html', page(f"페이지를 찾을 수 없습니다 | {B['name']}", '', '404.html',
                           f'<section class="sec page-head"><div class="wrap narrow"><h1 class="h1">페이지를 찾을 수 없습니다</h1>'
                           f'<p class="lead"><a href="{u("")}">홈으로 가기</a></p>{call_block("급하신가요?", "바로 전화 주세요.")}</div></section>'))
    if INDEX and SITE_URL:
        urls = [u('')] + [u('case/')] + [u(f"case/{c['slug']}/") for c in CASES] + \
            ([u('guide/')] + [u(f"guide/{g['slug']}/") for g in GUIDES] if GUIDES else [])
        sm = ''.join(f'<url><loc>{esc(SITE_URL + x)}</loc></url>' for x in urls)
        write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
        write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}{u("sitemap.xml")}\n')
    else:
        write('robots.txt', 'User-agent: *\nDisallow: /\n')
    write('.nojekyll', '')
    print(f'built {len(CASES)} cases, {len(GUIDES)} guides -> {OUT} (BASE={BASE}, INDEX={INDEX})')


if __name__ == '__main__':
    main()
