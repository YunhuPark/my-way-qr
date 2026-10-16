"""사용자 테스트 CSV 분석 (표준 라이브러리만 사용)

사용:  python tools/analyze.py 참가자1.csv 참가자2.csv ...   (또는 한 파일에 모두 합쳐도 됨)
- 같은 기록(참가자·과업·화면·시작 시각이 같은 줄)이 여러 CSV에 겹쳐 있으면 한 번만 센다.
- 결과는 사람 수·횟수 그대로 보여 준다. 표본이 작으므로 통계적 유의성(p값)은 계산하지 않는다.
- 리허설/파일럿 기록을 빼려면 --exclude P0 처럼 참가자 코드를 지정한다.
"""
import argparse
import csv
import statistics as st
import sys
from collections import defaultdict

SCEN = {"cafe": "카페 주문", "civil": "민원서류 발급", "hospital": "병원 접수"}
MODE = {"plain": "기본 화면", "mine": "내 방식 화면"}
RES = {"success": "성공", "assisted": "도움받음", "failed": "실패"}


def load(paths, exclude):
    seen, rows = set(), []
    for p in paths:
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                key = (r["pid"], r["scenario"], r["mode"], r["start"])
                if key in seen or r["pid"] in exclude:
                    continue
                seen.add(key)
                r["duration_sec"] = float(r["duration_sec"])
                for k in ("wrong", "backs", "timeouts", "helps"):
                    r[k] = int(r[k])
                rows.append(r)
    return rows


def med(xs):
    return f"{st.median(xs):.1f}" if xs else "-"


def summarize(rows):
    out = ["## 조건별 요약", "",
           "| 화면 | 시행 수 | 도움 없이 성공 | 도움받음 | 실패 | 완료 시간 중앙값(초) | 시간 초과 없는 시행의 중앙값(초) | 오선택 합계 | 뒤로 합계 | 시간 초과 합계 | 도움 요청 합계 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in ("plain", "mine"):
        rs = [r for r in rows if r["mode"] == m]
        if not rs:
            continue
        n = len(rs)
        cnt = {k: sum(1 for r in rs if r["result"] == k) for k in RES}
        done = [r["duration_sec"] for r in rs if r["result"] != "failed"]
        clean = [r["duration_sec"] for r in rs if r["result"] != "failed" and r["timeouts"] == 0]
        out.append(f"| {MODE[m]} | {n} | {cnt['success']}/{n} | {cnt['assisted']} | {cnt['failed']} | {med(done)} | {med(clean)} | "
                   f"{sum(r['wrong'] for r in rs)} | {sum(r['backs'] for r in rs)} | {sum(r['timeouts'] for r in rs)} | {sum(r['helps'] for r in rs)} |")
    return out


def by_scenario(rows):
    out = ["", "## 과업 × 화면 (도움 없이 성공 / 시행 수)", "", "| 과업 | 기본 화면 | 내 방식 화면 |", "|---|---|---|"]
    for s in SCEN:
        cells = []
        for m in ("plain", "mine"):
            rs = [r for r in rows if r["scenario"] == s and r["mode"] == m]
            cells.append(f"{sum(1 for r in rs if r['result'] == 'success')}/{len(rs)}" if rs else "-")
        out.append(f"| {SCEN[s]} | {cells[0]} | {cells[1]} |")
    return out


def per_person(rows):
    out = ["", "## 참가자별 (개별 값 공개용)", "",
           "| 참가자 | 순서 | 과업 | 화면 | 시간(초) | 결과 | 오선택 | 뒤로 | 시간 초과 | 도움 |", "|---|---|---|---|---|---|---|---|---|---|"]
    byp = defaultdict(list)
    for r in rows:
        byp[r["pid"]].append(r)
    for pid in sorted(byp):
        for i, r in enumerate(sorted(byp[pid], key=lambda x: x["start"]), 1):
            out.append(f"| {pid} | {i} | {SCEN.get(r['scenario'], r['scenario'])} | {MODE.get(r['mode'], r['mode'])} | "
                       f"{r['duration_sec']:.1f} | {RES.get(r['result'], r['result'])} | {r['wrong']} | {r['backs']} | {r['timeouts']} | {r['helps']} |")
    return out


def checks(rows):
    out = ["", "## 데이터 점검 (분석 전에 확인)", ""]
    byp = defaultdict(list)
    for r in rows:
        byp[r["pid"]].append(r)
    problems = []
    for pid, rs in sorted(byp.items()):
        modes = sorted(r["mode"] for r in rs)
        if len(rs) != 2 or modes != ["mine", "plain"]:
            problems.append(f"- {pid}: 시행 {len(rs)}건, 화면 구성 {modes} (한 사람이 기본 1건 + 내 방식 1건이어야 함)")
        if len({r["scenario"] for r in rs}) != len(rs):
            problems.append(f"- {pid}: 같은 과업을 두 번 함")
    out += problems or ["- 참가자마다 기본 화면 1건 + 내 방식 화면 1건, 서로 다른 과업입니다. 이상 없음."]
    out.append(f"- 참가자 {len(byp)}명, 시행 {len(rows)}건")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--exclude", nargs="*", default=[], help="분석에서 뺄 참가자 코드 (예: DEV P0)")
    a = ap.parse_args()
    rows = load(a.csv, set(a.exclude))
    if not rows:
        sys.exit("분석할 기록이 없습니다.")
    print("\n".join(checks(rows) + [""] + summarize(rows) + by_scenario(rows) + per_person(rows)))
    print("\n※ 표본이 작아 통계적 유의성은 주장하지 않는다. 사람 수·횟수와 개별 값을 그대로 보고한다.")


if __name__ == "__main__":
    main()
