f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) 지도 컨테이너에 배경색 + z-index 수정
content = content.replace(
    'id="mapContainer" style="height:560px;border-radius:8px;border:1px solid var(--border);z-index:1;"',
    'id="mapContainer" style="height:560px;border-radius:8px;border:1px solid var(--border);z-index:1;background:#f0f0f0;"'
)

# 2) initMap에서 relayout 추가 + 강제 resize
old_init = '''  kakao.maps.load(function(){
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
  });'''

new_init = '''  kakao.maps.load(function(){
    if(mapInitialized) return;
    mapInitialized=true;
    var container=document.getElementById('mapContainer');
    if(!container) return;
    container.style.width='100%';
    container.style.height='560px';
    var options={
      center:new kakao.maps.LatLng(36.0,127.5),
      level:13
    };
    kakaoMap=new kakao.maps.Map(container,options);
    kakaoMap.addControl(new kakao.maps.ZoomControl(),kakao.maps.ControlPosition.RIGHT);
    kakaoMap.addControl(new kakao.maps.MapTypeControl(),kakao.maps.ControlPosition.TOPRIGHT);
    setTimeout(function(){
      kakaoMap.relayout();
      kakaoMap.setCenter(new kakao.maps.LatLng(36.0,127.5));
      renderKakaoMarkers(D.map_hospitals);
    },300);
  });'''

content = content.replace(old_init, new_init)

# 3) 탭 전환 시 relayout 강화
content = content.replace(
    '''setTimeout(function(){
      initMap();
      if(kakaoMap) kakaoMap.relayout();
    },200);''',
    '''setTimeout(function(){
      initMap();
      if(kakaoMap){
        kakaoMap.relayout();
        kakaoMap.setCenter(new kakao.maps.LatLng(36.0,127.5));
      }
    },300);'''
)

open(f, "w", encoding="utf-8").write(content)
print("완료: 지도 컨테이너 크기 강제 설정 + relayout 강화")
