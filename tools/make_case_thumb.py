"""네이버 현장일지 썸네일(1080x1080, 실제 현장 사진 배경 + 후킹 문구).
사용: python3 tools/make_case_thumb.py <사진> <출력.jpg> <번호> <지역 키워드> "<제목 줄1|*강조*|줄3>" "<부제>"
예: python3 tools/make_case_thumb.py static/cases/x/a.jpg out.jpg 23 "평택 누수탐지" "장판 밑 물,|*2.02%*에서|잡았다" "송탄 빌라 바닥 난방배관 누수"
규칙: 제목 3줄, 한 줄 9자 안팎. 숫자·장면은 현장 사실만(지어낸 수치 금지). 사진은 얼굴·호수·학교명·타 업체 글씨가 없는 컷."""
import base64, html, os, re, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(__file__), '..')
LOGO = open(os.path.join(ROOT, 'static/logo.svg')).read()
F = "'Noto Sans CJK KR','Noto Sans KR',sans-serif"
img, out, no, kw, title, sub = sys.argv[1:7]
def t(x):
    return '<br>'.join(re.sub(r'\*(.+?)\*', r'<span style="color:#FF8A4C">\1</span>', html.escape(l)) for l in x.split('|'))
d = base64.b64encode(open(img, 'rb').read()).decode()
h = f'''<div style="width:1080px;height:1080px;position:relative;overflow:hidden;font-family:{F};color:#fff;letter-spacing:-.03em;word-break:keep-all;background:url(data:image/jpeg;base64,{d}) 50% 50%/cover">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,31,58,.55) 0%,rgba(11,31,58,.25) 30%,rgba(11,31,58,.55) 55%,rgba(11,31,58,.95) 100%)"></div>
<div style="position:absolute;left:72px;top:72px;display:flex;gap:14px;align-items:center">
<span style="background:#E2510C;border-radius:14px;padding:10px 26px;font-size:46px;font-weight:900">작업일지 #{html.escape(no.lstrip('#'))}</span>
<span style="background:rgba(11,31,58,.75);border:3px solid rgba(255,255,255,.5);border-radius:14px;padding:8px 24px;font-size:40px;font-weight:800">{html.escape(kw)}</span></div>
<div style="position:absolute;left:72px;right:72px;bottom:250px;font-size:112px;font-weight:900;line-height:1.16;text-shadow:0 4px 18px rgba(0,0,0,.55)">{t(title)}</div>
<div style="position:absolute;left:72px;right:72px;bottom:168px;font-size:44px;font-weight:700;color:#E4ECF8;text-shadow:0 2px 10px rgba(0,0,0,.6)">{html.escape(sub)}</div>
<div style="position:absolute;left:72px;bottom:64px;display:flex;align-items:center;gap:18px">
<div style="width:76px;height:76px">{LOGO}</div><div style="font-size:42px;font-weight:900">내집홈케어</div>
<div style="font-size:32px;color:#C9D6EA;font-weight:700">배관무사 · 010-2877-5304</div></div></div>'''
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1080})
    pg.set_content(f'<html><body style="margin:0">{h}</body></html>'); pg.wait_for_timeout(300)
    pg.screenshot(path=out, type='jpeg', quality=88); b.close()
print('thumb', out)
