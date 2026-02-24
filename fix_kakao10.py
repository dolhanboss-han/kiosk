f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) 기존 SDK 태그 제거
content = content.replace(
    '<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>\n',
    ''
)
content = content.replace(
    '<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>',
    ''
)

# 2) initMap 함수를 kakao.maps.load 없이 직접 호출로 변경
content = content.replace(
    '''  kakao.maps.load(function(){
    if(mapInitialized) return;
    mapInitialized=true;''',
    '''  if(mapInitialized) return;
    mapInitialized=true;'''
)

# 닫는 }); 제거 (kakao.maps.load의 콜백 닫기)
# renderKakaoMarkers 호출 후의 }); 를 찾아서 제거
content = content.replace(
    '''    },300);
  });
}''',
    '''    },300);
}'''
)

# 3) 메인 <script> 바로 앞에 SDK를 동적 로드하는 방식으로 삽입
sdk_loader = '''<script>
(function(){
  var s=document.createElement('script');
  s.src='https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false';
  s.onload=function(){
    window._kakaoSDKReady=true;
    console.log('Kakao SDK loaded');
  };
  document.head.appendChild(s);
})();
</script>
'''

content = content.replace(
    '<script>\nvar D=',
    sdk_loader + '<script>\nvar D='
)

# 4) initMap에서 SDK 로드 대기
content = content.replace(
    '''function initMap(){
  if(mapInitialized) return;
  if(typeof kakao==="undefined"){
    setTimeout(initMap,300);
    return;
  }''',
    '''function initMap(){
  if(mapInitialized) return;
  if(typeof kakao==="undefined"||typeof kakao.maps==="undefined"){
    setTimeout(initMap,500);
    return;
  }
  kakao.maps.load(function(){
    _doInitMap();
  });
}
function _doInitMap(){'''
)

# 5) _doInitMap 닫기 수정 - initMap 끝부분 찾기
# 이미 복잡해졌으므로 전체 지도 JS를 깨끗하게 재작성
# 위 변환이 꼬일 수 있으므로 원복 후 깔끔하게 처리

open(f, "w", encoding="utf-8").write(content)
print("1차 적용 완료")
