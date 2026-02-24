# -*- coding: utf-8 -*-
r"""
BlueSwell 키오스크 현황 대시보드 v14 - Flask 버전 (로그인 포함)
"""

from flask import Flask, request, session, redirect
import pandas as pd
import numpy as np
import json
import os
import glob
import base64
from string import Template
from datetime import datetime
import math

app = Flask(__name__)
app.secret_key = 'blueswell-kiosk-2026-secret-key'

# ================================================================
# ★ 아이디/비밀번호 설정
# ================================================================
USERS = {
    "admin": "bs1506",
    "manager": "kiosk0804",
}

# ================================================================
# 경로 설정
# ================================================================
BASE_DIR = "/home/blueswell/data"
OUTPUT_DIR = "/home/blueswell"
FILE_HOSPITAL = os.path.join(BASE_DIR, "지역별_병원관리_리스트_좌표포함.xlsx")
LOGO_FILE = os.path.join(OUTPUT_DIR, "blueswell_logo.png")

# 로고
LOGO_B64 = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode("utf-8")

def find_latest_kiosk_file():
    pattern = os.path.join(BASE_DIR, "bs_kiosk_use_*.xlsx")
    files = sorted(glob.glob(pattern))
    if files:
        return files[-1]
    return None


# ================================================================
# 로그인 페이지
# ================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        uid = request.form.get('username', '')
        pwd = request.form.get('password', '')
        if uid in USERS and USERS[uid] == pwd:
            session['user'] = uid
            return redirect('/')
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'

    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>로그인 - BlueSwell</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Segoe UI','Malgun Gothic',sans-serif;
     background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
     height:100vh;display:flex;align-items:center;justify-content:center;}
.box{background:#fff;border-radius:16px;padding:40px 36px;
     width:90%%;max-width:380px;box-shadow:0 20px 60px rgba(0,0,0,.2);}
.box h2{text-align:center;margin-bottom:8px;color:#1e293b;font-size:20px;}
.box .sub{text-align:center;color:#64748b;font-size:12px;margin-bottom:28px;}
.field{margin-bottom:16px;}
.field label{display:block;font-size:12px;font-weight:600;color:#475569;margin-bottom:6px;}
.field input{width:100%%;padding:12px 14px;border:1px solid #e2e8f0;border-radius:8px;
             font-size:14px;outline:none;transition:.2s;}
.field input:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.15);}
.btn{width:100%%;padding:12px;background:linear-gradient(135deg,#667eea,#764ba2);
     color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;
     cursor:pointer;margin-top:8px;transition:.2s;}
.btn:hover{opacity:.9;transform:translateY(-1px);}
.error{background:#fee2e2;color:#991b1b;padding:10px 14px;border-radius:8px;
       font-size:12px;margin-bottom:16px;text-align:center;}
.logo{text-align:center;margin-bottom:20px;font-size:28px;}
</style>
</head>
<body>
<div class="box">
    <div class="logo">🏥</div>
    <h2>키오스크 현황 대시보드</h2>
    <div class="sub">BlueSwell Kiosk Management</div>
    ''' + ('<div class="error">{}</div>'.format(error) if error else '') + '''
    <form method="POST">
        <div class="field">
            <label>아이디</label>
            <input type="text" name="username" placeholder="아이디 입력" required autofocus>
        </div>
        <div class="field">
            <label>비밀번호</label>
            <input type="password" name="password" placeholder="비밀번호 입력" required>
        </div>
        <button type="submit" class="btn">로그인</button>
    </form>
</div>
</body>
</html>
'''


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# ================================================================
# 메인 대시보드
# ================================================================
@app.route('/')
def dashboard():
    # ★ 로그인 체크
    if 'user' not in session:
        return redirect('/login')

    # ============================================================
    # 데이터 로딩
    # ============================================================
    df_h = pd.read_excel(FILE_HOSPITAL)

    FILE_KIOSK = find_latest_kiosk_file()
    if not FILE_KIOSK:
        return "<h1>키오스크 데이터 파일이 없습니다</h1>"

    kiosk_filename = os.path.basename(FILE_KIOSK)
    print("  📂 로딩 파일: {}".format(kiosk_filename))

    df_raw = pd.read_excel(FILE_KIOSK, header=None)
    header_row = 0
    for i in range(min(10, len(df_raw))):
        row_vals = [str(v).strip() for v in df_raw.iloc[i].values]
        if "일자" in row_vals or "병원명" in row_vals:
            header_row = i
            break

    df_k = pd.read_excel(FILE_KIOSK, header=header_row)
    df_k.columns = [str(c).strip() for c in df_k.columns]

    # ============================================================
    # 컬럼 매핑
    # ============================================================
    col_map_k = {}
    for c in df_k.columns:
        cl = c.lower().replace(" ", "")
        if "일자" in cl:
            col_map_k["일자"] = c
        elif "병원코드" in cl:
            col_map_k["병원코드"] = c
        elif "병원명" in cl:
            col_map_k["병원명"] = c
        elif "키오스크" in cl and "이용" not in cl:
            col_map_k["키오스크"] = c
        elif "재진" in cl:
            col_map_k["재진접수"] = c
        elif "진료예약" in cl:
            col_map_k["진료예약"] = c
        elif "진료비" in cl:
            col_map_k["진료비수납"] = c
        elif "세부" in cl:
            col_map_k["세부내역서"] = c
        elif "수납금액" in cl or "금액합계" in cl:
            col_map_k["수납금액합계"] = c

    # ============================================================
    # 데이터 전처리
    # ============================================================
    for fc in ["일자", "병원코드", "병원명"]:
        if fc in col_map_k:
            df_k[col_map_k[fc]] = df_k[col_map_k[fc]].ffill()

    num_cols = ["재진접수", "진료예약", "진료비수납", "세부내역서", "수납금액합계"]
    for nc in num_cols:
        if nc in col_map_k:
            df_k[col_map_k[nc]] = pd.to_numeric(df_k[col_map_k[nc]], errors="coerce").fillna(0)

    use_cols_keys = ["재진접수", "진료예약", "진료비수납", "세부내역서"]
    use_cols = [col_map_k[k] for k in use_cols_keys if k in col_map_k]
    if use_cols:
        df_k["이용건수"] = df_k[use_cols].sum(axis=1)
    else:
        df_k["이용건수"] = 0

    if "키오스크" in col_map_k:
        kiosk_col = col_map_k["키오스크"]
        mask_valid = (
            df_k[kiosk_col].astype(str).str.contains(r"KIOSK|KIO|BSK|K\d", case=False, na=False)
            | df_k[kiosk_col].astype(str).str.match(r"^[A-Za-z0-9_\-]+$", na=False)
        )
        mask_not_sum = ~df_k[kiosk_col].astype(str).str.contains("합계|소계|총계|전체", na=False)
        df_k = df_k[mask_valid & mask_not_sum]

    if "일자" in col_map_k:
        df_k["날짜"] = pd.to_datetime(df_k[col_map_k["일자"]], errors="coerce")
        df_k = df_k.dropna(subset=["날짜"])

    # ============================================================
    # 병원 컬럼 매핑
    # ============================================================
    col_h_name = "병원명" if "병원명" in df_h.columns else df_h.columns[0]
    col_h_region1 = "지역1" if "지역1" in df_h.columns else None
    col_h_status = "상태" if "상태" in df_h.columns else None
    col_h_isv = "ISV" if "ISV" in df_h.columns else None
    col_h_gubun = "구분" if "구분" in df_h.columns else None
    col_h_equip = "장비종류" if "장비종류" in df_h.columns else None
    col_h_van = "VAN" if "VAN" in df_h.columns else None
    col_h_install = "설치일" if "설치일" in df_h.columns else None
    col_h_qty = "수량" if "수량" in df_h.columns else None

    # ============================================================
    # 지역 매핑
    # ============================================================
    region_map = {}
    if col_h_region1:
        for _, r in df_h.iterrows():
            hname = str(r[col_h_name]).strip()
            region_map[hname] = str(r[col_h_region1]).strip()

    if "병원명" in col_map_k:
        df_k["지역"] = df_k[col_map_k["병원명"]].astype(str).str.strip().map(region_map).fillna("기타")
    else:
        df_k["지역"] = "기타"

    # ============================================================
    # KPI 계산
    # ============================================================
    total_hospitals = int(df_h[col_h_name].nunique())

    if col_h_qty:
        df_h["_qty_num"] = pd.to_numeric(df_h[col_h_qty], errors="coerce").fillna(0).astype(int)
        total_kiosks = int(df_h["_qty_num"].sum())
    else:
        total_kiosks = total_hospitals

    kiosk_col_name = col_map_k.get("키오스크", "")
    if kiosk_col_name:
        active_kiosks = int(df_k.groupby("지역")[kiosk_col_name].nunique().sum())
    else:
        active_kiosks = 0

    if total_kiosks > 0:
        op_rate = round(active_kiosks / total_kiosks * 100, 1)
    else:
        op_rate = 0

    total_usage = int(df_k["이용건수"].sum())
    rev_col = col_map_k.get("수납금액합계", "")
    total_revenue = int(df_k[rev_col].sum()) if rev_col else 0

    if col_h_status:
        status_counts = df_h[col_h_status].astype(str).value_counts().to_dict()
    else:
        status_counts = {}

    # ============================================================
    # 지역별 통계
    # ============================================================
    region_hospital = df_h.groupby(col_h_region1)[col_h_name].nunique().to_dict() if col_h_region1 else {}
    region_usage = df_k.groupby("지역")["이용건수"].sum().to_dict()
    region_kiosk_total = {}
    if col_h_region1 and col_h_qty:
        region_kiosk_total = df_h.groupby(col_h_region1)["_qty_num"].sum().to_dict()
    region_kiosk_active = {}
    if kiosk_col_name:
        region_kiosk_active = df_k.groupby("지역")[kiosk_col_name].nunique().to_dict()

    all_regions = sorted(set(list(region_hospital.keys()) + list(region_usage.keys())))
    region_stats = []
    for rg in all_regions:
        if rg in ["nan", ""]:
            continue
        rg_total_k = int(region_kiosk_total.get(rg, 0))
        rg_active_k = int(region_kiosk_active.get(rg, 0))
        rg_op_rate = round(rg_active_k / rg_total_k * 100, 1) if rg_total_k > 0 else 0
        region_stats.append({
            "region": rg,
            "hospitals": int(region_hospital.get(rg, 0)),
            "kiosks_total": rg_total_k,
            "kiosks_active": rg_active_k,
            "kiosk_rate": rg_op_rate,
            "usage": int(region_usage.get(rg, 0)),
        })

    # ============================================================
    # 일별/유형별/병원별 집계
    # ============================================================
    daily = df_k.groupby("날짜").agg(usage=("이용건수", "sum")).reset_index().sort_values("날짜")
    daily_labels = [d.strftime("%m/%d") for d in daily["날짜"]]
    daily_usage = [int(v) for v in daily["usage"]]

    type_data = {}
    for tk in ["재진접수", "진료예약", "진료비수납", "세부내역서"]:
        if tk in col_map_k:
            type_data[tk] = int(df_k[col_map_k[tk]].sum())

    hosp_col = col_map_k.get("병원명", "")
    all_hosp_usage = []
    if hosp_col:
        hosp_usage_all = df_k.groupby(hosp_col)["이용건수"].sum().sort_values(ascending=False)
        all_hosp_usage = [{"name": str(n), "value": int(v)} for n, v in hosp_usage_all.items()]

    # ============================================================
    # 인프라 분석
    # ============================================================
    isv_data = df_h[col_h_isv].astype(str).value_counts().to_dict() if col_h_isv else {}
    equip_data = df_h[col_h_equip].astype(str).value_counts().to_dict() if col_h_equip else {}
    van_data = df_h[col_h_van].astype(str).value_counts().to_dict() if col_h_van else {}
    gubun_data = df_h[col_h_gubun].astype(str).value_counts().to_dict() if col_h_gubun else {}

    install_year = {}
    if col_h_install:
        df_h["설치연도"] = pd.to_datetime(df_h[col_h_install], errors="coerce").dt.year
        install_year = df_h["설치연도"].dropna().astype(int).value_counts().sort_index().to_dict()

    # ============================================================
    # 병원 테이블 데이터
    # ============================================================
    hosp_usage_map = {}
    hosp_kiosk_active_map = {}
    if hosp_col:
        hosp_usage_map = df_k.groupby(hosp_col)["이용건수"].sum().to_dict()
        if kiosk_col_name:
            hosp_kiosk_active_map = df_k.groupby(hosp_col)[kiosk_col_name].nunique().to_dict()

    hosp_merged = {}
    for _, r in df_h.iterrows():
        hname = str(r[col_h_name]).strip()
        qty = int(r["_qty_num"]) if col_h_qty and pd.notna(r.get("_qty_num", None)) else 0
        if hname in hosp_merged:
            hosp_merged[hname]["qty"] += qty
        else:
            hosp_merged[hname] = {
                "name": hname,
                "region": str(r.get(col_h_region1, "")) if col_h_region1 else "",
                "isv": str(r.get(col_h_isv, "")) if col_h_isv else "",
                "gubun": str(r.get(col_h_gubun, "")) if col_h_gubun else "",
                "equip": str(r.get(col_h_equip, "")) if col_h_equip else "",
                "qty": qty,
            }

    hospital_table = []
    for hname, info in hosp_merged.items():
        info["usage"] = int(hosp_usage_map.get(hname, 0))
        hospital_table.append(info)

    # ============================================================
    # 미매칭/미사용 병원
    # ============================================================
    unmatched_hospitals = []
    if hosp_col and kiosk_col_name:
        df_etc = df_k[df_k["지역"] == "기타"]
        if len(df_etc) > 0:
            etc_group = df_etc.groupby(hosp_col).agg(
                kiosk_count=(kiosk_col_name, "nunique"),
                usage=("이용건수", "sum"),
            ).reset_index()
            for _, row in etc_group.iterrows():
                unmatched_hospitals.append({
                    "name": str(row[hosp_col]),
                    "kiosks": int(row["kiosk_count"]),
                    "usage": int(row["usage"]),
                })

    unused_hospitals = []
    if hosp_col:
        all_list_names = set(df_h[col_h_name].astype(str).str.strip().unique())
        used_names = set(df_k[hosp_col].astype(str).str.strip().unique())
        unused_names = all_list_names - used_names - {"nan", "", "합계", "소계", "총계"}
        for nm in sorted(unused_names):
            rows = df_h[df_h[col_h_name].astype(str).str.strip() == nm]
            if len(rows) == 0:
                continue
            row0 = rows.iloc[0]
            q = int(rows["_qty_num"].sum()) if col_h_qty else 0
            unused_hospitals.append({
                "name": nm,
                "region": str(row0.get(col_h_region1, "")).strip() if col_h_region1 else "",
                "isv": str(row0.get(col_h_isv, "")).strip() if col_h_isv else "",
                "qty": q,
                "status": str(row0.get(col_h_status, "")).strip() if col_h_status else "",
            })

    # ============================================================
    # KPI 상세 데이터
    # ============================================================
    kpi_hospital_detail = sorted(region_stats, key=lambda x: -x["hospitals"])
    kpi_kiosk_detail = sorted(region_stats, key=lambda x: -x["kiosks_total"])
    kpi_usage_detail = [{"type": k, "count": v} for k, v in type_data.items()]
    kpi_status_detail = sorted(region_stats, key=lambda x: -x["kiosk_rate"])

    filter_regions = sorted(set(r["region"] for r in hospital_table if r["region"] and r["region"] != "nan"))
    filter_isv = sorted(set(r["isv"] for r in hospital_table if r["isv"] and r["isv"] != "nan"))

    # ============================================================
    # 지도용 병원 데이터 (엑셀 좌표 사용)
    # ============================================================
    # 엑셀에 위도/경도 컬럼이 있으면 사용, 없으면 지역 기준 대략 좌표
    col_h_lat = "위도" if "위도" in df_h.columns else None
    col_h_lng = "경도" if "경도" in df_h.columns else None
    col_h_addr = "주소" if "주소" in df_h.columns else None
    col_h_phone = "전화번호" if "전화번호" in df_h.columns else None

    REGION_COORDS = {
        "서울": [37.5665, 126.9780], "부산": [35.1796, 129.0756], "대구": [35.8714, 128.6014],
        "인천": [37.4563, 126.7052], "광주": [35.1595, 126.8526], "대전": [36.3504, 127.3845],
        "울산": [35.5384, 129.3114], "세종": [36.4800, 127.2590], "경기": [37.2750, 127.0094],
        "강원": [37.8228, 128.1555], "충북": [36.6357, 127.4917], "충남": [36.6588, 126.6728],
        "전북": [35.8203, 127.1088], "전남": [34.8161, 126.4629], "경북": [36.4919, 128.8889],
        "경남": [35.4606, 128.2132], "제주": [33.4996, 126.5312],
    }

    map_hospitals = []
    used_names_set = set(df_k[hosp_col].astype(str).str.strip().unique()) if hosp_col else set()

    # 병원별 좌표 맵 구성 (엑셀에서)
    hosp_coord_map = {}
    hosp_addr_map = {}
    hosp_phone_map = {}
    for _, r in df_h.iterrows():
        hname = str(r[col_h_name]).strip()
        if col_h_lat and col_h_lng:
            lat = pd.to_numeric(r.get(col_h_lat, 0), errors="coerce")
            lng = pd.to_numeric(r.get(col_h_lng, 0), errors="coerce")
            if pd.notna(lat) and pd.notna(lng) and lat != 0 and lng != 0:
                hosp_coord_map[hname] = [float(lat), float(lng)]
        if col_h_addr:
            addr = str(r.get(col_h_addr, "")).strip()
            if addr and addr != "nan":
                hosp_addr_map[hname] = addr
        if col_h_phone:
            phone = str(r.get(col_h_phone, "")).strip()
            if phone and phone != "nan":
                hosp_phone_map[hname] = phone

    for hname, info in hosp_merged.items():
        rg = info["region"]

        # 1순위: 엑셀 좌표 사용
        if hname in hosp_coord_map:
            lat, lng = hosp_coord_map[hname]
        else:
            # 2순위: 지역 기준 대략 좌표
            base_coord = [36.5, 127.5]
            for key in REGION_COORDS:
                if key in rg or rg in key:
                    base_coord = REGION_COORDS[key]
                    break
            lat = base_coord[0] + (hash(hname) % 100 - 50) * 0.001
            lng = base_coord[1] + (hash(hname) % 100 - 50) * 0.001

        is_active = hname in used_names_set
        usage = int(hosp_usage_map.get(hname, 0))

        map_hospitals.append({
            "name": hname,
            "region": rg,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "qty": info["qty"],
            "isv": info["isv"],
            "gubun": info["gubun"],
            "equip": info["equip"],
            "active": is_active,
            "usage": usage,
            "address": hosp_addr_map.get(hname, ""),
            "phone": hosp_phone_map.get(hname, ""),
        })

    # ============================================================
    # JSON 데이터
    # ============================================================
    DATA = {
        "kpi": {
            "hospitals": total_hospitals,
            "kiosks_total": total_kiosks,
            "kiosks_active": active_kiosks,
            "usage": total_usage,
            "op_rate": op_rate,
        },
        "region_stats": region_stats,
        "daily": {"labels": daily_labels, "usage": daily_usage},
        "type_data": type_data,
        "all_hosp_usage": all_hosp_usage,
        "isv": isv_data,
        "equip": equip_data,
        "van": van_data,
        "gubun": gubun_data,
        "install_year": {str(k): v for k, v in install_year.items()},
        "status": status_counts,
        "hospital_table": hospital_table,
        "unmatched": unmatched_hospitals,
        "unused": unused_hospitals,
        "map_hospitals": map_hospitals,
        "kpi_detail": {
            "hospital": kpi_hospital_detail,
            "kiosk": kpi_kiosk_detail,
            "usage": kpi_usage_detail,
            "status": kpi_status_detail,
        },
    }
    DATA_JSON = json.dumps(DATA, ensure_ascii=False, default=str)

    region_opts = "".join('<option value="{0}">{0}</option>'.format(r) for r in filter_regions)
    isv_opts = "".join('<option value="{0}">{0}</option>'.format(s) for s in filter_isv)

    if LOGO_B64:
        logo_html = '<img src="data:image/png;base64,{}" style="height:17px;image-rendering:auto;" alt="BlueSwell">'.format(LOGO_B64)
    else:
        logo_html = '<div style="background:#2563eb;color:#fff;font-weight:800;font-size:12px;padding:3px 8px;border-radius:5px;">BS</div>'

    if len(daily) > 0:
        date_from = daily["날짜"].min().strftime("%Y.%m.%d")
        date_to = daily["날짜"].max().strftime("%Y.%m.%d")
    else:
        date_from = "-"
        date_to = "-"

    # ============================================================
    # HTML 템플릿 (기존 100% 동일)
    # ============================================================
    HTML_TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>BlueSwell 키오스크 현황 대시보드</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#f5f7fa;--card:#fff;--text:#1e293b;--sub:#64748b;
  --blue:#2563eb;--green:#10b981;--orange:#f59e0b;--red:#ef4444;--purple:#8b5cf6;
  --border:#e2e8f0;--shadow:0 1px 3px rgba(0,0,0,.08);
}
body{font-family:'Segoe UI','Malgun Gothic',sans-serif;background:var(--bg);color:var(--text);font-size:13px;overflow-x:hidden;}
.hd{position:fixed;top:0;left:0;right:0;height:44px;background:#fff;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 12px;z-index:100;box-shadow:var(--shadow);gap:6px;}
.hd img{height:17px;flex-shrink:0;image-rendering:auto;}
.hd-title{font-size:14px;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.hd-right{margin-left:auto;font-size:10px;color:var(--sub);white-space:nowrap;flex-shrink:0;}
.tab-bar{position:fixed;top:44px;left:0;right:0;height:32px;background:#fff;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 8px;gap:3px;z-index:99;overflow-x:auto;-webkit-overflow-scrolling:touch;}
.tab-btn{padding:3px 10px;border:none;background:transparent;font-size:11px;font-weight:600;color:var(--sub);cursor:pointer;border-radius:5px;white-space:nowrap;transition:.2s;}
.tab-btn:hover{background:#e0e7ff;color:var(--blue);}
.tab-btn.active{background:var(--blue);color:#fff;}
.kpi-row{position:fixed;top:76px;left:0;right:0;height:56px;background:#fff;border-bottom:1px solid var(--border);display:flex;align-items:stretch;padding:4px 8px;gap:6px;z-index:98;}
.kpi{flex:1;display:flex;align-items:center;gap:6px;padding:0 10px;border-radius:7px;cursor:pointer;position:relative;transition:.15s;border-left:3px solid transparent;overflow:visible;min-width:0;}
.kpi:hover{background:#f0f5ff;transform:translateY(-1px);}
.kpi:nth-child(1){border-left-color:var(--blue);}
.kpi:nth-child(2){border-left-color:var(--green);}
.kpi:nth-child(3){border-left-color:var(--orange);}
.kpi:nth-child(4){border-left-color:var(--red);}
.kpi-icon{font-size:20px;flex-shrink:0;}
.kpi-info{display:flex;flex-direction:column;min-width:0;}
.kpi-label{font-size:8px;color:var(--sub);font-weight:600;letter-spacing:.2px;}
.kpi-val{font-size:16px;font-weight:800;color:var(--text);white-space:nowrap;}
.kpi-sub{font-size:8px;color:var(--sub);white-space:nowrap;}
.kpi-arrow{position:absolute;right:4px;top:50%;transform:translateY(-50%);font-size:11px;color:var(--sub);opacity:0;transition:.2s;}
.kpi:hover .kpi-arrow{opacity:1;}
.content{margin-top:134px;padding:8px 10px 40px;}
.tab-page{display:none;}
.tab-page.show{display:block;}
.grid{display:grid;gap:8px;}
.g2{grid-template-columns:repeat(2,1fr);}
.g3{grid-template-columns:repeat(3,1fr);}
.card{background:var(--card);border-radius:10px;padding:12px;box-shadow:var(--shadow);border:1px solid var(--border);}
.card-title{font-size:12px;font-weight:700;color:var(--text);margin-bottom:8px;display:flex;align-items:center;gap:5px;}
.card-title span{font-size:13px;}
.tbl-wrap{overflow-x:auto;max-height:400px;overflow-y:auto;}
table{width:100%;border-collapse:collapse;font-size:11px;}
th{background:#f1f5f9;padding:6px 7px;text-align:left;font-weight:700;position:sticky;top:0;z-index:1;border-bottom:2px solid var(--border);}
th.tc{text-align:center;}
td{padding:5px 7px;border-bottom:1px solid var(--border);}
td.tc{text-align:center;}
tr:hover{background:#f8fafc;}
.bold-val{font-weight:800;color:#1e3a5f;}
.badge{display:inline-block;padding:2px 6px;border-radius:10px;font-size:10px;font-weight:600;}
.badge-green{background:#d1fae5;color:#065f46;}
.badge-red{background:#fee2e2;color:#991b1b;}
.badge-gray{background:#f1f5f9;color:#475569;}
.badge-blue{background:#dbeafe;color:#1e40af;}
.filter-bar{display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;align-items:center;}
.filter-bar input,.filter-bar select{padding:4px 8px;border:1px solid var(--border);border-radius:5px;font-size:11px;background:#fff;}
.filter-bar input{width:160px;}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.4);z-index:200;align-items:center;justify-content:center;}
.modal-overlay.show{display:flex;}
.modal{background:#fff;border-radius:14px;width:92%;max-width:650px;max-height:85vh;overflow-y:auto;padding:18px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.2);}
.modal-close{position:absolute;top:10px;right:12px;font-size:20px;cursor:pointer;color:var(--sub);background:none;border:none;}
.modal-close:hover{color:var(--text);}
.modal h3{font-size:15px;font-weight:700;margin-bottom:12px;color:var(--text);}
.modal-chart{width:100%;max-height:260px;margin-bottom:12px;}
.modal table{font-size:11px;}
.alert-banner{background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:10px 14px;margin-bottom:8px;}
.alert-title{font-size:12px;font-weight:700;color:#92400e;margin-bottom:6px;}
.alert-desc{font-size:11px;color:#92400e;margin-bottom:6px;}
.alert-hint{font-size:10px;color:#b45309;margin-top:6px;}
@media(max-width:1200px){.g3{grid-template-columns:repeat(2,1fr);}}
@media(max-width:800px){
  .g2,.g3{grid-template-columns:1fr;}
  .hd{height:40px;padding:0 8px;gap:5px;}
  .hd img{height:14px;}
  .hd-title{font-size:12px;}
  .hd-right{font-size:9px;}
  .tab-bar{top:40px;height:30px;padding:0 6px;}
  .tab-btn{font-size:10px;padding:2px 7px;}
  .kpi-row{top:70px;height:auto;min-height:44px;flex-wrap:wrap;padding:4px 6px;gap:4px;}
  .kpi{min-width:calc(50% - 4px);height:42px;padding:0 6px;gap:4px;}
  .kpi-icon{font-size:16px;}
  .kpi-val{font-size:13px;}
  .kpi-label{font-size:7px;}
  .kpi-sub{font-size:7px;}
  .content{margin-top:160px;padding:6px;}
}
@media(max-width:500px){
  .hd img{height:12px;}
  .hd-title{font-size:11px;}
  .kpi{min-width:calc(50% - 4px);}
  .filter-bar{flex-direction:column;}
  .filter-bar input,.filter-bar select{width:100%;}
}


.map-popup-title{font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px;border-bottom:2px solid #2563eb;padding-bottom:4px;}
.map-popup-row{display:flex;justify-content:space-between;padding:2px 0;}
.map-popup-label{color:#64748b;font-size:11px;}
.map-popup-val{font-weight:700;font-size:11px;}
.map-badge-active{background:#d1fae5;color:#065f46;padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;}
.map-badge-inactive{background:#fee2e2;color:#991b1b;padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;}
</style>
</head>
<body>

<div class="hd">
  $LOGO_HTML
  <span class="hd-title">키오스크 현황 대시보드</span>
  <div class="hd-right">$DATE_FROM ~ $DATE_TO</div>
</div>

<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab('overview',this)">📊 종합현황</button>
  <button class="tab-btn" onclick="showTab('region',this)">🗺️ 지역분석</button>
  <button class="tab-btn" onclick="showTab('hospital',this)">🏥 병원상세</button>
  <button class="tab-btn" onclick="showTab('trend',this)">📈 추이분석</button>
  <button class="tab-btn" onclick="showTab('infra',this)">⚙️ 인프라</button>
  <button class="tab-btn" onclick="showTab('map',this)">🗺️ 전국지도</button>
</div>

<div class="kpi-row">
  <div class="kpi" onclick="openM('hospital')">
    <div class="kpi-icon">🏥</div>
    <div class="kpi-info"><div class="kpi-label">관리 병원</div><div class="kpi-val">$TOTAL_HOSPITALS</div><div class="kpi-sub">$REGION_COUNT개 지역</div></div>
    <div class="kpi-arrow">›</div>
  </div>
  <div class="kpi" onclick="openM('kiosk')">
    <div class="kpi-icon">🖥️</div>
    <div class="kpi-info"><div class="kpi-label">키오스크</div><div class="kpi-val">$TOTAL_KIOSKS 대</div><div class="kpi-sub">사용 $ACTIVE_KIOSKS대</div></div>
    <div class="kpi-arrow">›</div>
  </div>
  <div class="kpi" onclick="openM('usage')">
    <div class="kpi-icon">📋</div>
    <div class="kpi-info"><div class="kpi-label">이용건수</div><div class="kpi-val">$TOTAL_USAGE 건</div><div class="kpi-sub">기간합계</div></div>
    <div class="kpi-arrow">›</div>
  </div>
  <div class="kpi" onclick="openM('rate')">
    <div class="kpi-icon">✅</div>
    <div class="kpi-info"><div class="kpi-label">가동률</div><div class="kpi-val">$OP_RATE%</div><div class="kpi-sub">$ACTIVE_KIOSKS / $TOTAL_KIOSKS</div></div>
    <div class="kpi-arrow">›</div>
  </div>
</div>

<div class="content">

<div id="tab-overview" class="tab-page show">
  <div class="grid g2" style="margin-bottom:8px;">
    <div class="card"><div class="card-title"><span>📈</span> 일별 이용 추이</div><canvas id="cDaily" height="160"></canvas></div>
    <div class="card"><div class="card-title"><span>📊</span> 이용유형 비율</div><canvas id="cType" height="160"></canvas></div>
  </div>
  <div class="card" style="margin-bottom:8px;">
    <div class="card-title"><span>📅</span> 설치연도별 추이</div>
    <canvas id="cInstall" height="100"></canvas>
  </div>
  <div id="unmatchedAlert" class="alert-banner" style="display:none;">
    <div class="alert-title">⚠️ 병원관리 리스트에 없는 병원 (<span id="unmatchedCnt"></span>개) — 키오스크 <span id="unmatchedKiosk"></span>대</div>
    <div class="alert-desc">아래 병원이 이용 데이터에는 있으나 병원관리 리스트에 없습니다.</div>
    <div class="tbl-wrap" style="max-height:160px;"><table>
      <thead><tr><th>병원명</th><th>키오스크 수</th><th>이용건수</th><th>조치</th></tr></thead>
      <tbody id="tblUnmatched"></tbody>
    </table></div>
    <div class="alert-hint">💡 지역별_병원관리_리스트.xlsx 에 해당 병원을 추가하거나, 이용 데이터의 병원명 오타를 확인해주세요.</div>
  </div>
  <div id="unusedAlert" class="alert-banner" style="display:none;background:#fff7ed;border-color:#fb923c;">
    <div class="alert-title" style="color:#9a3412;">📋 미사용 병원 현황 (<span id="unusedCnt"></span>개) — 이용 데이터 등록 필요</div>
    <div class="alert-desc" style="color:#9a3412;">아래 병원은 관리 리스트에 등록되어 있으나, 조회 기간 내 이용 데이터가 확인되지 않습니다.</div>
    <div class="tbl-wrap" style="max-height:300px;"><table>
      <thead><tr><th style="width:30px;">No</th><th>병원명</th><th class="tc">지역</th><th class="tc">ISV</th><th class="tc">수량(대)</th><th class="tc">운영상태</th><th>조치</th></tr></thead>
      <tbody id="tblUnused"></tbody>
    </table></div>
    <div class="alert-hint" style="color:#c2410c;">💡 해당 병원에 키오스크 이용 데이터가 존재하는지 확인하고, 누락 시 데이터를 등록해주세요.</div>
  </div>
</div>

<div id="tab-region" class="tab-page">
  <div class="grid g2">
    <div class="card">
      <div class="card-title"><span>🗺️</span> 지역별 병원 & 키오스크</div>
      <div class="tbl-wrap"><table>
        <thead><tr><th>지역</th><th class="tc">병원수</th><th class="tc">키오스크(총)</th><th class="tc">키오스크(사용)</th><th class="tc">가동률</th></tr></thead>
        <tbody id="tblRegionHK"></tbody>
      </table></div>
    </div>
    <div class="card">
      <div class="card-title"><span>📊</span> 지역별 이용건수</div>
      <div class="tbl-wrap"><table>
        <thead><tr><th>지역</th><th class="tc">이용건수</th><th class="tc">비율</th></tr></thead>
        <tbody id="tblRegionU"></tbody>
      </table></div>
    </div>
  </div>
</div>

<div id="tab-hospital" class="tab-page">
  <div class="filter-bar">
    <input type="text" id="fSearch" placeholder="🔍 병원명 검색..." oninput="filterH()">
    <select id="fRegion" onchange="filterH()"><option value="">전체 지역</option>$REGION_OPTS</select>
    <select id="fIsv" onchange="filterH()"><option value="">전체 ISV</option>$ISV_OPTS</select>
  </div>
  <div class="card">
    <div class="tbl-wrap"><table>
      <thead><tr><th>병원명</th><th>지역</th><th>ISV</th><th>구분</th><th>장비</th><th class="tc">수량</th><th class="tc">이용건수</th></tr></thead>
      <tbody id="tblHosp"></tbody>
    </table></div>
  </div>
</div>

<div id="tab-trend" class="tab-page">
  <div class="card" style="margin-bottom:8px;">
    <div class="card-title"><span>📈</span> 일별 이용건수 추이</div>
    <canvas id="cTrendU" height="140"></canvas>
  </div>
  <div class="card">
    <div class="card-title"><span>🏥</span> 병원별 이용건수</div>
    <div class="tbl-wrap" style="max-height:500px;"><table>
      <thead><tr><th style="width:40px;">#</th><th>병원명</th><th class="tc">이용건수</th></tr></thead>
      <tbody id="tblAllHosp"></tbody>
    </table></div>
  </div>
</div>

<div id="tab-infra" class="tab-page">
  <div class="grid g2" style="margin-bottom:8px;">
    <div class="card"><div class="card-title"><span>🏢</span> ISV 분포</div><canvas id="cISV" height="200"></canvas></div>
    <div class="card"><div class="card-title"><span>🔧</span> 장비종류</div><canvas id="cEquip" height="200"></canvas></div>
  </div>
  <div class="grid g2" style="margin-bottom:8px;">
    <div class="card"><div class="card-title"><span>📑</span> 구분별</div><canvas id="cGubun" height="120"></canvas></div>
    <div class="card"><div class="card-title"><span>✅</span> 운영상태</div><canvas id="cStatusChart" height="120"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title"><span>💳</span> VAN 분포</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>VAN사</th><th class="tc">병원수</th><th class="tc">비율</th></tr></thead>
      <tbody id="tblVAN"></tbody>
    </table></div>
  </div>
</div>

<div id="tab-map" class="tab-page">
  <div class="card" style="margin-bottom:8px;">
    <div class="card-title"><span>🗺️</span> 전국 키오스크 설치 현황 지도</div>
    <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;align-items:center;">
      <select id="mapRegionFilter" onchange="filterMap()" style="padding:4px 8px;border:1px solid var(--border);border-radius:5px;font-size:11px;">
        <option value="">전체 지역</option>$REGION_OPTS
      </select>
      <select id="mapStatusFilter" onchange="filterMap()" style="padding:4px 8px;border:1px solid var(--border);border-radius:5px;font-size:11px;">
        <option value="">전체 상태</option>
        <option value="active">정상 가동</option>
        <option value="inactive">미사용</option>
      </select>
      <span style="font-size:11px;color:var(--sub);margin-left:auto;">
        🟢 정상가동 &nbsp; 🔴 미사용 &nbsp; 원 크기 = 키오스크 수량
      </span>
    </div>
    <div id="mapContainer" style="height:560px;border-radius:8px;border:1px solid var(--border);z-index:1;background:#f0f0f0;"></div>
  </div>

</div>

</div>

<div class="modal-overlay" id="modalOverlay" onclick="closeM(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="document.getElementById('modalOverlay').classList.remove('show')">&times;</button>
    <h3 id="modalTitle"></h3>
    <canvas id="mcChart" class="modal-chart" height="250"></canvas>
    <div id="modalBody"></div>
  </div>
</div>

<script>
var D=$DATA_JSON;
var C=['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16','#e11d48','#0ea5e9','#a855f7','#eab308'];

function showTab(id,btn){
  document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('show');});
  document.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active');});
  document.getElementById('tab-'+id).classList.add('show');
  btn.classList.add('active');
}

var mcInst=null;
function openM(type){
  var ov=document.getElementById('modalOverlay');
  var tt=document.getElementById('modalTitle');
  var bd=document.getElementById('modalBody');
  var cv=document.getElementById('mcChart');
  ov.classList.add('show');
  if(mcInst){mcInst.destroy();mcInst=null;}
  var ctx=cv.getContext('2d');
  var dd=D.kpi_detail;
  var html='';

  if(type==='hospital'){
    tt.textContent='🏥 관리 병원 상세 (지역별)';
    var lb=[],dt=[];
    dd.hospital.forEach(function(r){lb.push(r.region);dt.push(r.hospitals);});
    mcInst=new Chart(ctx,{type:'bar',data:{labels:lb,datasets:[{label:'병원수',data:dt,backgroundColor:C}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}});
    html='<table><thead><tr><th>지역</th><th class="tc">병원수</th><th class="tc">키오스크(총)</th><th class="tc">키오스크(사용)</th><th class="tc">가동률</th></tr></thead><tbody>';
    dd.hospital.forEach(function(r){html+='<tr><td>'+r.region+'</td><td class="tc">'+r.hospitals.toLocaleString()+'</td><td class="tc">'+r.kiosks_total.toLocaleString()+'</td><td class="tc">'+r.kiosks_active.toLocaleString()+'</td><td class="tc">'+r.kiosk_rate+'%</td></tr>';});
    html+='</tbody></table>';

  }else if(type==='kiosk'){
    tt.textContent='🖥️ 키오스크 현황 (총 '+D.kpi.kiosks_total+'대 / 사용 '+D.kpi.kiosks_active+'대 / 가동률 '+D.kpi.op_rate+'%)';
    var lb=[],d1=[],d2=[];
    dd.kiosk.forEach(function(r){lb.push(r.region);d1.push(r.kiosks_total);d2.push(r.kiosks_active);});
    mcInst=new Chart(ctx,{type:'bar',data:{labels:lb,datasets:[{label:'총 키오스크',data:d1,backgroundColor:'#94a3b8'},{label:'사용 키오스크',data:d2,backgroundColor:'#2563eb'}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}});
    html='<table><thead><tr><th>지역</th><th class="tc">총 키오스크</th><th class="tc">사용 키오스크</th><th class="tc">가동률</th></tr></thead><tbody>';
    dd.kiosk.forEach(function(r){html+='<tr><td>'+r.region+'</td><td class="tc">'+r.kiosks_total.toLocaleString()+'</td><td class="tc">'+r.kiosks_active.toLocaleString()+'</td><td class="tc">'+r.kiosk_rate+'%</td></tr>';});
    html+='</tbody></table>';

  }else if(type==='usage'){
    tt.textContent='📋 이용건수 상세 (유형별)';
    var lb=[],dt=[];
    dd.usage.forEach(function(r){lb.push(r.type);dt.push(r.count);});
    mcInst=new Chart(ctx,{type:'bar',data:{labels:lb,datasets:[{label:'건수',data:dt,backgroundColor:C}]},options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}}}});
    html='<table><thead><tr><th>유형</th><th class="tc">건수</th><th class="tc">비율</th></tr></thead><tbody>';
    var tot=dt.reduce(function(a,b){return a+b;},0);
    dd.usage.forEach(function(r){html+='<tr><td>'+r.type+'</td><td class="tc">'+r.count.toLocaleString()+'</td><td class="tc">'+(tot?((r.count/tot)*100).toFixed(1):0)+'%</td></tr>';});
    html+='</tbody></table>';

  }else if(type==='rate'){
    tt.textContent='✅ 가동률 상세 (사용 키오스크 / 총 키오스크 × 100)';
    var lb=[],d1=[],d2=[];
    dd.status.forEach(function(r){lb.push(r.region);d1.push(r.kiosks_total);d2.push(r.kiosks_active);});
    mcInst=new Chart(ctx,{type:'bar',data:{labels:lb,datasets:[{label:'총',data:d1,backgroundColor:'#e2e8f0'},{label:'사용',data:d2,backgroundColor:'#10b981'}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}});
    html='<p style="margin-bottom:10px;font-size:13px;font-weight:700;">전체 가동률: '+D.kpi.kiosks_active+' / '+D.kpi.kiosks_total+' = '+D.kpi.op_rate+'%</p>';
    html+='<table><thead><tr><th>지역</th><th class="tc">총 키오스크</th><th class="tc">사용 키오스크</th><th class="tc">가동률</th></tr></thead><tbody>';
    dd.status.forEach(function(r){html+='<tr><td>'+r.region+'</td><td class="tc">'+r.kiosks_total.toLocaleString()+'</td><td class="tc">'+r.kiosks_active.toLocaleString()+'</td><td class="tc"><b>'+r.kiosk_rate+'%</b></td></tr>';});
    html+='</tbody></table>';
  }
  bd.innerHTML=html;
}
function closeM(e){if(e.target===document.getElementById('modalOverlay'))document.getElementById('modalOverlay').classList.remove('show');}

if(D.unmatched&&D.unmatched.length>0){
  document.getElementById('unmatchedAlert').style.display='block';
  document.getElementById('unmatchedCnt').textContent=D.unmatched.length;
  var totalUK=0;
  D.unmatched.forEach(function(r){totalUK+=r.kiosks;});
  document.getElementById('unmatchedKiosk').textContent=totalUK;
  var uhtml='';
  D.unmatched.forEach(function(r){
    uhtml+='<tr><td><b style="color:#dc2626;">'+r.name+'</b></td><td>'+r.kiosks+'</td><td>'+r.usage.toLocaleString()+'</td><td style="font-size:10px;color:#b45309;">리스트 추가 또는 병원명 확인</td></tr>';
  });
  document.getElementById('tblUnmatched').innerHTML=uhtml;
}

if(D.unused&&D.unused.length>0){
  document.getElementById('unusedAlert').style.display='block';
  document.getElementById('unusedCnt').textContent=D.unused.length;
  var uuhtml='';
  D.unused.forEach(function(r,i){
    uuhtml+='<tr><td class="tc">'+(i+1)+'</td><td><b>'+r.name+'</b></td><td class="tc">'+r.region+'</td><td class="tc">'+r.isv+'</td><td class="tc"><b>'+r.qty+'</b></td><td class="tc">'+r.status+'</td><td style="font-size:10px;color:#9a3412;">이용 데이터 등록 필요</td></tr>';
  });
  document.getElementById('tblUnused').innerHTML=uuhtml;
}

(function(){
  new Chart(document.getElementById('cDaily').getContext('2d'),{type:'line',data:{labels:D.daily.labels,datasets:[
    {label:'이용건수',data:D.daily.usage,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,.1)',fill:true,tension:.3,pointRadius:1}
  ]},options:{responsive:true,scales:{y:{beginAtZero:true}}}});
})();

(function(){
  var lb=Object.keys(D.type_data),dt=Object.values(D.type_data);
  new Chart(document.getElementById('cType').getContext('2d'),{type:'bar',data:{labels:lb,datasets:[{label:'건수',data:dt,backgroundColor:C}]},options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}}}});
})();

(function(){
  var lb=Object.keys(D.install_year),dt=Object.values(D.install_year);
  new Chart(document.getElementById('cInstall').getContext('2d'),{type:'line',data:{labels:lb,datasets:[{label:'설치수',data:dt,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,.1)',fill:true,tension:.3}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}});
})();

(function(){
  var tb=document.getElementById('tblRegionHK');var html='';
  var sorted=D.region_stats.slice().sort(function(a,b){return b.hospitals-a.hospitals;});
  sorted.forEach(function(r){
    html+='<tr><td><b>'+r.region+'</b></td><td class="tc">'+r.hospitals+'</td><td class="tc">'+r.kiosks_total+'</td><td class="tc">'+r.kiosks_active+'</td><td class="tc"><b>'+r.kiosk_rate+'%</b></td></tr>';
  });
  tb.innerHTML=html;
})();

(function(){
  var tb=document.getElementById('tblRegionU');var html='';
  var sorted=D.region_stats.slice().sort(function(a,b){return b.usage-a.usage;});
  var tot=sorted.reduce(function(s,r){return s+r.usage;},0);
  sorted.forEach(function(r){
    var pct=tot?(r.usage/tot*100).toFixed(1):'0';
    html+='<tr><td><b>'+r.region+'</b></td><td class="tc">'+r.usage.toLocaleString()+'</td><td class="tc">'+pct+'%</td></tr>';
  });
  tb.innerHTML=html;
})();

(function(){
  new Chart(document.getElementById('cTrendU').getContext('2d'),{type:'line',data:{labels:D.daily.labels,datasets:[{label:'이용건수',data:D.daily.usage,borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,.08)',fill:true,tension:.3,pointRadius:2}]},options:{responsive:true,scales:{y:{beginAtZero:true}}}});
})();

(function(){
  var tb=document.getElementById('tblAllHosp');var html='';
  D.all_hosp_usage.forEach(function(r,i){
    html+='<tr><td class="tc">'+(i+1)+'</td><td>'+r.name+'</td><td class="tc">'+r.value.toLocaleString()+'</td></tr>';
  });
  tb.innerHTML=html;
})();

function barOpts(small){
  return {responsive:true,indexAxis:'y',plugins:{legend:{display:false},datalabels:false},scales:{y:{ticks:{font:{size:small?10:11},autoSkip:false}},x:{beginAtZero:true}}};
}

(function(){
  var lb=Object.keys(D.isv),dt=Object.values(D.isv);
  new Chart(document.getElementById('cISV').getContext('2d'),{type:'bar',data:{labels:lb,datasets:[{label:'병원수',data:dt,backgroundColor:C}]},options:barOpts(false)});
})();

(function(){
  var lb=Object.keys(D.equip),dt=Object.values(D.equip);
  new Chart(document.getElementById('cEquip').getContext('2d'),{type:'bar',data:{labels:lb,datasets:[{label:'수량',data:dt,backgroundColor:C.slice(3)}]},options:barOpts(false)});
})();

(function(){
  var lb=Object.keys(D.gubun),dt=Object.values(D.gubun);
  new Chart(document.getElementById('cGubun').getContext('2d'),{
    type:'bar',data:{labels:lb,datasets:[{label:'수량',data:dt,backgroundColor:C.slice(2)}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},scales:{y:{ticks:{font:{size:10},autoSkip:false}},x:{beginAtZero:true}}},
    plugins:[{afterDatasetsDraw:function(chart){var ctx2=chart.ctx;ctx2.font='bold 11px sans-serif';ctx2.fillStyle='#1e293b';ctx2.textAlign='left';chart.getDatasetMeta(0).data.forEach(function(bar,i){ctx2.fillText(dt[i],bar.x+4,bar.y+4);});}}]
  });
})();

(function(){
  var lb=Object.keys(D.status),dt=Object.values(D.status);
  new Chart(document.getElementById('cStatusChart').getContext('2d'),{
    type:'bar',data:{labels:lb,datasets:[{label:'수량',data:dt,backgroundColor:['#10b981','#ef4444','#f59e0b','#94a3b8','#8b5cf6']}]},
    options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},scales:{y:{ticks:{font:{size:10},autoSkip:false}},x:{beginAtZero:true}}},
    plugins:[{afterDatasetsDraw:function(chart){var ctx2=chart.ctx;ctx2.font='bold 11px sans-serif';ctx2.fillStyle='#1e293b';ctx2.textAlign='left';chart.getDatasetMeta(0).data.forEach(function(bar,i){ctx2.fillText(dt[i],bar.x+4,bar.y+4);});}}]
  });
})();

(function(){
  var lb=Object.keys(D.van),dt=Object.values(D.van);
  var tot=dt.reduce(function(a,b){return a+b;},0);
  var tb=document.getElementById('tblVAN');var html='';
  lb.forEach(function(k,i){
    var pct=tot?(dt[i]/tot*100).toFixed(1):'0';
    html+='<tr><td><b>'+k+'</b></td><td class="tc bold-val">'+dt[i]+'</td><td class="tc">'+pct+'%</td></tr>';
  });
  tb.innerHTML=html;
})();

// ============================================================
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
renderH(hospData);
</script>
</body>
</html>''')

    # ============================================================
    # HTML 생성 & 반환
    # ============================================================
    html_out = HTML_TEMPLATE.safe_substitute(
        DATA_JSON=DATA_JSON,
        LOGO_HTML=logo_html,
        DATE_FROM=date_from,
        DATE_TO=date_to,
        TOTAL_HOSPITALS="{:,}".format(total_hospitals),
        TOTAL_KIOSKS="{:,}".format(total_kiosks),
        ACTIVE_KIOSKS="{:,}".format(active_kiosks),
        TOTAL_USAGE="{:,}".format(total_usage),
        OP_RATE=op_rate,
        REGION_COUNT=len([r for r in region_stats if r["region"] != "기타"]),
        REGION_OPTS=region_opts,
        ISV_OPTS=isv_opts,
    )

    return html_out


# ================================================================
# 서버 실행
# ================================================================
if __name__ == '__main__':
    print("=" * 55)
    print("  BlueSwell 키오스크 대시보드 서버 시작")
    print("=" * 55)
    print("  로컬:  http://localhost:5000")
    print("  종료:  Ctrl+C")
    print("=" * 55)

    app.run(host='0.0.0.0', port=5000, debug=False)
