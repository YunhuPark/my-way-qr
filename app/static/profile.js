// 프로필 = 화면 선호 설정만 담는다 (장애 유형 등 민감정보 없음)
// fs: 글자 배율, ez: 쉬운 말, hc: 고대비, vo: 음성 안내, st: 한 번에 한 단계, tm: 제한 시간 연장
const DEFAULT_PROFILE = { fs: 1.0, ez: false, hc: false, vo: false, st: false, tm: false };

function encodeProfile(p) {
  return btoa(JSON.stringify(p)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeProfile(s) {
  if (!s) return null;
  try {
    const raw = JSON.parse(atob(s.replace(/-/g, "+").replace(/_/g, "/")));
    const p = { ...DEFAULT_PROFILE };
    if ([1.0, 1.4, 1.8, 2.2].includes(raw.fs)) p.fs = raw.fs;
    for (const k of ["ez", "hc", "vo", "st", "tm"]) p[k] = raw[k] === true;
    return p;
  } catch {
    return null;
  }
}

// 짧은 DOM 헬퍼
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid);
  return el;
}
