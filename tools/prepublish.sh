#!/usr/bin/env bash
# 게시 전 필수 단계 한 번에: bash tools/prepublish.sh <slug> [<slug> ...]
# 1) 설비 상식이면 썸네일 생성  2) OG 이미지  3) 정식 빌드  4) 검사(--strict)  5) 화면 미리보기 저장
# 마지막 줄이 "PREPUBLISH OK"가 아니면 절대 push하지 말 것. 미리보기 PNG(preview/)는 반드시 직접 열어 확인.
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "사용: bash tools/prepublish.sh <slug>"; exit 2; }
for s in "$@"; do
  if [ -f "content/guides/$s.md" ]; then python3 tools/make_thumb.py "$s"; fi
done
python3 tools/make_og.py
BASE="/" SITE_URL="https://naezipcare.kr" INDEX=1 python3 build.py
python3 tools/check.py --strict "$@"
python3 tools/preview.py "$@"
echo "PREPUBLISH OK — preview/*.png 를 열어 그림 중복·잘림·겹침이 없는지 확인한 뒤 push"
