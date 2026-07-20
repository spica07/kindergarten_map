# -*- coding: utf-8 -*-
"""check_homepages.py에서 실패로 나온 URL만 재검증한다.
많은 실패가 오래된 학교 홈페이지 서버의 구형 TLS 설정 때문일 수 있어서,
- 완화된 SSL 컨텍스트(레거시 재협상 허용, SECLEVEL 낮춤)로 재시도
- https 실패 시 http로도 재시도
- 스킴 누락(MissingSchema) URL은 http:// 붙여서 재시도
- 그래도 실패하면 15초 타임아웃으로 한 번 더 재시도
순서로 재검증하고, 최종 결과를 homepage_recheck.json으로 저장한다.
"""
import json
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning
from urllib3.poolmanager import PoolManager

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
IN_FILE = TOOLS / "homepage_check.json"
OUT = TOOLS / "homepage_recheck.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
WORKERS = 16


class LegacySSLAdapter(HTTPAdapter):
    """구형 TLS(재협상 허용, 낮은 보안레벨)를 허용하는 어댑터. 오래된 학교 서버용."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
        try:
            ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        except ssl.SSLError:
            pass
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        kwargs["ssl_context"] = ctx
        self.poolmanager = PoolManager(*args, **kwargs)


def make_session():
    s = requests.Session()
    s.mount("https://", LegacySSLAdapter())
    return s


def try_get(session, url, timeout):
    return session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, verify=False, stream=True)


def recheck(item):
    kdgt_id, name, url, prev_error = item["id"], item["name"], item["url"], item.get("error")
    session = make_session()
    candidates = [url]
    if prev_error == "MissingSchema" or not url.startswith(("http://", "https://")):
        candidates = ["http://" + url]
    elif url.startswith("https://"):
        candidates.append("http://" + url[len("https://"):])

    last_exc = None
    for cand in candidates:
        for timeout in (8, 15):
            try:
                r = try_get(session, cand, timeout)
                ok = r.status_code < 400
                return {"id": kdgt_id, "name": name, "url": url, "tried": cand,
                        "ok": ok, "status": r.status_code, "final_url": r.url}
            except requests.exceptions.RequestException as e:
                last_exc = e
                continue
    return {"id": kdgt_id, "name": name, "url": url, "tried": candidates[-1],
            "ok": False, "status": None, "error": type(last_exc).__name__ if last_exc else "Unknown"}


def main():
    fails = [d for d in json.loads(IN_FILE.read_text(encoding="utf-8")) if not d["ok"]]
    print(f"재검증 대상: {len(fails)}건")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(recheck, d): d for d in fails}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(fails)} 진행")

    recovered = sum(1 for r in results if r["ok"])
    print(f"완료: 재검증 {len(results)}건 중 살아있음(복구) {recovered} / 여전히 실패 {len(results) - recovered}")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("저장:", OUT)


if __name__ == "__main__":
    main()
