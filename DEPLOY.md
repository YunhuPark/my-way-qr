# 공개 URL 배포 안내

목표: 심사위원·투표자가 **https 주소 하나**로 접속하게 한다. 휴대폰으로 QR을 찍어도 열린다.

## 호스팅 선택
| 후보 | 장점 | 주의 |
|---|---|---|
| **Render (Web Service, 무료)** | GitHub 저장소 연결만으로 배포, Dockerfile 자동 인식, https 기본 | 무료 플랜은 15분 무접속 시 잠들고, 다시 깨어날 때 **30~60초 지연** |
| Hugging Face Spaces (Docker) | 무료, 카드 불필요 | Dockerfile의 포트를 7860으로 맞춰야 함 (`PORT` 환경변수) |
| Fly.io / Railway | 안 잠들게 설정 가능 | 대체로 카드 등록 필요, 요금 확인 |

> 이 문서의 절차는 Render 기준이다. 서비스 약관·요금·플랜 조건은 바뀔 수 있으니 가입 화면에서 직접 확인할 것.

## 배포 전 확인 (이미 해 둔 것)
- `requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore` 준비됨 (`.env`, `libs/`, `forms/`는 올라가지 않음)
- 프록시 뒤에서도 QR에 **https 주소**가 들어가도록 처리됨 (`/api/base`)
- `/healthz` 상태 확인용 주소
- AI 호출은 IP당 분당 20회, 하루 전체 500회로 제한되고, 넘으면 규칙/사전 모드로 자동 전환 (`AI_PER_MIN`, `AI_DAILY_CAP` 환경변수로 조정)
- 프로필 생성기 화면에 "입력 문장이 외부 AI 서비스로 전송될 수 있다"는 고지 추가

## Render 배포 절차
1. **GitHub 저장소 만들기** (비공개 권장) 후 이 폴더를 올린다.
   ```bash
   git init
   git add .
   git status        # .env, libs/, forms/ 가 목록에 없는지 반드시 확인
   git commit -m "내 방식 QR 프로토타입"
   git remote add origin <본인 저장소 주소>
   git push -u origin main
   ```
2. Render 대시보드 → **New → Web Service** → 위 저장소 선택.
3. Language/Runtime은 **Docker**(Dockerfile 자동 인식). 플랜은 Free.
4. **Environment** 에 아래 값을 추가한다.
   - `ANTHROPIC_API_KEY` = 본인 API 키 (**비밀값: 코드·저장소·채팅에 붙여넣지 말고 이 칸에만 입력**)
   - (선택) `AI_PER_MIN`=20, `AI_DAILY_CAP`=500
5. **Health Check Path** 를 `/healthz` 로 지정하고 배포한다.
6. 배포가 끝나면 `https://<서비스명>.onrender.com` 이 공개 주소다.

## 배포 후 점검 (순서대로)
1. `https://<주소>/healthz` → `{"ok":true,"ai":true}` 이면 키가 연결된 것 (`ai:false`면 키 미설정)
2. `https://<주소>/` 에서 프로필 생성기 열기 → 말로 입력 → "AI가 설정했어요" 배지 확인 (규칙 모드면 "AI 키 없음")
3. QR을 **휴대폰으로 직접 찍어** 키오스크 화면이 열리는지 확인 (주소가 https인지)
4. 키오스크에서 쉬운 말 변환이 AI로 되는지 확인 (하단에 "AI가 쉬운 말로 바꿨어요")

## 운영 주의
- **무료 플랜은 잠든다.** 시연 10분 전에 주소를 한 번 열어 깨워 둔다. 심사 기간(11월)에도 처음 접속이 느릴 수 있음을 보고서·안내에 감안.
- **API 비용:** 공개 주소는 누구나 쓸 수 있다. 위 한도가 비용 상한을 막아 주지만, 사용량 한도와 요금 알림은 Anthropic 콘솔에서 따로 설정하는 것을 권한다.
- **개인정보:** 서버는 프로필·입력 문장을 저장하지 않지만, 호스팅 서비스의 접속 로그에는 주소가 남는다. 프로필 주소(`?p=`)에는 선호 설정만 들어 있다.
- 키가 노출됐다고 의심되면 콘솔에서 즉시 폐기하고 새로 발급한다.
- 대회 종료 후 서비스를 내리거나 키를 폐기할지 정해 둔다.
