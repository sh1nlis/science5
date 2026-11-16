import streamlit as st
import requests
from pathlib import Path

# 조원들이 보내준 5개의 지표 함수 모두 불러오기!
from practice1 import render_toptier
from practice2 import render_industry_collab
from practice3 import render_interdisciplinarity
from practice4 import render_lab_size
from practice5 import render_continuity

# =========================================================
# [엔진 1] 동명이인 검색용 함수
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def search_author_candidates(query_name):
    search_url = f"https://api.openalex.org/authors?search={query_name}&per-page=5"
    res = requests.get(search_url).json()
    candidates = []
    
    for author in res.get("results", []):
        inst = "소속 정보 없음"
        if author.get("last_known_institution"):
            inst = author["last_known_institution"].get("display_name", "소속 정보 없음")
        
        candidates.append({
            "id": author["id"],
            "name": author["display_name"],
            "institution": inst,
            "works_count": author.get("works_count", 0)
        })
    return candidates

# =========================================================
# [엔진 2] 선택된 특정 교수님(ID)의 실시간 논문 100편 분석기
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_openalex_lab_data_by_id(author_id, author_name):
    works_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_year:desc&per-page=100"
    works_res = requests.get(works_url).json()
    raw_works = works_res.get("results", [])

    lab_dict = {
        "lab_name": f"{author_name} 연구실", "professor_id": author_id, "professor": author_name,
        "total_papers": len(raw_works), "collaboration": {"external_papers": 0, "industry_papers": 0, "industry_partners": []},
        "works": [], "interdisciplinarity_demo_papers": [], "toptier_papers": []
    }
    industry_partners = set()

    for w in raw_works:
        year = w.get("publication_year")
        pub_date = w.get("publication_date")
        authorships = w.get("authorships", [])

        # 지표 4, 5번 용
        lab_dict["works"].append({"id": w["id"], "year": year, "publication_year": year, "publication_date": pub_date, "authorships": authorships})
        
        # 지표 3번 용 (분야)
        concepts = [c["display_name"] for c in w.get("concepts", []) if c.get("level", 1) == 0]
        lab_dict["interdisciplinarity_demo_papers"].append({"id": w["id"], "title": w.get("title", ""), "year": year, "field_ids": concepts})

        # 💡 지표 1번 용 (탑티어 판별을 위한 게재처 및 전 분야 확장 지표 추출)
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        venue_name = src.get("display_name", "")
        venue_type = src.get("type", "")
        source_impact = (src.get("summary_stats") or {}).get("2yr_mean_citedness")

        lab_dict["toptier_papers"].append({
            "title": w.get("title", ""),
            "year": year,
            "venue": venue_name,
            "venue_type": venue_type,
            "type": w.get("type", ""),
            "url": w.get("id", ""),
            "fwci": w.get("fwci"),
            "citation_normalized_percentile": w.get("citation_normalized_percentile"),
            "2yr_mean_citedness": source_impact,
        })

        # 지표 2번 용
        is_external = False
        is_industry = False
        for auth in authorships:
            if auth["author"]["id"] != author_id:
                for inst in auth.get("institutions", []):
                    if inst.get("id"):
                        is_external = True
                        if inst.get("type") == "company":
                            is_industry = True
                            if inst.get("display_name"): industry_partners.add(inst.get("display_name"))
        if is_external: lab_dict["collaboration"]["external_papers"] += 1
        if is_industry: lab_dict["collaboration"]["industry_papers"] += 1

    lab_dict["collaboration"]["industry_partners"] = list(industry_partners)
    return lab_dict

# 1. 기본 페이지 설정
st.set_page_config(page_title="LABMATCH", layout="wide")
st.markdown(
    """<style>
    .stTextInput label p { font-size: 18px !important; font-weight: bold !important; }
    .stTextInput input { font-size: 20px !important; height: 55px !important; }
    div.stButton > button, div.stDownloadButton > button { background-color: #F8FAFC !important; height: 58px !important; border-radius: 8px !important; }
    div.stButton > button *, div.stDownloadButton > button * { color: #000000 !important; font-size: 19px !important; font-weight: 800 !important; }
    </style>""", unsafe_allow_html=True
)

# 3. Session State 초기화
if "step" not in st.session_state: st.session_state.step = 1
if "query_a" not in st.session_state: st.session_state.query_a = "Kwanghoon Sohn"
if "query_b" not in st.session_state: st.session_state.query_b = "Bumsub Ham"
if "cands_a" not in st.session_state: st.session_state.cands_a = []
if "cands_b" not in st.session_state: st.session_state.cands_b = []
if "data_a" not in st.session_state: st.session_state.data_a = None
if "data_b" not in st.session_state: st.session_state.data_b = None
if "summary_1" not in st.session_state: st.session_state.summary_1 = ""
if "summary_2" not in st.session_state: st.session_state.summary_2 = ""

# =========================================================
# [공통 상단 바]
# =========================================================
top_spacer, top_btn1, top_btn2 = st.columns([6.5, 1.7, 1.8])
with top_btn1:
    with st.popover("📊 5대 핵심 체감 지표 안내", use_container_width=True):
        st.markdown("""
        | 지표명 | 이용자 관점 질문 | 화면 시각화 안내 |
        |---|---|---|
        | **1. 탑티어 논문 비중** | 유명한 학회/저널에 논문을 자주 내는가? | 🏆 도넛형 차트 + 피라미드 |
        | **2. 산학/외부 협업** | 기업 과제 or 학술 연구 중심인가? | 📊 막대 그래프 + 태그 |
        | **3. 학제 간 융합도** | 타 전공 출신도 적응할 수 있는가? | 🔗 생키 다이어그램 |
        | **4. 연구실 규모** | 연구실에 질문할 사수가 몇 명인가? | 👥 사람 아이콘 그리드 |
        | **5. 연구 산출 연속성** | 논문이 끊김 없이 꾸준히 나오는가? | 🚦 신호등 배지 + 꺾은선 |
        """)
with top_btn2:
    with st.popover("⚠️ 분석 시 주의 사항 및 한계점", use_container_width=True):
        st.markdown("""
        - **동명이인 (저자 식별):** 글로벌 DB 특성상 동명이인이 혼재할 수 있어, 검색 후 소속 기관명으로 교차 검증하는 과정이 포함되어 있습니다.
        - **영문 검색 원칙:** 기계 번역과 실제 공식 논문 영문명의 불일치를 막고자 영문 검색을 원칙으로 합니다.
        - **빠른 시연을 위한 제한:** 웹사이트 과부하 방지 및 쾌적한 데모를 위해 연구자별 **최근 논문 100편**으로 분석 범위를 제한했습니다.
        """)

# =========================================================
# [STEP 1] 검색어 입력
# =========================================================
if st.session_state.step == 1:
    st.write("\n\n")
    _, center_col, _ = st.columns([1.5, 5, 1.5])
    with center_col:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 0px;'>🔬 LABMATCH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94A3B8; margin-bottom: 35px;'>예비 대학원생을 위한 연구실 1:1 체감 지표 비교 플랫폼</p>", unsafe_allow_html=True)

        lab_a_input = st.text_input("첫 번째 교수님 성함 입력", value=st.session_state.query_a)
        lab_b_input = st.text_input("두 번째 교수님 성함 입력", value=st.session_state.query_b)
        st.write("\n\n")

        if st.button("🔍 동명이인 확인 및 교수님 검색", use_container_width=True):
            if not lab_a_input.strip() or not lab_b_input.strip():
                st.error("⚠️ 교수님 성함을 모두 입력해 주세요!")
            else:
                name_map = {"손광훈": "Kwanghoon Sohn", "함범섭": "Bumsub Ham"}
                query_a_eng = name_map.get(lab_a_input.strip(), lab_a_input.strip())
                query_b_eng = name_map.get(lab_b_input.strip(), lab_b_input.strip())
                
                st.session_state.query_a = query_a_eng
                st.session_state.query_b = query_b_eng
                
                with st.spinner("글로벌 DB에서 해당하는 학자들을 찾고 있습니다..."):
                    st.session_state.cands_a = search_author_candidates(query_a_eng)
                    st.session_state.cands_b = search_author_candidates(query_b_eng)
                st.session_state.step = 2
                st.rerun()

# =========================================================
# [STEP 2] 동명이인 걸러내기 및 에러 친절 피드백
# =========================================================
elif st.session_state.step == 2:
    st.title("🔎 정확한 교수님을 선택해 주세요 (동명이인 방지)")
    st.caption("OpenAlex DB에서 검색된 학자들입니다. 소속 대학을 확인하고 올바른 교수님을 선택하세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"1️⃣ '{st.session_state.query_a}' 검색 결과")
        if not st.session_state.cands_a:
            st.error("💡 **검색 결과가 없습니다.**\n\n- 논문에 기재된 공식 영문 스펠링과 다를 수 있습니다.\n- 구글 스칼라 등에서 정확한 영문 성함을 확인 후 다시 입력해 보세요.")
            sel_a = None
        else:
            options_a = {c["id"]: f"{c['name']} (소속: {c['institution']} / 논문 {c['works_count']}편)" for c in st.session_state.cands_a}
            sel_a = st.radio("교수님을 선택하세요:", options=list(options_a.keys()), format_func=lambda x: options_a[x])

    with col2:
        st.subheader(f"2️⃣ '{st.session_state.query_b}' 검색 결과")
        if not st.session_state.cands_b:
            st.error("💡 **검색 결과가 없습니다.**\n\n- 논문에 기재된 공식 영문 스펠링과 다를 수 있습니다.\n- 구글 스칼라 등에서 정확한 영문 성함을 확인 후 다시 입력해 보세요.")
            sel_b = None
        else:
            options_b = {c["id"]: f"{c['name']} (소속: {c['institution']} / 논문 {c['works_count']}편)" for c in st.session_state.cands_b}
            sel_b = st.radio("교수님을 선택하세요:", options=list(options_b.keys()), format_func=lambda x: options_b[x], key="radio_b")

    st.divider()
    btn_prev, btn_next = st.columns(2)
    with btn_prev:
        if st.button("⬅️ 다시 검색하기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with btn_next:
        if st.button("🚀 선택한 교수님으로 지표 분석 시작", use_container_width=True):
            if sel_a and sel_b:
                name_a = [c["name"] for c in st.session_state.cands_a if c["id"] == sel_a][0]
                name_b = [c["name"] for c in st.session_state.cands_b if c["id"] == sel_b][0]
                with st.spinner("선택하신 교수님의 최근 100편 논문을 수집해 분석 중입니다..."):
                    st.session_state.data_a = fetch_openalex_lab_data_by_id(sel_a, name_a)
                    st.session_state.data_b = fetch_openalex_lab_data_by_id(sel_b, name_b)
                st.session_state.step = 3
                st.rerun()

# =========================================================
# [STEP 3] 5대 핵심 체감 지표 분석
# =========================================================
elif st.session_state.step == 3:
    data_a, data_b = st.session_state.data_a, st.session_state.data_b
    st.title("📊 5대 핵심 체감 지표 비교")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["① 탑티어 비중", "② 산학/외부 협업", "③ 학제 간 융합도", "④ 연구실 규모·사수", "⑤ 연구 산출 연속성"])
    
    with tab1: 
        try:
            res_1 = render_toptier(data_a, data_b)
            # 탑티어 지표 요약 문장 조립
            n_top_a = res_1["lab_a"]["n_top"]
            n_top_b = res_1["lab_b"]["n_top"]
            st.session_state.summary_1 = f"{data_a['professor']} 연구실은 최근 {n_top_a}편, {data_b['professor']} 연구실은 {n_top_b}편의 탑티어 논문을 게재했습니다."
        except Exception as e: st.error(f"지표 1 오류: {e}")
    with tab2:
        try:
            res_2 = render_industry_collab(data_a, data_b)
            st.session_state.summary_2 = res_2.get("summary", "")
        except Exception as e: st.error(f"지표 2 오류: {e}")
    with tab3:
        try: render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
        except Exception as e: st.error(f"지표 3 오류: {e}")
    with tab4:
        try: render_lab_size(data_a, data_b)
        except Exception as e: st.error(f"지표 4 오류: {e}")
    with tab5:
        try: render_continuity([data_a, data_b])
        except Exception as e: st.error(f"지표 5 오류: {e}")

    st.divider()
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 동명이인 선택으로 돌아가기", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("📌 최종 Visual Brief 리포트 다운로드 ➡️", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# =========================================================
# [STEP 4] 리포트 다운로드 (PDF 오류 해결)
# =========================================================
elif st.session_state.step == 4:
    st.title("📌 최종 비교 리포트 다운로드")
    st.divider()

    st.subheader("💡 맞춤형 Visual Brief")
    st.success(
        f"1. **연구 역량:** {st.session_state.summary_1}\n"
        "2. **연구실 규모:** 구체적인 인원과 협업 방식을 데이터로 확인했습니다.\n"
        f"3. **산학/외부 협업:** {st.session_state.summary_2 if st.session_state.summary_2 else '데이터 산출 완료'}\n"
    )

    st.divider()
    st.markdown("**📂 다운로드 파일 포맷 안내**")
    st.caption("기존에 PDF나 HWP 형식을 선택했을 때 파일이 깨지거나 열리지 않던 현상을 해결하기 위해, 텍스트가 완벽하게 호환되는 순수 텍스트(TXT)와 마크다운(MD) 형식으로 지원 포맷을 최적화했습니다.")
    
    col_fmt, col_dl = st.columns([1, 2])
    with col_fmt: 
        file_format = st.selectbox("파일 형식", ["TXT (일반 텍스트)", "MD (마크다운 포맷)"])
    
    ext = "txt" if "TXT" in file_format else "md"
    report_content = f"# LABMATCH 최종 리포트\n\n## 1. 요약 결과\n- {st.session_state.summary_1}\n- {st.session_state.summary_2}\n\n## 2. 면담 질문 가이드\n- 사수 배정 및 프로젝트 진행 방식 확인\n- 신입생 연구 주제 선정 자율성 확인"
    
    with col_dl:
        st.write("")
        st.download_button(f"📄 {ext.upper()} 리포트 다운로드", data=report_content.encode("utf-8"), file_name=f"labmatch_report.{ext}", use_container_width=True)

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
