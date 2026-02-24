f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) renderKakaoMarkers에 안전 체크 추가
content = content.replace(
    'function renderKakaoMarkers(hospitals){',
    'function renderKakaoMarkers(hospitals){\n  if(typeof kakao==="undefined"||!kakaoMap) return;'
)

# 2) filterMap에 안전 체크 추가
content = content.replace(
    'function filterMap(){',
    'function filterMap(){\n  if(typeof kakao==="undefined"||!kakaoMap){initMap();return;}'
)

# 3) togglePopup에 안전 체크
content = content.replace(
    'function togglePopup(idx){',
    'function togglePopup(idx){\n  if(!kakaoOverlays||!kakaoOverlays[idx]) return;'
)

open(f, "w", encoding="utf-8").write(content)
print("완료: renderKakaoMarkers, filterMap, togglePopup 안전 체크 추가")
