# 내 방식 QR (AI 라이프 솔루션 챌린지 출품용 프로토타입)

화면 선호(글자 크기·쉬운 말·고대비·음성·한 단계씩·시간 연장)를 QR에 담아, 모의 키오스크가 그 방식으로 바뀌는 웹 서비스.
QR/URL에는 **선호 설정만** 들어가며 장애 유형 등 민감정보는 저장·전송하지 않는다.

## 실행
```powershell
python -m pip install --target .\libs -r requirements.txt   # 처음 한 번
.\run.ps1                                                   # http://localhost:8765
```
- 휴대폰으로 QR을 찍어 보려면 PC와 같은 Wi-Fi여야 한다 (QR에는 PC의 LAN 주소가 들어간다).
- AI 기능: 이 폴더에 `.env`를 만들고 `ANTHROPIC_API_KEY=...`를 적는다. 없으면 규칙/사전 모드로 동작한다.

## 사용 방법
- 사용·테스트 진행 방법: [docs/usage-guide.md](docs/usage-guide.md)
- 배포 방법: [DEPLOY.md](DEPLOY.md)

## 구조
- `app/main.py` — FastAPI. `/api/profile/parse`(말 → 설정), `/api/rewrite`(쉬운 말 변환), `/api/qr`, `/api/base`
- `app/scenarios.json` — 키오스크 시나리오(카페·민원·병원)와 쉬운 말 사전 작성본
- `app/static/index.html` — 프로필 생성기 + QR / `kiosk.html` — 모의 키오스크

## 다음 할 일
- [ ] 사용자 테스트(고령자 3~5명, 기본 화면 vs 내 방식 화면 과업 완료 시간 비교) — 성과보고서 근거
- [ ] 시연 영상 1~2분 (비포/애프터)
- [ ] 무료 호스팅 배포(공개 URL)
- [ ] 성과보고서·참가신청서 서식 확인 후 작성, 10/30까지 relations2@keit.re.kr 제출
