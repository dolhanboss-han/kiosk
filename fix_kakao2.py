f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) SDK에 autoload=false 추가
content = content.replace(
    'https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c"',
    'https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"'
)

# 2) initMap 함수 내부에 kakao.maps.load 래핑 추가
old_init = '''function initMap(){
  if(mapInitialized) return;
  mapInitialized=true;

  var container=document.getElementById('mapContainer');
  var options={
    center:new kakao.maps.LatLng(36.0,127.5),
    level:13
  };
  kakaoMap=new kakao.maps.Map(container,options);

  // 줌 컨트롤
  kakaoMap.addControl(new kakao.maps.ZoomControl(),kakao.maps.ControlPosition.RIGHT);
  // 지도 타입 컨트롤
  kakaoMap.addControl(new kakao.maps.MapTypeControl(),kakao.maps.ControlPosition.TOPRIGHT);

  renderKakaoMarkers(D.map_hospitals);
}'''

new_init = '''function initMap(){
  if(mapInitialized) return;
  mapInitialized=true;

  kakao.maps.load(function(){
    var container=document.getElementById('mapContainer');
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

content = content.replace(old_init, new_init)

open(f, "w", encoding="utf-8").write(content)
print("완료: kakao.maps.load() 래핑 + autoload=false 적용")
