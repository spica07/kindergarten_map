# -*- coding: utf-8 -*-
"""assets/js/data.js의 유치원 홈페이지 URL을 전수 점검해
살아있는지/죽었는지 판정하고 결과를 homepage_check.json으로 저장한다.
데이터를 직접 고치지는 않는다 (검토 후 별도 스크립트로 반영).
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "assets" / "js" / "data.js"
OUT = Path(__file__).resolve().parent / "homepage_check.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 8
WORKERS = 24


def check(item):
    kdgt_id, name, url = item
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True, verify=False, stream=True)
        ok = r.status_code < 400
        return {"id": kdgt_id, "name": name, "url": url, "ok": ok, "status": r.status_code, "final_url": r.url}
    except requests.exceptions.SSLError:
        # SSL 오류는 GET을 verify=False로 이미 시도했으니 실패로 기록
        return {"id": kdgt_id, "name": name, "url": url, "ok": False, "status": None, "error": "SSLError"}
    except requests.exceptions.RequestException as e:
        return {"id": kdgt_id, "name": name, "url": url, "ok": False, "status": None, "error": type(e).__name__}


def main():
    t = DATA_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.KINDERGARTENS = (\[.*?\]);", t, re.S)
    data = json.loads(m.group(1))
    targets = [(d["id"], d["name"], d["homepage"]) for d in data if d.get("homepage")]
    print(f"점검 대상: {len(targets)}건")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(check, t): t for t in targets}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(targets)} 진행")

    ok_count = sum(1 for r in results if r["ok"])
    print(f"완료: 정상 {ok_count} / 실패 {len(results) - ok_count} (총 {len(results)})")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("저장:", OUT)


if __name__ == "__main__":
    main()
