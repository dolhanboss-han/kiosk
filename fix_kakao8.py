f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# 1) 이전 SDK (autoload 없는 것) 제거
content = content.replace(
    '<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c"></script>\n',
    ''
)
content = content.replace(
    '<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c"></script>',
    ''
)

# 2) autoload=false 버전도 제거
content = content.replace(
    '<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>\n',
    ''
)
content = content.replace(
    '<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>',
    ''
)

# 3) Chart.js 바로 다음에 카카오 SDK 1개만 삽입 (autoload=false)
content = content.replace(
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false"></script>'
)

open(f, "w", encoding="utf-8").write(content)
print("완료: 카카오 SDK 중복 제거, 1개만 유지")
