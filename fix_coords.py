import pandas as pd

FILE = "/home/blueswell/data/지역별_병원관리_리스트_좌표포함.xlsx"
df = pd.read_excel(FILE)

# 검색으로 찾은 좌표
coords = {
    "바로웰병원":       (37.3240, 127.1065),   # 경기 용인시 수지구 현암로 72
    "배곧정형외과":     (37.3785, 126.7335),   # 경기 시흥시 배곧3로 96
    "삼성본병원":       (37.1340, 127.0695),   # 경기 오산시 북삼미로 175
    "상주적십자병원":   (36.4109, 128.1591),   # 경북 상주시 상서문로 53
    "송도미소어린이병원":(37.3812, 126.6609),  # 인천 연수구 하모니로 158
    "안성성모병원":     (37.0054, 127.2796),   # 경기 안성시 시장길 58
    "오산한국병원":     (37.1497, 127.0697),   # 경기 오산시 밀머리로1번길 16
    "의왕시티병원":     (37.3447, 126.9683),   # 경기 의왕시 오전천로 29
    "흥케이병원":       (37.4279, 126.8088),   # 경기 시흥시 능곡번영길 22
}

updated = 0
for idx, row in df.iterrows():
    name = str(row.get("병원명", "")).strip()
    for key, (lat, lng) in coords.items():
        if key in name or name in key:
            df.at[idx, "위도"] = lat
            df.at[idx, "경도"] = lng
            print(f"  OK: {name} -> ({lat}, {lng})")
            updated += 1
            break

df.to_excel(FILE, index=False)

# 확인
no_coord = df[(df["위도"].isna()) | (df["위도"] == 0)]
print(f"\n업데이트: {updated}개")
print(f"좌표 없는 병원: {len(no_coord)}개")
if len(no_coord) > 0:
    for _, r in no_coord.iterrows():
        print(f"  - {r.get('병원명','')}")
print("\nWeb 탭 → Reload 후 지도 확인!")
