# -*- coding: utf-8 -*-
"""homepage_diagnosis.json에서 DNS 자체가 실패(dns=='fail')한, 확실히 죽은 홈페이지만
data.js와 organs_merged.json에서 지운다. DNS는 되는데 접속만 막힌 애매한 건 손대지 않는다.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DATA_JS = ROOT / "assets" / "js" / "data.js"
MERGED = TOOLS / "organs_merged.json"
DIAG = TOOLS / "homepage_diagnosis.json"


def main():
    diag = json.loads(DIAG.read_text(encoding="utf-8"))
    dead = [d for d in diag if d["dns"] == "fail"]
    dead_ids = {d["id"] for d in dead}
    dead_names = {(d["name"]) for d in dead}
    print(f"확실히 죽은 홈페이지: {len(dead)}건")

    # 1) data.js 패치
    t = DATA_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.KINDERGARTENS = (\[.*?\]);", t, re.S)
    data = json.loads(m.group(1))
    cleared = 0
    for item in data:
        if item["id"] in dead_ids and item.get("homepage"):
            item["homepage"] = ""
            cleared += 1
    print(f"data.js에서 지운 건수: {cleared}")

    meta_m = re.search(r"window\.DATA_META = (\{.*?\});", t, re.S)
    meta = json.loads(meta_m.group(1))

    new_js = (
        "/* 서울 유치원 데이터 — 자동 생성 파일 */\n"
        "window.KINDERGARTENS = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
        "window.DATA_META = " + json.dumps(meta, ensure_ascii=False, indent=2) + ";\n"
    )
    DATA_JS.write_text(new_js, encoding="utf-8")
    print("저장:", DATA_JS)

    # 2) organs_merged.json도 이름 매칭으로 패치 (파이프라인 재실행 시 되살아나지 않도록)
    merged = json.loads(MERGED.read_text(encoding="utf-8"))
    cleared2 = 0
    for item in merged:
        if item["name"] in dead_names and item.get("homepage"):
            item["homepage"] = ""
            cleared2 += 1
    MERGED.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"organs_merged.json에서 지운 건수: {cleared2}")
    print("저장:", MERGED)


if __name__ == "__main__":
    main()
