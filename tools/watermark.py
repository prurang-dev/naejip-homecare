"""현장 사진 워터마크(오른쪽 아래 '로고 + 내집홈케어 · 010-2877-5304').
사용: python3 tools/watermark.py [--backup <원본 보관 폴더>]
- static/cases/**/*.jpg 중 아직 안 찍은 사진만 처리(기록: tools/watermarked.json). 여러 번 돌려도 두 번 찍히지 않음.
- --backup 을 주면 찍기 전 원본을 그 폴더에 같은 경로로 복사(운영 저장소 naejip-ops/originals 권장).
- prepublish.sh 가 자동 실행. 설비 상식 그림(static/guides)과 OG 이미지는 대상 아님."""
import json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
REC = os.path.join(ROOT, 'tools', 'watermarked.json')
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
if not os.path.exists(FONT):
    FONT = next((os.path.join(d, f) for d, _, fs in os.walk('/usr/share/fonts') for f in fs if 'NotoSansCJK' in f or 'NanumGothicBold' in f), None)
TEXT = '내집홈케어 · 010-2877-5304'
backup = sys.argv[sys.argv.index('--backup') + 1] if '--backup' in sys.argv else None
done = set(json.load(open(REC))) if os.path.exists(REC) else set()
logo0 = Image.open(os.path.join(ROOT, 'tools', 'wm_logo.png')).convert('RGBA')

def mark(path):
    im = Image.open(path).convert('RGB'); W, H = im.size; s = min(W, H)
    fs = max(18, round(s * 0.034)); pad = round(fs * 0.55); m = round(s * 0.03)
    font = ImageFont.truetype(FONT, fs)
    tw = font.getbbox(TEXT)[2]; lh = round(fs * 1.25)
    logo = logo0.resize((lh, lh))
    bw, bh = pad + lh + round(fs * .45) + tw + pad, lh + pad
    x0, y0 = W - m - bw, H - m - bh
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=bh // 2, fill=(11, 31, 58, 120))
    ov.alpha_composite(logo, (x0 + pad, y0 + (bh - lh) // 2))
    d.text((x0 + pad + lh + round(fs * .45), y0 + bh // 2), TEXT, font=font, fill=(255, 255, 255, 225), anchor='lm')
    Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB').save(path, quality=86, optimize=True)

n = 0
for d, _, fs in os.walk(os.path.join(ROOT, 'static', 'cases')):
    for f in sorted(fs):
        if not f.lower().endswith(('.jpg', '.jpeg')):
            continue
        p = os.path.join(d, f); rel = os.path.relpath(p, os.path.join(ROOT, 'static'))
        if rel in done:
            continue
        if backup:
            dst = os.path.join(backup, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst): shutil.copy2(p, dst)
        mark(p); done.add(rel); n += 1
json.dump(sorted(done), open(REC, 'w'), ensure_ascii=False, indent=0)
print(f'watermark: {n}장 새로 처리, 누적 {len(done)}장')
