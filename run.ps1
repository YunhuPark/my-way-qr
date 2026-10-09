# 실행: .\run.ps1
# 처음이면 먼저: python -m pip install --target .\libs -r requirements.txt
# AI 기능: 이 폴더에 .env 파일을 만들고 ANTHROPIC_API_KEY=... 를 직접 적으세요. (없어도 사전/규칙 모드로 동작)
$env:PYTHONPATH = Join-Path $PSScriptRoot "libs"
python -B -m uvicorn app.main:app --host 0.0.0.0 --port 8765
