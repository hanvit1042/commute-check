"""수도권 주유소 휘발유 가격과 지역 평균가를 모아 gas.json으로 저장합니다."""
import json, math, os, sys, time, datetime, urllib.request
from pyproj import Transformer

KEY = os.environ.get("OPINET_KEY") or "8MHzrzppSCVs1XZ5ERWnXyrzLIZ6n6xg2CyCSWfPwI"
BASE = "https://www.opinet.co.kr/api/"
KATEC = ("+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 +x_0=400000 +y_0=600000 "
         "+ellps=bessel +towgs84=-146.43,507.89,681.46 +units=m +no_defs")
to_k = Transformer.from_crs("EPSG:4326", KATEC, always_xy=True)
from_k = Transformer.from_crs(KATEC, "EPSG:4326", always_xy=True)

# 수도권 조회 범위 (서울·인천·경기 중심부)
LAT0, LAT1, LNG0, LNG1 = 37.10, 37.85, 126.45, 127.40
LIMIT = int(os.environ.get("GRID_LIMIT") or 0)


def get(path, **p):
    q = "&".join(f"{k}={v}" for k, v in p.items())
    url = f"{BASE}{path}?out=json&certkey={KEY}&{q}"
    for t in range(3):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)["RESULT"]["OIL"]
        except Exception as e:
            print("retry", path, e, file=sys.stderr)
            time.sleep(2)
    return []


def grid():
    d = 8.6  # km, 반경 5km 원이 빈틈없이 겹치는 간격
    dlat = 7.45 / 111.32
    pts, row, lat = [], 0, LAT0
    while lat <= LAT1:
        dlng = d / (111.32 * math.cos(math.radians(lat)))
        lng = LNG0 + (dlng / 2 if row % 2 else 0)
        while lng <= LNG1:
            pts.append((lat, lng))
            lng += dlng
        lat += dlat
        row += 1
    return pts


stations = {}
pts = grid()
if LIMIT:
    pts = pts[:LIMIT]
print("조회 지점", len(pts))
for lat, lng in pts:
    x, y = to_k.transform(lng, lat)
    for o in get("aroundAll.do", x=round(x), y=round(y), radius=5000, prodcd="B027", sort=1):
        sx, sy = from_k.transform(o["GIS_X_COOR"], o["GIS_Y_COOR"])
        stations[o["UNI_ID"]] = {"n": o["OS_NM"], "b": o["POLL_DIV_CD"], "p": o["PRICE"],
                                 "y": round(sy, 5), "x": round(sx, 5)}
    time.sleep(0.15)

sido = [{"c": o["SIDOCD"], "n": o["SIDONM"], "p": o["PRICE"]} for o in get("avgSidoPrice.do", prodcd="B027")]
kst = datetime.timezone(datetime.timedelta(hours=9))
out = {
    "updated": datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M"),
    "bbox": [LAT0, LAT1, LNG0, LNG1],
    "sido": sido,
    "stations": list(stations.values()),
}
with open("gas.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print("주유소", len(stations), "곳 / 시도평균", len(sido), "건")
