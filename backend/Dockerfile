FROM python:3.12-slim

# uv 바이너리 복사 (Rust 기반 빠른 패키지 관리자)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 의존성 명세만 먼저 복사 → Docker 레이어 캐시 활용
COPY pyproject.toml /app/

# 컨테이너 내부에서는 venv 격리가 불필요하므로 시스템 Python에 직접 설치
RUN uv pip install --system --no-cache -r pyproject.toml

# 소스 복사 (개발 시에는 compose의 bind mount가 이 위를 덮어씀)
COPY . /app

EXPOSE 8000

ENTRYPOINT ["bash", "/app/scripts/entrypoint.sh"]
