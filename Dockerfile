FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 호스팅 서비스가 PORT를 주입한다 (없으면 8765). 프록시 뒤의 https 주소·클라이언트 IP를 읽도록 헤더 신뢰 설정.
ENV PORT=8765
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
