FROM python:3.12-slim

# uv 바이너리 복사 (Rust 기반 빠른 패키지 관리자)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Phase 8: OCR 엔진(Tesseract) + 한글/영어 글자 데이터 설치
# opencv-python-headless는 GUI 라이브러리가 불필요하므로 추가 시스템 패키지 없이 동작
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# 고정된 의존성 명세만 먼저 복사 → Docker 레이어 캐시 활용
# requirements.txt가 버전 고정의 원본(source of truth). 업데이트는 uv pip compile 등으로 재생성.
COPY requirements.txt /app/

# 컨테이너 내부에서는 venv 격리가 불필요하므로 시스템 Python에 직접 설치
RUN uv pip install --system --no-cache -r requirements.txt

# 소스 복사 (개발 시에는 compose의 bind mount가 이 위를 덮어씀)
COPY . /app

EXPOSE 8000

ENTRYPOINT ["bash", "/app/scripts/entrypoint.sh"]
