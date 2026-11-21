// LABMATCH 첫 화면 컴포넌트 (st.components.v2)
// Python이 data로 넘겨주는 것: slots, yonsei, fields(스냅샷), search(검색 결과)
// Python으로 보내는 것: setTriggerValue('event', {type: 'slots' | 'search' | 'compare', ...})

const UI = { mode: 'hero', dept: null, idx: 0, field: null, sub: null, showAll: false, help: false, drop: false, q: '', popSlot: null };

const UNI_KO = {
  'Yonsei University': '연세대', 'Seoul National University': '서울대', 'Korea Advanced Institute of Science and Technology': 'KAIST',
  'Pohang University of Science and Technology': 'POSTECH', 'Korea University': '고려대', 'Sungkyunkwan University': '성균관대',
  'Hanyang University': '한양대', 'Ulsan National Institute of Science and Technology': 'UNIST', 'Ewha Womans University': '이화여대',
  'Kyungpook National University': '경북대', 'Pusan National University': '부산대', 'Gwangju Institute of Science and Technology': 'GIST',
  'Daegu Gyeongbuk Institute of Science and Technology': 'DGIST', 'Kyung Hee University': '경희대', 'Chung-Ang University': '중앙대',
  'Sogang University': '서강대', 'Seoul National University Hospital': '서울대병원', 'Samsung Medical Center': '삼성서울병원',
  'Asan Medical Center': '서울아산병원', 'Severance Hospital': '세브란스병원', 'Chonnam National University': '전남대',
  'Chungnam National University': '충남대', 'Inha University': '인하대', 'Ajou University': '아주대', 'Konkuk University': '건국대',
  'Dongguk University': '동국대', 'Hankuk University of Foreign Studies': '한국외대', 'University of Seoul': '서울시립대',
  'Korea Institute of Science and Technology': 'KIST', 'Catholic University of Korea': '가톨릭대', 'Chonbuk National University': '전북대',
  'Jeonbuk National University': '전북대', 'Chungbuk National University': '충북대', 'Gyeongsang National University': '경상국립대',
  'Kangwon National University': '강원대', 'Hallym University': '한림대', 'Sejong University': '세종대', 'Kookmin University': '국민대',
};
const uniKo = (s) => (s && UNI_KO[s]) || s || '소속 정보 없음';
const isYonsei = (s) => !!s && /Yonsei|연세/.test(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmtGrowth = (g) => (g == null ? '' : (g >= 0 ? '+' : '') + Math.round(g * 100) + '%');

function ensureFonts() {
  if (document.getElementById('lm-fonts')) return;
  const l = document.createElement('link');
  l.id = 'lm-fonts'; l.rel = 'stylesheet';
  l.href = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap';
  document.head.appendChild(l);
}

const HTML = `
<div class="lm">
  <div class="top"><div class="logo">LAB<i>MATCH</i></div><button class="ghost" data-act="help" type="button">이용 안내</button></div>
  <div class="hero">
    <div>
      <h1>어느 연구실이 나에게 맞을까?</h1>
      <p class="lead">교수님 두 분을 고르면 최근 논문으로 5가지 지표를 비교합니다.</p>
      <div class="searchbox">
        <div class="searchrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input class="q" type="text" autocomplete="off" placeholder="교수님 성함 (한글/영문)" aria-label="교수님 성함">
          <button class="go" data-act="search" type="button">검색</button>
        </div>
        <div class="modes">
          <button class="mode" data-mode="hero" type="button">이름으로 찾기</button>
          <button class="mode" data-mode="dept" type="button">연세대 학과로 둘러보기</button>
          <button class="mode" data-mode="field" type="button">분야별 연구자 찾기</button>
        </div>
        <div class="drop" hidden></div>
      </div>
      <div class="suggest">
        <div class="lbl">아는 교수님이 없다면 이렇게 시작해 보세요</div>
        <button type="button" data-mode="dept"><span>↳</span>내 전공 학과 교수님 둘러보기</button>
        <button type="button" data-mode="field"><span>↳</span>요즘 논문이 많이 나오는 분야의 전국 연구자 보기</button>
        <button type="button" data-act="sample"><span>↳</span><span class="sample-label" style="color:inherit"></span></button>
      </div>
    </div>
    <div class="arena" aria-label="비교할 연구실">
      <div class="arena-top"><b>비교할 연구실</b><span class="count"></span></div>
      <div class="duel"><div class="pc A"></div><div class="vs">VS</div><div class="pc B"></div></div>
      <button class="cta" data-act="compare" type="button">비교 시작</button>
      <div class="cta-hint"></div>
    </div>
  </div>
  <section class="sec-dept">
    <div class="sh"><h2>연세대 학과로 둘러보기</h2><p class="dept-cap"></p></div>
    <div class="chips dept-chips"></div>
    <div class="strip"><button class="nav l" data-act="prev" type="button" aria-label="이전">‹</button><button class="nav r" data-act="next" type="button" aria-label="다음">›</button></div>
    <div class="dots"></div>
  </section>
  <section class="sec-field">
    <div class="sh"><h2>분야별 국내 연구자 별자리</h2><p>점 하나가 연구자 한 명이에요. 클수록 최근 3년 논문이 많아요. 점을 눌러 담아 보세요.</p></div>
    <div class="field-body"></div>
  </section>
  <div class="scrim" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-label="이용 안내">
      <button class="close" data-act="close" type="button" aria-label="닫기">✕</button>
      <h3>이용 안내</h3>
      <p class="msub">예비 대학원생이 연구실을 고를 때 궁금한 다섯 가지를 논문 데이터로 보여드려요.</p>
      <div class="steps">
        <div class="step"><b>STEP 1</b><p>이름, 학과, 분야로 교수님 찾기</p></div>
        <div class="step"><b>STEP 2</b><p>A, B에 한 분씩 담기</p></div>
        <div class="step"><b>STEP 3</b><p>5가지 지표 비교 후 리포트 저장</p></div>
      </div>
      <table>
        <tr><th>지표</th><th>이런 질문에 답해요</th></tr>
        <tr><td>① 우수 학회·저널 비중</td><td>주요 학회와 저널에 얼마나 자주 싣나요?</td></tr>
        <tr><td>② 산학·외부 협업 비율</td><td>기업 과제 중심인가요, 학술 연구 중심인가요?</td></tr>
        <tr><td>③ 학제 간 융합도</td><td>다른 전공 출신도 적응할 수 있을까요?</td></tr>
        <tr><td>④ 연구실 규모·사수</td><td>질문할 선배와 동료가 얼마나 있나요?</td></tr>
        <tr><td>⑤ 연구 산출 연속성</td><td>논문이 꾸준히 나오나요?</td></tr>
      </table>
      <ul>
        <li>동명이인은 소속 기관으로 구분합니다.</li>
        <li>최근 논문 100편을 분석하며, 핵심 지표는 2021~2025년 기준입니다.</li>
        <li>연구실 분위기, 인건비처럼 논문에 없는 정보는 면담에서 확인하세요.</li>
      </ul>
    </div>
  </div>
</div>`;

export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  ensureFonts();
  const D = data || {};
  const slots = { A: (D.slots && D.slots.A) || null, B: (D.slots && D.slots.B) || null };
  const YON = (D.yonsei || []).map((p) => ({ ...p, key: 'y:' + p.name, aff: `연세대 ${p.dept}` }));
  const FS = D.fields || null;

  let root = parentElement.querySelector('.lm');
  if (!root) {
    const holder = document.createElement('div');
    holder.innerHTML = HTML;
    parentElement.appendChild(holder);
    root = holder.querySelector('.lm');
  }
  const $ = (s) => root.querySelector(s);
  const $$ = (s) => Array.from(root.querySelectorAll(s));
  const send = (ev) => setTriggerValue('event', { ...ev, t: Date.now() });

  // ---------- 비교함 ----------
  const sameP = (a, b) => a && b && a.key === b.key;
  function put(slot, p) {
    const other = slot === 'A' ? 'B' : 'A';
    if (sameP(slots[other], p)) slots[other] = null;
    slots[slot] = p;
    UI.popSlot = slot;
    send({ type: 'slots', A: slots.A, B: slots.B });
    renderAll();
  }
  function cardHTML(p, slot) {
    if (!p) return `<div class="qm">?</div><p><b>${slot}</b> 칸이 비어 있어요<br>아래에서 교수님을 담아 주세요</p>`;
    const s1 = p.works != null ? `<div class="st"><small>${esc(p.works_label || '논문')}</small><b>${p.works}</b></div>` : `<div class="st"><small>단과대</small><b style="font-size:12.5px">${esc(p.col || '-')}</b></div>`;
    const s2 = p.field || p.dept ? `<div class="st"><small>${p.field ? '주 분야' : '학과'}</small><b style="font-size:12.5px">${esc(p.field || p.dept)}</b></div>` : '';
    return `<div class="sheen"></div><button class="rm" type="button" data-rm="${slot}">빼기</button>
      <div class="slot">LAB ${slot}</div><div class="mono">${esc((p.name || '?')[0])}</div>
      <div class="pn">${esc(p.name)}</div><div class="pe">${esc(p.eng || '')}</div><div class="pa">${esc(p.aff || '')}</div>
      <div class="stats">${s1}${s2}</div>`;
  }
  function renderSlots() {
    ['A', 'B'].forEach((k) => {
      const el = $('.pc.' + k);
      const p = slots[k];
      el.className = 'pc ' + k + (p ? ' filled' : ' empty') + (UI.popSlot === k ? ' pop' : '');
      el.innerHTML = cardHTML(p, k);
    });
    UI.popSlot = null;
    const n = (slots.A ? 1 : 0) + (slots.B ? 1 : 0);
    $('.count').textContent = n + ' / 2';
    $('.cta').classList.toggle('ready', n === 2);
    $('.cta-hint').textContent = n === 2 ? `${slots.A.name} vs ${slots.B.name}` : !slots.A ? 'A 연구실을 선택하세요' : 'B 연구실을 선택하세요';
    const hint = $('.cta-hint');
    hint.classList.toggle('warn', !!D.notice);
    if (D.notice) hint.textContent = D.notice;
  }

  // ---------- 검색 ----------
  function personFromOA(r) {
    return { key: 'oa:' + r.oa_id, oa_id: r.oa_id, name: r.name, eng: '', aff: uniKo(r.inst), works: r.works, works_label: r.works_label || '전체 논문', field: r.field || null };
  }
  function rowHTML(p) {
    const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
    const extra = p.works != null ? `, ${esc(p.works_label || '논문')} ${p.works}편` : '';
    return `<div class="row"><div class="avatar">${esc((p.name || '?')[0])}</div><div class="meta"><div class="nm">${esc(p.name)} <span style="color:var(--faint);font-weight:400">${esc(p.eng || '')}</span></div><div class="af">${esc(p.aff)}${extra}</div></div>
      <div class="mini"><button class="a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}">A</button><button class="b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}">B</button></div></div>`;
  }
  const searchPool = {};
  function renderDrop() {
    const d = $('.drop');
    const q = UI.q.trim();
    if (!UI.drop || !q) { d.hidden = true; return; }
    const local = YON.filter((p) => p.name.includes(q) || (p.eng || '').toLowerCase().includes(q.toLowerCase()));
    local.forEach((p) => (searchPool[p.key] = p));
    let html = '';
    if (local.length) html += `<div class="grp">연세대 등록 교수님</div>` + local.map(rowHTML).join('');
    const S = D.search;
    if (S && S.q === q) {
      if (S.error) html += `<div class="note">${esc(S.error)}</div>`;
      else if (S.results && S.results.length) {
        const ps = S.results.map(personFromOA);
        ps.forEach((p) => (searchPool[p.key] = p));
        html += `<div class="grp">OpenAlex 검색 결과</div>` + ps.map(rowHTML).join('') + `<div class="note">동명이인은 소속을 확인하세요</div>`;
      } else html += `<div class="note">검색 결과가 없습니다. 영문 이름으로 다시 검색하세요.</div>`;
    } else if (!local.length) {
      html += `<div class="note">Enter 또는 검색 버튼을 누르면 OpenAlex에서 찾아요.</div>`;
    } else {
      html += `<div class="note">다른 대학 교수님은 검색 버튼을 누르면 OpenAlex에서 찾아요.</div>`;
    }
    d.innerHTML = html;
    d.hidden = false;
  }
  function doSearch() {
    const q = UI.q.trim();
    if (!q) return;
    UI.drop = true;
    renderDrop();
    if (!(D.search && D.search.q === q)) send({ type: 'search', q });
  }

  // ---------- 학과 필름스트립 ----------
  const DEPTS = [...new Set(YON.map((y) => y.dept))];
  if (!UI.dept || !DEPTS.includes(UI.dept)) { UI.dept = DEPTS[0] || null; UI.idx = 0; }
  function renderDept() {
    $('.dept-cap').textContent = `${DEPTS.length}개 학과, 교수님 ${YON.length}명 등록`;
    $('.dept-chips').innerHTML = DEPTS.map((d) => {
      const c = YON.find((y) => y.dept === d).col;
      return `<button class="chip ${d === UI.dept ? 'on' : ''}" type="button" data-dept="${esc(d)}">${esc(d)}<em>${esc(c)}</em></button>`;
    }).join('');
    const st = $('.strip');
    st.querySelectorAll('.fc').forEach((n) => n.remove());
    const list = YON.filter((y) => y.dept === UI.dept);
    if (UI.idx >= list.length) UI.idx = 0;
    list.forEach((p, i) => {
      searchPool[p.key] = p;
      const off = i - UI.idx;
      const el = document.createElement('div');
      el.className = 'fc';
      el.style.transform = `translateX(${off * 190}px) scale(${off === 0 ? 1 : 0.84}) rotateY(${off * -8}deg)`;
      el.style.opacity = Math.abs(off) > 2 ? 0 : off === 0 ? 1 : 0.55;
      el.style.zIndex = 10 - Math.abs(off);
      const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
      el.innerHTML = `<div class="mono">${esc(p.name[0])}</div><div class="pn">${esc(p.name)}</div><div class="pe">${esc(p.eng)}</div>
        <div class="pd">${esc(p.col)}<br>${esc(p.dept)}</div>
        <div class="acts"><button class="add a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}">${onA ? 'A에 담김' : 'A에 담기'}</button><button class="add b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}">${onB ? 'B에 담김' : 'B에 담기'}</button></div>`;
      el.dataset.idx = i;
      st.appendChild(el);
    });
    $('.dots').innerHTML = list.map((_, i) => `<i class="${i === UI.idx ? 'on' : ''}"></i>`).join('');
    $('.nav.l').disabled = UI.idx === 0;
    $('.nav.r').disabled = UI.idx >= list.length - 1;
  }

  // ---------- 분야 ----------
  const fieldsById = {};
  (FS && FS.fields ? FS.fields : []).forEach((f) => (fieldsById[f.id] = f));
  const featured = FS ? (FS.featured || []).filter((id) => fieldsById[id]) : [];
  if (FS && (!UI.field || !fieldsById[UI.field])) { UI.field = featured[0] || (FS.fields[0] && FS.fields[0].id); UI.sub = null; }
  const curField = () => fieldsById[UI.field];
  const curSubs = () => ((curField() && curField().subfields) || []).filter((s) => s.researchers && s.researchers.length);
  function researchersOf(field, subId) {
    const subs = (field && field.subfields) || [];
    const pick = subId ? subs.filter((s) => s.id === subId) : subs;
    const seen = {};
    const out = [];
    pick.forEach((s) => (s.researchers || []).forEach((r) => {
      const prev = seen[r.oa_id];
      if (prev) { prev.works = Math.max(prev.works, r.works); return; }
      const p = { key: 'oa:' + r.oa_id, oa_id: r.oa_id, name: r.name, eng: '', aff: uniKo(r.inst), inst: r.inst, works: r.works, works_label: '3년 논문', field: s.ko || s.en, sub: s.id, yon: isYonsei(r.inst) };
      seen[r.oa_id] = p; out.push(p); searchPool[p.key] = p;
    }));
    return out.sort((a, b) => b.works - a.works);
  }
  function renderFields() {
    const body = $('.field-body');
    if (!FS || !FS.fields || !FS.fields.length) {
      body.innerHTML = `<div class="empty-note">분야 데이터를 아직 불러오지 못했어요. 이름 검색과 학과 둘러보기는 그대로 쓸 수 있어요.</div>`;
      stopSky();
      return;
    }
    const f = curField();
    const chip = (x, on) => `<button class="chip ${on ? 'on' : ''}" type="button" data-field="${esc(x.id)}">${esc(x.ko || x.en)}<em>${fmtGrowth(x.growth)}</em></button>`;
    let chips = featured.map((id) => chip(fieldsById[id], id === UI.field)).join('');
    if (!featured.includes(UI.field)) chips += chip(f, true);
    chips += `<button class="chip more" type="button" data-act="all">${UI.showAll ? '접기' : `더보기 (${FS.fields.length}개 분야)`}</button>`;
    let all = '';
    if (UI.showAll) {
      const groups = {};
      FS.fields.forEach((x) => (groups[x.domain || '기타'] = groups[x.domain || '기타'] || []).push(x));
      all = `<div class="allfields">` + Object.keys(groups).map((g) => `<div><h4>${esc(g)}</h4>${groups[g].sort((a, b) => b.works - a.works).map((x) => `<button type="button" class="${x.id === UI.field ? 'on' : ''}" data-field="${esc(x.id)}"><span>${esc(x.ko || x.en)}</span><em>${fmtGrowth(x.growth)}</em></button>`).join('')}</div>`).join('') + `</div>`;
    }
    const subs = curSubs();
    const subChips = subs.length ? `<div class="chips sub"><button class="chip ${!UI.sub ? 'on' : ''}" type="button" data-sub="">${esc(f.ko || f.en)} 전체</button>${subs.map((s) => `<button class="chip ${s.id === UI.sub ? 'on' : ''}" type="button" data-sub="${esc(s.id)}">${esc(s.ko || s.en)}</button>`).join('')}</div>` : '';
    const sel = UI.sub ? subs.find((s) => s.id === UI.sub) : null;
    const title = `${esc(sel ? sel.ko || sel.en : f.ko || f.en)} 상위 연구자`;
    const [y0, y1] = FS.window || [2023, 2025];
    body.innerHTML = `<p class="basis">국내 기관 논문이 ${FS.prev ? FS.prev[0] + '~' + FS.prev[1] + '년 대비 ' : ''}${y0}~${y1}년에 많이 늘어난 분야 순</p>
      <div class="chips">${chips}</div>${all}${subChips}
      <div class="sky"><div class="canvasbox"><canvas></canvas><div class="legend"><span><i style="background:var(--A)"></i>연세대</span><span><i style="background:#9AA5B3"></i>다른 국내 기관</span></div></div>
      <div class="rank"><h3>${title}</h3><p class="cap">국내 기관 전체, ${y0}~${y1}년 논문 수 기준</p><div class="rank-list"></div><div class="src">출처: OpenAlex (${esc(FS.generated || '')} 집계)</div></div></div>`;
    renderRank();
    startSky();
  }
  function renderRank() {
    const box = $('.rank-list');
    if (!box) return;
    const list = researchersOf(curField(), UI.sub).slice(0, 8);
    const mx = list[0] ? list[0].works : 1;
    box.innerHTML = list.length ? list.map((p, i) => {
      const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
      return `<div class="rk"><span class="n">${i + 1}</span><div style="min-width:0"><div class="nm">${esc(p.name)}${p.yon ? '<span class="yon">연세대</span>' : ''}</div><div class="af">${esc(p.aff)}, 논문 ${p.works}편</div><div class="bar"><i style="width:${(p.works / mx) * 100}%"></i></div></div>
        <div class="mini"><button class="a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}">A</button><button class="b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}">B</button></div></div>`;
    }).join('') : `<div class="empty-note">이 분야의 연구자 데이터가 없어요.</div>`;
  }

  // ---------- 별자리 캔버스 ----------
  let sky = parentElement.__lmSky || null;
  function stopSky() { if (sky && sky.raf) cancelAnimationFrame(sky.raf); sky = null; parentElement.__lmSky = null; }
  function startSky() {
    stopSky();
    const box = $('.canvasbox');
    const cv = box.querySelector('canvas');
    const ctx = cv.getContext('2d');
    const r = box.getBoundingClientRect();
    const W = r.width || 700, H = r.height || 420, dpr = window.devicePixelRatio || 1;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const subs = curSubs().slice(0, 6);
    const centers = subs.map((s, i) => {
      if (subs.length === 1) return { x: W / 2, y: H / 2 + 10 };
      const a = (i / subs.length) * Math.PI * 2 - Math.PI / 2;
      return { x: W / 2 + Math.cos(a) * W * 0.32, y: H / 2 + 14 + Math.sin(a) * H * 0.27 };
    });
    let seed = 11; const rnd = () => ((seed = (seed * 9301 + 49297) % 233280), seed / 233280);
    const nodes = [];
    subs.forEach((s, ci) => {
      const list = researchersOf(curField(), s.id).slice(0, 14);
      const mx = list[0] ? list[0].works : 1;
      list.forEach((p) => {
        const a = rnd() * Math.PI * 2, d = 12 + rnd() * Math.min(W, H) * 0.12;
        nodes.push({ p, ci, x: centers[ci].x + Math.cos(a) * d, y: centers[ci].y + Math.sin(a) * d, r: 3 + (p.works / mx) * 6 });
      });
    });
    sky = { nodes, hover: null, raf: 0 };
    parentElement.__lmSky = sky;
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const draw = (t) => {
      ctx.clearRect(0, 0, W, H);
      const act = (n) => !UI.sub || subs[n.ci].id === UI.sub;
      nodes.forEach((a, i) => nodes.forEach((b, j) => {
        if (j <= i || a.ci !== b.ci) return;
        if (Math.hypot(a.x - b.x, a.y - b.y) < 62) { ctx.strokeStyle = act(a) ? 'rgba(61,90,128,.22)' : 'rgba(150,160,175,.12)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
      }));
      nodes.forEach((n) => {
        const on = act(n), tw = on && !reduce ? 1 + Math.sin(t / 600 + n.x) * 0.08 : 1;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r * tw, 0, Math.PI * 2);
        ctx.fillStyle = n.p.yon ? (on ? '#3D5A80' : 'rgba(61,90,128,.35)') : (on ? '#7D8898' : 'rgba(154,165,179,.35)');
        ctx.fill();
        const isA = sameP(slots.A, n.p), isB = sameP(slots.B, n.p);
        if (isA || isB || sky.hover === n) { ctx.lineWidth = 2; ctx.strokeStyle = isB ? '#5E8C83' : '#1C2430'; ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 4, 0, Math.PI * 2); ctx.stroke(); }
      });
      ctx.font = '600 13px "IBM Plex Sans KR", sans-serif'; ctx.textAlign = 'center';
      subs.forEach((s, i) => { ctx.fillStyle = !UI.sub || s.id === UI.sub ? '#1C2430' : '#98A2B0'; ctx.fillText(s.ko || s.en, centers[i].x, Math.max(18, centers[i].y - Math.min(W, H) * 0.15 - 8)); });
      if (!reduce && sky) sky.raf = requestAnimationFrame(draw);
    };
    sky.raf = requestAnimationFrame(draw);
    let tip = null;
    const showTip = (n) => {
      if (tip) tip.remove(); tip = null;
      if (!n) return;
      tip = document.createElement('div'); tip.className = 'tip';
      const x = n.x > W / 2 ? Math.max(8, n.x - 222) : Math.min(n.x + 16, W - 218);
      const y = Math.min(Math.max(n.y - 40, 8), H - 140);
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
      tip.innerHTML = `<b>${esc(n.p.name)}</b>${n.p.yon ? ' <span style="font-size:11px;color:var(--A)">연세대</span>' : ''}<div class="af">${esc(n.p.aff)}</div><div class="af">${esc(n.p.field)}, 최근 3년 논문 ${n.p.works}편</div>
        <div class="acts"><button class="add a" type="button" data-add="A" data-key="${esc(n.p.key)}">A에 담기</button><button class="add b" type="button" data-add="B" data-key="${esc(n.p.key)}">B에 담기</button></div>`;
      box.appendChild(tip);
    };
    cv.onpointermove = (e) => {
      const rr = cv.getBoundingClientRect(), x = e.clientX - rr.left, y = e.clientY - rr.top;
      const h = nodes.find((n) => Math.hypot(n.x - x, n.y - y) < n.r + 5) || null;
      if (h !== sky.hover) { sky.hover = h; cv.style.cursor = h ? 'pointer' : 'default'; if (reduce) draw(0); }
    };
    cv.onclick = () => showTip(sky && sky.hover);
  }

  // ---------- 전체 그리기 ----------
  function renderModes() { $$('.mode').forEach((b) => b.classList.toggle('on', b.dataset.mode === UI.mode)); }
  function renderAll() {
    renderModes(); renderSlots(); renderDrop(); renderDept();
    if (FS) { renderRank(); } else renderFields();
    $('.scrim').hidden = !UI.help;
  }

  // 예시 비교: 문헌정보학과 송민 vs 이지연 (없으면 교수님이 두 분 이상인 첫 학과)
  const pref = ['송민', '이지연'].map((n) => YON.find((y) => y.name === n)).filter(Boolean);
  const sampleDept = pref.length === 2 ? pref[0].dept : DEPTS.find((d) => YON.filter((y) => y.dept === d).length >= 2);
  const sample = pref.length === 2 ? pref : sampleDept ? YON.filter((y) => y.dept === sampleDept).slice(0, 2) : [];
  $('.sample-label').textContent = sample.length === 2 ? `예시 비교: ${sample[0].name} vs ${sample[1].name} (${sampleDept})` : '예시 비교';

  // ---------- 이벤트 (한 번만 연결) ----------
  root.__lm = { put, doSearch, send, slots, searchPool, renderAll, renderFields, renderDept, renderDrop, sample };
  if (!root.__bound) {
    root.__bound = true;
    const S = () => root.__lm;
    const input = root.querySelector('.q');
    input.addEventListener('input', () => { UI.q = input.value; UI.drop = true; S().renderDrop(); });
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') S().doSearch(); if (e.key === 'Escape') { UI.drop = false; S().renderDrop(); } });
    input.addEventListener('focus', () => { if (UI.q) { UI.drop = true; S().renderDrop(); } });
    root.addEventListener('click', (e) => {
      const t = e.target;
      const rm = t.closest('[data-rm]');
      if (rm) { const s = S(); s.slots[rm.dataset.rm] = null; s.send({ type: 'slots', A: s.slots.A, B: s.slots.B }); s.renderAll(); return; }
      const ad = t.closest('[data-add]');
      if (ad) { const p = S().searchPool[ad.dataset.key]; if (p) { UI.drop = false; S().put(ad.dataset.add, p); } return; }
      const md = t.closest('[data-mode]');
      if (md) {
        UI.mode = md.dataset.mode;
        root.querySelectorAll('.mode').forEach((b) => b.classList.toggle('on', b.dataset.mode === UI.mode));
        if (UI.mode === 'hero') input.focus();
        else root.querySelector(UI.mode === 'dept' ? '.sec-dept' : '.sec-field').scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      const dp = t.closest('[data-dept]');
      if (dp) { UI.dept = dp.dataset.dept; UI.idx = 0; S().renderDept(); return; }
      const fc = t.closest('.fc');
      if (fc && !t.closest('button')) { UI.idx = +fc.dataset.idx; S().renderDept(); return; }
      const fd = t.closest('[data-field]');
      if (fd) { UI.field = fd.dataset.field; UI.sub = null; S().renderFields(); return; }
      const sb = t.closest('[data-sub]');
      if (sb) { UI.sub = sb.dataset.sub || null; S().renderFields(); return; }
      const act = t.closest('[data-act]');
      if (act) {
        const a = act.dataset.act;
        if (a === 'search') S().doSearch();
        else if (a === 'help') { UI.help = true; root.querySelector('.scrim').hidden = false; }
        else if (a === 'close') { UI.help = false; root.querySelector('.scrim').hidden = true; }
        else if (a === 'prev') { UI.idx = Math.max(0, UI.idx - 1); S().renderDept(); }
        else if (a === 'next') { UI.idx = UI.idx + 1; S().renderDept(); }
        else if (a === 'all') { UI.showAll = !UI.showAll; S().renderFields(); }
        else if (a === 'sample') { const s = S(); if (s.sample.length === 2) { s.slots.A = s.sample[0]; s.put('B', s.sample[1]); } }
        else if (a === 'compare') { const s = S(); if (s.slots.A && s.slots.B) s.send({ type: 'compare', A: s.slots.A, B: s.slots.B }); }
        return;
      }
      if (t.classList && t.classList.contains('scrim')) { UI.help = false; t.hidden = true; return; }
      if (!t.closest('.searchbox')) { UI.drop = false; S().renderDrop(); }
    });
    root.addEventListener('pointermove', (e) => {
      const el = e.target.closest && e.target.closest('.pc.filled');
      if (!el) return;
      const r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.style.transform = `rotateY(${(x - 0.5) * 14}deg) rotateX(${(0.5 - y) * 12}deg)`;
      el.style.setProperty('--mx', x * 100 + '%'); el.style.setProperty('--my', y * 100 + '%');
    });
    root.addEventListener('pointerout', (e) => { const el = e.target.closest && e.target.closest('.pc'); if (el && !el.contains(e.relatedTarget)) el.style.transform = ''; });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && UI.help) { UI.help = false; root.querySelector('.scrim').hidden = true; } });
  }

  // 처음 그리기 (데이터가 바뀔 때마다 다시 호출됨)
  const input = $('.q');
  if (input.value !== UI.q) input.value = UI.q;
  renderModes(); renderSlots(); renderDrop(); renderDept(); renderFields();
  $('.scrim').hidden = !UI.help;
  return () => stopSky();
}
