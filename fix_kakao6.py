f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 탭 전환 시 initMap 호출 부분을 안전하게 변경
# 기존: setTimeout(function(){ initMap(); kakaoMap.relayout(); },200);
old1 = """setTimeout(function(){
      initMap();
      kakaoMap.relayout();
    },200);"""

new1 = """setTimeout(function(){
      initMap();
      if(kakaoMap) kakaoMap.relayout();
    },200);"""

content = content.replace(old1, new1)

# 혹시 한줄 형태일 경우
content = content.replace(
    "setTimeout(function(){initMap();kakaoMap.relayout();},200);",
    "setTimeout(function(){initMap();if(kakaoMap)kakaoMap.relayout();},200);"
)

# SDK를 body 끝에서 로드하도록 변경 (script 위치 이동)
# 현재: <head> 안에 SDK가 있으면 </script></body> 앞으로 이동
old_sdk = '<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>'

# head에서 제거
content = content.replace(old_sdk, '')

# </body> 바로 앞, 메인 <script> 바로 앞에 삽입
content = content.replace(
    '<script>\nvar D=',
    old_sdk + '\n<script>\nvar D='
)

# 혹시 줄바꿈 없는 경우
content = content.replace(
    "<script>\r\nvar D=",
    old_sdk + "\n<script>\nvar D="
)

open(f, "w", encoding="utf-8").write(content)
print("완료:")
print("  1) 카카오 SDK → <script> 바로 앞으로 이동")
print("  2) kakaoMap.relayout() 안전 체크 추가")
