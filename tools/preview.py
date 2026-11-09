"""게시 전 화면 확인: python3 tools/preview.py <slug> [...]
dist/를 로컬로 띄워 휴대폰(390px)·PC(1280px) 전체 화면을 preview/<slug>-mobile.png, -desktop.png로 저장.
에이전트는 이 이미지를 직접 열어 그림 중복·잘림·겹침·빈 칸이 없는지 확인한 뒤에만 게시한다."""
import os, sys, threading, http.server, functools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import build
from playwright.sync_api import sync_playwright
ROOT = build.ROOT; OUT = os.path.join(ROOT, 'preview'); os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
h = functools.partial(Q, directory=build.OUT)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
gs = {g['slug'] for g in build.GUIDES}
with sync_playwright() as p:
    br = p.chromium.launch()
    for s in sys.argv[1:]:
        path = f"{'guide' if s in gs else 'case'}/{s}/"
        for name, w in [('mobile', 390), ('desktop', 1280)]:
            pg = br.new_page(viewport={'width': w, 'height': 900})
            pg.goto(f'http://127.0.0.1:{port}/{path}')
            pg.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(900)
            pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(200)
            broken = pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)")
            out = os.path.join(OUT, f'{s}-{name}.png'); pg.screenshot(path=out, full_page=True); pg.close()
            print(out, '깨진 이미지:', broken or '없음')
    # 목록 카드도 확인
    pg = br.new_page(viewport={'width': 390, 'height': 900}); pg.goto(f'http://127.0.0.1:{port}/guide/'); pg.wait_for_timeout(400)
    pg.screenshot(path=os.path.join(OUT, 'guide-list-mobile.png'), full_page=True); br.close()
srv.shutdown()
