"""설비 상식 썸네일(1080x1080) 생성: python3 tools/make_thumb.py [slug]
frontmatter: thumb_title (줄바꿈은 |, 강조할 단어는 *단어*), thumb_sub (한 줄)
결과: static/guides/<slug>/thumb.jpg  — 사이트 카드·네이버 블로그 대표 이미지용"""
import os, re, sys, html
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import build
from playwright.sync_api import sync_playwright
ROOT = build.ROOT
LOGO = open(os.path.join(ROOT, 'static/logo.svg')).read()
F = "'Noto Sans CJK KR','Noto Sans KR',sans-serif"
ICON = {  # 큰 배경 그림 (stroke)
 'leak': '<path d="M3 5h18M7 9v2M12 9v5M17 9v3"/><path d="M12 17c1 1.3 1.5 2.2 1.5 3a1.5 1.5 0 0 1-3 0c0-.8.5-1.7 1.5-3z"/>',
 'cost': '<path d="M3 5h18M7 9v2M12 9v5M17 9v3"/><path d="M12 17c1 1.3 1.5 2.2 1.5 3a1.5 1.5 0 0 1-3 0c0-.8.5-1.7 1.5-3z"/>',
 'drain': '<circle cx="12" cy="12" r="9"/><path d="M8.5 7.5v9M12 6v12M15.5 7.5v9"/>',
 'pipe': '<path d="M3 7h9a4 4 0 0 1 4 4v10"/><path d="M3 11h8a1 1 0 0 1 1 1v9"/><path d="M3 5v8M14 21h6"/>',
 'heating': '<path d="M3 20h18"/><path d="M5 16c1.5-2 3-2 4.5 0s3 2 4.5 0 3-2 4.5 0"/><path d="M8 4c1 1.2 1 2.3 0 3.5S7 9.8 8 11M12 4c1 1.2 1 2.3 0 3.5s-1 2.3 0 3.5M16 4c1 1.2 1 2.3 0 3.5s-1 2.3 0 3.5"/>',
 'bath': '<path d="M12 3l7 2.6V11c0 4.4-3 7.2-7 8.2-4-1-7-3.8-7-8.2V5.6z"/><path d="M12 8c1.4 1.9 2.2 3 2.2 4a2.2 2.2 0 0 1-4.4 0c0-1 .8-2.1 2.2-4z"/>',
 'season': '<path d="M12 2v20M4.9 4.9l14.2 14.2M2 12h20M4.9 19.1 19.1 4.9"/>',
}
def title_html(t):
    lines = [html.escape(x.strip()) for x in t.split('|')]
    lines = [re.sub(r'\*(.+?)\*', r'<span style="color:#FF8A4C">\1</span>', l) for l in lines]
    return '<br>'.join(lines)
def card(g):
    icon = ICON.get(g.get('category'), ICON['leak'])
    cat = build.GUIDE_CAT.get(g.get('category'), '설비 상식')
    return f'''<div style="width:1080px;height:1080px;position:relative;overflow:hidden;font-family:{F};color:#fff;
background:radial-gradient(90% 70% at 85% 90%,#1d4479 0%,#0B1F3A 65%);letter-spacing:-.03em;word-break:keep-all">
<svg style="position:absolute;right:-90px;bottom:-60px;opacity:.13" width="640" height="640" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{icon}</svg>
<div style="position:absolute;left:84px;top:96px;display:flex;gap:14px">
<span style="background:#E2510C;border-radius:999px;padding:12px 30px;font-size:34px;font-weight:800">설비 상식</span>
<span style="border:3px solid rgba(255,255,255,.35);border-radius:999px;padding:9px 28px;font-size:34px;font-weight:700;color:#C9D6EA">{html.escape(cat)}</span></div>
<div style="position:absolute;left:84px;right:84px;top:250px;font-size:116px;font-weight:900;line-height:1.18">{title_html(g.get('thumb_title') or g['title'])}</div>
<div style="position:absolute;left:84px;right:84px;bottom:220px;font-size:44px;font-weight:700;color:#E4ECF8;line-height:1.35">{html.escape(g.get('thumb_sub',''))}</div>
<div style="position:absolute;left:84px;bottom:84px;display:flex;align-items:center;gap:20px">
<div style="width:88px;height:88px">{LOGO}</div><div style="font-size:46px;font-weight:900">내집홈케어</div>
<div style="font-size:30px;color:#9FB3CC;font-weight:700;margin-left:6px">설비 경력 20년 이상</div></div></div>'''
want = sys.argv[1:]
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width': 1080, 'height': 1080})
    for g in build.GUIDES:
        if want and g['slug'] not in want:
            continue
        out = os.path.join(ROOT, 'static/guides', g['slug']); os.makedirs(out, exist_ok=True)
        pg.set_content(f'<html><body style="margin:0">{card(g)}</body></html>'); pg.wait_for_timeout(200)
        pg.screenshot(path=os.path.join(out, 'thumb.jpg'), type='jpeg', quality=88)
        print('thumb', g['slug'])
    br.close()
