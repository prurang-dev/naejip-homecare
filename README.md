# 설비업체 홈페이지

평택 중심 종합설비(누수탐지·하수구·배관) 업체 홈페이지. 의존성 없는 Python 정적 사이트.

## 구조
- `data/business.json` — 업체명·전화·주소 등 (한 곳에서만 관리, `[ ]`·null은 확인 후 채움)
- `content/cases/*.md` — 시공 사례 글 (1 현장 = 1 파일)
- `static/` — CSS, 사례 사진·영상
- `drafts/naver/` — 네이버 블로그 초안 (공개 저장소에 올리지 않음, 로컬·승인함에서만 관리)
- `inbox/` — 동생이 보낸 현장 사진·메모 대기함
- `build.py` — `python3 build.py` → `dist/`

## 배포
`main`에 push하면 GitHub Actions가 빌드해 GitHub Pages에 올린다.
도메인을 사면 Cloudflare Pages로 옮기고 `SITE_URL`, `INDEX=1`을 켠다 (그 전까지는 검색 노출 차단).

## 로컬 미리보기
`python3 build.py && cd dist && python3 -m http.server`
