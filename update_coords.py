import pandas as pd
import time
import urllib.request
import urllib.parse
import json

FILE = "/home/blueswell/data/지역별_병원관리_리스트_좌표포함.xlsx"
BACKUP = FILE.replace(".xlsx", "_백업.xlsx")

df = pd.read_excel(FILE)
df.to_excel(BACKUP, index=False)
print(f"총 {len(df)}개 병원 (백업 저장 완료)")

# 주소가 있는 모든 병원 대상 (기존 좌표 덮어쓰기)
need = df[
    (df["주소"].notna()) & 
    (df["주소"].astype(str).str.strip() != "") & 
    (df["주소"].astype(str) != "nan")
]

# 주소 없고 좌표도 없는 병원
no_addr = df[
    ((df["주소"].isna()) | (df["주소"].astype(str).str.strip() == "") | (df["주소"].astype(str) == "nan")) &
    ((df["위도"].isna()) | (df["위도"] == 0))
]

print(f"주소 있음 → 좌표 변환: {len(need)}개")
print(f"주소 없고 좌표 없음: {len(no_addr)}개")
if len(no_addr) > 0:
    for _, r in no_addr.iterrows():
        print(f"  ⚠ {r.get('병원명','')} - 주소/좌표 모두 없음")

def geocode(address):
    try:
        query = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1, "countrycodes": "kr", "accept-language": "ko"})
        url = f"https://nominatim.openstreetmap.org/search?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "BlueSwell-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    에러: {e}")
    return None, None

ok = 0
fail_list = []

print(f"\n좌표 변환 시작 (약 {len(need)*1.5:.0f}초 소요)...")
print("=" * 50)

for idx, row in need.iterrows():
    name = row.get("병원명", "")
    addr = str(row["주소"]).strip()
    print(f"  [{ok+len(fail_list)+1}/{len(need)}] {name}: {addr}", end=" -> ")
    
    lat, lng = geocode(addr)
    if lat and lng:
        df.at[idx, "위도"] = lat
        df.at[idx, "경도"] = lng
        print(f"OK ({lat:.6f}, {lng:.6f})")
        ok += 1
    else:
        # 주소 축약 재시도
        parts = addr.split()
        if len(parts) >= 2:
            short = " ".join(parts[:3])
            time.sleep(1.2)
            lat, lng = geocode(short)
            if lat and lng:
                df.at[idx, "위도"] = lat
                df.at[idx, "경도"] = lng
                print(f"OK-재시도 ({lat:.6f}, {lng:.6f})")
                ok += 1
            else:
                print("FAIL")
                fail_list.append(name)
        else:
            print("FAIL")
            fail_list.append(name)
    
    time.sleep(1.2)

df.to_excel(FILE, index=False)

print("\n" + "=" * 50)
print(f"완료! 성공: {ok}, 실패: {len(fail_list)}")
if fail_list:
    print(f"실패 목록: {', '.join(fail_list)}")
    print("→ 엑셀에서 수동으로 좌표 입력 필요")
print(f"\nWeb 탭 → Reload 후 지도 확인하세요!")
