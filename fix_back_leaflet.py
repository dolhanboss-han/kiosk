import re

f = "/home/blueswell/bs_dashboard_flask.py"
content = open(f, "r", encoding="utf-8").read()

# ═══════════════════════════════════════
# 1) 카카오 SDK 동적 로드 제거
# ═══════════════════════════════════════
content = re.sub(r'<script src="[^"]*dapi\.kakao\.com[^"]*"></script>\s*', '', content)

# ═══════════════════════════════════════
# 2) <head>에 Leaflet CSS/JS + 예쁜 타일 CDN 추가
# ═══════════════════════════════════════
content = content.replace(
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>\n<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)

# ═══════════════════════════════════════
# 3) 카카오맵 JS → Leaflet JS 전체 교체
# ═══════════════════════════════════════
old_map = re.compile(
    r'// =+\s*\n// 카카오맵 기능\s*\n// =+\s*\n.*?renderH\(hospData\);',
    re.DOTALL
)

new_map = r'''// ============================================================
// 지도 기능 (Leaflet + CartoDB Voyager)
// ============================================================
var mapInstance=null;
var mapMarkers=[];
var mapInitialized=false;

function initMap(){
  if(mapInitialized) return;
  mapInitialized=true;
  mapInstance=L.map('mapContainer').setView([36.0,127.5],7);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{
    attribution:'&copy; OpenStreetMap &copy; CARTO',
    subdomains:'abcd',
    maxZoom:19
  }).addTo(mapInstance);
  renderMapMarkers(D.map_hospitals);
}

function renderMapMarkers(hospitals){
  mapMarkers.forEach(function(m){mapInstance.removeLayer(m);});
  mapMarkers=[];
  var bounds=[];

  hospitals.forEach(function(h){
    var color=h.active?'#10b981':'#ef4444';
    var border=h.active?'#065f46':'#991b1b';
    var radius=Math.max(6,Math.min(18,5+h.qty*3));

    var marker=L.circleMarker([h.lat,h.lng],{
      radius:radius,fillColor:color,color:border,
      weight:2,opacity:1,fillOpacity:0.8
    }).addTo(mapInstance);

    var statusBadge=h.active
      ?'<span style="background:#d1fae5;color:#065f46;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:600;">정상가동</span>'
      :'<span style="background:#fee2e2;color:#991b1b;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:600;">미사용</span>';

    var popup='<div style="font-size:12px;line-height:1.6;min-width:200px;">'
      +'<div style="font-size:14px;font-weight:800;color:#1e293b;border-bottom:2px solid #2563eb;padding-bottom:6px;margin-bottom:8px;">'+h.name+'</div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">상태</span>'+statusBadge+'</div>'
      +(h.address?'<div style="display:flex;justify-content:space-between;padding:2px 0;gap:8px;"><span style="color:#64748b;">주소</span><span style="font-weight:600;font-size:10px;text-align:right;max-width:180px;">'+h.address+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">지역</span><span style="font-weight:700;">'+h.region+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">키오스크</span><span style="font-weight:700;">'+h.qty+'대</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">이용건수</span><span style="font-weight:700;color:#2563eb;">'+h.usage.toLocaleString()+'건</span></div>'
      +(h.phone?'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">전화</span><span style="font-weight:600;">'+h.phone+'</span></div>':'')
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">ISV</span><span style="font-weight:600;">'+h.isv+'</span></div>'
      +'<div style="display:flex;justify-content:space-between;padding:2px 0;"><span style="color:#64748b;">장비</span><span style="font-weight:600;">'+h.equip+'</span></div>'
      +'</div>';

    marker.bindPopup(popup,{maxWidth:300});
    marker.bindTooltip(h.name,{permanent:false,direction:'top',offset:[0,-radius]});
    mapMarkers.push(marker);
    bounds.push([h.lat,h.lng]);
  });

  if(bounds.length>0) mapInstance.fitBounds(bounds,{padding:[30,30]});
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
  renderMapMarkers(filtered);
}

var origShowTab=showTab;
showTab=function(id,btn){
  origShowTab(id,btn);
  if(id==='map'){
    setTimeout(function(){
      initMap();
      if(mapInstance) mapInstance.invalidateSize();
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

result = old_map.sub(new_map, content)

if result == content:
    print("경고: 카카오맵 JS 블록을 찾지 못했습니다")
else:
    content = result

open(f, "w", encoding="utf-8").write(content)

# 검증
c2 = open(f, "r", encoding="utf-8").read()
print(f"Leaflet CSS: {'leaflet.css' in c2}")
print(f"Leaflet JS: {'leaflet.js' in c2}")
print(f"카카오 SDK 잔존: {'dapi.kakao' in c2}")
print(f"CartoDB Voyager: {'voyager' in c2}")
print(f"initMap: {'initMap' in c2}")
print("완료: Leaflet + CartoDB Voyager 복원")
