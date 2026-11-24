#!/usr/bin/env python3
"""사진 가벼운 판 만들기(WebP 640·1200px) + 크기 목록.

  python3 tools/make_variants.py      # 새로 생기거나 바뀐 사진만 처리

static/cases/, static/guides/ 의 jpg·png 마다 static/v/<같은 경로>-640.webp, -1200.webp 를 만들고
static/v/manifest.json 에 원본 가로·세로와 만든 폭(원본이 작으면 원본 폭)을 적는다. build.py 는 이 목록이 있으면
<picture> 로 WebP 를 먼저 내보내고, 없으면 원래 jpg 만 쓴다(CI 에는 Pillow 가 없으므로 결과물을 커밋한다).
prepublish.sh 가 자동으로 부른다.
"""
import hashlib, json, os, sys
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, 'static')
VDIR = os.path.join(STATIC, 'v')
MAN = os.path.join(VDIR, 'manifest.json')
WIDTHS = (640, 1200)
DIRS = ('cases', 'guides')


def main():
    man = json.load(open(MAN, encoding='utf-8')) if os.path.exists(MAN) else {}
    seen, made = set(), 0
    for d in DIRS:
        for dp, _, fs in os.walk(os.path.join(STATIC, d)):
            for f in sorted(fs):
                if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                src = os.path.join(dp, f)
                rel = os.path.relpath(src, STATIC).replace(os.sep, '/')
                seen.add(rel)
                mt = hashlib.md5(open(src, 'rb').read()).hexdigest()[:12]
                base = os.path.join(VDIR, os.path.splitext(rel)[0])
                ent = man.get(rel)
                if ent and ent.get('mt') == mt and all(os.path.exists(f'{base}-{w}.webp') for w in ent['v']):
                    continue
                im = ImageOps.exif_transpose(Image.open(src))
                W, H = im.size
                if im.mode not in ('RGB', 'RGBA'):
                    im = im.convert('RGB')
                os.makedirs(os.path.dirname(base), exist_ok=True)
                vs = sorted({min(w, W) for w in WIDTHS})
                for tw in vs:
                    out = im if tw == W else im.resize((tw, round(H * tw / W)), Image.LANCZOS)
                    out.save(f'{base}-{tw}.webp', 'WEBP', quality=78, method=6)
                man[rel] = {'w': W, 'h': H, 'v': vs, 'mt': mt}
                made += 1
    for rel in [r for r in man if r not in seen]:
        base = os.path.join(VDIR, os.path.splitext(rel)[0])
        for w in man[rel]['v']:
            p = f'{base}-{w}.webp'
            if os.path.exists(p):
                os.remove(p)
        del man[rel]
    os.makedirs(VDIR, exist_ok=True)
    json.dump(dict(sorted(man.items())), open(MAN, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'variants: {made} new/updated, {len(man)} total')


if __name__ == '__main__':
    sys.exit(main())
