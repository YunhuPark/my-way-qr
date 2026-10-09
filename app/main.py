"""내 방식 QR - 범용 접근성 프로필 패스 (시연용 서버)

프로필은 QR/URL에 담기는 '선호 설정'뿐이며 장애 유형 등 민감정보는 저장·전송하지 않는다.
ANTHROPIC_API_KEY가 없으면 사전 작성본/키워드 규칙으로 동작한다.
"""
import io
import json
import os
import re
import socket
import sys
import time
from collections import defaultdict, deque
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent  # 라이브러리는 run.ps1이 PYTHONPATH(.\libs)로 지정한다

import qrcode
import qrcode.image.svg
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(ROOT.parent / ".env")

MODEL = "claude-haiku-4-5-20251001"
FONT_SCALES = (1.0, 1.4, 1.8, 2.2)
DEFAULT_PROFILE = {"fs": 1.0, "ez": False, "hc": False, "vo": False, "st": False, "tm": False}

app = FastAPI(title="내 방식 QR")

_scenarios = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))


def _build_easy_map() -> dict[str, str]:
    """시연 시나리오의 사전 작성본(원문 -> 쉬운 말). AI를 쓸 수 없을 때의 대체."""
    pairs: list[dict] = list(_scenarios["ui"].values())
    for sc in _scenarios["scenarios"].values():
        pairs.append(sc["final"])
        for step in sc["steps"]:
            pairs.append(step["q"])
            pairs.extend(step["opts"])
    return {p["t"]: p["e"] for p in pairs}


EASY_MAP = _build_easy_map()
GLOSSARY = [
    ("하십시오", "하세요"), ("하여 주십시오", "해 주세요"), ("수령", "받기"), ("제시", "보여주기"),
    ("결제", "돈 내기"), ("발급", "서류 받기"), ("인식", "읽히기"), ("열람", "보기"),
    ("선택", "고르기"), ("확인", "확인"), ("완료", "끝남"), ("대기", "기다림"),
]
_ai_cache: dict[str, str] = {}
_client = None


def _get_client():
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        import anthropic
        _client = anthropic.Anthropic()
    return _client


# 공개 배포 시 API 비용·남용 방지: IP별 분당 호출 수와 하루 전체 호출 수를 제한한다.
# 한도를 넘으면 AI 대신 규칙/사전 모드로 자동 전환된다.
AI_PER_MIN = int(os.environ.get("AI_PER_MIN", "20"))
AI_DAILY_CAP = int(os.environ.get("AI_DAILY_CAP", "500"))
_hits: dict[str, deque] = defaultdict(deque)
_daily = {"day": "", "n": 0}


def _ai_allowed(ip: str) -> bool:
    now = time.monotonic()
    today = date.today().isoformat()
    if _daily["day"] != today:  # 날짜가 바뀌면 하루 카운터를 초기화하고 오래된 IP 기록을 정리
        _daily.update(day=today, n=0)
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
            del _hits[k]
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= AI_PER_MIN or _daily["n"] >= AI_DAILY_CAP:
        return False
    q.append(now)
    _daily["n"] += 1
    return True


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _ask(system: str, user: str, max_tokens: int, ip: str = "unknown") -> str | None:
    client = _get_client()
    if client is None or not _ai_allowed(ip):
        return None
    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    except Exception as exc:  # 네트워크/키 오류 시 대체 경로로
        print(f"[ai] 호출 실패: {exc}", file=sys.stderr)
        return None


def _clean_profile(raw: dict) -> dict:
    p = dict(DEFAULT_PROFILE)
    try:
        fs = float(raw.get("fs", 1.0))
        p["fs"] = min(FONT_SCALES, key=lambda s: abs(s - fs))
    except (TypeError, ValueError):
        pass
    for k in ("ez", "hc", "vo", "st", "tm"):
        p[k] = bool(raw.get(k, False))
    return p


def _rule_profile(text: str) -> dict:
    p = dict(DEFAULT_PROFILE)
    if re.search(r"가장 크|제일 크|아주 크|매우 크|엄청 크", text):
        p["fs"] = 2.2
    elif re.search(r"크게|큰 ?글|큰 ?글씨|잘 ?안 ?보", text):
        p["fs"] = 1.8
    if re.search(r"쉬운|쉽게|어려운 ?말|한자", text):
        p["ez"] = True
    if re.search(r"대비|선명|눈이 ?나|시력|잘 ?안 ?보", text):
        p["hc"] = True
    if re.search(r"음성|읽어|소리|들려", text):
        p["vo"] = True
    if re.search(r"한 ?번에 ?하나|단계|복잡|하나씩", text):
        p["st"] = True
    if re.search(r"천천히|시간|느리|느려|급하", text):
        p["tm"] = True
        p["st"] = True
    return p


class ParseIn(BaseModel):
    text: str


class RewriteIn(BaseModel):
    texts: list[str]


@app.post("/api/profile/parse")
def parse_profile(body: ParseIn, request: Request):
    text = body.text.strip()[:500]
    system = (
        "사용자가 키오스크 사용 시 원하는 화면 방식을 말로 설명한다. 아래 JSON 객체만 출력하라(설명 금지).\n"
        '{"fs": 1.0|1.4|1.8|2.2 (글자 크기 배율), "ez": 쉬운 말 사용 여부, "hc": 고대비 여부, '
        '"vo": 음성 안내 여부, "st": 한 번에 한 단계씩 보여주기 여부, "tm": 제한 시간 연장 여부}\n'
        "사용자가 언급하지 않은 항목은 기본값(fs 1.0, 나머지 false)으로 둔다. 건강/장애 상태를 추측하지 말고 "
        "요청한 화면 선호만 반영한다."
    )
    out = _ask(system, text, 200, _client_ip(request)) if text else None
    if out:
        m = re.search(r"\{.*\}", out, re.S)
        if m:
            try:
                return {"profile": _clean_profile(json.loads(m.group())), "source": "ai"}
            except json.JSONDecodeError:
                pass
    return {"profile": _rule_profile(text), "source": "rule"}


@app.post("/api/rewrite")
def rewrite(body: RewriteIn, request: Request):
    texts = [t[:300] for t in body.texts[:60]]
    results: dict[str, str] = {}
    todo = []
    for t in texts:
        if t in _ai_cache:
            results[t] = _ai_cache[t]
        else:
            todo.append(t)

    source = "cache" if texts and not todo else "dict"
    if todo:
        system = (
            "너는 키오스크 문구를 고령자와 인지 약자도 바로 이해하는 쉬운 우리말로 바꾸는 편집자다. "
            "뜻은 유지하고, 문장은 짧게, 한자어·외래어·관공서 말투는 일상어로 바꾸고 '~하세요' 체를 쓴다. "
            "입력은 JSON 문자열 배열이다. 같은 길이의 JSON 문자열 배열만 출력하라."
        )
        out = _ask(system, json.dumps(todo, ensure_ascii=False), 1500, _client_ip(request))
        ai_list = None
        if out:
            m = re.search(r"\[.*\]", out, re.S)
            if m:
                try:
                    cand = json.loads(m.group())
                    if isinstance(cand, list) and len(cand) == len(todo) and all(isinstance(x, str) for x in cand):
                        ai_list = cand
                except json.JSONDecodeError:
                    pass
        if ai_list:
            source = "ai"
            for t, e in zip(todo, ai_list):
                results[t] = _ai_cache[t] = e
        else:
            for t in todo:
                if t in EASY_MAP:
                    results[t] = EASY_MAP[t]
                else:
                    e = t
                    for a, b in GLOSSARY:
                        e = e.replace(a, b)
                    results[t] = e
    return {"results": results, "source": source}


@app.get("/api/base")
def base_url(request: Request):
    """휴대폰이 QR로 접속할 수 있는 주소.
    로컬(localhost)이면 PC의 LAN IP로 바꾸고, 배포 환경에서는 프록시가 알려준 https 주소를 그대로 쓴다."""
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    hostport = request.headers.get("host") or "localhost"
    host, _, port = hostport.partition(":")
    if host in ("localhost", "127.0.0.1", "::1"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            host = s.getsockname()[0]
            s.close()
        except OSError:
            pass
    return {"base": f"{scheme}://{host}" + (f":{port}" if port else "")}


@app.get("/healthz")
def healthz():
    return {"ok": True, "ai": _get_client() is not None}


@app.get("/api/qr")
def qr(url: str = Query(max_length=1000)):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    return Response(buf.getvalue(), media_type="image/svg+xml")


@app.get("/api/scenarios")
def scenarios():
    return _scenarios


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/", StaticFiles(directory=ROOT / "static"), name="static")
