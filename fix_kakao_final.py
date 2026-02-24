import re

f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# ═══════════════════════════════════════
# 1) 기존 카카오 SDK 태그 모두 제거
# ═══════════════════════════════════════
content = re.sub(r'<script src="[^"]*dapi\.kakao\.com[^"]*"></script>\s*', '', content)

# ═══════════════════════════════════════
# 2) 기존 지도 JS 전체를 찾아서 교체
# ═══════════════════════════════════════
old_map = re.compile(
    r'// =+\s*\n// 카카오맵 기능\s*\n// =+\s*\n.*?renderH\(hospData\);',
    re.DOTALL
)

new_map = r'''// ============================================================
// 카카오맵 기능
// ============================================================
var kakaoMap=null;
var kakaoMarkers=[];
var kakaoOverlays=[];
var mapInitialized=false;

// SDK 동적 로드
(function(){
  var s=document.createElement('script');
  s.src='https://dapi.kakao.com/v2/maps/sdk.js?appkey=d67fb9a68a5f643587e7bfef00072b4c&autoload=false';
  s.onload=function(){console.log('Kakao Maps SDK loaded');};
  s.onerror=function(){console.error('Kakao Maps SDK load failed');};
  document.head.appendChild(s);
})();

function initMap(){
  if(mapInitialized) return;
  if(typeof kakao==='undefined'||typeof kakao.maps==='undefined'){
    setTimeout(initMap,500);
    return;
  }
  kakao.maps.load(function(){
    if(mapInitialized) return;
    mapInitialized=true;
    var container=document.getElementById('mapContainer');
    if(!container) return;
    container.style.width='100%';
    container.style.height='560px';
    kakaoMap=new kakao.maps.Map(container,{
      center:new kakao.maps.LatLng(36.0,127.5),
      level:13
    });
    kakaoMap.addControl(new kakao.maps.ZoomControl(),kakao.maps.ControlPosition.RIGHT);
    kakaoMap.addControl(new kakao.maps.MapTypeControl(),kakao.maps.ControlPosition.TOPRIGHT);
    setTimeout(function(){
      kakaoMap.relayout();
      renderKakaoMarkers(D.map_hospitals);
    },300);
  });
}

function renderKakaoMarkers(hospitals){
  if(typeof kakao==='undefined'||!kakaoMap) return;
  kakaoMarkers.forEach(function(m){m.setMap(null);});
  kakaoOverlays.forEach(function(o){o.setMap(null);});
  kakaoMarkers=[];
  kakaoOverlays=[];
  var bounds=new kakao.maps.LatLngBounds();

  hospitals.forEach(function(h){
    var pos=new kakao.maps.LatLng(h.lat,h.lng);
    bounds.extend(pos);
    var color=h.active?'#10b981':'#ef4444';
    var border=h.active?'#065f46':'#991b1b';
    var size=Math.max(12,Math.min(30,10+h.qty*4));
    var statusText=h.active?'정상가동':'미사용';
    var statusBg=h.active?'#d1fae5':'#fee2e2';
    var statusClr=h.active?'#065f46':'#991b1b';
    var idx=kakaoOverlays.length;

    var dot='<div onclick="togglePopup('+idx+')" style="width:'+size+'px;height:'+size+'px;background:'+color+';border:2px solid '+border+';border-radius:50%;cursor:pointer;opacity:0.85;display:flex;align-items:center;justify-content:center;font-size:8px;color:#fff;font-weight:700;transition:all .2s;" onmouseover="this.style.opacity=1;this.style.transform=\'scale(1.3)\'" onmouseout="this.style.opacity=0.85;this.style.transform=\'scale(1)\'">'+h.qty+'</div>';

    var marker=new kakao.maps.CustomOverlay({position:pos,content:dot,yAnchor:0.5,xAnchor:0.5,zIndex:1});
    marker.setMap(kakaoMap);
    kakaoMarkers.push(marker);

    var pop='<div style="background:#fff;border-radius:12px;padding:14px 16px;box-shadow:0 4px 20px rgba(0,0,0,.15);border:1px solid #e2e8f0;min-width:220px;max-width:280px;font-size:12px;line-height:1.6;position:relative;">'
      +'<div style="font-size:14px;font-weight:800;color:#1e293b;border-bottom:2px solid #2563eb;padding-bottom:6px;margin-bottom:8px;">'+h.name+'</div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">상태</span><span style="background:'+statusBg+';color:'+statusClr+';padding:1px 8px;border-radius:8px;font-size:10px;font-weight:600;">'+statusText+'</span></div>'
      +(h.address?'<div style="display:flex;justify-content:space-between;padding:2px 0;gap:8px;"><span style="color:#64748b;">주소</span><span style="font-weight:600;font-size:10px;text-align:right;">'+h.address+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">지역</span><span style="font-weight:700;">'+h.region+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">키오스크</span><span style="font-weight:700;">'+h.qty+'대</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">이용건수</span><span style="font-weight:700;color:#2563eb;">'+h.usage.toLocaleString()+'건</span></div>'
      +(h.phone?'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">전화</span><span style="font-weight:600;">'+h.phone+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">ISV</span><span style="font-weight:600;">'+h.isv+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">장비</span><span style="font-weight:600;">'+h.equip+'</span></div>'
      +'<div onclick="closeAllPopups()" style="position:absolute;top:8px;right:10px;cursor:pointer;font-size:16px;color:#94a3b8;font-weight:700;">&times;</div>'
      +'</div>';

    var popup=new kakao.maps.CustomOverlay({position:pos,content:pop,yAnchor:1.3,xAnchor:0.5,zIndex:10});
    kakaoOverlays.push(popup);
  });

  if(hospitals.length>0) kakaoMap.setBounds(bounds,100,100,100,100);
}

function togglePopup(idx){
  if(!kakaoOverlays||!kakaoOverlays[idx]) return;
  closeAllPopups();
  kakaoOverlays[idx].setMap(kakaoMap);
}
function closeAllPopups(){
  kakaoOverlays.forEach(function(o){o.setMap(null);});
}
function filterMap(){
  if(typeof kakao==='undefined'||!kakaoMap){initMap();return;}
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

var origShowTab=showTab;
showTab=function(id,btn){
  origShowTab(id,btn);
  if(id==='map'){
    setTimeout(function(){
      initMap();
      if(kakaoMap){
        kakaoMap.relayout();
        kakaoMap.setCenter(new kakao.maps.LatLng(36.0,127.5));
      }
    },300);
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

content = old_map.sub(new_map, content)

open(f, "w", encoding="utf-8").write(content)

# 검증
c2 = open(f, "r", encoding="utf-8").read()
sdk_count = c2.count('dapi.kakao.com')
print(f"카카오 SDK 참조 수: {sdk_count} (1이어야 정상)")
print(f"initMap 존재: {'initMap' in c2}")
print(f"renderKakaoMarkers 존재: {'renderKakaoMarkers' in c2}")
print("완료: 카카오맵 JS 전체 재작성 (동적 SDK 로드)")
