"""
지표 1. 탑티어 논문 비중 및 건수 (전 분야 확장 하이브리드 버전)

수식 (2021~2025)
- 전체 논문 수 = 정식 게재 논문 수 (프리프린트 제외)
- 탑티어 비중(%) = 탑티어 논문 수 / 전체 논문 수 * 100
- 연평균 탑티어 = 탑티어 논문 수 / 활동 연수 (기간 중 첫 논문 연도부터)

하이브리드 등급 판별 규칙 (전 학문 분야 대응)
1. [CS/AI 특화] 공개 등급표(CORE A*, CCF A) 매칭 시 우선 적용
2. [전 분야 공통 ①] OpenAlex 분야 보정 피인용 백분위 상위 10% 이내(>= 0.90) 또는 FWCI >= 2.0 -> 탑티어
   (상위 25% 이내(>= 0.75) 또는 FWCI >= 1.2 -> 중위권)
3. [전 분야 공통 ②] 게재 저널/학회 임팩트(2yr_mean_citedness) >= 5.0 -> 탑티어 (2.0 이상 -> 중위권)
- 워크숍·Findings·프리프린트는 탑티어로 보지 않음
"""

import json
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

MOCK_PATH = Path(__file__).with_name("mock-up-data-toptier-demo.json")
START, END = 2021, 2025

# 등급표: CS/AI 핵심 학회·저널 우선 매칭용
TIER_TABLE = {
    # 학회 · CORE A* -> 탑티어
    "CVPR": (1, ["CVPR", "Computer Vision and Pattern Recognition"]),
    "ICCV": (1, ["ICCV", "International Conference on Computer Vision"]),
    "ECCV": (1, ["ECCV", "European Conference on Computer Vision"]),
    "NeurIPS": (1, ["NeurIPS", "NIPS", "Neural Information Processing Systems"]),
    "ICML": (1, ["ICML", "International Conference on Machine Learning"]),
    "ICLR": (1, ["ICLR", "International Conference on Learning Representations"]),
    "AAAI": (1, ["AAAI"]),
    "IJCAI": (1, ["IJCAI"]),
    "ACL": (1, ["ACL", "Annual Meeting of the Association for Computational Linguistics"]),
    "EMNLP": (1, ["EMNLP", "Empirical Methods in Natural Language Processing"]),
    "KDD": (1, ["KDD", "Knowledge Discovery and Data Mining"]),
    # 학회 · CORE A -> 중위권
    "WACV": (2, ["WACV", "Winter Conference on Applications of Computer Vision"]),
    "BMVC": (2, ["BMVC", "British Machine Vision Conference"]),
    "NAACL": (2, ["NAACL", "North American Chapter of the Association for Computational Linguistics"]),
    # 저널 · CCF A -> 탑티어
    "TPAMI": (1, ["TPAMI", "Transactions on Pattern Analysis and Machine Intelligence"]),
    "IJCV": (1, ["IJCV", "International Journal of Computer Vision"]),
    "JMLR": (1, ["JMLR", "Journal of Machine Learning Research"]),
    "AIJ": (1, ["^Artificial Intelligence$"]),
    "TIP": (1, ["Transactions on Image Processing"]),
    "TOG": (1, ["ACM Transactions on Graphics"]),
    "TVCG": (1, ["Transactions on Visualization and Computer Graphics"]),
    # 저널 · CCF B -> 중위권
    "PR": (2, ["^Pattern Recognition$"]),
    "TCSVT": (2, ["Transactions on Circuits and Systems for Video Technology"]),
    "TMM": (2, ["IEEE Transactions on Multimedia"]),
    "TNNLS": (2, ["Transactions on Neural Networks and Learning Systems"]),
    "CVIU": (2, ["Computer Vision and Image Understanding"]),
    "NN": (2, ["^Neural Networks$"]),
    "TACL": (2, ["Transactions of the Association for Computational Linguistics"]),
}
TIER_LABEL = {1: "탑티어", 2: "중위권", 3: "기타"}

# 임계값 설정 (타 전공 확장 시 기준치)
TOP_PERCENTILE_THRESHOLD = 0.90   # 분야 내 상위 10%
MID_PERCENTILE_THRESHOLD = 0.75   # 분야 내 상위 25%
TOP_FWCI_THRESHOLD = 2.0          # 세계 평균 대비 2배 이상 피인용
MID_FWCI_THRESHOLD = 1.2          # 세계 평균 대비 1.2배 이상 피인용
TOP_IMPACT_THRESHOLD = 5.0        # 저널 2년 평균 피인용(IF 유사) 5.0 이상
MID_IMPACT_THRESHOLD = 2.0        # 저널 2년 평균 피인용(IF 유사) 2.0 이상

# 연구실 색 (A, B) / 연한 색
COLOR = ("#3D5A80", "#5E8C83")
LIGHT = ("#E3E8EF", "#E2ECEA")
TEXT, MUTE, LINE = "#31333F", "#6b7280", "#e6e8ec"

_EXCLUDED_TYPES = {"preprint", "paratext", "erratum", "retraction", "editorial"}
_NOT_MAIN = re.compile(r"workshop|findings|\b\w+W\)", re.IGNORECASE)
_ALIASES = sorted(((a, k, t) for k, (t, al) in TIER_TABLE.items() for a in al),
                  key=lambda x: len(x[0]), reverse=True)


def _extract_metrics(paper):
    """OpenAlex 원시 데이터 또는 정제된 딕셔너리에서 백분위, FWCI, 저널 임팩트를 안전하게 추출"""
    # 1. 분야 보정 백분위 추출 (OpenAlex API 구조 및 커스텀 키 모두 대응)
    pct_obj = paper.get("citation_normalized_percentile")
    if isinstance(pct_obj, dict):
        percentile = pct_obj.get("value")
    else:
        percentile = pct_obj if isinstance(pct_obj, (int, float)) else paper.get("percentile")

    # 2. FWCI 추출
    fwci = paper.get("fwci")

    # 3. 게재처(Source) 2년 평균 피인용 지수 추출
    impact = paper.get("2yr_mean_citedness") or paper.get("source_impact")
    if impact is None:
        loc = paper.get("primary_location") or {}
        src = loc.get("source") or {}
        summary = src.get("summary_stats") or {}
        impact = summary.get("2yr_mean_citedness")

    return percentile, fwci, impact


def classify_paper(paper):
    """
    논문 1편의 등급(1: 탑티어, 2: 중위권, 3: 기타), 정규화된 게재처명, 판별 근거를 반환
    """
    venue = paper.get("venue")
    if not venue:
        loc = paper.get("primary_location") or {}
        src = loc.get("source") or {}
        venue = src.get("display_name")

    clean_venue = venue.strip() if venue else "(게재처 없음)"

    # 워크숍·Findings 등은 무조건 기타(3) 처리
    if not venue or _NOT_MAIN.search(clean_venue):
        return 3, clean_venue, "제외 대상(워크숍 등)"

    # [1단계] CS/AI 학회·저널 등급표 매칭
    for alias, key, tier in _ALIASES:
        pattern = (rf"{alias}" if alias.startswith("^")
                   else rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])")
        if re.search(pattern, clean_venue, re.IGNORECASE):
            return tier, key, "학회/저널 등급표"

    # [2단계] OpenAlex 분야 보정 백분위 & FWCI 기준 (전 분야 공통)
    percentile, fwci, impact = _extract_metrics(paper)

    if percentile is not None:
        if percentile >= TOP_PERCENTILE_THRESHOLD:
            return 1, clean_venue, f"분야 상위 {(1 - percentile) * 100:.1f}%"
        elif percentile >= MID_PERCENTILE_THRESHOLD:
            return 2, clean_venue, f"분야 상위 {(1 - percentile) * 100:.1f}%"

    if fwci is not None:
        if fwci >= TOP_FWCI_THRESHOLD:
            return 1, clean_venue, f"FWCI {fwci:.2f}"
        elif fwci >= MID_FWCI_THRESHOLD:
            return 2, clean_venue, f"FWCI {fwci:.2f}"

    # [3단계] 게재 저널/학회 자체 임팩트(2yr_mean_citedness) 기준 (신생 논문 보완)
    if impact is not None:
        if impact >= TOP_IMPACT_THRESHOLD:
            return 1, clean_venue, f"저널 임팩트 {impact:.1f}"
        elif impact >= MID_IMPACT_THRESHOLD:
            return 2, clean_venue, f"저널 임팩트 {impact:.1f}"

    return 3, clean_venue, "일반 게재"


def compute_toptier(lab, start=START, end=END):
    base = {"lab_name": lab.get("lab_name", ""), "professor": lab.get("professor", "")}
    papers = lab.get("toptier_papers")

    if papers is None:
        n_all, n_top = lab.get("total_papers") or 0, lab.get("top_tier_papers") or 0
        years = [w["year"] for w in lab.get("yearly_works", []) if w.get("count")]
        active = end - max(min(years), start) + 1 if years else 0
        return {**base, "has_papers": False, "n_all": n_all, "n_top": n_top,
                "n_mid": None, "n_oth": None, "active": active, "df": pd.DataFrame()}

    rows = []
    for p in papers:
        y = p.get("year") or p.get("publication_year")
        if y is None or not start <= int(y) <= end:
            continue
        if (p.get("type") or "").lower() in _EXCLUDED_TYPES or p.get("venue_type") == "repository":
            continue

        tier, key, basis = classify_paper(p)
        rows.append({
            "year": int(y),
            "title": p.get("title", ""),
            "venue": key,
            "tier": tier,
            "등급": TIER_LABEL[tier],
            "판별기준": basis,
            "url": p.get("url") or p.get("id")
        })

    df = pd.DataFrame(rows, columns=["year", "title", "venue", "tier", "등급", "판별기준", "url"])
    count = df["tier"].value_counts()
    active = end - max(int(df["year"].min()), start) + 1 if len(df) else 0
    return {**base, "has_papers": True, "n_all": len(df), "n_top": int(count.get(1, 0)),
            "n_mid": int(count.get(2, 0)), "n_oth": int(count.get(3, 0)),
            "active": active, "df": df}


def _ratio(r):
    return r["n_top"] / r["n_all"] * 100 if r["n_all"] else None


def _per_year(r):
    return r["n_top"] / r["active"] if r["active"] else None


# ---------------- 화면 조각 (HTML) ----------------

def _badge(mine, other, unit):
    if mine is None or other is None or mine <= other:
        return ""
    return (f"<span style='font-size:12px;padding:1px 8px;border-radius:999px;background:#F0F2F6;"
            f"border:1px solid #e1e4ea;color:{TEXT};margin-left:6px'>+{mine - other:.3g}{unit}</span>")


def _ring(r, color, light):
    v = _ratio(r)
    rad, circ = 56, 2 * 3.14159 * 56
    dash = circ * (v or 0) / 100
    label = "정보 없음" if v is None else f"{v:.3g}%"
    return (f"<svg width='140' height='140'>"
            f"<circle cx='70' cy='70' r='{rad}' fill='none' stroke='{light}' stroke-width='15'/>"
            f"<circle cx='70' cy='70' r='{rad}' fill='none' stroke='{color}' stroke-width='15' "
            f"stroke-linecap='round' stroke-dasharray='{dash} {circ}' transform='rotate(-90 70 70)'/>"
            f"<text x='70' y='76' text-anchor='middle' font-size='26' font-weight='800' fill='{color}'>{label}</text>"
            f"<text x='70' y='97' text-anchor='middle' font-size='11' fill='{MUTE}'>{r['n_top']} / {r['n_all']}편</text>"
            f"</svg>")


def _pyramid(r, color):
    if r["n_mid"] is None:
        return f"<div style='font-size:13px;color:{MUTE}'>등급별 정보 없음 · 수집 예정</div>"
    levels = [(1, r["n_top"], color, "#fff"), (2, r["n_mid"], "#D5D9E0", TEXT),
              (3, r["n_oth"], "#EEF0F3", "#4b5563")]
    edges = [40, 60, 80, 100]          # 층별 윗변·아랫변 너비(%)
    html = []
    for i, (tier, n, bg, fg) in enumerate(levels):
        top, bottom = (100 - edges[i]) / 2, (100 - edges[i + 1]) / 2
        pct = round(n / r["n_all"] * 100) if r["n_all"] else 0
        star = "★ " if tier == 1 else ""
        html.append(
            "<div style='margin-bottom:4px'>"
            f"<div style='height:40px;display:flex;align-items:center;justify-content:center;"
            f"background:{bg};color:{fg};font-weight:800;font-size:15px;"
            f"clip-path:polygon({top}% 0,{100 - top}% 0,{100 - bottom}% 100%,{bottom}% 100%)'>"
            f"{star}{TIER_LABEL[tier]} {n}편<span style='font-weight:500;font-size:12px;margin-left:4px'>({pct}%)</span></div>"
            "</div>"
        )
    return "".join(html)


def _stickers(r, top_n=6):
    if not r["has_papers"]:
        return ""
    vc = r["df"][r["df"]["tier"] == 1]["venue"].value_counts().head(top_n)
    if vc.empty:
        return f"<div style='font-size:13px;color:{MUTE}'>탑티어 게재 이력 없음</div>"
    mx = vc.max()
    return "".join(
        f"<span style='display:inline-flex;align-items:center;gap:6px;font-weight:700;border-radius:8px;"
        f"padding:4px 10px;margin:4px 3px;color:{TEXT};background:#fff;border:1px solid #d5d9e0;"
        f"box-shadow:0 1px 0 {LINE};font-size:{13 + 10 * n / mx:.0f}px'>"
        f"<span style='font-size:.7em;color:#9aa3af'>★</span>{v}"
        f"<b style='background:#F0F2F6;border-radius:999px;font-size:11px;padding:1px 6px;font-weight:600'>{n}</b></span>"
        for v, n in vc.items()
    )


def _panel(r, other, idx, max_top):
    color, light = COLOR[idx], LIGHT[idx]
    title = "font-size:13px;color:#6b7280;font-weight:700;margin-bottom:6px"
    per_year = _per_year(r)
    per_year_txt = "-" if per_year is None else f"{per_year:.1f}편"
    width = r["n_top"] / max_top * 100 if max_top else 0
    return (
        f"<div style='border:1px solid {LINE};border-radius:12px;overflow:hidden;background:#fff;"
        f"border-top:4px solid {color};padding-bottom:16px'>"
        f"<div style='padding:12px 20px 10px;border-bottom:1px solid #eef0f3'>"
        f"<div style='font-size:20px;font-weight:800;color:{color}'>{r['lab_name']}</div>"
        f"<div style='font-size:13px;color:{MUTE}'>{r['professor']} 교수 · 논문 {r['n_all']}편</div></div>"
        f"<div style='padding:4px 20px 0'>"
        f"<div style='display:grid;grid-template-columns:165px 1fr;gap:14px;margin-top:14px'>"
        f"<div><div style='{title}'>탑티어 비중{_badge(_ratio(r), _ratio(other), '%p')}</div>"
        f"{_ring(r, color, light)}</div>"
        f"<div><div style='{title}'>탑티어 건수 (5년 합계){_badge(r['n_top'], other['n_top'], '편')}</div>"
        f"<div style='font-size:34px;font-weight:800;line-height:1;color:{color}'>{r['n_top']}"
        f"<span style='font-size:16px'>편</span></div>"
        f"<div style='height:12px;background:#f3f4f6;border-radius:999px;overflow:hidden;margin:10px 0 6px'>"
        f"<div style='height:100%;width:{width:.0f}%;background:{color};border-radius:999px'></div></div>"
        f"<div style='font-size:12px;color:{MUTE}'>연평균 {per_year_txt} · 막대는 두 연구실 같은 기준</div>"
        f"</div></div>"
        f"<div style='margin-top:16px'><div style='{title}'>게재처 등급별 논문 수</div>{_pyramid(r, color)}</div>"
        f"<div style='margin-top:14px'><div style='{title}'>★ 탑티어 게재처 TOP</div>{_stickers(r)}</div>"
        f"</div></div>"
    )


# ---------------- 그래프 ----------------

def _yearly_chart(ra, rb):
    frames = []
    for r in (ra, rb):
        g = r["df"].groupby("year")
        y = pd.DataFrame({"전체": g.size(), "탑티어": g["tier"].apply(lambda s: int((s == 1).sum()))})
        y = y.reindex(range(START, END + 1), fill_value=0).reset_index(names="year")
        y["연구실"] = r["lab_name"]
        frames.append(y)
    data = pd.concat(frames)
    labs = [ra["lab_name"], rb["lab_name"]]
    base = alt.Chart(data).encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("연구실:N", sort=labs),
        tooltip=["연구실", alt.Tooltip("year:O", title="연도"), "탑티어", "전체"])
    total = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y=alt.Y("전체:Q", title="논문 수 (편)"),
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(LIGHT)), legend=None))
    top = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y="탑티어:Q",
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(COLOR)),
                        legend=alt.Legend(orient="top", title=None)))
    text = base.mark_text(dy=10, fontSize=11, color="white", fontWeight="bold").encode(
        y="탑티어:Q", text="탑티어:Q")
    return alt.layer(total, top, text).resolve_scale(color="independent").properties(height=280)


def _venue_chart(ra, rb):
    rows = []
    for r, sign in ((ra, -1), (rb, 1)):
        for v, n in r["df"][r["df"]["tier"] == 1]["venue"].value_counts().items():
            rows.append({"학회": v, "연구실": r["lab_name"], "편수": int(n), "x": sign * int(n)})
    if not rows:
        return None
    data = pd.DataFrame(rows)
    order = data.groupby("학회")["편수"].sum().sort_values(ascending=False).index.tolist()
    labs = [ra["lab_name"], rb["lab_name"]]
    mx = data["편수"].max() + 1
    base = alt.Chart(data).encode(
        y=alt.Y("학회:N", sort=order, title=None, axis=alt.Axis(labelOverlap=False)),
        tooltip=["학회", "연구실", "편수"])
    bars = base.mark_bar(cornerRadius=3).encode(
        x=alt.X("x:Q", title=f"← {labs[0]}   |   {labs[1]} →", scale=alt.Scale(domain=[-mx, mx]),
                axis=alt.Axis(labelExpr="abs(datum.value)", tickMinStep=1)),
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(COLOR)),
                        legend=alt.Legend(orient="top", title=None)))
    left = base.transform_filter("datum.x < 0").mark_text(align="right", dx=-4, fontSize=11).encode(
        x="x:Q", text="편수:Q")
    right = base.transform_filter("datum.x > 0").mark_text(align="left", dx=4, fontSize=11).encode(
        x="x:Q", text="편수:Q")
    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#9ca3af").encode(x="x:Q")
    return (bars + left + right + rule).properties(height=34 * len(order) + 20)


def _paper_table(ra, rb):
    c1, c2 = st.columns([1, 2])
    who = c1.radio("연구실", [ra["lab_name"], rb["lab_name"], "둘 다"], horizontal=True,
                   key="toptier_list_lab")
    tiers = c2.multiselect("등급", list(TIER_LABEL.values()), default=["탑티어"],
                           key="toptier_list_tier")
    frames = [r["df"].assign(연구실=r["lab_name"]) for r in (ra, rb) if who in (r["lab_name"], "둘 다")]
    df = pd.concat(frames)
    df = df[df["등급"].isin(tiers)].sort_values(["year", "venue"], ascending=[False, True])
    st.caption(f"{len(df)}편")
    st.dataframe(
        df[["연구실", "year", "등급", "판별기준", "venue", "title", "url"]].rename(
            columns={"year": "연도", "venue": "학회/저널", "title": "제목", "url": "링크"}),
        hide_index=True, use_container_width=True,
        column_config={"링크": st.column_config.LinkColumn("링크", display_text="원문"),
                       "연도": st.column_config.NumberColumn("연도", format="%d")})


# ---------------- 메인 ----------------

def render_toptier(lab_a, lab_b):
    ra, rb = compute_toptier(lab_a), compute_toptier(lab_b)

    st.subheader("1. 탑티어 논문 비중 및 건수")
    st.caption(f"유명한 학회·저널에 논문을 자주 내는가? · {START}–{END}")

    max_top = max(ra["n_top"], rb["n_top"])
    col_a, col_b = st.columns(2, gap="medium")
    col_a.markdown(_panel(ra, rb, 0, max_top), unsafe_allow_html=True)
    col_b.markdown(_panel(rb, ra, 1, max_top), unsafe_allow_html=True)

    st.write("")
    if ra["has_papers"] and rb["has_papers"]:
        t1, t2, t3 = st.tabs(["연도별 추이", "학회/저널별 비교", "논문 목록"])
        with t1:
            st.caption("진한 막대 = 탑티어 · 연한 막대 = 전체 논문")
            st.altair_chart(_yearly_chart(ra, rb), use_container_width=True)
        with t2:
            chart = _venue_chart(ra, rb)
            if chart is None:
                st.caption("탑티어 논문이 없어요.")
            else:
                st.caption("탑티어 학회/저널별 논문 수 (왼쪽 A · 오른쪽 B)")
                st.altair_chart(chart, use_container_width=True)
        with t3:
            _paper_table(ra, rb)
    else:
        st.info("논문 목록이 없어 연도별·학회별 그래프는 수집 예정이에요.")

    return {"lab_a": ra, "lab_b": rb}


if __name__ == "__main__":
    st.set_page_config(page_title="탑티어 논문 비중 및 건수", layout="wide")
    data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    render_toptier(data["lab_A"], data["lab_B"])