"""링크 미리보기(OG) 이미지 생성. 새 사례를 추가하면 다시 실행: python3 tools/make_og.py
결과: static/og/default.jpg, static/og/<slug>.jpg (1200x630)"""
import json, os, sys, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import build
from playwright.sync_api import sync_playwright
ROOT = build.ROOT; B = build.B
logo = open(os.path.join(ROOT, 'static/logo.svg')).read()
FONT = "'Pretendard','Noto Sans CJK KR','Noto Sans KR',sans-serif"
def data_uri(p):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
def card_default():
    return f'''<div style="width:1200px;height:630px;background:radial-gradient(900px 500px at 90% -10%,#1C3F73,transparent 60%),#0B1F3A;color:#fff;font-family:{FONT};display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box">
<div style="display:flex;align-items:center;gap:30px"><div style="width:150px;height:150px;border-radius:34px;box-shadow:0 0 0 3px rgba(255,255,255,.18);overflow:hidden">{logo}</div>
<div><div style="font-size:96px;font-weight:800;letter-spacing:-3px;line-height:1">{B['name']}</div>
<div style="font-size:38px;color:#C9D6EA;margin-top:14px;font-weight:600">{B['tagline']}</div></div></div>
<div style="margin-top:56px;display:flex;align-items:center;gap:22px">
<div style="background:#E2510C;border-radius:20px;padding:18px 34px;font-size:46px;font-weight:800;white-space:nowrap">☎ {B['phone']}</div>
<div style="font-size:32px;color:#E4ECF8;font-weight:600;line-height:1.4">{B['hours']} · {B['region']} 출동<br>{' · '.join(B['areas'])}</div></div></div>'''
def card_case(c):
    img = data_uri(os.path.join(ROOT, 'static', c['cover'].lstrip('/')))
    return f'''<div style="width:1200px;height:630px;position:relative;font-family:{FONT};color:#fff;overflow:hidden;background:#0B1F3A">
<img src="{img}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,31,58,0) 30%,rgba(11,31,58,.92) 72%)"></div>
<div style="position:absolute;left:60px;right:60px;bottom:50px;display:flex;align-items:center;gap:26px">
<div style="width:110px;height:110px;flex:none">{logo}</div>
<div style="flex:1;min-width:0"><div style="font-size:58px;font-weight:800;letter-spacing:-2px">{B['name']}</div>
<div style="font-size:32px;color:#DCE6F5;font-weight:600;margin-top:6px">{build.case_place(c)} · {build.SERVICE.get(c.get('service'),'')} 실제 현장</div></div>
<div style="background:#E2510C;border-radius:18px;padding:16px 26px;font-size:38px;font-weight:800;white-space:nowrap">☎ {B['phone']}</div></div></div>'''
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width':1200,'height':630})
    def shot(html, out):
        pg.set_content(f'<html><body style="margin:0">{html}</body></html>'); pg.wait_for_timeout(200)
        pg.screenshot(path=out, type='jpeg', quality=85)
    shot(card_default(), os.path.join(ROOT, 'static/og/default.jpg'))
    for c in build.CASES:
        shot(card_case(c), os.path.join(ROOT, f"static/og/{c['slug']}.jpg"))
    pg.set_viewport_size({'width':180,'height':180})
    pg.set_content(f'<html><body style="margin:0;width:180px;height:180px">{logo}</body></html>')
    pg.screenshot(path=os.path.join(ROOT, 'static/apple-touch-icon.png'))
    br.close()
print('og done', len(build.CASES) + 1)
