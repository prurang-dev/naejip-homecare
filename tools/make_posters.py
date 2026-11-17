"""현장 영상 썸네일(포스터) 생성: python3 tools/make_posters.py [--force]
사례 frontmatter의 video 마다 같은 폴더에 <영상이름>-poster.jpg 를 만든다(이미 있으면 건너뜀).
영상 길이 40% 지점 한 프레임 → 1080px 폭, 아래 남색 그라데이션, 가운데 주황 재생 버튼,
왼쪽 아래 길이 + video_title, 오른쪽 아래 '내집홈케어'. ffmpeg 가 없으면 아무것도 하지 않는다."""
import os, sys, shutil, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import build
from PIL import Image, ImageDraw, ImageFont

ROOT = build.ROOT
NAVY = (11, 31, 58); ORANGE = (226, 81, 12); LIGHT_ORANGE = (255, 196, 160)
FD = '/usr/share/fonts/opentype/noto/'
def font(w, size):
    return ImageFont.truetype(FD + f'NotoSansCJK-{w}.ttc', size, index=1)  # index 1 = KR

def duration(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', p],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)

def make(video, title, dst):
    d = duration(video)
    with tempfile.TemporaryDirectory() as td:
        fr = os.path.join(td, 'f.jpg')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{d * 0.4:.2f}', '-i', video, '-frames:v', '1', fr], check=True)
        im = Image.open(fr).convert('RGB')
    W = 1080; H = round(im.height * W / im.width)
    im = im.resize((W, H), Image.LANCZOS)
    # 아래쪽 남색 그라데이션
    grad = Image.new('L', (1, H))
    for y in range(H):
        t = max(0.0, (y / H - 0.45) / 0.55)
        grad.putpixel((0, y), int(235 * t))
    im.paste(Image.new('RGB', (W, H), NAVY), (0, 0), grad.resize((W, H)))
    dr = ImageDraw.Draw(im, 'RGBA')
    # 가운데 재생 버튼
    cx, cy, r = W // 2, H // 2, 95
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE + (255,))
    s = 44
    dr.polygon([(cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s), (cx + s * 1.05, cy)], fill=(255, 255, 255, 255))
    # 왼쪽 아래: 길이 + 제목
    m = 48; tf = font('Bold', 62); df = font('Bold', 34); bf = font('Bold', 38)
    sec = int(round(d)); dur = f'{sec // 60}:{sec % 60:02d}'
    tb = dr.textbbox((0, 0), title, font=tf)
    ty = H - m - (tb[3] - tb[1]) - tb[1]
    db = dr.textbbox((0, 0), dur, font=df)
    bh = db[3] - db[1] + 20; by = ty + tb[1] - 18 - bh
    dr.rounded_rectangle((m, by, m + db[2] - db[0] + 28, by + bh), 10, fill=(0, 0, 0, 150))
    dr.text((m + 14 - db[0], by + 10 - db[1]), dur, font=df, fill=LIGHT_ORANGE)
    dr.text((m, ty), title, font=tf, fill=(255, 255, 255))
    # 오른쪽 아래 상호
    nb = dr.textbbox((0, 0), '내집홈케어', font=bf)
    dr.text((W - m - nb[2], H - m - nb[3]), '내집홈케어', font=bf, fill=(255, 255, 255, 230))
    im.save(dst, quality=86, optimize=True, progressive=True)

def main():
    force = '--force' in sys.argv
    if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
        print('make_posters: ffmpeg 없음 — 포스터 생략'); return
    n = 0
    for c in build.CASES:
        v = c.get('video')
        if not v:
            continue
        src = os.path.join(ROOT, 'static', v.lstrip('/'))
        dst = src.rsplit('.', 1)[0] + '-poster.jpg'
        if not os.path.exists(src) or (os.path.exists(dst) and not force):
            continue
        make(src, c.get('video_title') or '현장 영상', dst); n += 1
        print('poster:', os.path.relpath(dst, ROOT))
    print(f'make_posters: {n}개 생성')

if __name__ == '__main__':
    main()
