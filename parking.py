"""전국주차장정보 표준데이터(CSV)에서 수도권 공영주차장만 골라 parking.json으로 저장합니다.
사용: python3 parking.py 전국주차장정보표준데이터.csv  (결과: parking.json)"""
import csv, json, re, sys

LAT0, LAT1, LNG0, LNG1 = 36.8, 38.2, 126.2, 127.7  # 수도권 범위


def read(path):
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit("CSV 인코딩을 읽지 못했습니다")


def col(row, *names):
    """헤더 이름이 정확히 같거나 포함되는 첫 열의 값을 돌려줍니다."""
    for n in names:
        for k, v in row.items():
            if k and k.strip() == n:
                return (v or "").strip()
    for n in names:
        for k, v in row.items():
            if k and n in k:
                return (v or "").strip()
    return ""


def num(v):
    v = re.sub(r"[^\d.\-]", "", v or "")
    try:
        return float(v) if v else 0.0
    except ValueError:
        return 0.0


def main(path):
    rows = read(path)
    out, skipped = [], 0
    date = ""
    for r in rows:
        kind = col(r, "주차장구분")
        if "공영" not in kind:
            continue
        lat, lng = num(col(r, "위도")), num(col(r, "경도"))
        if not (LAT0 <= lat <= LAT1 and LNG0 <= lng <= LNG1):
            skipped += 1
            continue
        fee = col(r, "요금정보")
        bc, ac, dc = (int(num(col(r, n))) for n in ("주차기본요금", "추가단위요금", "1일주차권요금"))
        free = int(("무료" in fee and "유료" not in fee) or (bc == 0 and ac == 0 and dc == 0 and "무료" in fee))
        bt, at = int(num(col(r, "주차기본시간"))), int(num(col(r, "추가단위시간")))
        s, e = col(r, "평일운영시작시각"), col(r, "평일운영종료시각")
        oper = f"{s[:5]}~{e[:5]}" if s and e and (s, e) != ("00:00", "23:59") else ("24시간" if s and e else "")
        date = date or col(r, "데이터기준일자")
        out.append([
            col(r, "주차장명"), round(lat, 6), round(lng, 6), free, bt, bc, at, ac, dc,
            col(r, "소재지도로명주소") or col(r, "소재지지번주소"), col(r, "전화번호"), oper,
            int(num(col(r, "주차구획수"))),
        ])
    with open("parking.json", "w", encoding="utf-8") as f:
        json.dump({"d": date, "p": out}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"공영주차장 {len(out)}곳 저장 (수도권 밖 제외 {skipped}곳)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
