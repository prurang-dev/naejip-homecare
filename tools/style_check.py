#!/usr/bin/env python3
"""문체 점검(AGENT.md 규칙 27). 사용: python3 tools/style_check.py <글.md> [<글.md> ...]
경고만 출력하고 항상 0으로 끝난다. 글을 고친 뒤 다시 돌려 경고를 줄인다."""
import re, sys

BANNED = ["를 통해", "을 통해", "에 있어서", "라고 볼 수 있습니다", "하는 것이 중요합니다", "다양한", "효과적으로",
          "정리해 드렸", "알아보겠습니다", "결론부터", "시사하는 바", "되어집니다", "할 수 있겠습니다"]


def body(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def check(path):
    t = body(open(path, encoding="utf-8").read())
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    prose = re.sub(r"^\[[^\]]*\]\s*$|^— 서명 —$", "", prose, flags=re.M)  # 네이버 사진 자리·서명 줄
    out = []
    bold = len(re.findall(r"\*\*[^*]+\*\*", prose))
    if bold > 5:
        out.append(f"굵은 글씨 {bold}개 (5개 이하)")
    dash = prose.count("—")
    if dash:
        out.append(f"긴 줄표(—) {dash}개 (0개)")
    for w in BANNED:
        n = prose.count(w)
        if n:
            out.append(f"상투구 '{w}' {n}번")
    lists = len(re.findall(r"(?:^\s*(?:[-*]|\d+\.) .+\n?)+", prose, re.M))
    if lists > 3:
        out.append(f"목록 묶음 {lists}개 (3개 이하)")
    sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", re.sub(r"[#>*\-]", " ", prose)) if len(s.strip()) > 5]
    run = 1
    for a, b in zip(sents, sents[1:]):
        same_end = a[-5:] == b[-5:]
        run = run + 1 if same_end else 1
        if run == 3:
            out.append(f"같은 말끝 3연속: …{b[-12:]}")
            run = 1
    print(f"== {path}: " + ("통과" if not out else f"경고 {len(out)}개"))
    for o in out:
        print("  - " + o)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        check(p)
