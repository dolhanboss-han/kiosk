import pandas as pd

FILE = "/home/blueswell/mysite/data/지역별_병원관리_리스트_좌표포함.xlsx"
df = pd.read_excel(FILE)

coords = {
    "바로웰병원":       (37.3240, 127.1065),
    "배곧정형외과":     (37.3785, 126.7335),
    "삼성본병원":       (37.1340, 127.0695),
    "상주적십자병원":   (36.4109, 128.1591),
    "송도미소어린이병원":(37.3812, 126.6609),
    "안성성모병원":     (37.0054, 127.2796),
    "오산한국병원":     (37.1497, 127.0697),
    "의왕시티병원":     (37.3447, 126.9683),
    "흥케이병원":       (37.4279, 126.8088),
    "아름누리":         (36.5040, 127.0095),
    "연세김앤정":       (37.4747, 126.8676),
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

no = df[(df["위도"].isna()) | (df["위도"] == 0)]
print(f"\n업데이트: {updated}개")
print(f"좌표 없는 병원: {len(no)}개")
if len(no) > 0:
    for _, r in no.iterrows():
        print(f"  - {r.get('병원명','')}")
else:
    print("모든 병원 좌표 완료!")
