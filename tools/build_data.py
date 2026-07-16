# -*- coding: utf-8 -*-
"""kindergartens_raw.json -> organs_merged.json
설립구분 정규화(공립/사립), 주소 정제, 학급수·원아수 합산.
좌표는 geocode.py에서 별도로 채운다.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
SRC = TOOLS / "kindergartens_raw.json"
OUT = TOOLS / "organs_merged.json"

DISTRICT_ORDER = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
]


def clean_address(raw):
    if not raw:
        return ""
    a = re.sub(r"^\(\d{5}\)\s*", "", raw.strip())
    return " ".join(a.split())


def extract_district(address):
    for d in DISTRICT_ORDER:
        if d in address:
            return d
    return ""


def clean_phone(raw):
    if not raw:
        return ""
    cleaned = re.sub(r"[^0-9-]", "", raw.strip())  # 선행 마침표 등 잡문자 제거
    cleaned = re.sub(r"^-+|-+$", "", cleaned)
    if re.fullmatch(r"-*", cleaned):
        return ""
    return cleaned


def clean_url(raw):
    if not raw:
        return ""
    return raw.strip()


def to_int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return 0


def main():
    records = json.loads(SRC.read_text(encoding="utf-8"))

    merged = []
    no_district = 0
    for r in records:
        address = clean_address(r.get("ADDR", ""))
        district = extract_district(address)
        if not district:
            no_district += 1

        fndn = r.get("FNDN_TYPE", "")
        kind = "공립" if fndn.startswith("공립") else ("사립" if fndn.startswith("사립") else fndn)

        classes = {
            "age3": to_int(r.get("AGE_3_CLAS_CNT")),
            "age4": to_int(r.get("AGE_4_CLAS_CNT")),
            "age5": to_int(r.get("AGE_5_CLAS_CNT")),
            "mix": to_int(r.get("MIX_CLAS_CNT")),
            "special": to_int(r.get("SPCL_CLAS_CNT")),
        }
        students = {
            "age3": to_int(r.get("AGE_3_TDL_CNT")),
            "age4": to_int(r.get("AGE_4_TDL_CNT")),
            "age5": to_int(r.get("AGE_5_TDL_CNT")),
            "mix": to_int(r.get("MIX_TDL_CNT")),
            "special": to_int(r.get("SPCL_TDL_CNT")),
        }
        class_count = sum(classes.values())
        student_count = sum(students.values())

        merged.append({
            "kdgtCd": r.get("KDGT_CD", ""),
            "name": r.get("KDGT_NM", ""),
            "district": district,
            "address": address,
            "kind": kind,
            "kindDetail": fndn,
            "eduSupport": r.get("EDU_SPRT_NM", ""),
            "phone": clean_phone(r.get("TELNO", "")),
            "homepage": clean_url(r.get("HMPG", "")),
            "operHours": (r.get("OPER_HR", "") or "").strip(),
            "classCount": class_count,
            "studentCount": student_count,
            "classes": classes,
            "students": students,
            "hasSpecialClass": classes["special"] > 0,
        })

    OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"병합 완료: {len(merged)}건 -> {OUT} (자치구 추출 실패 {no_district}건)")

    from collections import Counter
    print("kind 분포:", dict(Counter(m["kind"] for m in merged)))


if __name__ == "__main__":
    main()
