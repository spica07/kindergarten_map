# -*- coding: utf-8 -*-
"""homepage_recheck.json에서 여전히 실패인 항목들에 대해 DNS 조회를 직접 해서
'도메인 자체가 없음'(진짜 죽은 링크)과 'DNS는 되는데 접속이 막힘'(불확실, 사람이 봐야 함)을 구분한다.
"""
import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
IN_FILE = TOOLS / "homepage_recheck.json"
OUT = TOOLS / "homepage_diagnosis.json"


def clean_url(url):
    return url.strip().replace(" ", "").replace("http://:", "http://")


def dns_check(item):
    kdgt_id, name, url = item["id"], item["name"], item["url"]
    cleaned = clean_url(url)
    host = urlparse(cleaned).netloc or urlparse("http://" + cleaned).netloc
    # 한글 도메인 등 IDNA 인코딩
    try:
        host_ascii = host.encode("idna").decode("ascii") if host else host
    except Exception:
        host_ascii = host
    try:
        socket.setdefaulttimeout(5)
        ip = socket.gethostbyname(host_ascii)
        return {"id": kdgt_id, "name": name, "url": url, "cleaned": cleaned, "host": host,
                "dns": "resolved", "ip": ip}
    except socket.gaierror as e:
        return {"id": kdgt_id, "name": name, "url": url, "cleaned": cleaned, "host": host,
                "dns": "fail", "error": str(e)}
    except Exception as e:
        return {"id": kdgt_id, "name": name, "url": url, "cleaned": cleaned, "host": host,
                "dns": "error", "error": str(e)}


def main():
    fails = [d for d in json.loads(IN_FILE.read_text(encoding="utf-8")) if not d["ok"]]
    print(f"진단 대상: {len(fails)}건")

    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(dns_check, d): d for d in fails}
        for fut in as_completed(futures):
            results.append(fut.result())

    from collections import Counter
    print("DNS 결과:", Counter(r["dns"] for r in results))
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("저장:", OUT)


if __name__ == "__main__":
    main()
