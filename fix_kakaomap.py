# -*- coding: utf-8 -*-
# Leaflet → 카카오맵 전환

import re

f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# ═══════════════════════════════════════
# 1) CDN 교체: Leaflet CSS/JS → 카카오맵 SDK
# ═══════════════════════════════════════
content = content.replace(
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>',
    ''
)
content = content.replace(
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
    '<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c"></script>'
)

# ═══════════════════════════════════════
# 2) Leaflet CSS 제거
# ═══════════════════════════════════════
content = re.sub(
    r'#mapContainer \.leaflet-popup-content\{[^}]*\}',
    '',
    content
)
content = re.sub(
    r'#mapContainer \.leaflet-popup-content [^}]*\}',
    '',
    content
)

# ═══════════════════════════════════════
# 3) 지도 JS 전체 교체
# ═══════════════════════════════════════
old_map_js = re.compile(
    r'// =+\s*\n// 지도 기능\s*\n// =+\s*\n.*?renderH\(hospData\);',
    re.DOTALL
)

new_map_js = r'''// ============================================================
// 카카오맵 기능
// ============================================================
var kakaoMap=null;
var kakaoMarkers=[];
var kakaoOverlays=[];
var mapInitialized=false;

function initMap(){
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
}

function renderKakaoMarkers(hospitals){
  // 기존 마커/오버레이 제거
  kakaoMarkers.forEach(function(m){m.setMap(null);});
  kakaoOverlays.forEach(function(o){o.setMap(null);});
  kakaoMarkers=[];
  kakaoOverlays=[];

  var bounds=new kakao.maps.LatLngBounds();

  hospitals.forEach(function(h){
    var pos=new kakao.maps.LatLng(h.lat,h.lng);
    bounds.extend(pos);

    var color=h.active?'#10b981':'#ef4444';
    var borderColor=h.active?'#065f46':'#991b1b';
    var size=Math.max(12,Math.min(30,10+h.qty*4));
    var statusText=h.active?'정상가동':'미사용';
    var statusBg=h.active?'#d1fae5':'#fee2e2';
    var statusColor=h.active?'#065f46':'#991b1b';

    // 커스텀 마커 (원형)
    var markerContent='<div style="'
      +'width:'+size+'px;height:'+size+'px;'
      +'background:'+color+';'
      +'border:2px solid '+borderColor+';'
      +'border-radius:50%;'
      +'cursor:pointer;'
      +'opacity:0.8;'
      +'transition:all .2s;'
      +'display:flex;align-items:center;justify-content:center;'
      +'font-size:8px;color:#fff;font-weight:700;'
      +'" onmouseover="this.style.opacity=1;this.style.transform=\'scale(1.3)\'" '
      +'onmouseout="this.style.opacity=0.8;this.style.transform=\'scale(1)\'">'
      +h.qty
      +'</div>';

    var marker=new kakao.maps.CustomOverlay({
      position:pos,
      content:markerContent,
      yAnchor:0.5,
      xAnchor:0.5,
      zIndex:1
    });
    marker.setMap(kakaoMap);
    kakaoMarkers.push(marker);

    // 팝업 오버레이
    var popupHtml='<div style="'
      +'background:#fff;border-radius:12px;padding:14px 16px;'
      +'box-shadow:0 4px 20px rgba(0,0,0,.15);'
      +'border:1px solid #e2e8f0;'
      +'min-width:220px;max-width:280px;'
      +'font-family:Segoe UI,Malgun Gothic,sans-serif;'
      +'font-size:12px;line-height:1.6;'
      +'position:relative;'
      +'">'
      +'<div style="font-size:14px;font-weight:800;color:#1e293b;border-bottom:2px solid #2563eb;padding-bottom:6px;margin-bottom:8px;">'+h.name+'</div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">상태</span><span style="background:'+statusBg+';color:'+statusColor+';padding:1px 8px;border-radius:8px;font-size:10px;font-weight:600;">'+statusText+'</span></div>'
      +(h.address?'<div style="display:flex;justify-content:space-between;padding:2px 0;gap:8px;"><span style="color:#64748b;white-space:nowrap;">주소</span><span style="font-weight:600;font-size:10px;text-align:right;word-break:keep-all;">'+h.address+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">지역</span><span style="font-weight:700;">'+h.region+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">키오스크</span><span style="font-weight:700;">'+h.qty+'대</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">이용건수</span><span style="font-weight:700;color:#2563eb;">'+h.usage.toLocaleString()+'건</span></div>'
      +(h.phone?'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">전화</span><span style="font-weight:600;">'+h.phone+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">ISV</span><span style="font-weight:600;">'+h.isv+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">장비</span><span style="font-weight:600;">'+h.equip+'</span></div>'
      +'<div onclick="closeAllPopups()" style="position:absolute;top:8px;right:10px;cursor:pointer;font-size:16px;color:#94a3b8;font-weight:700;">&times;</div>'
      +'</div>';

    var popup=new kakao.maps.CustomOverlay({
      position:pos,
      content:popupHtml,
      yAnchor:1.3,
      xAnchor:0.5,
      zIndex:10
    });
    kakaoOverlays.push(popup);

    // 마커 div에 클릭 이벤트
    var markerEl=marker.getContent?null:null;
    // CustomOverlay는 DOM 직접 접근 필요 → content div에 onclick 추가
    var idx=kakaoOverlays.length-1;
    var contentWithClick=markerContent.replace(
      'onmouseout="this.style.opacity=0.8;this.style.transform=\'scale(1)\'"',
      'onmouseout="this.style.opacity=0.8;this.style.transform=\'scale(1)\'" onclick="togglePopup('+idx+')"'
    );
    marker.setContent(contentWithClick);
  });

  if(hospitals.length>0){
    kakaoMap.setBounds(bounds,100,100,100,100);
  }
}

function togglePopup(idx){
  closeAllPopups();
  kakaoOverlays[idx].setMap(kakaoMap);
}

function closeAllPopups(){
  kakaoOverlays.forEach(function(o){o.setMap(null);});
}

function filterMap(){
  var rg=document.getElementById('mapRegionFilter').value;
  var st=document.getElementById('mapStatusFilter').value;
  var filtered=D.map_hospitals.filter(function(h){
    if(rg&&h.region!==rg) return false;
    if(st==='active'&&!h.active) return false;
    if(st==='inactive'&&h.active) return false;
    return true;
  });
  renderKakaoMarkers(filtered);
}

// 탭 전환 시 지도 초기화
var origShowTab=showTab;
showTab=function(id,btn){
  origShowTab(id,btn);
  if(id==='map'){
    setTimeout(function(){
      initMap();
      kakaoMap.relayout();
    },200);
  }
};

var hospData=D.hospital_table;
function renderH(data){
  var tb=document.getElementById('tblHosp');var html='';
  data.forEach(function(r){
    html+='<tr><td><b>'+r.name+'</b></td><td>'+r.region+'</td><td>'+r.isv+'</td><td>'+r.gubun+'</td><td>'+r.equip+'</td><td class="tc bold-val">'+r.qty+'</td><td class="tc bold-val">'+r.usage.toLocaleString()+'</td></tr>';
  });
  tb.innerHTML=html;
}
function filterH(){
  var s=document.getElementById('fSearch').value.toLowerCase();
  var rg=document.getElementById('fRegion').value;
  var iv=document.getElementById('fIsv').value;
  var filtered=hospData.filter(function(r){
    if(s&&r.name.toLowerCase().indexOf(s)<0) return false;
    if(rg&&r.region!==rg) return false;
    if(iv&&r.isv!==iv) return false;
    return true;
  });
  renderH(filtered);
}
renderH(hospData);'''

content = old_map_js.sub(new_map_js, content)

# ═══════════════════════════════════════
# 4) 지역별 설치 요약 테이블 제거
# ═══════════════════════════════════════
summary_pattern = re.compile(
    r'<div class="card">\s*<div class="card-title"><span>.*?</span> 지역별 설치 요약</div>.*?</table></div>\s*</div>',
    re.DOTALL
)
content = summary_pattern.sub('', content)

# renderMapSummary 관련 코드 제거
content = content.replace('renderMapSummary();', '')

open(f, "w", encoding="utf-8").write(content)
print("=" * 50)
print("  완료: Leaflet → 카카오맵 전환")
print("  - 카카오맵 SDK 적용")
print("  - 원형 마커 + 팝업 오버레이")
print("  - 줌/지도타입 컨트롤 추가")
print("  - 지역별 설치 요약 제거")
print("=" * 50)
