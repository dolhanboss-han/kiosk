import re

f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) 혹시 남은 Leaflet 코드 제거
content = content.replace('mapInstance.invalidateSize();', '')
content = content.replace('mapInstance.invalidateSize()', '')

# 2) 어디서든 직접 initMap() 호출하는 부분을 안전하게 변경
#    탭 전환 내부의 initMap()은 유지 (setTimeout 안)
#    그 외 직접 호출은 제거

# 3) initMap 함수를 완전히 안전하게 재작성
old_pattern = re.compile(r'function initMap\(\)\{.*?renderKakaoMarkers\(D\.map_hospitals\);\s*\}\);?\s*\}', re.DOTALL)

new_func = '''function initMap(){
  if(mapInitialized) return;
  if(typeof kakao==='undefined'){
    setTimeout(initMap,300);
    return;
  }
  kakao.maps.load(function(){
    if(mapInitialized) return;
    mapInitialized=true;
    var container=document.getElementById('mapContainer');
    if(!container) return;
    var options={
      center:new kakao.maps.LatLng(36.0,127.5),
      level:13
    };
    kakaoMap=new kakao.maps.Map(container,options);
    kakaoMap.addControl(new kakao.maps.ZoomControl(),kakao.maps.ControlPosition.RIGHT);
    kakaoMap.addControl(new kakao.maps.MapTypeControl(),kakao.maps.ControlPosition.TOPRIGHT);
    renderKakaoMarkers(D.map_hospitals);
  });
}'''

content = old_pattern.sub(new_func, content)

open(f, "w", encoding="utf-8").write(content)
print("완료: initMap 안전 재작성 (kakao 미로드시 자동 재시도)")
