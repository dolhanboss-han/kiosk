import pandas as pd

FILE = "/home/blueswell/data/지역별_병원관리_리스트_좌표포함.xlsx"
df = pd.read_excel(FILE)

coords = {
    "아름누리": (36.5040, 127.0095),   # 세종시 한누리대로 2022 소담동
    "연세김앤정": (37.4747, 126.8676),  # 경기 광명시 철산로 36
}

updated = 0
for idx, row in df.iterrows():
    name = str(row.get("병원명", "")).strip()
    for key, (lat, lng) in coords.items():
        if key in name:
            df.at[idx, "위도"] = lat
            df.at[idx, "경도"] = lng
            print(f"  OK: {name} -> ({lat}, {lng})")
            updated += 1
            break

df.to_excel(FILE, index=False)

# 최종 확인
no_coord = df[(df["위도"].isna()) | (df["위도"] == 0)]
print(f"\n업데이트: {updated}개")
print(f"좌표 없는 병원: {len(no_coord)}개")
if len(no_coord) > 0:
    for _, r in no_coord.iterrows():
        print(f"  - {r.get('병원명','')}")
else:
    print("모든 병원 좌표 완료!")
print("\nWeb 탭 → Reload 후 지도 확인!")
