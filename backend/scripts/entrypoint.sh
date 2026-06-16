#!/usr/bin/env bash
set -euo pipefail

# DB 마이그레이션 적용 (이미 최신이면 아무것도 하지 않음)
alembic upgrade head

# 개발 서버: --reload 로 코드 변경 자동 반영 (bind mount 와 함께 동작)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
