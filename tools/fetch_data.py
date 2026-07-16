# -*- coding: utf-8 -*-
"""서울 열린데이터광장 「서울시 유치원 일반현황」(childSchoolInfo, OA-20566)을
API로 전량 받아 tools/kindergartens_raw.json 으로 저장.
인증키는 .env(SEOUL_API_KEY)에서 읽는다.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "kindergartens_raw.json"
SERVICE = "childSchoolInfo"
PAGE_SIZE = 1000


def load_key():
    env_path = ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SEOUL_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(".env 에서 SEOUL_API_KEY를 찾을 수 없습니다.")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def main():
    key = load_key()
    records = []
    start = 1
    total = None
    while True:
        end = start + PAGE_SIZE - 1
        url = f"http://openapi.seoul.go.kr:8088/{key}/json/{SERVICE}/{start}/{end}/"
        data = get_json(url)
        inner = data.get(SERVICE)
        if inner is None:
            print("응답 오류:", data)
            break
        code = inner.get("RESULT", {}).get("CODE")
        if code not in ("INFO-000", None):
            print("API 오류:", inner.get("RESULT"))
            break
        if total is None:
            total = inner.get("list_total_count")
            print("전체 건수:", total)
        rows = inner.get("row", [])
        records.extend(rows)
        print(f"{start}~{end} 수신, 누적 {len(records)}/{total}")
        if not rows or len(records) >= total:
            break
        start += PAGE_SIZE

    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 완료: {len(records)}건 -> {OUT}")


if __name__ == "__main__":
    main()
